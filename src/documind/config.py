from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def get_setting(
    name: str,
    default: str | None = None,
) -> str | None:
    """Read a configuration value from environment variables."""
    return os.getenv(name, default)


def get_int(name: str, default: int) -> int:
    """Read an integer setting with a safe default."""
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default