from __future__ import annotations

import hashlib


def chunk_pages(
    pages: list[dict],
    chunk_size: int = 1800,
    overlap: int = 250,
) -> list[dict]:
    """
    Split page text into overlapping chunks.

    Every chunk retains its source filename and original page number.
    The chunk UID is a stable hash of its content and metadata.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be non-negative and smaller than chunk_size."
        )

    chunks: list[dict] = []
    step = chunk_size - overlap

    for page in pages:
        text = page["text"].strip()

        if not text:
            continue

        start = 0
        local_id = 0

        while start < len(text):
            piece = text[start:start + chunk_size].strip()

            if piece:
                source = str(page["source"])
                page_number = int(page["page"])

                raw_id = (
                    f"{source}|{page_number}|{local_id}|{piece}"
                )

                chunk_uid = hashlib.sha256(
                    raw_id.encode("utf-8")
                ).hexdigest()

                chunks.append(
                    {
                        "text": piece,
                        "source": source,
                        "page": page_number,
                        "chunk_id": local_id,
                        "chunk_uid": chunk_uid,
                    }
                )

            if start + chunk_size >= len(text):
                break

            start += step
            local_id += 1

    return chunks