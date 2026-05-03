# app file — Terms&Trust
# pip install streamlit
import streamlit as st
from tt_logic_2 import initialize_messages, get_termstrust_response

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Terms&Trust – Know Before You Click",
    page_icon="🔍",
    layout="centered"
)

# ── custom CSS styling ────────────────────────────────────────────────────────
st.markdown("""
    <style>
        /* ── Google Fonts import ──
           Playfair Display: elegant serif for headings
           DM Sans: clean modern sans-serif for body text        */
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

        /* ── background image ──
           Uses a free Unsplash photo — dark blue abstract legal/city theme
           Falls back to deep navy gradient if image doesn't load           */
        .stApp {
            background-image:
                linear-gradient(
                    135deg,
                    rgba(5, 15, 40, 0.92) 0%,
                    rgba(8, 25, 65, 0.88) 50%,
                    rgba(5, 20, 50, 0.92) 100%
                ),
                url('https://images.unsplash.com/photo-1557804506-669a67965ba0?w=1920&q=80');
            background-size: cover;
            background-position: center center;
            background-attachment: fixed;
            background-repeat: no-repeat;
        }

        /* ── apply DM Sans globally ── */
        html, body, [class*="css"], p, li, span, div {
            font-family: 'DM Sans', sans-serif !important;
            color: #dce8ff;
        }

        /* ── sidebar ── */
        [data-testid="stSidebar"] {
            background: rgba(5, 15, 45, 0.92) !important;
            border-right: 1px solid rgba(99, 155, 255, 0.2);
            backdrop-filter: blur(12px);
        }

        /* ── chat message bubbles ── */
        [data-testid="stChatMessageContent"] {
            background: rgba(10, 25, 65, 0.75) !important;
            border: 1px solid rgba(99, 155, 255, 0.25) !important;
            border-radius: 14px !important;
            padding: 14px 16px !important;
            color: #dce8ff !important;
            backdrop-filter: blur(8px);
            font-family: 'DM Sans', sans-serif !important;
        }

        /* ── chat input bar ── */
        [data-testid="stChatInput"] {
            background: rgba(8, 20, 55, 0.85) !important;
            border: 1px solid rgba(99, 155, 255, 0.35) !important;
            border-radius: 16px !important;
            backdrop-filter: blur(10px);
        }

        [data-testid="stChatInput"] textarea {
            background: transparent !important;
            color: #dce8ff !important;
            font-family: 'DM Sans', sans-serif !important;
            font-size: 0.95rem !important;
        }

        [data-testid="stChatInput"] textarea::placeholder {
            color: rgba(180, 200, 255, 0.45) !important;
        }

        /* ── header banner ── */
        .header-banner {
            background: linear-gradient(
                135deg,
                rgba(10, 30, 80, 0.85) 0%,
                rgba(15, 40, 100, 0.80) 50%,
                rgba(8, 25, 70, 0.85) 100%
            );
            border: 1px solid rgba(180, 200, 255, 0.2);
            border-radius: 20px;
            padding: 32px 36px;
            margin-bottom: 24px;
            text-align: center;
            backdrop-filter: blur(14px);
            box-shadow: 0 8px 32px rgba(0, 30, 100, 0.4);
        }

        /* ── Playfair Display for the main title ── */
        .header-title {
            font-family: 'Playfair Display', Georgia, serif !important;
            font-size: 2.6rem;
            font-weight: 800;
            background: linear-gradient(90deg, #a8c8ff, #dce8ff, #b8d4ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 0.5px;
            margin: 0;
            line-height: 1.2;
        }

        .header-tagline {
            font-family: 'DM Sans', sans-serif !important;
            font-size: 0.95rem;
            font-weight: 300;
            color: rgba(180, 210, 255, 0.7);
            margin-top: 8px;
            letter-spacing: 0.8px;
        }

        /* ── sidebar info cards ── */
        .info-card {
            background: rgba(8, 20, 60, 0.6);
            border: 1px solid rgba(99, 155, 255, 0.2);
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 12px;
            font-size: 0.84rem;
            color: rgba(180, 210, 255, 0.75);
            line-height: 1.7;
            backdrop-filter: blur(6px);
        }

        .info-card-title {
            font-family: 'DM Sans', sans-serif !important;
            font-size: 0.75rem;
            font-weight: 600;
            color: #a8c8ff;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            margin-bottom: 8px;
        }

        /* ── sidebar agent name ── */
        .sidebar-name {
            font-family: 'Playfair Display', serif !important;
            font-size: 1.15rem;
            font-weight: 700;
            color: #dce8ff;
            margin-top: 6px;
        }

        /* ── risk badges ── */
        .badge-high   { color: #ff6b7a; font-weight: 600; }
        .badge-medium { color: #ffd166; font-weight: 600; }
        .badge-low    { color: #74d7a8; font-weight: 600; }

        /* ── divider ── */
        hr {
            border-color: rgba(99, 155, 255, 0.2) !important;
            margin: 14px 0 !important;
        }

        /* ── spinner ── */
        .stSpinner > div {
            color: #a8c8ff !important;
        }

        /* ── example prompt pills ── */
        .prompt-pill {
            display: inline-block;
            background: rgba(10, 30, 80, 0.65);
            border: 1px solid rgba(99, 155, 255, 0.3);
            border-radius: 20px;
            padding: 7px 15px;
            font-size: 0.82rem;
            color: rgba(180, 210, 255, 0.75);
            margin: 4px 3px;
            font-family: 'DM Sans', sans-serif;
            backdrop-filter: blur(4px);
        }

        /* ── clear button ── */
        .stButton > button {
            background: rgba(10, 30, 80, 0.6) !important;
            border: 1px solid rgba(99, 155, 255, 0.3) !important;
            color: rgba(180, 210, 255, 0.75) !important;
            border-radius: 10px !important;
            font-family: 'DM Sans', sans-serif !important;
            font-size: 0.85rem !important;
            transition: all 0.2s ease;
        }

        .stButton > button:hover {
            background: rgba(30, 60, 130, 0.7) !important;
            border-color: rgba(140, 180, 255, 0.5) !important;
            color: #dce8ff !important;
        }

        /* ── scrollbar ── */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb {
            background: rgba(99, 155, 255, 0.3);
            border-radius: 3px;
        }
    </style>
""", unsafe_allow_html=True)

