"""
backfill_embeddings.py
Backfill embeddings using the multilingual embedding model
and ensure language metadata is present.
"""

import asyncio

from app.services.generation.embeddings import EmbeddingService
from app.services.ingestion.language_detection import LanguageDetector
from app.services.retrieval.vector_store.milvus import MilvusClient


async def backfill():
    print("Starting embedding backfill...")

    embedder = EmbeddingService()
    detector = LanguageDetector()
    vector_store = MilvusClient()

    # NOTE:
    # This assumes you have a way to iterate existing records.
    # In production, this is typically:
    # - a DB table
    # - a document store
    # - or a Milvus export job
    #
    # Here we show the SAFE pattern.

    documents = []  # TODO: replace with real document fetch

    for doc in documents:
        text = doc["text"]
        metadata = doc.get("metadata", {})

        language = metadata.get("language")
        if not language:
            language = detector.detect_language(text)
            metadata["language"] = language

        embedding = embedder.get_embedding(text)

        await vector_store.upsert(
            chunks=[text],
            metadata=[metadata],
            embeddings=[embedding],
        )

    print("Embedding backfill completed.")


def main():
    asyncio.run(backfill())


if __name__ == "__main__":
    main()
