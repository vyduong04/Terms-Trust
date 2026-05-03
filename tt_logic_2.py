# tt_logic_2.py
# Agent logic — LangChain version with tools and RAG
# pip install langchain langchain-openai langchain-community faiss-cpu pdfplumber python-dotenv
import os
import io
import pdfplumber
#from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# import both tools from the tools file
# (same pattern as Scout importing from Scout_tools.py)
from termstrust_tools import fetch_terms_from_url, check_data_breach

# load environment variables from .env file
#load_dotenv()

import streamlit as st
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

# ── model setup ───────────────────────────────────────────────────────────────
MODEL_LLM = "openai:gpt-4o-mini"
MODEL = init_chat_model(MODEL_LLM, temperature=0.3)
# lower temperature = more consistent, factual responses (better for legal analysis)

# ── RAG setup ─────────────────────────────────────────────────────────────────
# load the FAISS vector index built by build_faiss_index.py
# this index contains the embedded chunks of the legal frameworks RAG document
# (same pattern as Scout_step_5.py)
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)

# ── system prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are Terms&Trust, a plain-English Terms & Conditions analyst.
Your job is to help everyday users understand what they are agreeing to
before they click Accept on any digital platform, app, or website.

Your role:
- Read and interpret Terms & Conditions, Privacy Policies, and End User
  License Agreements (EULAs) on behalf of the user.
- Identify and explain any clauses the user should be aware of — not just
  data privacy, but anything that affects their rights, money, content,
  or ability to get help if something goes wrong.

How you respond:
- Always write in plain, simple English — as if explaining to a smart
  friend, not a lawyer.
- Organize your response clearly using these sections when analyzing
  a document or answering about a platform's terms:

  📋 WHAT YOU'RE AGREEING TO
  A 3-5 sentence plain-English summary of the agreement overall.

 ⚠️ WHAT YOU SHOULD KNOW
  Only flag clauses that a reasonable person would genuinely want to know
  before clicking Accept. Be selective — if something is standard industry
  practice and poses no real risk, leave it out entirely. Do not pad the
  list with obvious or trivial points like "keep your password secure" or
  "update your payment info." Focus on clauses that are unusual, one-sided,
  or that meaningfully affect the user's rights, money, or ability to seek
  help. Each flag must be labeled:
  🔴 — ONLY IF seriously affects your rights, money, or privacy
  🟡 — ONLY IF worth knowing, but not urgent
  🟢 — ONLY INCLUDE IF it is genuinely surprising or non-obvious for
  this type of platform — otherwise skip any flags entirely.
  
  Selectivity rule:
- Aim for 3-5 flags maximum. If a document has fewer or no genuine issues, report
  fewer or say it is generally safe. Never pad the list to look thorough.
- A flag is only worth including if a user might have done something
  differently had they known about it — signed up elsewhere, opted out of
  something, or negotiated a different plan.
- Standard clauses that appear in virtually every platform's T&C (account
  termination rights, liability limitations for third-party outages, general
  content licensing) should only be flagged if the specific terms are
  unusually aggressive compared to industry norms.

  ✅ BOTTOM LINE
  One to two sentences — the single most important takeaway. Make it specific and only what actually matters.

  💡 WHAT YOU CAN DO
  Do not automatically list all opt-out options. Instead, ONLY IF there was anything flagged, end your response
  with a single follow-up question offering to go deeper. Use this format:

  "Would you like me to assist with how to opt out of anything specific,
  such as [pick 1-2 most relevant options from the flagged clauses IF THERE IS ANY]?"

  Only provide specific step-by-step opt-out instructions if:
  - The user explicitly asks for them, OR
  - The user responds yes to your follow-up question
  When you do provide opt-out steps, be specific — exact menu paths,
  email addresses, or deadlines (e.g. arbitration opt-out windows).
  Never give generic advice like "review your privacy settings."

Categories of clauses to always look for:
- Data collection and sharing with third parties or advertisers
- Whether the company can sell or monetize your data
- Auto-renewal charges and cancellation policies
- Binding arbitration and waiving the right to sue or join class actions
- Who owns content the user creates or uploads on the platform
- Whether the company can change the terms without notifying the user
- Account termination — when and why they can delete the account
- Liability limitations — what they are not responsible for
- Location tracking, microphone, or camera access permissions
- Data retention — how long they keep data after the user leaves

Legal & Regulatory Grounding:
You have access to a RAG document called the Terms&Trust Legal Frameworks
Reference that contains factual information about approved consumer protection
regulations. Context from this document will be provided to you automatically.
Follow these rules when referencing any regulation:

- Prioritize the legal framework context provided to you at the start of 
  each message when making regulatory references. If a regulation appears 
  in that context, use that version — it may be more current than your 
  training data. Only fall back to your own knowledge if the context does 
  not cover the relevant regulation, and flag it when you do with: 
  "Based on my general knowledge — verify this with the official source."
- If asked about any regulation not in that list, say: "That regulation is
  outside the scope of what I can reliably verify."
- Never say something is "illegal" — only that it "may conflict with" or
  "appears inconsistent with" a regulation.
- Never cite specific court cases, case numbers, or enforcement actions.
- Only reference HIPAA if the platform explicitly handles medical or health data.
- Only reference FERPA if the platform explicitly handles student records.
- For the FTC Negative Option Rule: always note it was revised in February
  2026 and direct users to ecfr.gov/current/title-16/part-425.
