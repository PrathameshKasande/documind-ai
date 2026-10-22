import pytest

from documind.evaluation.retrieval_metrics import retrieval_metrics


def test_retrieval_metrics():
    result = retrieval_metrics(
        ranked_ids=["a", "b", "c"],
        relevant_ids={"b", "z"},
        k=3,
    )

    assert result["hit_rate@3"] == 1.0
    assert result["recall@3"] == 0.5
    assert result["precision@3"] == pytest.approx(1 / 3)
    assert result["mrr"] == 0.5


def test_no_relevant_results():
    result = retrieval_metrics(
        ranked_ids=["a", "b"],
        relevant_ids={"z"},
        k=2,
    )

    assert result["hit_rate@2"] == 0.0
    assert result["recall@2"] == 0.0
    assert result["mrr"] == 0.0