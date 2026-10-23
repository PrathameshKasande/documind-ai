
from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# =========================================================
# PROJECT PATH CONFIGURATION
# Fix imports for the src/documind package on Streamlit Cloud
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if SRC_DIR.is_dir() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

load_dotenv(PROJECT_ROOT / ".env")

# =========================================================
# APPLICATION IMPORTS
# =========================================================

from documind.agent.graph import run_research
from documind.ingestion.chunking import chunk_pages
from documind.ingestion.indexing import index_chunks
from documind.ingestion.loaders import load_pdf_bytes

logger = logging.getLogger(__name__)

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="DocuMind AI | Agentic Research Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# SESSION STATE
# =========================================================

DEFAULTS = {
    "indexed_names": [],
    "last_result": None,
    "research_question": "",
    "research_task": "Answer a question",
    "top_k": 5,
    "last_error": None,
}

for key, default in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default


def set_question(question: str) -> None:
    st.session_state.research_question = question


def clear_research() -> None:
    st.session_state.last_result = None
    st.session_state.last_error = None
    st.session_state.research_question = ""


def run_agent() -> None:
    question = st.session_state.research_question.strip()

    if not question:
        st.session_state.last_error = (
            "Enter a research question to continue."
        )
        return

    st.session_state.last_error = None

    try:
        with st.spinner(
            "🧠 DocuMind AI is searching your knowledge base "
            "and preparing your answer..."
        ):
            result = run_research(
                question=question,
                task=st.session_state.research_task,
                top_k=st.session_state.top_k,
            )

        if not isinstance(result, dict):
            raise TypeError(
                "The research workflow returned an unexpected result."
            )

        st.session_state.last_result = result

    except Exception as exc:
        logger.exception("Research workflow failed")
        st.session_state.last_error = (
            f"Unable to complete your research ({type(exc).__name__}). "
            "Please try again. If the problem persists, check the "
            "application logs."
        )


