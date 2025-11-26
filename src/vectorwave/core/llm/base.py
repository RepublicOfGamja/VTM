from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class BaseLLMClient(ABC):
    """
    Abstract interface that all LLM Providers (OpenAI, Anthropic, etc.) must implement.
    Implementations must handle internal token usage logging.
    """

    @abstractmethod
    def create_embedding(self, text: str, model: str, category: str = "default") -> Optional[List[float]]:
        """
        Generates text embeddings.

        Args:
            text: The text to embed.
            model: The name of the model to use.
            category: Category for aggregating token usage (e.g., 'execution_log', 'auto_doc').

        Returns:
            The generated list of embedding vectors (None on failure).
        """
        pass

    @abstractmethod
    def create_chat_completion(
            self,
            messages: List[Dict],
            model: str,
            temperature: float = 0.1,
            response_format: Optional[Dict] = None,
            category: str = "default"
    ) -> Optional[str]:
        """
        Generates a chat completion (response).

        Args:
            messages: List of conversation messages [{"role": "user", "content": "..."}].
            model: The name of the model to use.
            temperature: Parameter for controlling generation diversity.
            response_format: Response format (e.g., {"type": "json_object"}).
            category: Category for aggregating token usage (e.g., 'execution_log', 'auto_doc').

        Returns:
            The generated text response (None on failure).
        """
        pass