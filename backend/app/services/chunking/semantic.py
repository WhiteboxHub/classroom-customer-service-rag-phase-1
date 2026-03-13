"""
semantic.py
Chunking logic — splits documents into overlapping text chunks.

Each chunk is returned as a dict with:
    chunk_id      : unique UUID string
    text          : the chunk's text content
    source_document: identifier of the source document
    metadata      : dict of any additional metadata
"""
import uuid
from typing import List, Dict, Any


class SemanticChunker:
    """
    Splits a document into overlapping fixed-size character chunks.

    Phase 1: character-based splitting with configurable size + overlap.
    Phase 2 (future): replace with true semantic / sentence-boundary splitting.
    """

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(
        self,
        text: str,
        source_document: str = "unknown",
        metadata: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Split *text* into overlapping chunks.

        Args:
            text:            Raw document text.
            source_document: Name / ID of the originating document.
            metadata:        Optional extra metadata to attach to every chunk.

        Returns:
            List of chunk dicts, each containing:
                chunk_id, text, source_document, metadata, chunk_index.
        """
        if metadata is None:
            metadata = {}

        print(f"Chunking document '{source_document}' ({len(text)} chars)...")

        chunks: List[Dict[str, Any]] = []
        step = max(1, self.chunk_size - self.overlap)  # stride between chunk starts

        for index, start in enumerate(range(0, len(text), step)):
            chunk_text = text[start : start + self.chunk_size]
            if not chunk_text.strip():
                continue  # skip whitespace-only slices at the end

            chunks.append(
                {
                    "chunk_id": str(uuid.uuid4()),
                    "text": chunk_text,
                    "source_document": source_document,
                    "chunk_index": index,
                    "metadata": metadata,
                }
            )

        print(f"  → produced {len(chunks)} chunks")
        return chunks
