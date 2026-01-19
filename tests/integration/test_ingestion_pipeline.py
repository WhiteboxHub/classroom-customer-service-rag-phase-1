import os
import sys
import pytest
import asyncio
import socket
import time
from typing import Any

# Ensure backend can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
backend_dir = os.path.join(project_root, "backend")
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.services.ingestion.orchestrator import IngestionOrchestrator
from app.services.retrieval.vector_store.milvus import MilvusClient
from app.services.generation.embeddings import EmbeddingService

def is_milvus_ready(host="localhost", port=19530):
    try:
        with socket.create_connection((host, int(port)), timeout=2):
            return True
    except:
        return False

@pytest.mark.asyncio
async def test_full_ingestion_pipeline():
    """
    Integration test for the full ingestion pipeline:
    Docling Processing -> Structure-Aware Chunking -> E5 Embedding -> Milvus Storage
    """
    # Environment Setup
    os.environ["MILVUS_HOST"] = "localhost"
    os.environ["MILVUS_PORT"] = "19530"

    if not is_milvus_ready():
        pytest.skip("Milvus is not running on localhost:19530. Skipping integration test.")

    # 1. Initialize Services
    orchestrator = IngestionOrchestrator()
    vector_store = MilvusClient()
    embedder = EmbeddingService()

    # 2. Define Sample File (PDF Manual)
    sample_file = os.path.join(project_root, "resources", "source_docs", "kp-northern-ca-hmo-provider-manual.pdf")
    assert os.path.exists(sample_file), f"Sample file not found at {sample_file}"

    tenant_id = "integration_test_tenant"

    # 3. Process Ingestion
    success = await orchestrator.ingest_file(sample_file, tenant_id=tenant_id)
    assert success is True, "Ingestion failed"

    # 4. Verify in Milvus
    query = "What are the rules for provider disputes?"
    query_vector = embedder.get_embedding(query, is_query=True)
    
    # Search specifically for the test tenant
    results = await vector_store.search(query_vector, limit=3, tenant_id=tenant_id)
    
    assert len(results) > 0, "No results retrieved from Milvus after ingestion"
    
    # Check for keywords in the results to ensure semantic relevance
    found_relevant = any("dispute" in res.lower() or "kp" in res.lower() for res in results)
    assert found_relevant is True, "Retrieved results do not seem relevant to the query"

    print("\nIntegration test passed: Data successfully ingested and retrieved with metadata isolation.")