# =========================================================
# CUSTOM STYLING
# =========================================================

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1380px;
        padding-top: 1.8rem;
        padding-bottom: 3rem;
    }

    .hero {
        padding: 2rem;
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 20px;
        background: linear-gradient(
            120deg,
            rgba(99,102,241,.17),
            rgba(20,184,166,.09)
        );
        margin-bottom: 1.4rem;
    }

    .hero-eyebrow {
        font-size: .76rem;
        text-transform: uppercase;
        letter-spacing: .13em;
        font-weight: 700;
        opacity: .75;
        margin-bottom: .6rem;
    }

    .hero-title {
        font-size: clamp(2rem, 4vw, 2.8rem);
        line-height: 1.15;
        font-weight: 800;
        letter-spacing: -.045em;
        margin: 0 0 .65rem 0;
    }

    .hero-description {
        font-size: 1.02rem;
        line-height: 1.7;
        opacity: .82;
        max-width: 760px;
    }

    .section-eyebrow {
        font-size: .76rem;
        text-transform: uppercase;
        letter-spacing: .11em;
        font-weight: 700;
        opacity: .7;
    }

    .answer-card {
        padding: 1.35rem 1.5rem;
        border: 1px solid rgba(128,128,128,.28);
        border-radius: 16px;
        background: rgba(128,128,128,.045);
        margin: .6rem 0 1rem 0;
    }

    .answer-heading {
        font-size: 1.05rem;
        font-weight: 750;
        margin-bottom: .6rem;
    }

    .feature-card {
        border: 1px solid rgba(128,128,128,.22);
        border-radius: 13px;
        padding: 1rem;
        min-height: 110px;
    }

    .feature-title {
        font-weight: 700;
        margin-bottom: .4rem;
    }

    .feature-description {
        opacity: .76;
        font-size: .88rem;
        line-height: 1.5;
    }

    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,.22);
        border-radius: 12px;
        padding: .75rem 1rem;
    }

    div.stButton > button {
        border-radius: 10px;
        min-height: 2.65rem;
        font-weight: 600;
    }

    div[data-testid="stFileUploader"] {
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-eyebrow">
            AI-powered document intelligence
        </div>
        <div class="hero-title">🧠 DocuMind AI</div>
        <div class="hero-description">
            <b>Agentic Research Assistant</b><br>
            Turn your documents into useful answers. Ask questions,
            summarize information, and compare findings with an
            AI-powered research workflow.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# DOCUMENT LIBRARY
# =========================================================

with st.sidebar:
    st.markdown("## 📚 Document library")
    st.caption(
        "Build your private research workspace with PDFs."
    )

    uploaded_files = st.file_uploader(
        "Upload PDF documents",
        type=["pdf"],
        accept_multiple_files=True,
        help="Choose one or more PDFs to add to your knowledge base.",
    )

    if uploaded_files:
        total_mb = sum(
            file.size for file in uploaded_files
        ) / (1024 * 1024)

        st.caption(
            f"{len(uploaded_files)} selected · {total_mb:.2f} MB"
        )

    if st.button(
        "⚡ Index documents",
        type="primary",
        use_container_width=True,
        disabled=not uploaded_files,
    ):
        total_chunks = 0
        successful_files = 0
        failed_files = []

        progress = st.progress(
            0,
            text="Preparing your documents...",
        )

        for index, uploaded_file in enumerate(
            uploaded_files,
            start=1,
        ):
            try:
                pages = load_pdf_bytes(
                    uploaded_file.getvalue(),
                    uploaded_file.name,
                )

                chunks = chunk_pages(pages)

                if not chunks:
                    failed_files.append(
                        f"{uploaded_file.name}: no text extracted"
                    )
                else:
                    count = index_chunks(chunks)
                    total_chunks += count
                    successful_files += 1

                    if (
                        uploaded_file.name
                        not in st.session_state.indexed_names
                    ):
                        st.session_state.indexed_names.append(
                            uploaded_file.name
                        )

            except Exception as exc:
                logger.exception(
                    "Indexing failed for %s",
                    uploaded_file.name,
                )
                failed_files.append(
                    f"{uploaded_file.name}: {type(exc).__name__}"
                )

            progress.progress(
                index / len(uploaded_files),
                text=(
                    f"Processing document {index} "
                    f"of {len(uploaded_files)}"
                ),
            )

        progress.empty()

        if successful_files:
            st.success(
                f"Indexed {total_chunks} chunks from "
                f"{successful_files} document(s)."
            )
            st.session_state.last_result = None

        for error in failed_files:
            st.error(error)

        if successful_files:
            st.rerun()

    st.divider()
    st.markdown("### Your knowledge base")

    if st.session_state.indexed_names:
        st.caption(
            f"{len(st.session_state.indexed_names)} document(s) "
            "indexed this session"
        )

        for filename in st.session_state.indexed_names:
            st.markdown(f"📄 {filename}")
    else:
        st.info(
            "No documents indexed yet. Upload a PDF and index it "
            "to begin."
        )

    st.divider()

    with st.expander("About this application"):
        st.markdown(
            """
            **DocuMind AI — Agentic Research Assistant**

            - PDF document ingestion
            - Chunk-based knowledge indexing
            - Hybrid document retrieval
            - AI-generated research answers
            - Source-grounded evidence processing
            """
        )

    st.caption(
        "Demo tip: use public or synthetic documents. "
        "Review deployment security before uploading confidential data."
    )

# =========================================================
# WORKSPACE OVERVIEW
# =========================================================

st.markdown(
    '<div class="section-eyebrow">YOUR WORKSPACE</div>',
    unsafe_allow_html=True,
)

metric1, metric2 = st.columns(2)

with metric1:
    st.metric(
        "📄 Documents indexed this session",
        len(st.session_state.indexed_names),
    )

with metric2:
    st.metric(
        "✨ Research workspace",
        "Answer ready"
        if st.session_state.last_result
        else "Ready to use",
    )

st.divider()

# =========================================================
# RESEARCH INPUT
# =========================================================

st.markdown("### 🔍 Start your research")
st.caption(
    "Choose a research task and ask a question about your documents."
)

st.selectbox(
    "Research task",
    [
        "Answer a question",
        "Summarize evidence",
        "Compare documents",
    ],
    key="research_task",
)

st.markdown("**Need inspiration? Try one of these.**")

suggestions = [
    (
        "❓ Question answering",
        "What are the most important facts in these documents?",
    ),
    (
        "📝 Summarization",
        "Summarize the key findings and conclusions.",
    ),
    (
        "⚖️ Document comparison",
        "Compare the main findings across the uploaded documents.",
    ),
]

suggestion_columns = st.columns(3)

for column, (label, prompt) in zip(
    suggestion_columns,
    suggestions,
):
    with column:
        st.button(
            label,
            key=f"suggestion_{label}",
            use_container_width=True,
            on_click=set_question,
            args=(prompt,),
        )

st.text_area(
    "Your research question",
    key="research_question",
    height=125,
    placeholder=(
        "For example: How many books and DVDs can a member borrow at once?"
    ),
    help="Ask a clear question that can be answered from your documents.",
)

with st.expander("⚙️ Research settings"):
    st.slider(
        "Evidence passages for the AI",
        min_value=3,
        max_value=10,
        key="top_k",
        help=(
            "Controls how many retrieved passages are supplied "
            "to the research workflow."
        ),
    )

research_col, new_col, _ = st.columns([1.25, 1.2, 3])

with research_col:
    st.button(
        "🚀 Run research",
        type="primary",
        use_container_width=True,
        on_click=run_agent,
    )

with new_col:
    st.button(
        "＋ New research",
        use_container_width=True,
        on_click=clear_research,
    )

if st.session_state.last_error:
    st.error(st.session_state.last_error)

# =========================================================
# ANSWER AREA
# =========================================================

result = st.session_state.last_result

if result:
    answer = result.get("answer") or (
        "No answer was returned. Please try another question."
    )

    st.divider()

    st.markdown(
        '<div class="section-eyebrow">RESEARCH RESULT</div>',
        unsafe_allow_html=True,
    )
    st.markdown("## 💡 Your answer")

    st.markdown(
        '<div class="answer-card">'
        '<div class="answer-heading">🧠 DocuMind AI response</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(answer)

    st.write("")

    download_data = result.get("markdown") or answer

    download_col, new_question_col, _ = st.columns(
        [1.5, 1.5, 3]
    )

    with download_col:
        st.download_button(
            "⬇️ Download answer",
            data=download_data,
            file_name="documind-research-answer.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with new_question_col:
        st.button(
            "＋ Ask another question",
            use_container_width=True,
            on_click=clear_research,
        )

else:
    st.divider()

    if not st.session_state.indexed_names:
        st.markdown("### 👋 Welcome to DocuMind AI")
        st.info(
            "Upload your research PDFs in the sidebar, index them, "
            "and ask your first question."
        )
    else:
        st.markdown("### 🚀 Ready when you are")
        st.info(
            "Your workspace is ready. Enter a question above and "
            "click **Run research** to receive an answer."
        )

# =========================================================
# CAPABILITIES
# =========================================================

st.divider()
st.markdown("### Built for document research")

feature_columns = st.columns(3)

features = [
    (
        "📚 Document intelligence",
        "Process PDFs and build a searchable knowledge base.",
    ),
    (
        "🤖 Agentic research",
        "Use your existing AI research workflow to answer questions.",
    ),
    (
        "💡 Useful answers",
        "Read and download research results in a clean interface.",
    ),
]

for column, (title, description) in zip(
    feature_columns,
    features,
):
    with column:
        st.markdown(
            f"""
            <div class="feature-card">
                <div class="feature-title">{title}</div>
                <div class="feature-description">{description}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()

st.caption(
    "DocuMind AI — Agentic Research Assistant · "
    "Document intelligence powered by AI"
)
