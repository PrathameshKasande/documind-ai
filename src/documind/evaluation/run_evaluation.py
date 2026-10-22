from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean

from documind.agent.graph import run_research
from documind.evaluation.answer_metrics import basic_answer_metrics
from documind.retrieval.hybrid_search import hybrid_search


def run(
    dataset_path: Path,
    output_path: Path,
) -> dict:
    """Evaluate questions in a JSONL dataset and save a JSON report."""
    with dataset_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        dataset = [
            json.loads(line)
            for line in file
            if line.strip()
        ]

    results = []

    for case in dataset:
        question = case["question"]

        retrieved = hybrid_search(
            question,
            k=5,
        )

        research = run_research(
            question=question,
            task="Answer a question",
            top_k=5,
        )

        answer_metrics = basic_answer_metrics(
            answer=research.get("answer", ""),
            expected_answer=case.get("expected_answer", ""),
        )

        results.append(
            {
                "id": case.get("id"),
                "question": question,
                "answerable": case.get("answerable"),
                "retrieved_count": len(retrieved),
                "provider": research.get("provider"),
                "citations_valid": research.get("citations_valid"),
                "answer_metrics": answer_metrics,
                "answer": research.get("answer", ""),
            }
        )

    summary = {
        "note": (
            "Starter report. Token overlap is not semantic correctness. "
            "Use verified labels and a held-out test set before reporting "
            "performance claims."
        ),
        "num_questions": len(results),
        "mean_token_f1": (
            mean([
                item["answer_metrics"]["token_f1"]
                for item in results
            ])
            if results
            else 0.0
        ),
        "mean_retrieved_count": (
            mean([
                item["retrieved_count"]
                for item in results
            ])
            if results
            else 0.0
        ),
        "results": results,
    }

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate the DocuMind AI research workflow."
    )

    parser.add_argument(
        "--dataset",
        default="src/documind/evaluation/dataset.jsonl",
    )

    parser.add_argument(
        "--output",
        default="evaluation-results.json",
    )

    args = parser.parse_args()

    summary = run(
        dataset_path=Path(args.dataset),
        output_path=Path(args.output),
    )

    print(
        json.dumps(
            {
                key: value
                for key, value in summary.items()
                if key != "results"
            },
            indent=2,
        )
    )

    print(f"Detailed report saved to: {args.output}")


if __name__ == "__main__":
    main()