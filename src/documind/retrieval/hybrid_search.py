from __future__ import annotations

import re

from rank_bm25 import BM25Okapi

from documind.ingestion.indexing import get_collection
from documind.retrieval.vector_store import semantic_search


def tokenize(text: str) -> list[str]:
    """Tokenize text for the BM25 keyword retriever."""
    return re.findall(
        r"[A-Za-z0-9_]+",
        text.lower(),
    )


def get_all_indexed_records() -> list[dict]:
    """Load indexed text and metadata for BM25 ranking."""
    collection = get_collection()

    if collection.count() == 0:
        return []

    result = collection.get(
        include=[
            "documents",
            "metadatas",
        ],
    )

    records = []

    ids = result.get("ids", [])
    documents = result.get("documents", [])
    metadatas = result.get("metadatas", [])

    for uid, text, metadata in zip(
        ids,
        documents,
        metadatas,
    ):
        records.append(
            {
                "text": text,
                "source": metadata["source"],
                "page": metadata["page"],
                "chunk_id": metadata.get("chunk_id", 0),
                "chunk_uid": metadata.get("chunk_uid", uid),
            }
        )

    return records


def hybrid_search(
    question: str,
    k: int = 5,
) -> list[dict]:
    """
    Retrieve passages using semantic search and BM25,
    then combine ranks using reciprocal-rank fusion.
    """
    if k < 1:
        return []

    records = get_all_indexed_records()

    if not records:
        return []

    candidate_count = min(k * 3, len(records))

    semantic_results = semantic_search(
        question,
        k=candidate_count,
    )

    tokenized_corpus = [
        tokenize(record["text"])
        for record in records
    ]

    query_tokens = tokenize(question)

    if query_tokens:
        bm25 = BM25Okapi(tokenized_corpus)
        bm25_scores = bm25.get_scores(query_tokens)
    else:
        bm25_scores = [0.0] * len(records)

    bm25_ranked = sorted(
        zip(records, bm25_scores),
        key=lambda pair: pair[1],
        reverse=True,
    )[:candidate_count]

    combined_scores: dict[str, float] = {}
    record_by_uid: dict[str, dict] = {}

    # Reciprocal-rank fusion: 1 / (constant + rank)
    rank_constant = 60

    for rank, item in enumerate(
        semantic_results,
        start=1,
    ):
        uid = item["chunk_uid"]

        if not uid:
            continue

        record_by_uid[uid] = item
        combined_scores[uid] = (
            combined_scores.get(uid, 0.0)
            + 1.0 / (rank_constant + rank)
        )

    for rank, (item, _score) in enumerate(
        bm25_ranked,
        start=1,
    ):
        uid = item["chunk_uid"]

        if not uid:
            continue

        record_by_uid.setdefault(uid, item)
        combined_scores[uid] = (
            combined_scores.get(uid, 0.0)
            + 1.0 / (rank_constant + rank)
        )

    ranked_ids = sorted(
        combined_scores,
        key=combined_scores.get,
        reverse=True,
    )[:k]

    results = []

    for uid in ranked_ids:
        item = dict(record_by_uid[uid])
        item["score"] = combined_scores[uid]
        results.append(item)

    return results