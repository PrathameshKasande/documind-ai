class OllamaProvider:
    """Placeholder for a future local Ollama adapter."""

    name = "ollama"

    def __init__(self):
        raise RuntimeError(
            "Ollama is not configured. Use Gemini or Hugging Face."
        )