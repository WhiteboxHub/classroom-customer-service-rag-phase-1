"""
ingest.py
Ingestion API routes — triggers the GraphRAG ingestion pipeline.

POST /api/v1/ingest        — ingest a document from raw text or S3 key
GET  /api/v1/ingest/{job_id} — check job status (stub; extend with Celery)
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from app.services.ingestion.orchestrator import IngestionOrchestrator

router = APIRouter()


class IngestRequest(BaseModel):
    source_type: str          # "text" | "s3"
    source_url: str           # S3 key or document identifier
    content: Optional[str] = None   # raw text (used when source_type="text")
    pipeline_config: Optional[dict] = {}


# Module-level orchestrator instance (shared across requests)
_orchestrator: Optional[IngestionOrchestrator] = None


def _get_orchestrator() -> IngestionOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = IngestionOrchestrator()
    return _orchestrator


async def _run_ingestion(request: IngestRequest):
    """Background task that runs the full ingestion pipeline."""
    orchestrator = _get_orchestrator()

    if request.source_type == "text":
        if not request.content:
            raise ValueError("content must be provided when source_type='text'")
        await orchestrator.ingest_document(
            document_metadata={"id": request.source_url},
            content=request.content,
        )

    elif request.source_type == "s3":
        # Load from S3 then ingest
        from app.services.ingestion.loaders.s3 import S3Loader
        loader = S3Loader()
        content = loader.load(request.source_url)
        await orchestrator.ingest_document(
            document_metadata={"id": request.source_url},
            content=content,
        )
    else:
        raise ValueError(f"Unsupported source_type: {request.source_type}")


@router.post("/ingest")
async def trigger_ingestion(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
):
    """
    Trigger document ingestion into the Neo4j knowledge graph.

    - source_type="text": provide raw text in the `content` field.
    - source_type="s3":   provide an S3 object key in `source_url`.

    The ingestion runs as a FastAPI background task so the response is
    returned immediately. For production, replace with a Celery task.
    """
    job_id = f"job-{request.source_url.replace('/', '-')}"
    background_tasks.add_task(_run_ingestion, request)
    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"Ingestion started for '{request.source_url}'",
    }


from fastapi import APIRouter, HTTPException, BackgroundTasks, File, UploadFile
import io
import PyPDF2

@router.post("/ingest/pdf")
async def trigger_pdf_ingestion(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a PDF file, extract its text, and trigger ingestion into the Neo4j knowledge graph.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    try:
        # Read file contents into memory
        contents = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
        
        extracted_text = ""
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
                
        if not extracted_text.strip():
            raise ValueError("No extractable text found in PDF.")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")
        
    # Trigger background ingestion using the extracted text
    orchestrator = _get_orchestrator()
    job_id = f"job-pdf-{file.filename.replace('/', '-')}"
    
    background_tasks.add_task(
        orchestrator.ingest_document,
        document_metadata={"id": file.filename},
        content=extracted_text
    )
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"PDF Extraction complete. Graph Ingestion started for '{file.filename}'",
        "extracted_length": len(extracted_text)
    }

@router.get("/ingest/{job_id}")
async def get_ingestion_status(job_id: str):
    """Return ingestion job status (stub — extend with Celery result backend)."""
    return {"job_id": job_id, "status": "completed", "message": "Check Neo4j for graph data"}
