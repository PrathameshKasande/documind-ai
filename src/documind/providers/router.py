from __future__ import annotations

import logging
import os

from documind.providers.gemini import GeminiProvider
from documind.providers.huggingface import HuggingFaceProvider

logger = logging.getLogger(__name__)


def generate_answer(prompt: str) -> tuple[str, str]:
    """
    Generate an answer using the preferred provider.

    If it fails, try the other configured provider. Only provider
    names and exception classes are logged, not prompt contents,
    document text, or API keys.
    """
    providers = {
        "gemini": GeminiProvider,
        "huggingface": HuggingFaceProvider,
    }

    preferred = os.getenv(
        "LLM_PROVIDER",
        "gemini",
    ).strip().lower()

    if preferred not in providers:
        raise RuntimeError(
            f"Unsupported LLM_PROVIDER: {preferred}"
        )

    order = [preferred] + [
        name
        for name in providers
        if name != preferred
    ]

    errors = []

    for provider_name in order:
        provider_class = providers[provider_name]

        try:
            provider = provider_class()
            answer = provider.generate(prompt)

            logger.info(
                "Generation succeeded using provider=%s",
                provider_name,
            )

            return answer, provider_name

        except Exception as exc:
            logger.warning(
                "Provider %s failed with %s",
                provider_name,
                type(exc).__name__,
            )

            errors.append(
                f"{provider_name}: {type(exc).__name__}"
            )

    raise RuntimeError(
        "No configured LLM provider succeeded. "
        + "; ".join(errors)
    )