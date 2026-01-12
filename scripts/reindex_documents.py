"""
reindex_documents.py
Reindex documents using the current ingestion pipeline.
"""

import asyncio

from app.services.ingestion.orchestrator import IngestionOrchestrator


async def reindex():
    print("Starting document reindexing...")

    orchestrator = IngestionOrchestrator()

    # NOTE:
    # Replace this with your real document source
    # (DB, filesystem, object storage, etc.)
    documents = []  # TODO: fetch documents to reindex

    for doc in documents:
        metadata = {
            "id": doc["id"],
            "source": doc.get("source", doc["id"]),
        }
        content = doc["content"]

        await orchestrator.ingest_document(metadata, content)

    print("Document reindexing completed.")


def main():
    asyncio.run(reindex())


if __name__ == "__main__":
    main()
