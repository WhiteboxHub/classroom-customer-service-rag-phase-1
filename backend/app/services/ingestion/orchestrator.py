"""
orchestrator.py
Full GraphRAG ingestion pipeline: Load → Chunk → Extract → Embed → Store.

Replaces the old Milvus-based orchestrator. All storage now goes through
the Neo4j GraphIngestion layer. The pipeline exposes two public methods:

    ingest_document(metadata, content)  — process a single document string
    build_graph(file_paths)             — convenience wrapper for a list of files
"""
from typing import List, Dict, Any

from app.services.chunking.semantic import SemanticChunker
from app.services.preprocessing.entity_extractor import EntityExtractor
from app.services.preprocessing.relationship_extractor import RelationshipExtractor
from app.services.embeddings.embedding_model import EmbeddingModel
from app.services.database.neo4j_client import get_neo4j_client
from app.services.database.neo4j_schema import initialize_schema
from app.services.ingestion.graph_ingestion import GraphIngestion


class IngestionOrchestrator:
    """
    Coordinates the full document-to-graph ingestion pipeline.

    Steps for each document:
        1. Chunk the raw text (SemanticChunker).
        2. For every chunk:
           a. Extract entities   (EntityExtractor)
           b. Extract relations  (RelationshipExtractor)
           c. Generate embedding (EmbeddingModel)
           d. Write to Neo4j    (GraphIngestion)

    Attributes:
        chunker:      Splits text into overlapping chunk dicts.
        entity_ext:   spaCy-based named entity recognition.
        rel_ext:      Dependency-parse relationship extraction.
        embedder:     sentence-transformers all-MiniLM-L6-v2 (384-dim).
        graph_store:  Neo4j write interface.
    """

    def __init__(self):
        self.chunker = SemanticChunker()
        self.entity_ext = EntityExtractor()
        self.rel_ext = RelationshipExtractor()
        self.embedder = EmbeddingModel()

        neo4j_client = get_neo4j_client()
        # Ensure schema / indexes exist before any writes
        initialize_schema(neo4j_client)
        self.graph_store = GraphIngestion(neo4j_client)

    # ── public API ─────────────────────────────────────────────────────────────

    async def ingest_document(
        self,
        document_metadata: Dict[str, Any],
        content: str,
    ) -> bool:
        """
        Run the full ingestion pipeline for a single document.

        Args:
            document_metadata: Dict with at least an 'id' key. Used as the
                               source_document label on each Chunk node.
            content:           Raw text content of the document.

        Returns:
            True on success.

        Pipeline:
            text → chunks → [entities, relationships, embedding] → Neo4j
        """
        doc_id = document_metadata.get("id", "unknown")
        print(f"\n[Orchestrator] Starting ingestion: '{doc_id}'")

        # ── Step 1: Chunk ───────────────────────────────────────────────────────
        chunks = self.chunker.chunk(
            content,
            source_document=doc_id,
            metadata=document_metadata,
        )
        print(f"[Orchestrator]   → {len(chunks)} chunks produced")

        # ── Step 2: Per-chunk extraction + embedding + storage ─────────────────
        for i, chunk in enumerate(chunks):
            chunk_text = chunk["text"]

            # 2a. Entity extraction
            entities = self.entity_ext.extract(chunk_text)

            # 2b. Relationship extraction
            relationships = self.rel_ext.extract(chunk_text, entities)

            # 2c. Embedding generation
            embedding = self.embedder.embed(chunk_text)

            # 2d. Write everything to Neo4j
            self.graph_store.ingest_chunk_pipeline(
                chunk=chunk,
                embedding=embedding,
                entities=entities,
                relationships=relationships,
            )

            print(
                f"[Orchestrator]   chunk {i+1}/{len(chunks)} stored "
                f"({len(entities)} entities, {len(relationships)} rels)"
            )

        print(f"[Orchestrator] Ingestion complete: '{doc_id}'")
        return True

    async def build_graph(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Convenience method to ingest a list of local text files.

        Args:
            file_paths: Absolute paths to plain-text .txt files.

        Returns:
            Summary dict with total_files and ingested_files count.
        """
        results = {"total_files": len(file_paths), "ingested_files": 0, "errors": []}

        for path in file_paths:
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    content = fh.read()
                await self.ingest_document({"id": path}, content)
                results["ingested_files"] += 1
            except Exception as exc:
                print(f"[Orchestrator] ERROR processing {path}: {exc}")
                results["errors"].append({"file": path, "error": str(exc)})

        return results
