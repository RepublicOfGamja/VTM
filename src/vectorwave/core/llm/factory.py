from .base import BaseLLMClient
from .openai_client import VectorWaveOpenAIClient

_llm_instance: BaseLLMClient = None


def get_llm_client() -> BaseLLMClient:
    """Returns the singleton LLM client instance."""
    global _llm_instance
    if _llm_instance is None:
        # Can be extended later to return different clients (Anthropic, etc.) based on settings (VECTORIZER, etc.)
        _llm_instance = VectorWaveOpenAIClient()
    return _llm_instance