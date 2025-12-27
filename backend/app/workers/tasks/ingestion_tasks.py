"""
ingestion_tasks.py
Celery tasks for document ingestion.
"""
from app.workers.celery_app import celery_app
from app.services.ingestion.orchestrator import IngestionOrchestrator
import asyncio

@celery_app.task(name="ingest_pipeline")
def run_ingest_pipeline(doc_id: str, content: str):
    print(f"Task received: ingest_pipeline for {doc_id}")
    
    # Run async orchestrator in sync task
    orchestrator = IngestionOrchestrator()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(orchestrator.ingest_document({"id": doc_id}, content))
    
    return {"status": "success", "doc_id": doc_id}
