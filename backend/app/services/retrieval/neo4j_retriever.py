"""
neo4j_retriever.py
Retrieves relevant context from Neo4j for a user query.

Two-stage retrieval:
    Stage 1 — Vector similarity search
        Embeds the query and finds the top-k Chunk nodes with the most
        similar embedding vectors using Neo4j's built-in vector index.

    Stage 2 — Graph context expansion (optional)
        For each top chunk, follow :MENTIONED_IN edges backwards to find
        all Entities that appear in that chunk. Then find OTHER chunks
        those entities also appear in and include their text as additional
        context. This enriches the retrieval with related content that
        might not score highly in pure vector similarity.

Public API:
    retriever.retrieve_context(query, top_k=5)  → List[str]
"""
from typing import List

from app.services.embeddings.embedding_model import EmbeddingModel
from app.services.database.neo4j_client import Neo4jClient, get_neo4j_client


# ── Cypher queries ────────────────────────────────────────────────────────────

# Stage 1: vector similarity search on Chunk nodes.
# db.index.vector.queryNodes() is the Community Edition API for Neo4j ≥ 5.11.
_VECTOR_SEARCH = """
CALL db.index.vector.queryNodes(
    'chunk_embedding_index',
    $top_k,
    $query_embedding
)
YIELD node AS c, score
RETURN c.id AS chunk_id, c.text AS text, score
ORDER BY score DESC
"""

# Stage 2: for a given chunk_id, find all entities mentioned in it,
# then retrieve other chunks those entities also appear in.
_GRAPH_EXPAND = """
MATCH (e:Entity)-[:MENTIONED_IN]->(seed:Chunk {id: $chunk_id})
MATCH (e)-[:MENTIONED_IN]->(neighbour:Chunk)
WHERE neighbour.id <> $chunk_id
RETURN DISTINCT neighbour.id AS chunk_id, neighbour.text AS text
LIMIT $expand_limit
"""


class Neo4jRetriever:
    """
    Queries Neo4j for the most relevant chunks given a natural-language query.

    Args:
        client:        Neo4jClient instance (defaults to process singleton).
        expand_graph:  If True, add graph-neighbour chunks after vector search.
        expand_limit:  Max extra chunks to fetch per top chunk in graph expansion.
    """

    def __init__(
        self,
        client: Neo4jClient | None = None,
        expand_graph: bool = True,
        expand_limit: int = 2,
    ):
        self._client = client or get_neo4j_client()
        self._embedder = EmbeddingModel()
        self._expand_graph = expand_graph
        self._expand_limit = expand_limit

    # ── public API ─────────────────────────────────────────────────────────────

    def retrieve_context(self, query: str, top_k: int = 5) -> List[str]:
        """
        Return the most relevant chunk texts for *query*.

        Steps:
            1. Embed the query (384-dim cosine vector).
            2. Run vector similarity search → top_k Chunk nodes.
            3. Optionally expand via graph traversal.
            4. Return deduplicated chunk texts in relevance order.

        Args:
            query:  User question or search phrase.
            top_k:  Number of top chunks from vector search.

        Returns:
            List of chunk text strings, best matches first.
        """
        print(f"[Retriever] Query: '{query[:80]}...' " if len(query) > 80 else f"[Retriever] Query: '{query}'")

        # ── Stage 1: vector similarity ─────────────────────────────────────────
        query_embedding = self._embedder.embed(query)
        vector_results = self._run_vector_search(query_embedding, top_k)
        print(f"[Retriever] Vector search → {len(vector_results)} chunks")

        # Preserve insertion order while deduplicating
        seen_ids: set = set()
        context_chunks: List[str] = []

        for record in vector_results:
            chunk_id = record["chunk_id"]
            chunk_text = record["text"]
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                context_chunks.append(chunk_text)

            # ── Stage 2: graph expansion ───────────────────────────────────────
            if self._expand_graph:
                neighbours = self._run_graph_expand(chunk_id)
                for nb in neighbours:
                    nb_id = nb["chunk_id"]
                    if nb_id not in seen_ids:
                        seen_ids.add(nb_id)
                        context_chunks.append(nb["text"])

        print(f"[Retriever] Total context chunks returned: {len(context_chunks)}")
        return context_chunks

    # ── private helpers ────────────────────────────────────────────────────────

    def _run_vector_search(self, embedding: List[float], top_k: int):
        """Execute the vector index query and return raw records."""
        try:
            return self._client.run(
                _VECTOR_SEARCH,
                query_embedding=embedding,
                top_k=top_k,
            )
        except Exception as exc:
            print(f"[Retriever] Vector search failed: {exc}")
            return []

    def _run_graph_expand(self, chunk_id: str):
        """Execute the graph expansion query for a single seed chunk."""
        try:
            return self._client.run(
                _GRAPH_EXPAND,
                chunk_id=chunk_id,
                expand_limit=self._expand_limit,
            )
        except Exception as exc:
            print(f"[Retriever] Graph expand failed for chunk {chunk_id}: {exc}")
            return []
