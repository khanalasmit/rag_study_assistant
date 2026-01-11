"""API routes package."""
from .documents import router as documents_router
from .chat import router as chat_router
from .quiz import router as quiz_router
from .progress import router as progress_router

__all__ = [
    "documents_router",
    "chat_router",
    "quiz_router",
    "progress_router"
]
