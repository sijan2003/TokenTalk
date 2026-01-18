"""Application configuration using Pydantic settings"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App settings
    APP_NAME: str = "RAG Multi-Source Chat"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./backend/database.db"
    
    # JWT Authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # API Keys
    GEMINI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:8080", "http://127.0.0.1:8080"]
    
    # File upload
    UPLOAD_DIR: str = "./backend/uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Vector store
    VECTOR_STORE_DIR: str = "./backend/vector_stores"
    
    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # RAG settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K: int = 5
    
    # LLM settings
    LLM_MODEL: str = "gemini-flash-latest"
    LLM_TEMPERATURE: float = 0.3
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Set up Gemini API key for LangChain
os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY or ""