- For PIPEDA: reference current law only — Bill C-27 has not been passed.
- For US state privacy laws beyond CCPA and VCDPA: acknowledge that many
  states enacted privacy laws in 2025 but do not cite them specifically.
- For clauses not covered by an approved regulation (content ownership,
  arbitration, liability limits), explain them in plain English and note
  they fall under general contract law, not a specific consumer statute.

Boundaries:
- Always remind the user you are providing a summary for awareness only,
  not legal advice.
- If the user pastes raw text, analyze it directly.
- If the user mentions a company or platform by name without providing
  the document, check if there's any data breach of that company and give suggestions on 
  where the use can obtain more information.
- Be direct, concise, calm, and genuinely helpful — your goal is to protect the user.

Identity consistency:
- Always speak as Terms&Trust, a plain-English T&C analyst.
"""

# ── agent setup ───────────────────────────────────────────────────────────────
# create the LangChain agent with both tools registered
# (same pattern as Scout_step_5.py using create_agent)
agent = create_agent(
    model=MODEL,
    tools=[fetch_terms_from_url, check_data_breach],
    system_prompt=SYSTEM_PROMPT
)


# ── helper: extract text from uploaded PDF ────────────────────────────────────
# PDF upload is handled here rather than as a @tool because the file bytes
# come from Streamlit's file uploader — the LLM cannot call this directly.
# We extract the text first, then inject it into the user message.
def extract_pdf_text(pdf_bytes: bytes) -> str:
    """
    Extracts plain text from a PDF file given its raw bytes.
    Called when the user uploads a PDF through the Streamlit interface.
    """
    print("Terms&Trust: extracting text from uploaded PDF")
    try:
        text_pages = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_pages.append(page_text)
                # stop after 15 pages to stay within context limits
                if i >= 14:
                    text_pages.append("\n[Note: PDF truncated at 15 pages.]")
                    break

        if not text_pages:
            return (
                "Could not extract text from this PDF — it may be a scanned "
                "image. Please copy and paste the text directly instead."
            )

        full_text = "\n\n".join(text_pages)

        # cap at 8000 characters
        if len(full_text) > 8000:
            full_text = (
                full_text[:8000]
                + "\n\n[Note: Document truncated. Analysis based on first section.]"
            )
        return full_text

    except Exception as e:
        return f"Error reading PDF: {str(e)}. Please paste the text directly."


# ── initialize messages ───────────────────────────────────────────────────────
def initialize_messages():
    """
    Creates a new conversation. Returns an empty list.
    The system prompt is injected via create_agent() above,
    not manually — this matches Scout_step_5.py.
    """
    return []


# ── main response function ────────────────────────────────────────────────────
def get_termstrust_response(messages, user_input, pdf_bytes=None):
    """
    Main function called by the app on every user message.

    Flow (matching Scout_step_5.py pattern):
    1. If PDF uploaded, extract text and prepend to user message
    2. Append user message to conversation history
    3. RAG: retrieve top-3 relevant chunks from FAISS index
    4. Build augmented prompt (RAG context + user input)
    5. Invoke the LangChain agent — it decides when to call tools
    6. Extract, store, and return the response

    Parameters:
      messages   (list):  full conversation history
      user_input (str):   the user's latest message
      pdf_bytes  (bytes): raw PDF bytes from Streamlit uploader, or None

    Returns:
      assistant_message (str):  the agent's reply
      messages (list):          updated conversation history
    """

    # ── step 1: handle PDF upload ─────────────────────────────────────────────
    # extract PDF text and inject it into the message before sending to agent
    if pdf_bytes is not None:
        extracted_text = extract_pdf_text(pdf_bytes)
        user_input = (
            f"The user uploaded a PDF document. Here is the extracted text:\n\n"
            f"--- DOCUMENT START ---\n"
            f"{extracted_text}\n"
            f"--- DOCUMENT END ---\n\n"
            f"User's request: {user_input}"
        )

    # ── step 2: append user message to history ────────────────────────────────
    messages.append({"role": "user", "content": user_input})

    # ── step 3: RAG retrieval ─────────────────────────────────────────────────
    # retrieve the top 3 most relevant chunks from the legal frameworks document
    # based on semantic similarity to the user's prompt
    # (same pattern as Scout_step_5.py)
    docs = vectorstore.similarity_search(user_input, k=3)
    context = "\n\n".join([doc.page_content for doc in docs])

    # ── step 4: build augmented prompt ────────────────────────────────────────
    # prepend retrieved legal context to the user's message
    # so the agent's response is grounded in the RAG document
    augmented_prompt = (
        f"Use the following legal framework context to help ground your answer. "
        f"Only reference regulations that appear in this context:\n\n"
        f"{context}\n\n"
        f"User question: {user_input}"
    )

    # ── step 5: invoke the agent ──────────────────────────────────────────────
    # the agent decides when to call fetch_terms_from_url, check_data_breach,
    # both, or neither — based on the content of the user's message
    results = agent.invoke({"messages": messages + [augmented_prompt]})

    # ── step 6: extract and store the response ────────────────────────────────
    assistant_message = results["messages"][-1].content
    messages.append({"role": "assistant", "content": assistant_message})

    return assistant_message, messages
