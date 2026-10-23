
import html
import logging
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# ---------------------------------------------------------
# PROJECT SETUP
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("documind")

# ---------------------------------------------------------
# BACKEND IMPORTS
# ---------------------------------------------------------

try:
    from documind.agent.graph import run_research
    from documind.ingestion.chunking import chunk_pages
    from documind.ingestion.indexing import index_chunks
    from documind.ingestion.loaders import load_pdf_bytes

    BACKEND_READY = True
    BACKEND_ERROR = ""

except Exception as exc:
    BACKEND_READY = False
    BACKEND_ERROR = str(exc)
    logger.exception("Unable to import DocuMind backend")

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="DocuMind AI | Research Workspace",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

DEFAULTS = {
    "indexed_names": [],
    "conversation": [],
    "research_task": "Comprehensive Research",
    "top_k": 5,
    "last_error": "",
    "submitted_question": "",
    "question_input": "",
    "submission_pending": False,
    "processing": False,
    "total_questions": 0,
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Migrate earlier session-state keys safely.
if "last_question" in st.session_state and not st.session_state.get(
    "conversation"
):
    old_question = st.session_state.get("last_question")
    old_result = st.session_state.get("last_result")

    if old_question:
        st.session_state["conversation"] = [
            {
                "question": str(old_question),
                "answer": str(old_result or ""),
                "time": datetime.now().strftime("%I:%M %p"),
            }
        ]


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def queue_question():
    """Run before widgets are rebuilt, so resetting the input is safe."""
    st.session_state["submitted_question"] = str(
        st.session_state.get("question_input", "")
    ).strip()

    st.session_state["submission_pending"] = True
    st.session_state["question_input"] = ""


def clear_conversation():
    st.session_state["conversation"] = []
    st.session_state["submitted_question"] = ""
    st.session_state["submission_pending"] = False
    st.session_state["last_error"] = ""


def extract_answer(result):
    """Normalize common backend response formats."""
    if result is None:
        return "The research process returned no answer."

    if isinstance(result, str):
        return result.strip() or "No answer was returned."

    if isinstance(result, dict):
        for key in (
            "answer",
            "response",
            "result",
            "output",
            "final_answer",
            "final",
        ):
            value = result.get(key)

            if value is not None:
                if isinstance(value, str):
                    return value.strip() or "No answer was returned."
                return str(value)

        return str(result)

    return str(result)


def format_bytes(size):
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def build_transcript():
    lines = [
        "# DocuMind AI — Research Transcript",
        "",
        f"Exported: {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
        "",
    ]

    for item in st.session_state["conversation"]:
        lines.extend(
            [
                f"## You: {item['question']}",
                "",
                item["answer"],
                "",
                "---",
                "",
            ]
        )

    return "\n".join(lines)


# ---------------------------------------------------------
# PREMIUM DARK UI
# ---------------------------------------------------------

st.markdown(
    """
    <style>
    @import url(
      'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap'
    );

    :root {
        --bg: #08090d;
        --panel: #101119;
        --panel2: #141522;
        --border: #252638;
        --text: #f4f3ff;
        --muted: #9696ad;
        --purple: #a78bfa;
        --violet: #8b5cf6;
        --blue: #60a5fa;
        --green: #6ee7b7;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background: var(--bg) !important;
        color: var(--text) !important;
        font-family: 'DM Sans', sans-serif !important;
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(
                ellipse at 45% -12%,
                rgba(139, 92, 246, 0.15),
                transparent 43%
            ),
            var(--bg) !important;
    }

    [data-testid="stHeader"] {
        background: rgba(8, 9, 13, 0.8) !important;
    }

    [data-testid="stToolbar"] {
        right: 1rem;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 1450px;
        padding-top: 1.7rem;
        padding-bottom: 2rem;
    }

    h1, h2, h3, h4 {
        font-family: 'Space Grotesk', sans-serif !important;
        color: var(--text) !important;
        letter-spacing: -0.6px;
    }

    p, label, li, span {
        font-family: 'DM Sans', sans-serif;
    }

    .block-container {
        padding-left: 2.5rem;
        padding-right: 2.5rem;
    }

    /* Sidebar */

    [data-testid="stSidebar"] {
        background: #0c0d13 !important;
        border-right: 1px solid #222331;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.3rem;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #c3c3d5;
    }

    [data-testid="stSidebar"] hr {
        border-color: #28293a;
    }

    /* Brand */

    .brand-row {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 26px;
    }

    .brand-symbol {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 44px;
        height: 44px;
        border-radius: 14px;
        color: white;
        font-size: 24px;
        background: linear-gradient(135deg, #8b5cf6, #6366f1);
        box-shadow: 0 0 28px rgba(139, 92, 246, 0.3);
    }

    .brand-name {
        font-family: 'Space Grotesk', sans-serif;
        color: #fff;
        font-size: 23px;
        font-weight: 700;
        letter-spacing: -1px;
    }

    .brand-subtitle {
        color: #9696ad;
        font-size: 11px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-top: 1px;
    }

    /* Hero */

    .hero {
        position: relative;
        overflow: hidden;
        padding: 34px 35px;
        border: 1px solid #2c2943;
        border-radius: 24px;
        background:
            radial-gradient(
                circle at 90% 5%,
                rgba(139, 92, 246, 0.2),
                transparent 32%
            ),
            linear-gradient(120deg, #14121f, #11121b 65%, #111323);
        margin-bottom: 24px;
    }

    .hero-kicker {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        color: #c4b5fd;
        background: rgba(139, 92, 246, 0.12);
        border: 1px solid rgba(167, 139, 250, 0.22);
        border-radius: 999px;
        padding: 7px 12px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
    }

    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        color: #fff;
        font-size: clamp(29px, 4vw, 46px);
        font-weight: 700;
        line-height: 1.15;
        letter-spacing: -1.7px;
        margin: 20px 0 12px;
    }

    .gradient-text {
        background: linear-gradient(90deg, #c4b5fd, #818cf8, #7dd3fc);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-description {
        max-width: 700px;
        color: #aaa9c0;
        font-size: 15px;
        line-height: 1.8;
        margin-bottom: 20px;
    }

    .hero-note {
        color: #85859e;
        font-size: 12px;
    }

    /* Cards */

    .stat-card {
        background: linear-gradient(145deg, #151621, #101119);
        border: 1px solid #27283b;
        border-radius: 17px;
        padding: 18px 19px;
        min-height: 100px;
        margin-bottom: 10px;
    }

    .stat-label {
        color: #9999b1;
        font-size: 12px;
        margin-bottom: 10px;
    }

    .stat-value {
        color: #f6f4ff;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 25px;
        font-weight: 700;
    }

    .stat-detail {
        color: #a78bfa;
        font-size: 11px;
        margin-top: 3px;
    }

    .section-heading {
        color: #f4f3ff;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 21px;
        font-weight: 700;
        margin-top: 13px;
        margin-bottom: 5px;
    }

    .section-description {
        color: #9393aa;
        font-size: 13px;
        margin-bottom: 18px;
        line-height: 1.65;
    }

    .feature-card {
        height: 100%;
        min-height: 142px;
        padding: 20px;
        background: linear-gradient(145deg, #151620, #101119);
        border: 1px solid #28293a;
        border-radius: 17px;
        margin-bottom: 12px;
        transition: border-color 0.2s ease;
    }

    .feature-icon {
        font-size: 23px;
        margin-bottom: 12px;
    }

    .feature-title {
        color: #eeeaff;
        font-size: 14px;
        font-weight: 700;
        margin-bottom: 7px;
    }

    .feature-copy {
        color: #9999af;
        font-size: 12px;
        line-height: 1.7;
    }

    .panel {
        background: #101119;
        border: 1px solid #28293a;
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 15px;
    }

    .small-muted {
        color: #9292a9;
        font-size: 12px;
        line-height: 1.7;
    }

    .status-dot {
        display: inline-block;
        width: 7px;
        height: 7px;
        background: #6ee7b7;
        border-radius: 50%;
        margin-right: 7px;
        box-shadow: 0 0 9px rgba(110, 231, 183, 0.5);
    }

    /* Inputs */

    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea {
        background: #0d0e15 !important;
        color: #f4f3ff !important;
        border: 1px solid #303146 !important;
        border-radius: 12px !important;
    }

    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 0 1px #8b5cf6 !important;
    }

    [data-testid="stSelectbox"] > div > div,
    [data-testid="stNumberInput"] input {
        background: #101119 !important;
        color: #f4f3ff !important;
        border-color: #303146 !important;
        border-radius: 10px !important;
    }

    [data-testid="stFileUploader"] section {
        background: #11121b !important;
        border: 1px dashed #45405f !important;
        border-radius: 14px !important;
    }

    [data-testid="stFileUploader"] section * {
        color: #c8c4e2 !important;
    }

    [data-testid="stSlider"] [data-baseweb="slider"] {
        padding-top: 6px;
    }

    /* Buttons */

    .stButton > button,
    .stDownloadButton > button,
    [data-testid="stFormSubmitButton"] button {
        background: linear-gradient(110deg, #8b5cf6, #6d5ce7) !important;
        color: #fff !important;
        border: 1px solid #9a7af8 !important;
        border-radius: 11px !important;
        min-height: 42px;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    [data-testid="stFormSubmitButton"] button:hover {
        border-color: #c4b5fd !important;
        box-shadow: 0 0 22px rgba(139, 92, 246, 0.22);
        transform: translateY(-1px);
    }

    .stButton > button:focus,
    .stDownloadButton > button:focus {
        box-shadow: 0 0 0 2px rgba(167, 139, 250, 0.35) !important;
    }

    /* Chat */

    .chat-question {
        background: linear-gradient(120deg, #211b36, #191a2a);
        border: 1px solid #393052;
        border-radius: 17px 17px 4px 17px;
        padding: 16px 19px;
        color: #f4f0ff;
        line-height: 1.7;
        margin: 12px 0 10px 8%;
        overflow-wrap: anywhere;
    }

    .chat-answer {
        background: #11121a;
        border: 1px solid #292a3b;
        border-radius: 17px 17px 17px 4px;
        padding: 20px;
        color: #deddeb;
        line-height: 1.85;
        margin: 0 8% 20px 0;
        overflow-wrap: anywhere;
    }

    .chat-label {
        color: #a78bfa;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }

    .chat-time {
        color: #85859d;
        font-size: 10px;
        margin-top: 10px;
    }

    [data-testid="stChatMessage"] {
        background: #11121a;
        border: 1px solid #28293a;
        border-radius: 15px;
    }

    /* Alerts */

    [data-testid="stAlert"] {
        border-radius: 12px;
    }

    /* Footer */

    .footer {
        text-align: center;
        padding: 25px 10px 10px;
        margin-top: 35px;
        border-top: 1px solid #222331;
        color: #73738a;
        font-size: 11px;
        line-height: 1.9;
    }

    .footer strong {
        color: #b9a5ff;
        font-weight: 600;
    }

    /* Scrollbar */

    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #090a0f;
    }

    ::-webkit-scrollbar-thumb {
        background: #343047;
        border-radius: 99px;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .hero {
            padding: 23px 20px;
        }

        .hero-title {
            font-size: 30px;
        }

        .chat-question {
            margin-left: 2%;
        }

        .chat-answer {
            margin-right: 2%;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div class="brand-row">
            <div class="brand-symbol">✦</div>
            <div>
                <div class="brand-name">DocuMind</div>
                <div class="brand-subtitle">AI Research Workspace</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="small-muted">YOUR WORKSPACE</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### 📚 Knowledge Library")

    uploaded_files = st.file_uploader(
        "Add your PDF documents",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload PDFs you want DocuMind AI to analyze.",
    )

    st.caption("PDF documents only · Upload multiple files")

    if uploaded_files:
        st.markdown(
            f'<div class="small-muted">{len(uploaded_files)} '
            f'file(s) selected</div>',
            unsafe_allow_html=True,
        )

        for file in uploaded_files:
            st.caption(f"📄 {file.name} · {format_bytes(file.size)}")

        if st.button(
            "✦  Index documents",
            use_container_width=True,
            disabled=not BACKEND_READY,
        ):
            try:
                new_files = [
                    file
                    for file in uploaded_files
                    if file.name not in st.session_state["indexed_names"]
                ]

                if not new_files:
                    st.info("These filenames have already been indexed in this session.")
                else:
                    all_chunks = []

                    with st.status(
                        "Preparing your knowledge library...",
                        expanded=True,
                    ) as status:
                        for file in new_files:
                            st.write(f"Reading `{file.name}`...")

                            pages = load_pdf_bytes(
                                file.getvalue(),
                                file.name,
                            )

                            chunks = chunk_pages(pages)
                            all_chunks.extend(chunks)

                            st.write(
                                f"Prepared {len(chunks)} chunk(s) "
                                f"from `{file.name}`."
                            )

                        if all_chunks:
                            st.write("Adding document chunks to the index...")
                            index_chunks(all_chunks)

                        st.session_state["indexed_names"].extend(
                            file.name for file in new_files
                        )

                        status.update(
                            label="Your documents are ready!",
                            state="complete",
                            expanded=False,
                        )

                    st.success(
                        f"Indexed {len(new_files)} new document(s)."
                    )
                    st.rerun()

            except Exception as exc:
                logger.exception("Document indexing failed")
                st.session_state["last_error"] = str(exc)
                st.error("Document indexing failed. See the error details below.")

                with st.expander("Technical details"):
                    st.code(str(exc))

    st.divider()

    st.markdown("### ⚙️ Research Settings")

    task_options = [
        "Comprehensive Research",
        "Summarize Documents",
        "Compare Documents",
        "Find Key Insights",
    ]

    current_task = st.session_state["research_task"]

    if current_task not in task_options:
        current_task = task_options[0]

    st.session_state["research_task"] = st.selectbox(
        "Research mode",
        options=task_options,
        index=task_options.index(current_task),
        help="Choose the type of analysis you want.",
    )

    st.session_state["top_k"] = st.slider(
        "Retrieval depth",
        min_value=1,
        max_value=10,
        value=int(st.session_state["top_k"]),
        help="Controls the number of relevant chunks requested by the app.",
    )

    st.caption(
        "Higher retrieval depth can provide more context, "
        "but may increase processing time."
    )

    st.divider()

    st.markdown("### 🗂️ Session Overview")

    st.markdown(
        f"""
        <div class="panel">
            <div class="stat-label">Indexed document names</div>
            <div class="stat-value">{len(st.session_state["indexed_names"])}</div>
            <div class="small-muted">Tracked in this session</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state["indexed_names"]:
        with st.expander("View indexed filenames"):
            for name in st.session_state["indexed_names"]:
                st.caption(f"📄 {name}")

    col_clear, col_export = st.columns(2)

    with col_clear:
        st.button(
            "Clear chat",
            use_container_width=True,
            on_click=clear_conversation,
        )

    with col_export:
        st.download_button(
            "Export",
            data=build_transcript(),
            file_name="documind_research.md",
            mime="text/markdown",
            use_container_width=True,
            disabled=not st.session_state["conversation"],
        )

    st.divider()

    backend_status = (
        '<span class="status-dot"></span>Backend imports ready'
        if BACKEND_READY
        else "⚠️ Backend unavailable"
    )

    st.markdown(
        f"""
        <div class="small-muted">
            <strong style="color:#c4b5fd;">SYSTEM STATUS</strong><br><br>
            {backend_status}<br>
            <span style="color:#77778f;">
                Local workspace · Session-based UI
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not BACKEND_READY:
        with st.expander("Backend import error"):
            st.code(BACKEND_ERROR)

# ---------------------------------------------------------
# HERO
# ---------------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <div class="hero-kicker">✦ YOUR AI RESEARCH COMPANION</div>
        <div class="hero-title">
            Think deeper.<br>
            <span class="gradient-text">Discover more.</span>
        </div>
        <div class="hero-description">
            Turn complex documents into clear answers and useful insights.
            Upload your PDFs, ask meaningful questions, and explore your
            knowledge with an AI-powered research workspace.
        </div>
        <div class="hero-note">
            ◈ Document intelligence &nbsp; · &nbsp;
            ◈ Context-aware research &nbsp; · &nbsp;
            ◈ One focused workspace
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# DASHBOARD METRICS
# ---------------------------------------------------------

metric1, metric2, metric3 = st.columns(3)

with metric1:
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-label">📚 Knowledge library</div>
            <div class="stat-value">
                {len(st.session_state["indexed_names"]):02d}
            </div>
            <div class="stat-detail">Document names tracked</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with metric2:
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-label">💬 Research conversations</div>
            <div class="stat-value">
                {len(st.session_state["conversation"]):02d}
            </div>
            <div class="stat-detail">Questions answered in this session</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with metric3:
    status_text = "Ready to explore" if BACKEND_READY else "Setup required"
    status_color = "#6ee7b7" if BACKEND_READY else "#fbbf24"

    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-label">✦ Workspace status</div>
            <div class="stat-value" style="font-size:21px;">
                {status_text}
            </div>
            <div class="stat-detail" style="color:{status_color};">
                {"Backend imports available" if BACKEND_READY else "Check backend setup"}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# FEATURE CARDS
# ---------------------------------------------------------

st.markdown(
    """
    <div class="section-heading">Your research toolkit</div>
    <div class="section-description">
        Everything you need to move from reading to understanding.
    </div>
    """,
    unsafe_allow_html=True,
)

feature1, feature2, feature3 = st.columns(3)

with feature1:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">📖</div>
            <div class="feature-title">Understand documents</div>
            <div class="feature-copy">
                Explore your uploaded PDFs and ask questions
                about the information they contain.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with feature2:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">✧</div>
            <div class="feature-title">Find useful insights</div>
            <div class="feature-copy">
                Summarize key ideas, investigate topics,
                and compare information across documents.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with feature3:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">⌘</div>
            <div class="feature-title">Stay in your flow</div>
            <div class="feature-copy">
                Keep your questions and answers together
                in one clean research conversation.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# RESEARCH CHAT
# ---------------------------------------------------------

st.markdown(
    """
    <div class="section-heading">Research workspace</div>
    <div class="section-description">
        Ask a question about your knowledge base or choose a research task
        from the sidebar to get started.
    </div>
    """,
    unsafe_allow_html=True,
)

if not st.session_state["indexed_names"]:
    st.markdown(
        """
        <div class="panel">
            <div style="font-size:25px;margin-bottom:10px;">🌙</div>
            <div style="font-size:16px;font-weight:700;color:#eeeaff;">
                Your next discovery starts here
            </div>
            <div class="small-muted" style="margin-top:8px;">
                Upload one or more PDFs using the left sidebar, then click
                <strong style="color:#c4b5fd;">Index documents</strong>.
                Once your backend is configured and the documents are indexed,
                you can begin asking research questions.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Display the conversation history.
for item in st.session_state["conversation"]:
    safe_question = html.escape(item["question"])
    safe_time = html.escape(item.get("time", ""))

    st.markdown(
        f"""
        <div class="chat-question">
            <div class="chat-label">You</div>
            {safe_question}
            <div class="chat-time">{safe_time}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="chat-answer">
            <div class="chat-label">✦ DocuMind AI</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(item["answer"])

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# QUESTION COMPOSER
# ---------------------------------------------------------

st.markdown(
    """
    <div class="panel">
        <div style="font-size:15px;font-weight:700;color:#f4f3ff;">
            ✦ What would you like to discover?
        </div>
        <div class="small-muted" style="margin-top:5px;">
            Be specific for more focused research results.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("research_form", clear_on_submit=False):
    st.text_area(
        "Your research question",
        key="question_input",
        placeholder=(
            "Example: What are the main findings in these documents, "
            "and how do they relate to one another?"
        ),
        height=105,
        label_visibility="collapsed",
    )

    submit_col, hint_col = st.columns([1, 2])

    with submit_col:
        st.form_submit_button(
            "✦  Start research",
            use_container_width=True,
            on_click=queue_question,
        )

    with hint_col:
        st.markdown(
            """
            <div class="small-muted" style="padding-top:12px;">
                Your question will use the selected research mode
                and retrieval depth.
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------
# PROCESS SUBMITTED QUESTION
# ---------------------------------------------------------

if st.session_state["submission_pending"]:
    question = st.session_state["submitted_question"]

    # Consume the pending submission so it cannot run twice.
    st.session_state["submission_pending"] = False
    st.session_state["submitted_question"] = ""

    if not question:
        st.warning("Please enter a research question before submitting.")

    elif not BACKEND_READY:
        st.error("The DocuMind backend could not be imported.")
        st.caption("Check the backend import error in the sidebar.")
        st.code(BACKEND_ERROR)

    elif not st.session_state["indexed_names"]:
        st.warning(
            "Upload and index at least one PDF from the sidebar before "
            "starting research."
        )

    else:
        try:
            st.session_state["processing"] = True

            with st.spinner(
                "✦ DocuMind is exploring your question and preparing an answer..."
            ):
                result = run_research(
                    question=question,
                    task=st.session_state["research_task"],
                    top_k=st.session_state["top_k"],
                )

                answer = extract_answer(result)

            st.session_state["conversation"].append(
                {
                    "question": question,
                    "answer": answer,
                    "time": datetime.now().strftime("%I:%M %p"),
                }
            )

            st.session_state["total_questions"] += 1
            st.session_state["last_error"] = ""
            st.rerun()

        except Exception as exc:
            logger.exception("Research execution failed")
            st.session_state["last_error"] = str(exc)
            st.error(
                "Research could not be completed. Check the technical "
                "details below."
            )

            with st.expander("Technical error details", expanded=True):
                st.code(str(exc))

        finally:
            st.session_state["processing"] = False

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.markdown(
    """
    <div class="footer">
        <strong>✦ DocuMind AI</strong><br>
        A calmer way to explore complex information.<br>
        <span>
            Research responsibly · Review important findings ·
            Verify critical information
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)
