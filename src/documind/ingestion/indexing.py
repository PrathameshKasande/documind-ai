from __future__ import annotations

import chromadb
from sentence_transformers import SentenceTransformer

from documind.config import get_setting

_embedder = None
_client = None
_collection = None


def get_embedder() -> SentenceTransformer:
    """Load and reuse the configured local embedding model."""
    global _embedder

    if _embedder is None:
        model_name = get_setting(
            "EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2",
        )

        _embedder = SentenceTransformer(model_name)

    return _embedder


def get_collection():
    """Return the persistent ChromaDB collection."""
    global _client, _collection

    if _collection is None:
        database_path = get_setting(
            "CHROMA_PATH",
            "chroma_db",
        )

        _client = chromadb.PersistentClient(
            path=database_path,
        )

        _collection = _client.get_or_create_collection(
            name="documind_chunks",
            metadata={"hnsw:space": "cosine"},
        )

    return _collection


def index_chunks(chunks: list[dict]) -> int:
    """Embed and upsert chunks; return the number processed."""
    if not chunks:
        return 0

    embedder = get_embedder()
    collection = get_collection()

    texts = [
        item["text"]
        for item in chunks
    ]

    vectors = embedder.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).tolist()

    ids = [
        item.get("chunk_uid")
        or (
            f'{item["source"]}:'
            f'{item["page"]}:'
            f'{item["chunk_id"]}'
        )
        for item in chunks
    ]

    metadatas = []

    for index, item in enumerate(chunks):
        metadatas.append(
            {
                "source": str(item["source"]),
                "page": int(item["page"]),
                "chunk_id": int(item["chunk_id"]),
                "chunk_uid": ids[index],
            }
        )

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=vectors,
        metadatas=metadatas,
    )

    return len(chunks)