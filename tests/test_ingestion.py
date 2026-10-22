from documind.ingestion.chunking import chunk_pages


def test_chunk_pages_preserves_metadata():
    pages = [
        {
            "text": "abcdefghij" * 10,
            "source": "sample.pdf",
            "page": 2,
        }
    ]

    chunks = chunk_pages(
        pages,
        chunk_size=30,
        overlap=5,
    )

    assert chunks
    assert all(
        chunk["source"] == "sample.pdf"
        for chunk in chunks
    )
    assert all(
        chunk["page"] == 2
        for chunk in chunks
    )
    assert all(
        chunk["chunk_uid"]
        for chunk in chunks
    )


def test_empty_pages_produce_no_chunks():
    assert chunk_pages([]) == []


def test_invalid_overlap_is_rejected():
    import pytest

    with pytest.raises(ValueError):
        chunk_pages(
            [{"text": "example", "source": "a.pdf", "page": 1}],
            chunk_size=10,
            overlap=10,
        )