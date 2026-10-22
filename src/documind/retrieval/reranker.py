from __future__ import annotations


def rerank(
    question: str,
    passages: list[dict],
    top_n: int = 5,
) -> list[dict]:
    """
    Baseline reranker interface.

    Currently preserves the hybrid search order. A cross-encoder
    can replace this implementation when needed.
    """
    if top_n < 1:
        return []

    return passages[:top_n]