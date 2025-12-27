"""
rag_generation.py
Handles LLM interaction for RAG.
"""
import os

class RAGGenerator:
    def __init__(self):
        self.model = os.getenv("DEFAULT_MODEL", "gpt-4")

    async def generate_answer(self, query: str, context: list[str]) -> str:
        print(f"Generating answer for query: {query} with {len(context)} contexts")
        
        prompt = f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
        
        # Call LLM API (OpenAI, Anthropic, etc.)
        return f"Generated answer based on {len(context)} contexts."
