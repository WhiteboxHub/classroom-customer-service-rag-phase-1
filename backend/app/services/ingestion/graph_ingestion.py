"""
graph_ingestion.py
Writes chunks, entities, and relationships into the Neo4j knowledge graph.

The GraphIngestion class is the single point of contact between the
ingestion pipeline and the Neo4j database. It provides three atomic
write methods plus a convenience top-level method used by the orchestrator.

Graph writes
────────────
store_chunk()        → creates a :Chunk node with its embedding
store_entities()     → MERGEs :Entity nodes + (:Entity)-[:MENTIONED_IN]->(:Chunk)
store_relationships()→ MERGEs (:Entity)-[:<RELATION>]->(:Entity)
"""
from typing import List, Dict, Any

from app.services.database.neo4j_client import Neo4jClient


# ── Cypher templates ──────────────────────────────────────────────────────────

_MERGE_CHUNK = """
MERGE (c:Chunk {id: $chunk_id})
SET c.text            = $text,
    c.embedding       = $embedding,
    c.source_document = $source_document,
    c.chunk_index     = $chunk_index
"""

_MERGE_ENTITY = """
MERGE (e:Entity {name: $name})
SET e.type = $type
"""

_MERGE_MENTIONED_IN = """
MATCH (e:Entity {name: $entity_name})
MATCH (c:Chunk   {id:   $chunk_id})
MERGE (e)-[:MENTIONED_IN]->(c)
"""

# Dynamic relationship type — inject via Python string formatting after
# validating that the type is safe (alphanumeric + underscores only).
_MERGE_ENTITY_REL = """
MATCH (a:Entity {{name: $source}})
MATCH (b:Entity {{name: $target}})
MERGE (a)-[:{rel_type}]->(b)
"""


def _safe_rel_type(rel: str) -> str:
    """
    Sanitise a relationship type string so it is safe to embed in Cypher.
    Keeps A-Z, 0-9, underscore; replaces everything else with underscore.
    """
    import re
    sanitised = re.sub(r"[^A-Z0-9_]", "_", rel.upper())
    return sanitised.strip("_") or "RELATED_TO"


class GraphIngestion:
    """
    High-level interface for writing GraphRAG data to Neo4j.

    Args:
        client: An active Neo4jClient instance.
    """

    def __init__(self, client: Neo4jClient):
        self._client = client

    # ── atomic write methods ──────────────────────────────────────────────────

    def store_chunk(
        self,
        chunk: Dict[str, Any],
        embedding: List[float],
    ) -> None:
        """
        Create (or update) a Chunk node in Neo4j.

        Args:
            chunk:     Chunk dict from SemanticChunker (must have chunk_id, text,
                       source_document, chunk_index).
            embedding: 384-dimensional float list from EmbeddingModel.
        """
        self._client.run(
            _MERGE_CHUNK,
            chunk_id=chunk["chunk_id"],
            text=chunk["text"],
            embedding=embedding,
            source_document=chunk["source_document"],
            chunk_index=chunk.get("chunk_index", 0),
        )

    def store_entities(
        self,
        entities: List[Dict[str, str]],
        chunk_id: str,
    ) -> None:
        """
        MERGE all entities and link them to a Chunk via :MENTIONED_IN.

        Args:
            entities: Output of EntityExtractor.extract().
            chunk_id: The chunk_id of the chunk these entities appear in.
        """
        for entity in entities:
            name = entity["entity"]
            etype = entity["type"]
            self._client.run(_MERGE_ENTITY, name=name, type=etype)
            self._client.run(_MERGE_MENTIONED_IN, entity_name=name, chunk_id=chunk_id)

    def store_relationships(
        self,
        relationships: List[Dict[str, str]],
    ) -> None:
        """
        MERGE entity-to-entity relationships in the graph.

        The relationship type comes from RelationshipExtractor and is
        upper-cased / sanitised before being embedded in Cypher.

        Args:
            relationships: Output of RelationshipExtractor.extract().
        """
        for rel in relationships:
            rel_type = _safe_rel_type(rel["relation"])
            cypher = _MERGE_ENTITY_REL.format(rel_type=rel_type)
            self._client.run(
                cypher,
                source=rel["source"],
                target=rel["target"],
            )

    # ── convenience top-level ─────────────────────────────────────────────────

    def ingest_chunk_pipeline(
        self,
        chunk: Dict[str, Any],
        embedding: List[float],
        entities: List[Dict[str, str]],
        relationships: List[Dict[str, str]],
    ) -> None:
        """
        Write one complete chunk's data to Neo4j in a single logical operation.

        Order:
            1. Store Chunk node (with embedding)
            2. Store Entity nodes + :MENTIONED_IN edges
            3. Store entity-to-entity relationships

        Args:
            chunk:         Chunk dict from SemanticChunker.
            embedding:     Vector from EmbeddingModel.
            entities:      Entities from EntityExtractor.
            relationships: Relationships from RelationshipExtractor.
        """
        self.store_chunk(chunk, embedding)
        self.store_entities(entities, chunk["chunk_id"])
        self.store_relationships(relationships)
