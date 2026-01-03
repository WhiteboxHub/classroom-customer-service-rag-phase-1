# classroom-customer-service-rag-phase-1\backend\app\api\v1\chat.py
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

@router.post("/v1/chat/completions")
async def openai_compatible_chat(request: ChatCompletionRequest):
    return await chat_completions(request)

@router.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    # Mock response for now
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": request.model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": f"Echo: {request.messages[-1].content} (Staging Backend)"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 9,
            "completion_tokens": 12,
            "total_tokens": 21
        }
    }
