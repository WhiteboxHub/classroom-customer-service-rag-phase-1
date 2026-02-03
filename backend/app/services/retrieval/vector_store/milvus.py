"""
milvus.py
Client wrapper for Milvus Vector Database.
"""
import os
from typing import List, Dict, Any
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

class MilvusClient:
    def __init__(self):
        self.host = os.getenv("MILVUS_HOST")
        self.port = os.getenv("MILVUS_PORT")
        self.collection_name = "documents_768"
        self.dim = 768 # e5-base-v2 dim
        self._connect()
        self._ensure_collection()

    def _connect(self):
        try:
            connections.connect(alias="default", host=self.host, port=self.port)
            print(f"Connected to Milvus at {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to connect to Milvus: {e}")

    def _ensure_collection(self):
        if not utility.has_collection(self.collection_name):
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                
                # --- Multi-tenant & Metadata Layer Fields ---
                FieldSchema(name="tenant_id", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=256),
                FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="source_system", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="language", dtype=DataType.VARCHAR, max_length=16),
                FieldSchema(name="version", dtype=DataType.VARCHAR, max_length=32),
                FieldSchema(name="last_modified", dtype=DataType.INT64),
                FieldSchema(name="access_permissions", dtype=DataType.VARCHAR, max_length=1024),
                FieldSchema(name="page", dtype=DataType.INT64)
            ]
            schema = CollectionSchema(fields, "Document chunks with metadata layer")
            collection = Collection(self.collection_name, schema)
            
            # Create index for faster search (L2 for vectors)
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            collection.create_index(field_name="embedding", index_params=index_params)
            
            # Create scalar index for tenant-based filtering
            collection.create_index(field_name="tenant_id", index_name="idx_tenant")
            
            print(f"Created collection {self.collection_name} with advanced metadata schema.")
        else:
            print(f"Collection {self.collection_name} exists")
            self.collection = Collection(self.collection_name)
            self.collection.load()

    async def upsert(self, chunks: List[str], metadata: Dict[str, Any], embeddings: List[List[float]]):
        print(f"Upserting {len(chunks)} chunks to Milvus collection {self.collection_name}")
        
        collection = Collection(self.collection_name)
        
        # Prepare data for insertion (Milvus expects column-based data)
        # Order must match FieldSchema in _ensure_collection (excluding auto_id if applicable, 
        # but here we must omit 'id' if auto_id=True)
        
        count = len(chunks)
        entities = [
            embeddings,                                         # embedding
            chunks,                                             # text
            [metadata.get("tenant_id", "default_tenant")] * count, # tenant_id
            [metadata.get("document_id", "unknown_doc")] * count,  # document_id
            [metadata.get("source", "unknown")] * count,        # source
            [metadata.get("source_system", "system")] * count,  # source_system
            [metadata.get("language", "en")] * count,           # language
            [metadata.get("version", "1.0")] * count,           # version
            [int(metadata.get("last_modified", 0))] * count,    # last_modified
            [metadata.get("access_permissions", "public")] * count, # access_permissions
            [metadata.get("page", 0)] * count                   # page
        ]
        
        try:
            collection.insert(entities)
            collection.flush()
            print("Upsert successful")
            return True
        except Exception as e:
            print(f"Upsert failed: {e}")
            return False

    async def search(self, query_vector: List[float], limit: int = 5, tenant_id: str = "default_tenant"):
        print(f"Searching Milvus for tenant: {tenant_id}...")
        collection = Collection(self.collection_name)
        collection.load()
        
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10},
        }
        
        # Enforce tenant isolation via expression filter
        expr = f"tenant_id == '{tenant_id}'"
        
        results = collection.search(
            data=[query_vector], 
            anns_field="embedding", 
            param=search_params, 
            limit=limit, 
            expr=expr,
            output_fields=["text", "source", "page", "document_id", "tenant_id"]
        )
        
        retrieved = []
        for hits in results:
            for hit in hits:
                retrieved.append(hit.entity.get("text"))
                
        return retrieved
