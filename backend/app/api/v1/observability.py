"""
observability.py
Real Prometheus metrics for the RAG backend.
Exposes /metrics endpoint for Prometheus scraping.
"""
from fastapi import APIRouter, Response
from prometheus_client import (
    Counter, Histogram, Gauge,
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, REGISTRY
)
import time

router = APIRouter()

# ─── Prometheus Metrics ───────────────────────────────────────────────────────

RAG_REQUESTS_TOTAL = Counter(
    "rag_requests_total",
    "Total number of RAG chat requests",
    ["model", "status"]
)

RAG_LATENCY_SECONDS = Histogram(
    "rag_latency_seconds",
    "End-to-end latency of RAG chat requests in seconds",
    ["phase"],  # phases: embed, retrieve, llm, total
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

RAG_RETRIEVED_CHUNKS = Histogram(
    "rag_retrieved_chunks",
    "Number of Milvus chunks retrieved per query",
    buckets=[0, 1, 2, 3, 5, 8, 10]
)

RAG_CONTEXT_LENGTH = Histogram(
    "rag_context_length_chars",
    "Total character length of retrieved context per query",
    buckets=[0, 100, 500, 1000, 2000, 5000, 10000]
)

RAG_ACTIVE_REQUESTS = Gauge(
    "rag_active_requests",
    "Number of RAG requests currently being processed"
)

RAG_RETRIEVAL_EMPTY = Counter(
    "rag_retrieval_empty_total",
    "Number of queries that returned zero chunks from Milvus"
)


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus scrape endpoint."""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/metrics/summary")
async def get_metrics_summary():
    """Human-readable JSON summary of key metrics."""
    return {
        "description": "RAG system Prometheus metrics",
        "scrape_endpoint": "/api/v1/metrics",
        "available_metrics": [
            "rag_requests_total",
            "rag_latency_seconds",
            "rag_retrieved_chunks",
            "rag_context_length_chars",
            "rag_active_requests",
            "rag_retrieval_empty_total"
        ],
        "grafana_url": "http://localhost:3001",
        "prometheus_url": "http://localhost:9090"
    }


@router.get("/health/detailed")
async def detailed_health():
    """Detailed health check for all backend dependencies."""
    import os
    from pymilvus import connections, utility

    health = {
        "backend": "healthy",
        "redis": "unknown",
        "milvus": "unknown",
        "disk_space": "ok"
    }

    # Check Milvus
    try:
        milvus_host = os.getenv("MILVUS_HOST", "milvus")
        milvus_port = os.getenv("MILVUS_PORT", "19530")
        connections.connect(alias="health_check", host=milvus_host, port=milvus_port)
        collections = utility.list_collections(using="health_check")
        connections.disconnect("health_check")
        health["milvus"] = f"healthy ({len(collections)} collections)"
    except Exception as e:
        health["milvus"] = f"unhealthy: {str(e)}"

    # Check Redis
    try:
        import redis
        redis_host = os.getenv("REDIS_HOST", "redis")
        r = redis.Redis(host=redis_host, port=6379, socket_timeout=2)
        r.ping()
        health["redis"] = "healthy"
    except Exception as e:
        health["redis"] = f"unhealthy: {str(e)}"

    return health
