def test_provider_modules_import():
    from documind.providers.gemini import GeminiProvider
    from documind.providers.huggingface import HuggingFaceProvider

    assert GeminiProvider.name == "gemini"
    assert HuggingFaceProvider.name == "huggingface"