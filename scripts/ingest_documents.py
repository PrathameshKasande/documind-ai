from __future__ import annotations

import argparse
from pathlib import Path

from documind.ingestion.chunking import chunk_pages
from documind.ingestion.indexing import index_chunks
from documind.ingestion.loaders import load_pdf


def main():
    parser = argparse.ArgumentParser(
        description="Index PDF files for DocuMind AI."
    )

    parser.add_argument(
        "directory",
        help="Path to the directory containing PDF files.",
    )

    args = parser.parse_args()

    directory = Path(args.directory)

    if not directory.exists() or not directory.is_dir():
        raise SystemExit(
            f"Directory does not exist: {directory}"
        )

    pdf_paths = sorted(directory.glob("*.pdf"))

    if not pdf_paths:
        raise SystemExit(
            "No PDF files found in the specified directory."
        )

    total_chunks = 0

    for pdf_path in pdf_paths:
        pages = load_pdf(str(pdf_path))
        chunks = chunk_pages(pages)
        indexed = index_chunks(chunks)

        total_chunks += indexed

        print(
            f"{pdf_path.name}: indexed {indexed} chunks"
        )

    print(
        f"Finished. Total chunks indexed: {total_chunks}"
    )


if __name__ == "__main__":
    main()