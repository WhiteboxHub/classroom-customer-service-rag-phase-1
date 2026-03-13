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

_MERGE_DOCUMENT = """
MERGE (d:Document {id: $document_id})
"""

_MERGE_CHUNK = """
MATCH (d:Document {id: $document_id})
MERGE (c:Chunk {id: $chunk_id})
SET c.text            = $text,
    c.embedding       = $embedding,
    c.source_document = $source_document,
    c.chunk_index     = $chunk_index
MERGE (d)-[:HAS_CHUNK]->(c)
"""

# Dynamic node label — inject via Python string formatting after validating type
_MERGE_ENTITY = """
MERGE (e:Entity {{name: $name}})
SET e:{entity_type},
    e.type = $type,
    e.embedding = $embedding
"""

_MERGE_MENTIONED_IN = """
MATCH (c:Chunk   {id:   $chunk_id})
MATCH (e:Entity {name: $entity_name})
MERGE (c)-[:MENTIONS]->(e)
"""

# Dynamic relationship type — validate before injecting
_MERGE_ENTITY_REL = """
MATCH (a:Entity {{name: $source}})
MATCH (b:Entity {{name: $target}})
MERGE (a)-[:{rel_type}]->(b)
"""


def _safe_label(label: str) -> str:
    """Sanitise an entity type label to be safe for Cypher injection."""
    import re
    sanitised = re.sub(r"[^A-Z0-9_]", "_", label.upper())
    return sanitised.strip("_") or "ENTITY"

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

    def store_document(self, document_id: str) -> None:
        """Create or match the Document node."""
        self._client.run(_MERGE_DOCUMENT, document_id=document_id)

    def store_chunk(
        self,
        chunk: Dict[str, Any],
        embedding: List[float],
        document_id: str,
    ) -> None:
        """
        Create (or update) a Chunk node and link it to its Document.
        """
        self._client.run(
            _MERGE_CHUNK,
            document_id=document_id,
            chunk_id=chunk["chunk_id"],
            text=chunk["text"],
            embedding=embedding,
            source_document=chunk["source_document"],
            chunk_index=chunk.get("chunk_index", 0),
        )

    def store_entities(
        self,
        entities: List[Dict[str, Any]],
        chunk_id: str,
    ) -> None:
        """
        MERGE all entities, set their ontology label + embed, 
        and link Chunk -> Entity via :MENTIONS.
        """
        for entity in entities:
            name = entity["entity"]
            etype = entity["type"]
            emb = entity.get("embedding", [])
            safe_type = _safe_label(etype)
            
            cypher = _MERGE_ENTITY.format(entity_type=safe_type)
            self._client.run(cypher, name=name, type=etype, embedding=emb)
            self._client.run(_MERGE_MENTIONED_IN, chunk_id=chunk_id, entity_name=name)

    def store_relationships(
        self,
        relationships: List[Dict[str, str]],
    ) -> None:
        """
        MERGE entity-to-entity relationships in the graph.
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
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, str]],
        document_metadata: Dict[str, Any] = None,
    ) -> None:
        """
        Write one complete chunk's data to Neo4j in a single logical operation.
        """
        doc_id = chunk.get("source_document", "unknown")
        if document_metadata and "id" in document_metadata:
            doc_id = document_metadata["id"]
            
        self.store_document(doc_id)
        self.store_chunk(chunk, embedding, doc_id)
        self.store_entities(entities, chunk["chunk_id"])
        self.store_relationships(relationships)
