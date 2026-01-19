"""
orchestrator.py
Orchestrates the ingestion process: Loading (Docling) -> Chunking -> Embedding -> Storing.
"""
from typing import List, Dict, Any
import os
import glob
from app.services.chunking.semantic import SemanticChunker
from app.services.retrieval.vector_store.milvus import MilvusClient
from app.services.generation.embeddings import EmbeddingService
from app.services.ingestion.docling_processor import DoclingProcessor

class IngestionOrchestrator:
    def __init__(self):
        self.chunker = SemanticChunker()
        self.vector_store = MilvusClient()
        self.embedder = EmbeddingService()
        self.processor = DoclingProcessor()

    async def ingest_directory(self, directory_path: str, tenant_id: str = "default_tenant"):
        """
        Ingests all supported files in a directory recursively.
        """
        print(f"Scanning directory: {directory_path}")
        if not os.path.exists(directory_path):
            print(f"Directory not found: {directory_path}")
            return False

        # Extensions to look for
        extensions = ['**/*.pdf', '**/*.html', '**/*.txt', '**/*.json', '**/*.docx']
        files_to_ingest = []
        
        for ext in extensions:
            # recursive glob
            found = glob.glob(os.path.join(directory_path, ext), recursive=True)
            files_to_ingest.extend(found)

        print(f"Found {len(files_to_ingest)} files to ingest.")
        
        results = []
        for file_path in files_to_ingest:
            success = await self.ingest_file(file_path, tenant_id=tenant_id)
            results.append(success)
            
        return all(results)

    async def ingest_file(self, file_path: str, tenant_id: str = "default_tenant"):
        print(f"Starting ingestion for file: {file_path} (Tenant: {tenant_id})")
        
        # 1. Pre-processing / Loading with Docling (returns ConversionResult or str)
        content_obj = self.processor.process(file_path)
        
        if content_obj is None:
            print(f"Failed to extract content from {file_path}")
            return False
            
        # --- Metadata Collection Layer ---
        file_stat = os.stat(file_path)
        metadata = {
            "document_id": os.path.basename(file_path),
            "tenant_id": tenant_id,
            "source": os.path.basename(file_path),
            "path": file_path,
            "source_system": "local_filesystem",
            "language": "en", 
            "version": "1.0",
            "last_modified": int(file_stat.st_mtime),
            "access_permissions": "role:customer_service"
        }
        
        await self.ingest_document(metadata, content_obj)
        return True

    async def ingest_document(self, document_metadata: Dict[str, Any], content: Any):
        print(f"Starting chunking/embedding for: {document_metadata.get('document_id')}")
        
        # 2. Structure-Aware Chunking (Docling)
        chunks = self.chunker.chunk(content)
        print(f"Generated {len(chunks)} chunks")
        
        if not chunks:
            print("No chunks generated. Skipping storage.")
            return True
            
        # 3. Embedding
        embeddings = self.embedder.get_embeddings(chunks)
        
        # 4. Storage
        await self.vector_store.upsert(chunks, document_metadata, embeddings)
        
        print(f"Ingestion complete for: {document_metadata.get('document_id')}")
        return True
