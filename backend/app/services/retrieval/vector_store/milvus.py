"""
milvus.py
Client wrapper for Milvus Vector Database.
"""
import os
from typing import List, Dict, Any
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

class MilvusClient:
    def __init__(self):
        self.host = os.getenv("MILVUS_HOST", "milvus")
        self.port = os.getenv("MILVUS_PORT", "19530")
        self.collection_name = "documents"
        self.dim = 1536 # OpenAI embedding dimension
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
                FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="page", dtype=DataType.INT64)
            ]
            schema = CollectionSchema(fields, "Document chunks")
            collection = Collection(self.collection_name, schema)
            # Create index for faster search
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            collection.create_index(field_name="embedding", index_params=index_params)
            print(f"Created collection {self.collection_name}")
        else:
            print(f"Collection {self.collection_name} exists")
            self.collection = Collection(self.collection_name)
            self.collection.load()

    async def upsert(self, chunks: List[str], metadata: Dict[str, Any], embeddings: List[List[float]]):
        print(f"Upserting {len(chunks)} chunks to Milvus collection {self.collection_name}")
        
        collection = Collection(self.collection_name)
        
        # Prepare data for insertion
        # Milvus expects column-based data
        entities = [
            embeddings, 
            chunks,     
            [metadata.get("source", "unknown")] * len(chunks),
            [metadata.get("page", 0)] * len(chunks) 
        ]
        
        # NOTE: If we are passing per-chunk metadata, we should adjust the arguments.
        # For now, let's assume 'metadata' applies to the whole batch or we get a list of metadata.
        # Let's adjust upsert signature in caller or handle it here. 
        # Assuming simple case: Upserting chunks from ONE document.
        
        try:
            collection.insert(entities)
            collection.flush()
            print("Upsert successful")
            return True
        except Exception as e:
            print(f"Upsert failed: {e}")
            return False

    async def search(self, query_vector: List[float], limit: int = 5):
        print("Searching Milvus...")
        collection = Collection(self.collection_name)
        collection.load()
        
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10},
        }
        
        results = collection.search(
            data=[query_vector], 
            anns_field="embedding", 
            param=search_params, 
            limit=limit, 
            output_fields=["text", "source", "page"]
        )
        
        retrieved = []
        for hits in results:
            for hit in hits:
                retrieved.append(hit.entity.get("text"))
                
        return retrieved
