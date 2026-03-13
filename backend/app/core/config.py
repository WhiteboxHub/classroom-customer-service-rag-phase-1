"""
config.py
Application-level settings loaded from environment variables.
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Classroom CS RAG"
    API_V1_STR: str = "/api/v1"

    # Neo4j — replaces Milvus
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    # Embedding model (sentence-transformers)
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    # LLM
    LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    DEFAULT_MODEL: str = "llama3-8b-8192"

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"


settings = Settings()
