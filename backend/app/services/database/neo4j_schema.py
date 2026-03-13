"""
neo4j_schema.py
Creates all necessary Neo4j constraints and vector indexes for the GraphRAG pipeline.

Call initialize_schema() at application startup (or as a one-off migration).

Graph schema
────────────
Nodes:
    (:Chunk  {id, text, embedding, source_document, chunk_index})
    (:Entity {name, type})

Relationships:
    (:Entity)-[:MENTIONED_IN]->(:Chunk)          — entity appears in chunk
    (:Entity)-[:<VERB>]->(:Entity)               — extracted relationship
    (:Entity)-[:CO_OCCURS_WITH]->(:Entity)       — fallback co-occurrence

Indexes:
    chunk_embedding_index   — vector index on Chunk.embedding (384 dim, cosine)
    entity_name_index       — B-tree index on Entity.name for fast MERGE
"""
from app.services.database.neo4j_client import Neo4jClient


# ── Constraint & index statements ─────────────────────────────────────────────

_DOCUMENT_CONSTRAINT = """
CREATE CONSTRAINT document_id_unique IF NOT EXISTS
FOR (d:Document) REQUIRE d.id IS UNIQUE
"""

_CHUNK_CONSTRAINT = """
CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS
FOR (c:Chunk) REQUIRE c.id IS UNIQUE
"""

_ENTITY_CONSTRAINT = """
CREATE CONSTRAINT entity_name_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE e.name IS UNIQUE
"""

_CHUNK_VECTOR_INDEX = """
CREATE VECTOR INDEX chunk_embedding_index IF NOT EXISTS
FOR (c:Chunk) ON (c.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 384,
    `vector.similarity_function`: 'cosine'
  }
}
"""

_ENTITY_VECTOR_INDEX = """
CREATE VECTOR INDEX entity_embedding_index IF NOT EXISTS
FOR (e:Entity) ON (e.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 384,
    `vector.similarity_function`: 'cosine'
  }
}
"""

_CHUNK_TEXT_INDEX = """
CREATE FULLTEXT INDEX chunk_text_index IF NOT EXISTS
FOR (c:Chunk) ON EACH [c.text]
"""

_ENTITY_TEXT_INDEX = """
CREATE FULLTEXT INDEX entity_name_index_ft IF NOT EXISTS
FOR (e:Entity) ON EACH [e.name]
"""


def initialize_schema(client: Neo4jClient) -> None:
    """
    Idempotently create constraints and indexes.

    Safe to call multiple times — all statements use IF NOT EXISTS.

    Args:
        client: An active Neo4jClient instance.
    """
    statements = [
        ("Document ID constraint", _DOCUMENT_CONSTRAINT),
        ("Chunk ID constraint", _CHUNK_CONSTRAINT),
        ("Entity name constraint", _ENTITY_CONSTRAINT),
        ("Chunk embedding vector index", _CHUNK_VECTOR_INDEX),
        ("Entity embedding vector index", _ENTITY_VECTOR_INDEX),
        ("Chunk text full-text index", _CHUNK_TEXT_INDEX),
        ("Entity name full-text index", _ENTITY_TEXT_INDEX),
    ]

    with client.session() as session:
        for label, cypher in statements:
            try:
                session.run(cypher)
                print(f"  ✓ {label}")
            except Exception as exc:
                # Log but don't crash — may already exist with different config
                print(f"  ⚠ {label} skipped: {exc}")

    print("Neo4j schema initialisation complete.")
