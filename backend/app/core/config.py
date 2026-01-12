# classroom-customer-service-rag-phase-1/backend/app/core/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Classroom CS RAG"
    API_V1_STR: str = "/api/v1"

    # =========================
    # Multilingual Configuration
    # =========================

    # Embedding model used for vector generation
    # Example: text-embedding-3-large, multilingual-e5-base, etc.
    EMBEDDING_MODEL_NAME: str = "text-embedding-3-large"

    # Default language assumed when language is not detected
    # Example: "en", "fr", "de"
    DEFAULT_LANGUAGE: str = "en"

    # Toggle to enable/disable language-based filtering in retrieval
    ENABLE_LANGUAGE_FILTERING: bool = False

    class Config:
        case_sensitive = True


settings = Settings()
