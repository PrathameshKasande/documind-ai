# DocuMind AI — Agentic Research Assistant

Research across documents. Verify the evidence. Deliver reliable answers.

DocuMind AI is a document research assistant built with Python, Streamlit,
LangGraph, ChromaDB, sentence-transformers, and language model APIs.

## Features

- Upload and index multiple text-based PDF documents.
- Extract page-level text and metadata.
- Split documents into overlapping chunks.
- Perform semantic and BM25 keyword retrieval.
- Generate evidence-grounded answers using Gemini.
- Use Hugging Face Inference as a configured fallback.
- Run a bounded LangGraph research workflow.
- Display evidence passages and page references.
- Export research answers as Markdown.
- Evaluate retrieval and answer overlap in the backend.
- Run tests and package the app with Docker.

## Requirements

- Python 3.11
- A Gemini API key for model-generated answers
- Internet access for model/API calls and the initial embedding-model download

## Setup on Windows PowerShell

Create and activate a virtual environment:

    py -3.11 -m venv .venv
    .\.venv\Scripts\Activate.ps1

Install the project:

    python -m pip install --upgrade pip
    pip install -e .

Create the environment file:

    Copy-Item .env.example .env

Edit `.env` and add your Gemini API key.

Get a key from:
https://aistudio.google.com/

Never commit `.env` or share your API key.

## Run the application

    streamlit run app.py

Open the local URL shown in the terminal, usually:
http://localhost:8501

Upload one or more text-based PDFs, click **Index documents**, enter a
question, and click **Research**.

## Run tests

    pytest -q

## Run evaluation

    python -m documind.evaluation.run_evaluation

The included dataset is only a starter example. Replace it with a labeled,
verified benchmark before reporting metrics or making accuracy claims.

## Docker

Ensure Docker Desktop is installed and running. Create `.env`, then run:

    docker compose up --build

Open:
http://localhost:8501

## Limitations and security

- Scanned PDFs require OCR; text extraction alone cannot read image-only pages.
- Local ChromaDB persistence may not survive redeployment on some free hosting
  platforms.
- The starter app is not a production multi-user service.
- Add authentication, per-user document isolation, upload limits, data deletion,
  and durable storage before deploying to multiple users.
- Treat uploaded documents as untrusted content, never as agent instructions.
- Citation checks validate source/page references; they do not prove semantic
  entailment for every claim.
- Automated lexical-overlap metrics are not a substitute for human evaluation.
- API model availability, free quotas, and model IDs may change.