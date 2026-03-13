"""
chat.py
Chat completion API route — full RAG pipeline: retrieve → generate.

POST /api/v1/chat/completions
    Accepts an OpenAI-compatible request format.
    1. Takes the last user message as the query.
    2. Retrieves relevant context from Neo4j (vector + graph).
    3. Passes context + query to RAGGenerator for an LLM answer.
    4. Returns an OpenAI-compatible response envelope.
"""
import time
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from app.services.retrieval.neo4j_retriever import Neo4jRetriever
from app.services.generation.rag_generation import RAGGenerator

router = APIRouter()

# ── Shared instances (lazy-init) ───────────────────────────────────────────────
_retriever: Optional[Neo4jRetriever] = None
_generator: Optional[RAGGenerator] = None


def _get_retriever() -> Neo4jRetriever:
    global _retriever
    if _retriever is None:
        _retriever = Neo4jRetriever(expand_graph=True)
    return _retriever


def _get_generator() -> RAGGenerator:
    global _generator
    if _generator is None:
        _generator = RAGGenerator()
    return _generator


# ── Request / Response models ──────────────────────────────────────────────────

class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: Optional[bool] = False
    top_k: Optional[int] = 5         # Number of context chunks to retrieve


# ── Route ──────────────────────────────────────────────────────────────────────

@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    RAG chat endpoint.

    Retrieval:  Neo4jRetriever (vector similarity + graph expansion)
    Generation: RAGGenerator   (LLM call with context)

    The last message with role='user' is used as the retrieval query.
    """
    # Extract the latest user message as the query
    user_messages = [m for m in request.messages if m.role == "user"]
    if not user_messages:
        return _error_response("No user message found in request", request.model)

    query = user_messages[-1].content

    # ── Retrieve context from Neo4j ────────────────────────────────────────────
    retriever = _get_retriever()
    context_chunks = retriever.retrieve_context(query, top_k=request.top_k or 5)

    # ── Generate answer ────────────────────────────────────────────────────────
    generator = _get_generator()
    answer = await generator.generate_answer(query=query, context=context_chunks)

    # ── Return OpenAI-compatible envelope ─────────────────────────────────────
    return {
        "id": f"chatcmpl-graphrag-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": answer},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": sum(len(m.content.split()) for m in request.messages),
            "completion_tokens": len(answer.split()),
            "total_tokens": sum(len(m.content.split()) for m in request.messages)
                            + len(answer.split()),
        },
        "context_chunks_used": len(context_chunks),   # extra diagnostic field
    }


def _error_response(message: str, model: str) -> dict:
    return {
        "id": "chatcmpl-error",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": f"Error: {message}"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
