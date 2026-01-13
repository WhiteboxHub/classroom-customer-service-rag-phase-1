# classroom-customer-service-rag-phase-1\backend\app\api\v1\chat.py
import yaml
import os
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: Optional[bool] = False

# @router.post("/v1/chat/completions")
# async def openai_compatible_chat(request: ChatCompletionRequest):
#     return await chat_completions(request)

@router.get("/models")
async def list_models():
    models_file = "/resources/models.yaml"
    model_list = []
    
    # helper fallback
    def get_fallback_models():
        return [
            {
                "id": "llama-3.3-70b-versatile",
                "object": "model",
                "created": 1677610602,
                "owned_by": "groq"
            },
            {
                "id": "llama-3.1-8b-instant",
                "object": "model",
                "created": 1677610602,
                "owned_by": "groq"
            }
        ]

    if os.path.exists(models_file):
        try:
            with open(models_file, "r") as f:
                data = yaml.safe_load(f)
                if "models" in data:
                    for m in data["models"]:
                        # OpenAI format
                        model_list.append({
                            "id": m["id"],
                            "object": "model",
                            "created": 1677610602, # dummy timestamp
                            "owned_by": m.get("provider", "system")
                        })
        except Exception as e:
            print(f"Error reading models file: {e}")
            # fall back if parsing fails
            model_list = get_fallback_models()
    
    if not model_list:
        model_list = get_fallback_models()

    return {
        "object": "list",
        "data": model_list
    }


@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    # 1. Extract latest user query and history
    user_query = request.messages[-1].content
    
    search_query = user_query
    if len(request.messages) > 1:
        last_exchange = request.messages[-2].content if request.messages[-2].role == "assistant" else ""
        if len(request.messages) > 2 and request.messages[-3].role == "user":
             last_exchange = request.messages[-3].content + " " + last_exchange
        
        if len(user_query.split()) < 15: 
             # Find last user message
             for m in reversed(request.messages[:-1]):
                 if m.role == "user":
                     search_query = f"{m.content} {user_query}"
                     break
    
    print(f"Processing query: {user_query}")
    print(f"Search query derived from history: {search_query}")
    
    # 2. Embed query
    from app.services.generation.embeddings import EmbeddingService
    embedder = EmbeddingService()
    query_vector = embedder.get_embedding(search_query)
    
    # 3. Retrieve context
    from app.services.retrieval.vector_store.milvus import MilvusClient
    vector_store = MilvusClient()
    try:
        context_docs = await vector_store.search(query_vector, limit=5)
        context_text = "\n\n".join(context_docs)
    except Exception as e:
        print(f"Retrieval failed: {e}")
        context_text = ""
        
    print(f"Retrieved context length: {len(context_text)}")

    # 4. Construct System Prompt with Context
    system_prompt = f"""You are a helpful customer service assistant for Kaiser Permanente. 
Use the following context to answer the user's question. If the answer is not in the context, say you don't know.

Context:
{context_text}
"""
    
    # 5. Call LLM (supports both Groq and OpenAI)
    import os
    from openai import OpenAI
    
    # Determine which LLM provider to use
    llm_provider = os.getenv("LLM_PROVIDER", "groq").lower()
    
    if llm_provider == "openai":
        # OpenAI configuration
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = None  # Use default OpenAI endpoint
        default_model = "gpt-4o-mini"
        print(f"Using OpenAI LLM provider")
    else:
        # Groq configuration (default)
        api_key = os.getenv("GROQ_API_KEY")
        base_url = "https://api.groq.com/openai/v1"
        default_model = "llama-3.3-70b-versatile"
        print(f"Using Groq LLM provider")
    
    if not api_key:
        return {
            "id": "error",
            "object": "chat.completion",
            "created": 0,
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"Error: No API key configured for {llm_provider.upper()}. Please set {llm_provider.upper()}_API_KEY environment variable."
                },
                "finish_reason": "stop"
            }]
        }
        
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    # Prepare messages
    # 1. System Prompt
    messages = [{"role": "system", "content": system_prompt}]
    
    # 2. Add Chat History (from request)
    history_messages = [
        {"role": m.role, "content": m.content} 
        for m in request.messages[:-1] # Exclude the last message which we handled as 'user_query'
        if m.role in ["user", "assistant"]
    ]
    messages.extend(history_messages)
    
    # 3. Add Current User Query (with RAG context context already in system prompt, but we repeat query here)
    messages.append({"role": "user", "content": user_query})
    
    try:
        response = client.chat.completions.create(
            model=request.model or default_model,
            messages=messages,
            stream=False # simplified for now
        )
        
        return {
            "id": response.id,
            "object": "chat.completion",
            "created": response.created,
            "model": response.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response.choices[0].message.content
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    except Exception as e:
        print(f"LLM call failed: {e}")
        return {
            "id": "error",
            "object": "chat.completion",
            "created": 0,
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"I encountered an error processing your request: {str(e)}"
                },
                "finish_reason": "stop"
            }]
        }
