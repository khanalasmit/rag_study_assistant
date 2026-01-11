"""
LLM module for managing language model interactions.
Supports Groq, Mistral, OpenAI, and Ollama providers.
"""
from typing import Optional
from langchain_core.language_models import BaseChatModel
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class LLMManager:
    """Manages LLM instances for the application."""
    
    _instance: Optional[BaseChatModel] = None
    
    @classmethod
    def get_llm(cls) -> BaseChatModel:
        """Get or create the LLM instance."""
        if cls._instance is None:
            cls._instance = cls._create_llm()
        return cls._instance
    
    @classmethod
    def _create_llm(cls) -> BaseChatModel:
        """Create LLM based on configuration."""
        provider = settings.LLM_PROVIDER.lower()
        
        if provider == "groq":
            if not settings.GROQ_API_KEY:
                raise ValueError("Groq API key not configured. Set GROQ_API_KEY in .env")
            from langchain_groq import ChatGroq
            logger.info(f"Initializing Groq LLM: {settings.GROQ_MODEL}")
            return ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model=settings.GROQ_MODEL,
                temperature=0.3
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    @classmethod
    def reset(cls):
        """Reset the LLM instance."""
        cls._instance = None


def get_llm() -> BaseChatModel:
    """Convenience function to get LLM."""
    return LLMManager.get_llm()
