# classroom-customer-service-rag-phase-1\backend\app\core\config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Classroom CS RAG"
    API_V1_STR: str = "/api/v1"
    
    # Add other config vars here
    
    class Config:
        case_sensitive = True

settings = Settings()
