"""
test_retriever.py
Unit tests for the Neo4jRetriever.

All Neo4j and embedding calls are mocked to keep tests offline and fast.
"""
import pytest
from unittest.mock import MagicMock, patch


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_record(chunk_id: str, text: str, score: float = 0.9):
    """Create a fake Neo4j Record-like dict."""
    record = MagicMock()
    record.__getitem__ = lambda self, key: {
        "chunk_id": chunk_id,
        "text": text,
        "score": score,
    }[key]
    return record


# ── Fixture ───────────────────────────────────────────────────────────────────

@pytest.fixture
def retriever():
    """
    Return a Neo4jRetriever with:
      - EmbeddingModel.embed  → returns 384-dim zero vector
      - Neo4jClient.run       → returns 2 mock records for vector search,
                                 0 records for graph expansion
    """
    dummy_embedding = [0.0] * 384
    dummy_records = [
        _make_record("chunk-1", "Alice works at Acme Corp."),
        _make_record("chunk-2", "Acme Corp is based in New York."),
    ]

    with (
        patch("app.services.retrieval.neo4j_retriever.EmbeddingModel") as MockEmbedder,
        patch("app.services.retrieval.neo4j_retriever.get_neo4j_client") as MockGetClient,
    ):
        MockEmbedder.return_value.embed.return_value = dummy_embedding

        # First call (vector search) → dummy_records; subsequent (graph expand) → []
        mock_client = MagicMock()
        mock_client.run.side_effect = [dummy_records, [], []]  # search, expand×2
        MockGetClient.return_value = mock_client

        from app.services.retrieval.neo4j_retriever import Neo4jRetriever
        ret = Neo4jRetriever(expand_graph=True, expand_limit=2)
        yield ret


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_retrieve_context_returns_list(retriever):
    """retrieve_context must return a list."""
    result = retriever.retrieve_context("Who works at Acme?")
    assert isinstance(result, list)


def test_retrieve_context_nonempty(retriever):
    """retrieve_context should return at least one chunk when DB has data."""
    result = retriever.retrieve_context("Who works at Acme?")
    assert len(result) >= 1


def test_retrieve_context_calls_embed(retriever):
    """The query must be embedded before searching."""
    retriever.retrieve_context("test query")
    retriever._embedder.embed.assert_called_once_with("test query")


def test_retrieve_context_calls_neo4j(retriever):
    """Neo4j client.run must be called at least once (vector search)."""
    retriever.retrieve_context("test query")
    assert retriever._client.run.call_count >= 1


def test_retrieve_context_deduplication():
    """Duplicate chunk_ids must not appear twice in the result."""
    dummy_embedding = [0.0] * 384
    # Return the same chunk_id twice (once from vector, once from graph expand)
    dup_records = [
        _make_record("chunk-dup", "Duplicate text."),
        _make_record("chunk-dup", "Duplicate text."),
    ]

    with (
        patch("app.services.retrieval.neo4j_retriever.EmbeddingModel") as MockEmbedder,
        patch("app.services.retrieval.neo4j_retriever.get_neo4j_client") as MockGetClient,
    ):
        MockEmbedder.return_value.embed.return_value = dummy_embedding
        mock_client = MagicMock()
        mock_client.run.side_effect = [dup_records, []]
        MockGetClient.return_value = mock_client

        from app.services.retrieval.neo4j_retriever import Neo4jRetriever
        ret = Neo4jRetriever(expand_graph=False)
        result = ret.retrieve_context("anything")

    assert result.count("Duplicate text.") == 1


def test_retrieve_context_graceful_on_neo4j_failure():
    """If Neo4j throws, retrieve_context should return [] not crash."""
    with (
        patch("app.services.retrieval.neo4j_retriever.EmbeddingModel") as MockEmbedder,
        patch("app.services.retrieval.neo4j_retriever.get_neo4j_client") as MockGetClient,
    ):
        MockEmbedder.return_value.embed.return_value = [0.0] * 384
        mock_client = MagicMock()
        mock_client.run.side_effect = Exception("Connection refused")
        MockGetClient.return_value = mock_client

        from app.services.retrieval.neo4j_retriever import Neo4jRetriever
        ret = Neo4jRetriever(expand_graph=False)
        result = ret.retrieve_context("anything")

    assert result == []
