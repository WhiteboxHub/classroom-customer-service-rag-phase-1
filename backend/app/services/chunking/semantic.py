from typing import List, Optional


class SemanticChunker:
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, language: Optional[str] = None) -> List[str]:
        """
        Chunk text into overlapping segments.

        Args:
            text: Document text
            language: Optional ISO language code (e.g., 'en', 'es', 'fr')

        Behavior:
        - English or unknown → default chunking
        - Non-English → safer chunking to avoid over-fragmentation
        """
        print("Chunking document...")

        # Fallback behavior for non-English / low-confidence languages
        if language and language != "en":
            effective_chunk_size = int(self.chunk_size * 1.2)
            effective_overlap = int(self.overlap * 0.5)
        else:
            effective_chunk_size = self.chunk_size
            effective_overlap = self.overlap

        chunks = []
        step = max(effective_chunk_size - effective_overlap, 1)

        for i in range(0, len(text), step):
            chunks.append(text[i:i + effective_chunk_size])

        return chunks
