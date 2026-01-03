# classroom-customer-service-rag-phase-1\backend\app\api\v1\ingest.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class IngestRequest(BaseModel):
    source_type: str
    source_url: str
    pipeline_config: Optional[dict] = {}

@router.post("/ingest")
async def trigger_ingestion(request: IngestRequest):
    return {"job_id": "job-123", "status": "pending", "message": "Ingestion started"}

@router.get("/ingest/{job_id}")
async def get_ingestion_status(job_id: str):
    return {"job_id": job_id, "status": "completed", "processed_docs": 10}
