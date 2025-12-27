"""
rag_pipeline.py
Bridge to backend API for Open WebUI.
"""

from typing import List, Union, Generator, Iterator
import os
import requests

class Pipeline:
    def __init__(self):
        self.backend_url = os.getenv("BACKEND_URL", "http://backend:8000/api/v1")

    async def on_startup(self):
        print(f"RAG Pipeline started. Backend: {self.backend_url}")

    async def on_shutdown(self):
        print(f"RAG Pipeline stopped.")

    def pipe(self, user_message: str, model_id: str, messages: List[dict], body: dict) -> Union[str, Generator, Iterator]:
        print(f"Processing message: {user_message}")
        
        # Simple pass-through to backend chat completion for now
        # In a real scenario, this might do some pre-processing
        
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY', 'sk-dummy')}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_id,
            "messages": messages,
            "stream": body.get("stream", False)
        }

        try:
            response = requests.post(
                f"{self.backend_url}/chat/completions",
                json=payload,
                headers=headers,
                stream=body.get("stream", False)
            )
            response.raise_for_status()

            if body.get("stream", False):
                return response.iter_lines(decode_unicode=True)
            else:
                return response.json()['choices'][0]['message']['content']
                
        except Exception as e:
            return f"Error communicating with backend: {e}"
