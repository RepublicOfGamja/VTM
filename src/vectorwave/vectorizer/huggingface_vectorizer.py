from .base import BaseVectorizer
from typing import List
import os
import logging

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    logger.warning("The 'sentence-transformers' library is not installed.")
    logger.warning("To use HuggingFaceVectorizer, run 'pip install sentence-transformers'.")
    SentenceTransformer = None

class HuggingFaceVectorizer(BaseVectorizer):
    """[NEW] HuggingFace SentenceTransformer (Python Client) implementation"""

    def __init__(self, model_name: str):
        if SentenceTransformer is None:
            # Could not find the 'sentence-transformers' library.
            raise ImportError("Could not find the 'sentence-transformers' library.")

        # Force use of CPU (can be changed to 'cuda', etc., if needed)
        self.model = SentenceTransformer(model_name, device='cpu')
        logger.info("HuggingFaceVectorizer loaded model '%s' on CPU.", model_name)

    def embed(self, text: str) -> List[float]:
        # convert_to_numpy=True is faster on CPU
        vector = self.model.encode([text], convert_to_numpy=True)[0]
        return vector.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        vectors = self.model.encode(texts, convert_to_numpy=True)
        return vectors.tolist()