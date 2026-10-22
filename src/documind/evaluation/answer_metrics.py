
import re
from collections import Counter


def _tokens(text: str) -> list[str]:
    """Normalize text into lowercase word tokens."""
    return re.findall(r"\b[\w]+\b", (text or "").lower())


def basic_answer_metrics(
    answer: str,
    expected_answer: str,
) -> dict[str, float]:
    """
    Calculate token-overlap precision, recall, and F1.

    These metrics measure lexical overlap only. They do not establish
    factual correctness, semantic equivalence, or citation support.
    """
    predicted = Counter(_tokens(answer))
    expected = Counter(_tokens(expected_answer))

    if not predicted and not expected:
        return {
            "token_precision": 1.0,
            "token_recall": 1.0,
            "token_f1": 1.0,
        }

    overlap = sum((predicted & expected).values())

    precision = overlap / sum(predicted.values()) if predicted else 0.0
    recall = overlap / sum(expected.values()) if expected else 0.0

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "token_precision": round(precision, 4),
        "token_recall": round(recall, 4),
        "token_f1": round(f1, 4),
    }
