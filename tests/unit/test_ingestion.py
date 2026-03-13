"""
test_ingestion.py
Unit tests for the GraphRAG IngestionOrchestrator.

Strategy: every external dependency (Neo4j, spaCy, sentence-transformers)
is mocked so the tests are fast and offline.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


# ── Fixture: orchestrator with all heavy deps mocked ─────────────────────────

@pytest.fixture
def orchestrator():
    """
    Return an IngestionOrchestrator with:
      - SemanticChunker.chunk       → returns 2 dummy chunks
      - EntityExtractor.extract     → returns 2 dummy entities
      - RelationshipExtractor.extract → returns 1 dummy relationship
      - EmbeddingModel.embed        → returns a 384-dim zero vector
      - GraphIngestion.ingest_chunk_pipeline → no-op MagicMock
    """
    dummy_chunks = [
        {"chunk_id": "c1", "text": "Alice works at Acme.", "source_document": "doc1",
         "chunk_index": 0, "metadata": {}},
        {"chunk_id": "c2", "text": "Acme is in New York.", "source_document": "doc1",
         "chunk_index": 1, "metadata": {}},
    ]
    dummy_entities = [
        {"entity": "Alice", "type": "Person"},
        {"entity": "Acme",  "type": "Organization"},
    ]
    dummy_rels = [{"source": "Alice", "relation": "WORKS_AT", "target": "Acme"}]
    dummy_embedding = [0.0] * 384

    with (
        patch("app.services.ingestion.orchestrator.SemanticChunker") as MockChunker,
        patch("app.services.ingestion.orchestrator.EntityExtractor") as MockEntityExt,
        patch("app.services.ingestion.orchestrator.RelationshipExtractor") as MockRelExt,
        patch("app.services.ingestion.orchestrator.EmbeddingModel") as MockEmbedder,
        patch("app.services.ingestion.orchestrator.get_neo4j_client") as MockGetClient,
        patch("app.services.ingestion.orchestrator.initialize_schema") as MockSchema,
        patch("app.services.ingestion.orchestrator.GraphIngestion") as MockGraphIngestion,
    ):
        # Configure mock instances
        MockChunker.return_value.chunk.return_value = dummy_chunks
        MockEntityExt.return_value.extract.return_value = dummy_entities
        MockRelExt.return_value.extract.return_value = dummy_rels
        MockEmbedder.return_value.embed.return_value = dummy_embedding
        MockGetClient.return_value = MagicMock()
        MockSchema.return_value = None
        MockGraphIngestion.return_value.ingest_chunk_pipeline = MagicMock()

        from app.services.ingestion.orchestrator import IngestionOrchestrator
        orc = IngestionOrchestrator()
        # Expose mock for assertion below
        orc._mock_graph_store = MockGraphIngestion.return_value
        yield orc


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ingest_document_returns_true(orchestrator):
    """ingest_document should complete without error and return True."""
    result = await orchestrator.ingest_document({"id": "doc1"}, "Some content here.")
    assert result is True


@pytest.mark.asyncio
async def test_ingest_document_calls_chunker(orchestrator):
    """Chunker must be called exactly once per document."""
    await orchestrator.ingest_document({"id": "doc1"}, "Some content here.")
    orchestrator.chunker.chunk.assert_called_once()


@pytest.mark.asyncio
async def test_ingest_document_embeds_each_chunk(orchestrator):
    """embedder.embed must be called once per chunk."""
    await orchestrator.ingest_document({"id": "doc1"}, "Some content here.")
    # 2 chunks were returned by the mocked chunker
    assert orchestrator.embedder.embed.call_count == 2


@pytest.mark.asyncio
async def test_ingest_document_calls_graph_store(orchestrator):
    """graph_store.ingest_chunk_pipeline must be called once per chunk."""
    await orchestrator.ingest_document({"id": "doc1"}, "Some content here.")
    assert orchestrator.graph_store.ingest_chunk_pipeline.call_count == 2


@pytest.mark.asyncio
async def test_ingest_document_extracts_entities(orchestrator):
    """entity_ext.extract must be called once per chunk."""
    await orchestrator.ingest_document({"id": "doc1"}, "Some content here.")
    assert orchestrator.entity_ext.extract.call_count == 2


@pytest.mark.asyncio
async def test_ingest_document_extracts_relationships(orchestrator):
    """rel_ext.extract must be called once per chunk."""
    await orchestrator.ingest_document({"id": "doc1"}, "Some content here.")
    assert orchestrator.rel_ext.extract.call_count == 2
