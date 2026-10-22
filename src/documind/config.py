
from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def get_setting(
    name: str,
    default: str | None = None,
) -> str | None:
    """Read a setting from Streamlit secrets or environment variables."""
    try:
        value = st.secrets.get(name)
        if value is not None:
            return str(value)
    except Exception:
        # Streamlit secrets may not be configured locally.
        pass

    return os.getenv(name, default)


def get_int(name: str, default: int) -> int:
    """Read an integer setting with a safe default."""
    try:
        return int(get_setting(name, str(default)) or default)
    except (TypeError, ValueError):
        return default
