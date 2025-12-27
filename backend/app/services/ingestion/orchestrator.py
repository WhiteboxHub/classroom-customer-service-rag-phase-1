"""
orchestrator.py
Orchestrates the ingestion process: Loading -> Chunking -> Embedding -> Storing.
"""
from typing import List, Dict, Any
from app.services.chunking.semantic import SemanticChunker
from app.services.retrieval.vector_store.milvus import MilvusClient

class IngestionOrchestrator:
    def __init__(self):
        self.chunker = SemanticChunker()
        self.vector_store = MilvusClient()

    async def ingest_document(self, document_metadata: Dict[str, Any], content: str):
        print(f"Starting ingestion for: {document_metadata.get('id')}")
        
        # 1. Chunking
        chunks = self.chunker.chunk(content)
        
        # 2. Embedding & Storage (Delegated to Vector Store which handles embedding generation internally or via another service)
        # For this phase 1, we assume vector store client handles calls to embedding model or we do it here.
        # Let's assume the vector store upsert takes text and handles embedding or we pass embeddings.
        
        # Simulating embedding generation loop for now or assuming Milvus wrapper does it
        vectors = [] 
        for chunk in chunks:
            # vectors.append(embedding_service.embed(chunk))
            pass
            
        await self.vector_store.upsert(chunks, document_metadata)
        
        print(f"Ingestion complete for: {document_metadata.get('id')}")
        return True
