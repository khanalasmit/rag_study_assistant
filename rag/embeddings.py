"""
Embeddings module for generating vector representations of text.
Supports Sentence-Transformers and OpenAI embeddings.
"""
from typing import List, Optional
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages embedding generation for documents and queries."""
    
    _instance: Optional[Embeddings] = None
    
    @classmethod
    def get_embeddings(cls) -> Embeddings:
        """Get or create the embeddings instance (singleton pattern)."""
        if cls._instance is None:
            cls._instance = cls._create_embeddings()
        return cls._instance
    
    @classmethod
    def _create_embeddings(cls) -> Embeddings:
        """Create embeddings based on configuration."""
        provider = settings.EMBEDDING_PROVIDER.lower()
        
        if provider == "sentence-transformers":
            logger.info(f"Initializing Sentence-Transformers with model: {settings.EMBEDDING_MODEL}")
            return HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")
    
    @classmethod
    def reset(cls):
        """Reset the embeddings instance (useful for testing)."""
        cls._instance = None


def get_embeddings() -> Embeddings:
    """Convenience function to get embeddings."""
    return EmbeddingManager.get_embeddings()