# ── header banner ─────────────────────────────────────────────────────────────
st.markdown("""
    <div class="header-banner">
        <div style="font-size: 2.8rem; margin-bottom: 10px;">🔍</div>
        <p class="header-title">Terms&amp;Trust</p>
        <p class="header-tagline">Know what you're agreeing to — before you click Accept</p>
    </div>
""", unsafe_allow_html=True)

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:

    # agent identity
    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    with col2:
        st.image("images/Designer_2.png", use_container_width=True)
    st.markdown("""
        <div style="text-align:center; padding: 10px 0 8px 0;">
            <div class="sidebar-name">Terms&amp;Trust</div>
            <div style="font-size: 0.78rem; color: rgba(150,190,255,0.6);
                        margin-top: 0px; letter-spacing: 0.5px;">
                Your Personal T&amp;C Analyst
            </div>
        </div>
        <hr>
    """, unsafe_allow_html=True)

    # what this agent does
    st.markdown("""
        <div class="info-card">
            <div class="info-card-title">🤖 What I Do</div>
            I read Terms &amp; Conditions so you don't have to.
            Paste a URL or drop in raw text —
            I'll tell you what actually matters in plain English.
        </div>
    """, unsafe_allow_html=True)

    # how to use
    st.markdown("""
        <div class="info-card">
            <div class="info-card-title">💡 How To Use</div>
            <b style="color:#b8d4ff;">Option 1 — URL</b><br>
            Share a link to the T&amp;C page<br><br>
            <b style="color:#b8d4ff;">Option 2 — Paste Text</b><br>
            Copy and paste the terms directly<br><br>
            <b style="color:#b8d4ff;">Option 3 — Ask a question</b><br>
            Ask about a specific company or platform
        </div>
    """, unsafe_allow_html=True)

    # disclaimer
    st.markdown("""
        <div class="info-card">
            <div class="info-card-title">⚖️ Disclaimer</div>
            Terms&amp;Trust provides summaries for awareness only.
            This is not legal advice.
        </div>
    """, unsafe_allow_html=True)

    # clear conversation button
    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.messages = initialize_messages()
        st.rerun()

# ── initialize conversation memory ───────────────────────────────────────────
# stores the full message history in session so the agent remembers
# previous exchanges within the same conversation
if "messages" not in st.session_state:
    st.session_state.messages = initialize_messages()

# ── example prompts (shown only before first message) ────────────────────────
if len(st.session_state.messages) <= 1:
    st.markdown("""
        <div style="text-align:center; margin: 8px 0 20px 0;">
            <div style="font-size: 0.8rem; color: rgba(150,190,255,0.55);
                        margin-bottom: 10px; letter-spacing: 0.5px;">
                Try asking:
            </div>
            <span class="prompt-pill"> Analyze spotify.com/legal/end-user-agreement</span>
            <span class="prompt-pill"> I'll paste a privacy policy — what should I know?</span>
            <span class="prompt-pill"> What are TikTok's terms like?</span>
            <span class="prompt-pill"> What does "binding arbitration" mean for me?</span>
        </div>
    """, unsafe_allow_html=True)

# ── display chat history ──────────────────────────────────────────────────────
# loops through all previous messages and displays them in order
# skips the system prompt (role = "system")
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user", avatar="👤").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant", avatar="🔍").write(msg["content"])

# ── chat input ────────────────────────────────────────────────────────────────
# allows the user to type a new message
user_input = st.chat_input("Paste a URL, drop in T&C text, or ask a question...")

if user_input:
    # display the user's new message immediately in the chat
    st.chat_message("user", avatar="👤").write(user_input)

    # call get_termstrust_response() from the logic file
    # it appends the new message, runs the agent, and returns the response
    with st.spinner("🔍 Analyzing..."):
        response, updated_messages = get_termstrust_response(
            st.session_state.messages,
            user_input
        )

    # save the updated message history back to session state
    st.session_state.messages = updated_messages

    # display the agent's response
    st.chat_message("assistant", avatar="🔍").write(response)
