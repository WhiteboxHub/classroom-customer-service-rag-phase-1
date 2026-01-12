"""
milvus.py
Client wrapper for Milvus Vector Database.
"""

import os
from typing import List, Dict, Any, Optional

from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility,
)

from app.services.generation.embeddings import EmbeddingService


class MilvusClient:
    def __init__(self):
        self.host = os.getenv("MILVUS_HOST", "milvus")
        self.port = os.getenv("MILVUS_PORT", "19530")
        self.collection_name = "documents"

        # Dynamically determine embedding dimension
        self.embedder = EmbeddingService()
        self.dim = self.embedder.embedding_dim

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
                FieldSchema(
                    name="id",
                    dtype=DataType.INT64,
                    is_primary=True,
                    auto_id=True,
                ),
                FieldSchema(
                    name="embedding",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=self.dim,
                ),
                FieldSchema(
                    name="text",
                    dtype=DataType.VARCHAR,
                    max_length=65535,
                ),
                FieldSchema(
                    name="source",
                    dtype=DataType.VARCHAR,
                    max_length=512,
                ),
                FieldSchema(
                    name="page",
                    dtype=DataType.INT64,
                ),
                # NEW: language metadata (scalar, filterable)
                FieldSchema(
                    name="language",
                    dtype=DataType.VARCHAR,
                    max_length=16,
                ),
            ]

            schema = CollectionSchema(fields, "Document chunks")
            collection = Collection(self.collection_name, schema)

            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024},
            }
            collection.create_index(
                field_name="embedding",
                index_params=index_params,
            )
            collection.load()

            print(f"Created collection {self.collection_name}")
        else:
            print(f"Collection {self.collection_name} exists")
            collection = Collection(self.collection_name)
            collection.load()

    async def upsert(
        self,
        chunks: List[str],
        metadata: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ):
        """
        Upsert document chunks with per-chunk metadata.
        """
        print(
            f"Upserting {len(chunks)} chunks to Milvus collection "
            f"{self.collection_name}"
        )

        collection = Collection(self.collection_name)

        sources = [m.get("source", "unknown") for m in metadata]
        pages = [m.get("page", 0) for m in metadata]
        languages = [m.get("language", "en") for m in metadata]

        entities = [
            embeddings,
            chunks,
            sources,
            pages,
            languages,
        ]

        try:
            collection.insert(entities)
            collection.flush()
            print("Upsert successful")
            return True
        except Exception as e:
            print(f"Upsert failed: {e}")
            return False

    async def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        language: Optional[str] = None,
    ):
        """
        Vector search with optional language filtering.
        """
        print("Searching Milvus...")
        collection = Collection(self.collection_name)
        collection.load()

        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10},
        }

        expr = None
        if language:
            expr = f"language == '{language}'"

        results = collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=limit,
            expr=expr,
            output_fields=["text", "source", "page", "language"],
        )

        retrieved = []
        for hits in results:
            for hit in hits:
                retrieved.append(hit.entity.get("text"))

        return retrieved
