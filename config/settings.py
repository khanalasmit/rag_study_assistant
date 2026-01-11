"""
Configuration settings for the AI Study Assistant.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "AI Study Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    CHROMA_DB_DIR: Path = BASE_DIR / "chroma_db"
    
    # LLM Settings
    LLM_PROVIDER: str = "groq"  # groq, mistral, openai, ollama
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    MISTRAL_API_KEY: Optional[str] = os.getenv("MISTRAL_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Model names
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    MISTRAL_MODEL: str = "mistral-small-latest"
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OLLAMA_MODEL: str = "mistral"
    
    # Embedding Settings
    EMBEDDING_PROVIDER: str = "sentence-transformers"  # sentence-transformers, openai
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # RAG Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 5
    USE_SEMANTIC_CHUNKING: bool = True  
    USE_HYBRID_RETRIEVAL: bool = True  
    SEMANTIC_THRESHOLD: float = 0.8  
    
    # Quiz Settings
    DEFAULT_QUIZ_QUESTIONS: int = 5
    MAX_QUIZ_QUESTIONS: int = 20
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Create directories if they don't exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
