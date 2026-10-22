from __future__ import annotations

import os

from google import genai


class GeminiProvider:
    """Google Gemini API adapter."""

    name = "gemini"

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=api_key,
        )

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.8-flash",
        )

    def generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        answer = getattr(response, "text", None)

        if not answer:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return answer.strip()