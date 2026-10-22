from __future__ import annotations

import re
from pathlib import Path


CITATION_PATTERN = re.compile(
    r"\[(?:E\d+,\s*)?([^,\]\n]+),\s*p(?:age)?\.?\s*(\d+)\]",
    flags=re.IGNORECASE,
)


def verify_citations(
    answer: str,
    evidence: list[dict],
) -> dict:
    """Check cited source/page pairs against retrieved evidence."""
    known_pairs = set()

    for item in evidence:
        source = str(item.get("source", ""))
        page = int(item.get("page", -1))

        known_pairs.add(
            (source.casefold(), page)
        )

        known_pairs.add(
            (Path(source).name.casefold(), page)
        )

    citations = []

    for match in CITATION_PATTERN.finditer(answer):
        source = match.group(1).strip().strip("'\"")
        page = int(match.group(2))
        source_basename = Path(source).name.casefold()

        exists = (
            (source.casefold(), page) in known_pairs
            or (source_basename, page) in known_pairs
        )

        citations.append(
            {
                "source": source,
                "page": page,
                "exists": exists,
            }
        )

    valid = (
        bool(citations)
        and all(
            citation["exists"]
            for citation in citations
        )
    )

    return {
        "valid": valid,
        "citations": citations,
        "count": len(citations),
    }