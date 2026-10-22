from __future__ import annotations

from pathlib import Path

import fitz


def load_pdf_bytes(
    pdf_bytes: bytes,
    filename: str,
) -> list[dict]:
    """Extract non-empty page text from PDF bytes."""
    pages: list[dict] = []

    with fitz.open(
        stream=pdf_bytes,
        filetype="pdf",
    ) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text").strip()

            if text:
                pages.append(
                    {
                        "text": text,
                        "source": Path(filename).name,
                        "page": page_number,
                    }
                )

    return pages


def load_pdf(path: str) -> list[dict]:
    """Load a PDF from a local filesystem path."""
    pdf_path = Path(path)

    with pdf_path.open("rb") as file:
        return load_pdf_bytes(
            file.read(),
            pdf_path.name,
        )