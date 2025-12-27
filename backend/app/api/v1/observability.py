from fastapi import APIRouter

router = APIRouter()

@router.get("/metrics/summary")
async def get_metrics_summary():
    return {
        "active_users": 12,
        "total_requests": 1500,
        "avg_latency_ms": 120
    }

@router.get("/health/detailed")
async def detailed_health():
    return {
        "database": "healthy",
        "redis": "healthy",
        "milvus": "unknown",
        "disk_space": "ok"
    }
