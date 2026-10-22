from documind.citations.verifier import verify_citations


def test_valid_source_and_page():
    evidence = [
        {
            "source": "sample.pdf",
            "page": 3,
            "text": "Evidence from page three.",
        }
    ]

    result = verify_citations(
        "The report states this fact [E1, sample.pdf, p. 3].",
        evidence,
    )

    assert result["valid"] is True
    assert result["count"] == 1


def test_unknown_source_is_invalid():
    evidence = [
        {
            "source": "sample.pdf",
            "page": 3,
            "text": "Evidence from page three.",
        }
    ]

    result = verify_citations(
        "The report states this fact [missing.pdf, p. 8].",
        evidence,
    )

    assert result["valid"] is False


def test_missing_citations_are_not_valid():
    evidence = [
        {
            "source": "sample.pdf",
            "page": 1,
            "text": "Some evidence.",
        }
    ]

    result = verify_citations(
        "This answer contains no citations.",
        evidence,
    )

    assert result["valid"] is False