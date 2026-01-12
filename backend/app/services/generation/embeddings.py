# classroom-customer-service-rag-phase-1/backend/app/services/generation/embeddings.py

from sentence_transformers import SentenceTransformer
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        """
        Centralized embedding service.

        Uses a multilingual sentence-transformer model to ensure:
        - Single shared vector space
        - Cross-lingual retrieval
        - No pipeline restructuring
        """
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.model = SentenceTransformer(self.model_name)

        # Capture embedding dimension dynamically
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

        logger.info(
            f"EmbeddingService initialized with model={self.model_name}, "
            f"dim={self.embedding_dim}"
        )

    def get_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for a single text input.
        """
        try:
            embedding = self.model.encode(
                text,
                normalize_embeddings=True
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return [0.0] * self.embedding_dim

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a batch of texts.
        """
        try:
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=True
            )
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Error generating embeddings batch: {e}")
            return [[0.0] * self.embedding_dim for _ in texts]
