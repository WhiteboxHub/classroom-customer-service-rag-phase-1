"""
ingestion_tasks.py
Celery tasks for document ingestion.
"""

import asyncio
from app.workers.celery_app import celery_app
from app.services.ingestion.orchestrator import IngestionOrchestrator


@celery_app.task(name="ingest_pipeline")
def run_ingest_pipeline(doc_id: str, content: str):
    """
    Background ingestion task.

    Uses the SAME ingestion orchestrator as synchronous ingestion,
    ensuring:
    - chunk-level language detection
    - consistent metadata enrichment
    - identical storage behavior
    """
    print(f"Task received: ingest_pipeline for {doc_id}")

    orchestrator = IngestionOrchestrator()

    metadata = {
        "id": doc_id,
        "source": doc_id,  # keep parity with sync ingestion
    }

    # Run async orchestrator in sync Celery task
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(
        orchestrator.ingest_document(metadata, content)
    )

    return {
        "status": "success",
        "doc_id": doc_id,
    }
