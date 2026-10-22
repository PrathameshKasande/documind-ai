from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    question: str
    task: str
    top_k: int
    evidence: list[dict]
    answer: str
    attempts: int
    citations_valid: bool
    provider: str
    activity: list[str]