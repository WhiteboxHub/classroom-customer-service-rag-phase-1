"""
orchestrator.py
Orchestrates the ingestion process: Loading -> Chunking -> Embedding -> Storing.
"""
from typing import List, Dict, Any
import os
from pypdf import PdfReader
from app.services.chunking.semantic import SemanticChunker
from app.services.retrieval.vector_store.milvus import MilvusClient
from app.services.generation.embeddings import EmbeddingService

class IngestionOrchestrator:
    def __init__(self):
        self.chunker = SemanticChunker()
        self.vector_store = MilvusClient()
        self.embedder = EmbeddingService()

    async def ingest_file(self, file_path: str):
        print(f"Starting ingestion for file: {file_path}")
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return False
            
        text_content = ""
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return False
            
        # Metadata
        metadata = {
            "source": os.path.basename(file_path),
            "id": os.path.basename(file_path)
        }
        
        await self.ingest_document(metadata, text_content)
        return True

    async def ingest_document(self, document_metadata: Dict[str, Any], content: str):
        print(f"Starting ingestion process for: {document_metadata.get('id')}")
        
        # 1. Chunking
        chunks = self.chunker.chunk(content)
        print(f"Generated {len(chunks)} chunks")
        
        # 2. Embedding
        embeddings = self.embedder.get_embeddings(chunks)
        
        # 3. Storage
        await self.vector_store.upsert(chunks, document_metadata, embeddings)
        
        print(f"Ingestion complete for: {document_metadata.get('id')}")
        return True
