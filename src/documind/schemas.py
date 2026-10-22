from __future__ import annotations

from typing import TypedDict


class PageRecord(TypedDict):
    text: str
    source: str
    page: int


class ChunkRecord(TypedDict):
    text: str
    source: str
    page: int
    chunk_id: int
    chunk_uid: str


class EvidenceRecord(TypedDict, total=False):
    text: str
    source: str
    page: int
    chunk_id: int
    chunk_uid: str
    score: float
    distance: float