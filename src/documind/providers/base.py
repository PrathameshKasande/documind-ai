from __future__ import annotations

from typing import Protocol


class LLMProvider(Protocol):
    """Interface required from an LLM provider."""

    name: str

    def generate(self, prompt: str) -> str:
        """Generate a text response from a prompt."""
        ...