from __future__ import annotations

from documind.citations.verifier import verify_citations
from documind.retrieval.hybrid_search import hybrid_search


def search_documents(
    question: str,
    k: int = 5,
) -> list[dict]:
    """Search indexed documents using hybrid retrieval."""
    return hybrid_search(
        question=question,
        k=k,
    )


def compare_evidence(
    evidence: list[dict],
) -> str:
    """Format passages from multiple documents for comparison."""
    sections = []

    for item in evidence:
        sections.append(
            f"Document: {item['source']}\n"
            f"Page: {item['page']}\n"
            f"Evidence:\n{item['text']}"
        )

    return "\n\n---\n\n".join(sections)


def validate_answer(
    answer: str,
    evidence: list[dict],
) -> dict:
    """Validate cited source/page references."""
    return verify_citations(
        answer=answer,
        evidence=evidence,
    )