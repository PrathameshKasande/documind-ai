
def retrieval_metrics(
    ranked_ids: list[str],
    relevant_ids: list[str],
    k: int = 5,
) -> dict[str, float | int | None]:
    """
    Calculate retrieval metrics using verified relevant chunk IDs.

    ranked_ids: retrieved chunk IDs, ordered by relevance score.
    relevant_ids: ground-truth relevant chunk IDs, labeled by a reviewer.
    """
    if k < 1:
        raise ValueError("k must be at least 1")

    ranked = ranked_ids[:k]
    relevant = set(relevant_ids)

    if not relevant:
        return {
            "recall_at_k": None,
            "precision_at_k": None,
            "hit_rate_at_k": None,
            "mrr": None,
            "relevance_labels_available": False,
        }

    hits = [chunk_id for chunk_id in ranked if chunk_id in relevant]
    first_rank = next(
        (
            rank
            for rank, chunk_id in enumerate(ranked, start=1)
            if chunk_id in relevant
        ),
        None,
    )

    return {
        "recall_at_k": round(len(set(hits)) / len(relevant), 4),
        "precision_at_k": round(len(set(hits)) / k, 4),
        "hit_rate_at_k": int(bool(hits)),
        "mrr": round(1 / first_rank, 4) if first_rank else 0.0,
        "relevance_labels_available": True,
    }
