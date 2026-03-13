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

# Stage 1: Vector similarity search (Semantic)
_VECTOR_SEARCH_CHUNKS = """
CALL db.index.vector.queryNodes('chunk_embedding_index', $top_k, $query_embedding)
YIELD node AS c, score
RETURN 'chunk' AS type, c.id AS id, c.text AS text, score
"""

_VECTOR_SEARCH_ENTITIES = """
CALL db.index.vector.queryNodes('entity_embedding_index', $top_k, $query_embedding)
YIELD node AS e, score
RETURN 'entity' AS type, e.name AS name, e.type AS entity_type, score
"""

# Stage 2: Keyword Search (Full-text)
_KEYWORD_SEARCH_CHUNKS = """
CALL db.index.fulltext.queryNodes('chunk_text_index', $query)
YIELD node AS c, score
RETURN 'chunk' AS type, c.id AS id, c.text AS text, score
LIMIT $top_k
"""

_KEYWORD_SEARCH_ENTITIES = """
CALL db.index.fulltext.queryNodes('entity_name_index_ft', $query)
YIELD node AS e, score
RETURN 'entity' AS type, e.name AS name, e.type AS entity_type, score
LIMIT $top_k
"""

# Stage 3: Graph Traversal (Expand from known entities)
_GRAPH_TRAVERSAL = """
MATCH (e:Entity)-[r]->(related:Entity)
WHERE e.name IN $entity_names
RETURN e.name AS source, type(r) AS relation, related.name AS target
LIMIT $expand_limit
"""

# Stage 4: Fetch chunks for known entities
_FETCH_CHUNKS_FOR_ENTITIES = """
MATCH (c:Chunk)-[:MENTIONS]->(e:Entity)
WHERE e.name IN $entity_names
RETURN c.id AS id, c.text AS text
LIMIT $expand_limit
"""


class Neo4jRetriever:
    """
    Queries Neo4j using Hybrid Search (Semantic, Keyword, Graph Traversal).
    """

    def __init__(
        self,
        client: Neo4jClient | None = None,
        expand_limit: int = 15,
    ):
        self._client = client or get_neo4j_client()
        self._embedder = EmbeddingModel()
        self._expand_limit = expand_limit

    def retrieve_context(self, query: str, top_k: int = 5) -> dict:
        """
        Combines Semantic, Keyword, and Graph search across Chunks and Entities.
        Deduplicates results.
        
        Returns:
            { "chunks": [...], "entities": [...], "relationships": [...] }
        """
        print(f"[Retriever] Hybrid Query: '{query}'")
        query_embedding = self._embedder.embed(query)
        
        chunks_map = {}
        entities_map = {}
        relationships = set()

        # ── 1. Semantic Search ──────────────────────────────────────────────────
        try:
            vec_chunks = self._client.run(_VECTOR_SEARCH_CHUNKS, query_embedding=query_embedding, top_k=top_k)
            for rec in vec_chunks:
                chunks_map[rec["id"]] = rec["text"]
                
            vec_ents = self._client.run(_VECTOR_SEARCH_ENTITIES, query_embedding=query_embedding, top_k=top_k)
            for rec in vec_ents:
                entities_map[rec["name"]] = rec["entity_type"]
        except Exception as exc:
            print(f"[Retriever] Semantic search failed: {exc}")

        # ── 2. Keyword Search ───────────────────────────────────────────────────
        try:
            kw_chunks = self._client.run(_KEYWORD_SEARCH_CHUNKS, query=query, top_k=top_k)
            for rec in kw_chunks:
                chunks_map[rec["id"]] = rec["text"]
                
            kw_ents = self._client.run(_KEYWORD_SEARCH_ENTITIES, query=query, top_k=top_k)
            for rec in kw_ents:
                entities_map[rec["name"]] = rec["entity_type"]
        except Exception as exc:
            print(f"[Retriever] Keyword search warning (may need Neo4j Enterprise or config): {exc}")

        # ── 3. Graph Traversal ──────────────────────────────────────────────────
        entity_names = list(entities_map.keys())
        if entity_names:
            try:
                # 3a. Find related entities in graph
                rels = self._client.run(_GRAPH_TRAVERSAL, entity_names=entity_names, expand_limit=self._expand_limit)
                for rec in rels:
                    rel_tuple = (rec["source"], rec["relation"], rec["target"])
                    relationships.add(rel_tuple)
                    
                # 3b. Fetch chunks that mention these entities specifically
                ent_chunks = self._client.run(_FETCH_CHUNKS_FOR_ENTITIES, entity_names=entity_names, expand_limit=self._expand_limit)
                for rec in ent_chunks:
                    chunks_map[rec["id"]] = rec["text"]
            except Exception as exc:
                print(f"[Retriever] Graph traversal failed: {exc}")

        # Format and deduplicate final output
        results = {
            "chunks": list(chunks_map.values()),
            "entities": [{"name": k, "type": v} for k, v in entities_map.items()],
            "relationships": [{"source": s, "relation": r, "target": t} for s, r, t in relationships],
        }
        
        print(f"[Retriever] Returned {len(results['chunks'])} chunks, {len(results['entities'])} entities, {len(results['relationships'])} relationships.")
        return results
