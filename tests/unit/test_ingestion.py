"""
test_ingestion.py
Unit tests for ingestion orchestrator.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.ingestion.orchestrator import IngestionOrchestrator

@pytest.mark.asyncio
async def test_ingestion_orchestrator():
    orchestrator = IngestionOrchestrator()
    orchestrator.chunker.chunk = MagicMock(return_value=["chunk1", "chunk2"])
    orchestrator.vector_store.upsert = AsyncMock(return_value=True)
    
    result = await orchestrator.ingest_document({"id": "123"}, "dummy content")
    
    assert result is True
    orchestrator.chunker.chunk.assert_called_once()
    orchestrator.vector_store.upsert.assert_called_once()
