import os
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        # Initialize local embedding model: intfloat/e5-base-v2
        # Dimensions: 768
        self.model = SentenceTransformer('intfloat/e5-base-v2')
        self.dimension = 768

    def get_embedding(self, text: str, is_query: bool = True) -> list[float]:
        """
        Generates embedding for a single text.
        E5 models require 'query: ' prefix for queries and 'passage: ' for documents.
        """
        prefix = "query: " if is_query else "passage: "
        text = prefix + text.replace("\n", " ")
        
        try:
            embedding = self.model.encode(text).tolist()
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return [0.0] * self.dimension

    def get_embeddings(self, texts: list[str], is_query: bool = False) -> list[list[float]]:
        """
        Generates embeddings for a list of texts (batch).
        Default is_query=False because this is mostly used during ingestion (passages).
        """
        prefix = "query: " if is_query else "passage: "
        processed_texts = [prefix + t.replace("\n", " ") for t in texts]
        
        try:
            embeddings = self.model.encode(processed_texts).tolist()
            return embeddings
        except Exception as e:
            print(f"Error generating embeddings batch: {e}")
            return [[0.0] * self.dimension for _ in texts]
