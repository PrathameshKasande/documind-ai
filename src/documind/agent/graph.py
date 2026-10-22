from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from documind.agent.prompts import build_research_prompt
from documind.agent.state import AgentState
from documind.agent.tools import search_documents
from documind.citations.verifier import verify_citations
from documind.config import get_int
from documind.providers.router import generate_answer


def classify_query(state: AgentState) -> dict:
    """Validate the question and initialize workflow state."""
    question = state.get("question", "").strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    task = state.get(
        "task",
        "Answer a question",
    )

    return {
        "question": question,
        "task": task,
        "attempts": 0,
        "activity": [
            f"Task selected: {task}",
        ],
    }


def retrieve_context(state: AgentState) -> dict:
    """Retrieve evidence passages from the local index."""
    evidence = search_documents(
        question=state["question"],
        k=state.get("top_k", 5),
    )

    activity = list(state.get("activity", []))
    activity.append(
        f"Hybrid retrieval returned {len(evidence)} passages."
    )

    return {
        "evidence": evidence,
        "activity": activity,
    }


def grade_retrieval(state: AgentState) -> dict:
    """Perform a basic check for usable retrieved evidence."""
    evidence = state.get("evidence", [])
    activity = list(state.get("activity", []))

    if evidence:
        activity.append(
            "Evidence review completed; passages are available."
        )
    else:
        activity.append(
            "No evidence found. The agent will abstain."
        )

    return {
        "activity": activity,
    }


def generate_research_answer(state: AgentState) -> dict:
    """Generate an answer grounded in the retrieved passages."""
    evidence = state.get("evidence", [])
    activity = list(state.get("activity", []))

    if not evidence:
        return {
            "answer": (
                "I could not find relevant evidence in the indexed "
                "documents, so I cannot answer this reliably. "
                "Please index relevant documents and try again."
            ),
            "provider": "none",
            "activity": activity + [
                "Abstained because no evidence was retrieved."
            ],
        }

    prompt = build_research_prompt(
        question=state["question"],
        task=state.get("task", "Answer a question"),
        evidence=evidence,
    )

    # On a retry, specifically request correction of citation formatting.
    if state.get("attempts", 0) > 0:
        prompt += (
            "\n\nCitation correction attempt: use only the exact "
            "source filenames and page numbers in the evidence above. "
            "Cite claims using [E1, filename.pdf, p. 3] format. "
            "If you cannot support a claim, remove it or state that "
            "the evidence is insufficient."
        )

    answer, provider = generate_answer(prompt)

    activity.append(
        f"Generated answer using {provider}."
    )

    return {
        "answer": answer,
        "provider": provider,
        "activity": activity,
    }


def verify_citations_node(state: AgentState) -> dict:
    """Check whether citations point to retrieved source/page pairs."""
    verification = verify_citations(
        answer=state.get("answer", ""),
        evidence=state.get("evidence", []),
    )

    activity = list(state.get("activity", []))

    if verification["valid"]:
        activity.append(
            "Citation source/page check passed."
        )
    else:
        activity.append(
            "Citation source/page check failed or found no citations."
        )

    return {
        "citations_valid": verification["valid"],
        "attempts": state.get("attempts", 0) + 1,
        "activity": activity,
    }


def should_retry(state: AgentState) -> str:
    """Choose a bounded retry or finish the workflow."""
    max_attempts = max(
        1,
        get_int("MAX_AGENT_ATTEMPTS", 2),
    )

    if (
        not state.get("citations_valid", False)
        and state.get("attempts", 0) < max_attempts
        and state.get("evidence")
    ):
        return "retry"

    return "finish"


def finalize_answer(state: AgentState) -> dict:
    """Return the final answer with an appropriate citation warning."""
    answer = state.get("answer", "").strip()

    if not answer:
        answer = (
            "I could not produce a reliable answer from "
            "the available evidence."
        )

    if (
        state.get("evidence")
        and not state.get("citations_valid", False)
    ):
        answer += (
            "\n\n**Citation warning:** The automatic check could not "
            "validate the source/page references. Review the evidence "
            "passages below before relying on the answer. This check "
            "does not independently prove semantic support."
        )

    return {
        "answer": answer,
    }


def build_graph():
    """Build and compile the research agent graph."""
    workflow = StateGraph(AgentState)

    workflow.add_node("classify", classify_query)
    workflow.add_node("retrieve", retrieve_context)
    workflow.add_node("grade", grade_retrieval)
    workflow.add_node("generate", generate_research_answer)
    workflow.add_node("verify", verify_citations_node)
    workflow.add_node("finalize", finalize_answer)

    workflow.add_edge(START, "classify")
    workflow.add_edge("classify", "retrieve")
    workflow.add_edge("retrieve", "grade")
    workflow.add_edge("grade", "generate")
    workflow.add_edge("generate", "verify")

    workflow.add_conditional_edges(
        "verify",
        should_retry,
        {
            "retry": "generate",
            "finish": "finalize",
        },
    )

    workflow.add_edge("finalize", END)

    return workflow.compile()


_graph = None


def run_research(
    question: str,
    task: str = "Answer a question",
    top_k: int = 5,
) -> dict:
    """Execute the agent and return the answer, evidence, and activity."""
    global _graph

    if _graph is None:
        _graph = build_graph()

    initial_state: AgentState = {
        "question": question,
        "task": task,
        "top_k": top_k,
        "evidence": [],
        "answer": "",
        "attempts": 0,
        "citations_valid": False,
        "provider": "unknown",
        "activity": [],
    }

    state = _graph.invoke(initial_state)

    evidence = state.get("evidence", [])
    answer = state.get("answer", "")

    markdown = (
        "# DocuMind AI Research\n\n"
        f"{answer}\n\n"
        "## Retrieved Evidence\n"
    )

    for index, item in enumerate(evidence, start=1):
        markdown += (
            f"\n### [E{index}] {item['source']} — "
            f"page {item['page']}\n\n"
            f"{item['text']}\n"
        )

    return {
        "answer": answer,
        "evidence": evidence,
        "attempts": state.get("attempts", 0),
        "citations_valid": state.get("citations_valid", False),
        "provider": state.get("provider", "unknown"),
        "activity": state.get("activity", []),
        "markdown": markdown,
    }