"""
Main FastAPI application for AI Study Assistant.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys

# Add project root to path
sys.path.insert(0, str(__file__).rsplit("\\", 1)[0])

from config.settings import settings
from api.routes import documents_router, chat_router, quiz_router, progress_router
from rag.vector_store import VectorStoreManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting AI Study Assistant...")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    logger.info(f"Embedding Provider: {settings.EMBEDDING_PROVIDER}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Study Assistant...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    AI-powered Study Assistant for Exam Preparation.
    
    Features:
    - Upload and process study documents (PDF, TXT, Markdown)
    - Ask questions about your study materials
    - Generate practice quizzes
    - Track learning progress
    
    Built with RAG (Retrieval-Augmented Generation) to provide answers 
    grounded in your own study materials.
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


# Include routers
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(quiz_router)
app.include_router(progress_router)


# Root endpoint
@app.get("/")
async def root():
    """Welcome endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "documents": "/documents",
            "chat": "/chat",
            "quiz": "/quiz",
            "progress": "/progress"
        }
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check vector store
        stats = VectorStoreManager.get_collection_stats()
        
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "llm_provider": settings.LLM_PROVIDER,
            "embedding_provider": settings.EMBEDDING_PROVIDER,
            "documents_indexed": stats.get("document_count", 0)
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e)
        }


# System info
@app.get("/system/info")
async def system_info():
    """Get system configuration information."""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm": {
            "provider": settings.LLM_PROVIDER,
            "model": getattr(settings, f"{settings.LLM_PROVIDER.upper()}_MODEL", "unknown")
        },
        "embedding": {
            "provider": settings.EMBEDDING_PROVIDER,
            "model": settings.EMBEDDING_MODEL
        },
        "rag": {
            "chunk_size": settings.CHUNK_SIZE,
            "chunk_overlap": settings.CHUNK_OVERLAP,
            "top_k_results": settings.TOP_K_RESULTS
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
