from __future__ import annotations

from documind.ingestion.indexing import (
    get_collection,
    get_embedder,
)


def semantic_search(
    question: str,
    k: int = 5,
) -> list[dict]:
    """Find the nearest document chunks using vector similarity."""
    if k < 1:
        return []

    collection = get_collection()
    count = collection.count()

    if count == 0:
        return []

    query_vector = get_embedder().encode(
        [question],
        normalize_embeddings=True,
        show_progress_bar=False,
    ).tolist()[0]

    result = collection.query(
        query_embeddings=[query_vector],
        n_results=min(k, count),
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    matches = []

    for text, metadata, distance in zip(
        documents,
        metadatas,
        distances,
    ):
        matches.append(
            {
                "text": text,
                "source": metadata["source"],
                "page": metadata["page"],
                "chunk_id": metadata.get("chunk_id", 0),
                "chunk_uid": metadata.get("chunk_uid", ""),
                "distance": float(distance),
                "score": 1.0 - float(distance),
            }
        )

    return matches