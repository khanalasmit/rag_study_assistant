"""
Vector store module using ChromaDB for document storage and retrieval.
"""
from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
from langchain_chroma import Chroma
from rag.embeddings import get_embeddings
from config.settings import settings
import logging
import shutil

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages ChromaDB vector store operations."""
    
    _instance: Optional[Chroma] = None
    
    @classmethod
    def get_vector_store(cls, collection_name: str = "study_documents") -> Chroma:
        """Get or create the vector store instance."""
        if cls._instance is None:
            cls._instance = cls._create_vector_store(collection_name)
        return cls._instance
    
    @classmethod
    def _create_vector_store(cls, collection_name: str) -> Chroma:
        """Create a new ChromaDB vector store."""
        logger.info(f"Initializing ChromaDB at: {settings.CHROMA_DB_DIR}")
        
        embeddings = get_embeddings()
        
        return Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=str(settings.CHROMA_DB_DIR)
        )
    
    @classmethod
    def add_documents(
        cls,
        documents: List[Document],
        collection_name: str = "study_documents"
    ) -> List[str]:
        """Add documents to the vector store."""
        vector_store = cls.get_vector_store(collection_name)
        
        logger.info(f"Adding {len(documents)} documents to vector store")
        ids = vector_store.add_documents(documents)
        logger.info(f"Successfully added {len(ids)} documents")
        
        return ids
    
    @classmethod
    def similarity_search(
        cls,
        query: str,
        k: int = None,
        collection_name: str = "study_documents",
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Perform similarity search on the vector store."""
        k = k or settings.TOP_K_RESULTS
        vector_store = cls.get_vector_store(collection_name)
        
        logger.info(f"Performing similarity search for: '{query[:50]}...' with k={k}")
        
        results = vector_store.similarity_search(
            query=query,
            k=k,
            filter=filter
        )
        
        logger.info(f"Found {len(results)} relevant documents")
        return results
    
    @classmethod
    def similarity_search_with_score(
        cls,
        query: str,
        k: int = None,
        collection_name: str = "study_documents"
    ) -> List[tuple]:
        """Perform similarity search with relevance scores."""
        k = k or settings.TOP_K_RESULTS
        vector_store = cls.get_vector_store(collection_name)
        
        results = vector_store.similarity_search_with_score(query=query, k=k)
        return results
    
    @classmethod
    def get_collection_stats(cls, collection_name: str = "study_documents") -> Dict[str, Any]:
        """Get statistics about the vector store collection."""
        vector_store = cls.get_vector_store(collection_name)
        
        try:
            collection = vector_store._collection
            count = collection.count()
            return {
                "collection_name": collection_name,
                "document_count": count,
                "persist_directory": str(settings.CHROMA_DB_DIR)
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}
    
    @classmethod
    def delete_collection(cls, collection_name: str = "study_documents"):
        """Delete the entire collection."""
        vector_store = cls.get_vector_store(collection_name)
        
        try:
            vector_store.delete_collection()
            cls._instance = None
            logger.info(f"Deleted collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise
    
    @classmethod
    def reset_database(cls):
        """Reset the entire vector database."""
        try:
            cls._instance = None
            if settings.CHROMA_DB_DIR.exists():
                shutil.rmtree(settings.CHROMA_DB_DIR)
                settings.CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
            logger.info("Vector database reset successfully")
        except Exception as e:
            logger.error(f"Error resetting database: {e}")
            raise
    
    @classmethod
    def reset(cls):
        """Reset the vector store instance."""
        cls._instance = None


def get_vector_store(collection_name: str = "study_documents") -> Chroma:
    """Convenience function to get vector store."""
    return VectorStoreManager.get_vector_store(collection_name)
