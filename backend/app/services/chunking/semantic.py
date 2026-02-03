from typing import List, Any, Union
try:
    from docling.chunking import HybridChunker
    from docling.document_converter import ConversionResult
    DOCLING_CHUNK_AVAILABLE = True
except ImportError:
    DOCLING_CHUNK_AVAILABLE = False

class SemanticChunker:
    def __init__(self, tokenizer: str = "intfloat/e5-base-v2", max_tokens: int = 512, overlap: int = 50):
        self.max_tokens = max_tokens
        self.overlap = overlap
        if DOCLING_CHUNK_AVAILABLE:
            # The HybridChunker uses a tokenizer to ensure chunks fit into model constraints
            # It respects headings, sections, and tables out of the box.
            self.chunker = HybridChunker(
                tokenizer=tokenizer,
                merge_peers=True
            )
        else:
            self.chunker = None

    def chunk(self, content: Union[str, Any]) -> List[str]:
        """
        Chunks the content. 
        If content is a Docling ConversionResult, uses structural chunking.
        If content is a string, uses a simple fallback or Docling text-based chunking.
        """
        print("Chunking document with Docling structure-awareness...")
        
        if not DOCLING_CHUNK_AVAILABLE:
            return self._fallback_chunk(str(content))

        try:
            if isinstance(content, str):
                # For raw strings, we use the chunker's text processing
                # Better than simple character split as it preserves sentences
                chunks = list(self.chunker.chunk_text(content))
                return [c.text for c in chunks]
            
            # Handle Docling ConversionResult (Structure-aware)
            # This respects tables, headers, and section hierarchies
            chunk_iter = self.chunker.chunk(content.document)
            
            processed_chunks = []
            for chunk in chunk_iter:
                # We can extract extra metadata from chunk here if needed
                # chunk.meta contains section info, parent headers etc.
                chunk_text = self.chunker.serialize(chunk)
                processed_chunks.append(chunk_text)
                
            return processed_chunks

        except Exception as e:
            print(f"Docling chunking failed, falling back: {e}")
            return self._fallback_chunk(str(content))

    def _fallback_chunk(self, text: str) -> List[str]:
        # Quick fallback if Docling fails or is not available
        chunk_size = 1000
        overlap = 200
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i:i + chunk_size])
        return chunks
