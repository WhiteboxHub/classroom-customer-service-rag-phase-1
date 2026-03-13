"""
embedding_model.py
Generates dense vector embeddings using sentence-transformers.

Model: all-MiniLM-L6-v2  (384-dimensional, cosine-friendly)
Download happens automatically on first use (~80 MB).

Usage:
    model = EmbeddingModel()
    vec   = model.embed("Hello world")           # → List[float], len 384
    vecs  = model.embed_batch(["a", "b", "c"])   # → List[List[float]]
"""
from typing import List

from app.core.config import settings

_model_instance = None


def _get_model():
    """Lazy-load the SentenceTransformer model (singleton)."""
    global _model_instance
    if _model_instance is None:
        from sentence_transformers import SentenceTransformer
        print(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _model_instance = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model_instance


class EmbeddingModel:
    """
    Wraps SentenceTransformer to produce normalised float-list embeddings.

    The model is a process-level singleton — loaded once and reused.
    """

    def embed(self, text: str) -> List[float]:
        """
        Encode a single string.

        Args:
            text: Any natural-language string.

        Returns:
            384-dimensional float list (cosine-normalised).
        """
        model = _get_model()
        vector = model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Encode multiple strings in one efficient forward pass.

        Args:
            texts:      List of strings to embed.
            batch_size: Internal mini-batch size for the model.

        Returns:
            List of 384-dimensional float lists, one per input string.
        """
        model = _get_model()
        vectors = model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 50,
        )
        return [v.tolist() for v in vectors]
