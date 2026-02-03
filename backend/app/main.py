# classroom-customer-service-rag-phase-1\backend\app\main.py
from fastapi import FastAPI
from app.core.config import settings
from app.api.v1 import chat, ingest, admin, eval, database, observability

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# =================================================
# OpenAI-compatible routes (ROOT)
# =================================================
app.include_router(chat.router, prefix="/v1", tags=["openai"])

# =================================================
# Internal versioned API
# =================================================
app.include_router(chat.router, prefix=settings.API_V1_STR, tags=["chat"])
app.include_router(ingest.router, prefix=settings.API_V1_STR, tags=["ingestion"])
app.include_router(admin.router, prefix=settings.API_V1_STR, tags=["admin"])
app.include_router(eval.router, prefix=settings.API_V1_STR, tags=["evaluation"])
app.include_router(database.router, prefix=settings.API_V1_STR, tags=["database"])
app.include_router(observability.router, prefix=settings.API_V1_STR, tags=["observability"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
