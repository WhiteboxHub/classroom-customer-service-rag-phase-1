import os
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        # Initialize local embedding model (CPU-friendly, fast)
        # 384 dimensions for all-MiniLM-L6-v2
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def get_embedding(self, text: str) -> list[float]:
        text = text.replace("\n", " ")
        try:
            # Generate embedding
            embedding = self.model.encode(text).tolist()
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # all-MiniLM-L6-v2 has 384 dimensions
            return [0.0] * 384 

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        # clean newlines
        texts = [t.replace("\n", " ") for t in texts]
        try:
            embeddings = self.model.encode(texts).tolist()
            return embeddings
        except Exception as e:
            print(f"Error generating embeddings batch: {e}")
            return [[0.0]*384 for _ in texts]
