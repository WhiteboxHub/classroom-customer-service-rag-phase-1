from openai import OpenAI
import os

class EmbeddingService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE_URL")
        
        
        # NOTE: In this specific setup, the backend ITSELF needs to generate embeddings.
        # It should talk to OpenAI directly.
        if "backend" in str(base_url):
             # clear the mock base url for the internal client
             base_url = None
             
        self.client = OpenAI(api_key=api_key)

    def get_embedding(self, text: str) -> list[float]:
        text = text.replace("\n", " ")
        try:
            return self.client.embeddings.create(input=[text], model="text-embedding-ada-002").data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return [0.0] * 1536 

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        # clean newlines
        texts = [t.replace("\n", " ") for t in texts]
        try:
            resp = self.client.embeddings.create(input=texts, model="text-embedding-ada-002")
            return [d.embedding for d in resp.data]
        except Exception as e:
            print(f"Error generating embeddings batch: {e}")
            return [[0.0]*1536 for _ in texts]
