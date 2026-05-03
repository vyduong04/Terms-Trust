# termstrust_tools.py
# All tools available to the Terms&Trust agent
# pip install langchain requests beautifulsoup4 pdfplumber

import re
import io
import requests
import pdfplumber
from bs4 import BeautifulSoup
from langchain.tools import tool


# ══════════════════════════════════════════════════════════════════════════════
# TOOL 1 — TEXT EXTRACTOR
# Fetches and extracts raw text from a Terms & Conditions URL.
# The LLM cannot browse the internet on its own — this tool does it for it.
# ══════════════════════════════════════════════════════════════════════════════

@tool
def fetch_terms_from_url(url: str) -> str:
    """
    Use this tool whenever the user provides a URL to a Terms & Conditions,
    Privacy Policy, End User License Agreement, or any other legal document page.
    This tool fetches the webpage and returns the readable plain text so it
    can be analyzed.

    Use this tool when:
    - The user shares a link starting with http:// or https://
    - The user says 'here is the link', 'check this URL', 'analyze this page'
    - The user provides any web address for a legal document

    Do NOT use this tool when:
    - The user pastes raw text directly (no URL present)
    - The user asks a general question about a company without providing a link

    Input:  a URL string (e.g. https://spotify.com/legal/end-user-agreement)
    Output: extracted plain text from the page, ready for analysis
    """
    print(f"Terms&Trust Tool 1 (URL): fetching {url}")

    try:
        # mimic a real browser so websites don't block the request
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # parse the HTML and extract only readable content
        soup = BeautifulSoup(response.text, "html.parser")

        # remove non-content elements
        for tag in soup(["script", "style", "nav", "footer",
                          "header", "aside", "noscript", "iframe"]):
            tag.decompose()

        # extract text with line breaks between elements
        text = soup.get_text(separator="\n")

        # clean up blank lines and extra whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        # cap at 8000 characters to stay within the LLM context limit
        if len(clean_text) > 8000:
            clean_text = (
                clean_text[:8000]
                + "\n\n[Note: Document truncated due to length. "
                + "Analysis is based on the first section.]"
            )

        return clean_text

    except requests.exceptions.ConnectionError:
        return (
            "Could not connect to that URL. The site may be blocking "
            "automated requests. Ask the user to copy and paste the "
            "text directly instead."
        )
    except requests.exceptions.Timeout:
        return (
            "The request timed out. Ask the user to copy and paste "
            "the text directly instead."
        )
    except requests.exceptions.HTTPError as e:
        return (
            f"The site returned an error ({e.response.status_code}). "
            "Ask the user to copy and paste the text directly instead."
        )
    except Exception as e:
        return f"Something went wrong while fetching the URL: {str(e)}"


# ══════════════════════════════════════════════════════════════════════════════
# TOOL 2 — DATA BREACH LOOKUP
# Queries the HaveIBeenPwned public API to check if a company has known
# data breaches. The LLM cannot do this reliably — its knowledge has a
# cutoff date and it may hallucinate or miss recent breaches.
# ══════════════════════════════════════════════════════════════════════════════

@tool
def check_data_breach(company_name: str) -> str:
    """
    Use this tool to check whether a company or platform has a known history
    of data breaches, using the HaveIBeenPwned public breach database.

    Use this tool when:
    - The user asks if a company has had data breaches or been hacked
    - The user is analyzing a T&C and wants to know the company's data track record
    - The user asks 'is X safe', 'has X been breached', 'what happened to X's data'
    - Any time it would be helpful to provide real breach context alongside T&C analysis

    Do NOT guess or use your training knowledge to answer breach questions —
    always use this tool so the answer is based on real, up-to-date data.

    Input:  company name as a string (e.g. "Spotify", "LinkedIn", "Adobe")
    Output: a summary of any known breaches, or a confirmation of no results found
    """
    print(f"Terms&Trust Tool 2 (Breach): checking {company_name}")

    try:
        # fetch the full public breach list from HaveIBeenPwned
        # this endpoint is free — no API key required
        response = requests.get(
            "https://haveibeenpwned.com/api/v3/breaches",
            headers={"User-Agent": "TermsTrust-ClassProject"},
            timeout=10
        )
        response.raise_for_status()
        all_breaches = response.json()

        # search by company name or domain (case-insensitive)
        matches = [
            b for b in all_breaches
            if company_name.lower() in b.get("Name", "").lower()
            or company_name.lower() in b.get("Domain", "").lower()
        ]

        if not matches:
            return (
                f"No known data breaches found for '{company_name}' in the "
                f"HaveIBeenPwned database. This does not guarantee the company "
                f"has never had a breach — only that none are publicly documented "
                f"in this database."
            )

        # format results — cap at 3 to keep response clean
        result_lines = [
            f"Found {len(matches)} known breach(es) for '{company_name}':\n"
        ]
        for b in matches[:3]:
            data_exposed = ", ".join(b.get("DataClasses", [])[:5])
            accounts = f"{b.get('PwnCount', 0):,}"
            result_lines.append(
                f"• {b.get('Name')} | "
                f"Date: {b.get('BreachDate')} | "
                f"Accounts affected: {accounts} | "
                f"Data exposed: {data_exposed}"
            )

        if len(matches) > 3:
            result_lines.append(
                f"\n...and {len(matches) - 3} more breach(es) not shown."
            )

        return "\n".join(result_lines)

    except requests.exceptions.RequestException as e:
        return (
            f"Could not reach the breach database right now: {str(e)}. "
            f"Advise the user to check haveibeenpwned.com manually."
        )
    except Exception as e:
        return f"Something went wrong during the breach lookup: {str(e)}"
