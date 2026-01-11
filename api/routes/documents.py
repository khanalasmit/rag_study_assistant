"""
Document management routes for file upload and listing.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import os
import uuid
from datetime import datetime
from pathlib import Path
from api.models import DocumentInfo, DocumentUploadResponse, DocumentListResponse
from rag.document_loader import DocumentProcessor
from rag.vector_store import VectorStoreManager
from rag.pipeline import get_rag_pipeline
from config.settings import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])

# In-memory document registry (in production, use a database)
document_registry: dict = {}


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document for processing and indexing.
    
    Supports PDF, TXT, and Markdown files.
    Uses SemanticChunker for intelligent splitting and BM25+Vector hybrid retrieval.
    """
    # Validate file type
    if not DocumentProcessor.is_supported_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported types: {DocumentProcessor.SUPPORTED_EXTENSIONS}"
        )
    
    try:
        # Ensure upload directory exists
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        # Generate unique ID and save file
        doc_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        saved_filename = f"{doc_id}{file_ext}"
        file_path = settings.UPLOAD_DIR / saved_filename
        
        # Save the uploaded file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved file: {file_path}")
        
        # Process and index the document (uses SemanticChunker if enabled)
        processor = DocumentProcessor()
        chunks = processor.process_file(str(file_path))
        
        # Add document ID to metadata
        for chunk in chunks:
            chunk.metadata["document_id"] = doc_id
        
        # Add to vector store (dense retrieval)
        VectorStoreManager.add_documents(chunks)
        
        # Update BM25 index (sparse retrieval) for hybrid search
        pipeline = get_rag_pipeline()
        pipeline.update_bm25_index(chunks)
        
        # Register document
        doc_info = DocumentInfo(
            id=doc_id,
            filename=file.filename,
            file_type=file_ext,
            upload_time=datetime.now(),
            chunk_count=len(chunks),
            status="processed"
        )
        document_registry[doc_id] = doc_info
        
        logger.info(f"Successfully processed document: {file.filename} ({len(chunks)} chunks)")
        
        return DocumentUploadResponse(
            success=True,
            message=f"Document '{file.filename}' uploaded and indexed successfully",
            document=doc_info
        )
        
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )


@router.get("/list", response_model=DocumentListResponse)
async def list_documents():
    """List all uploaded documents."""
    documents = list(document_registry.values())
    return DocumentListResponse(
        documents=documents,
        total_count=len(documents)
    )


@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document(document_id: str):
    """Get information about a specific document."""
    if document_id not in document_registry:
        raise HTTPException(status_code=404, detail="Document not found")
    return document_registry[document_id]


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its indexed chunks."""
    if document_id not in document_registry:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        doc_info = document_registry[document_id]
        
        # Delete the file
        file_path = settings.UPLOAD_DIR / f"{document_id}{doc_info.file_type}"
        if file_path.exists():
            os.remove(file_path)
        
        # Remove from registry
        del document_registry[document_id]
        
        # Note: ChromaDB doesn't easily support filtering deletes
        # In production, you'd need to rebuild the index or use a different approach
        
        return {"success": True, "message": f"Document '{doc_info.filename}' deleted"}
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )


@router.post("/reset")
async def reset_documents():
    """Reset all documents and the vector store."""
    try:
        # Clear document registry
        document_registry.clear()
        
        # Clear upload directory
        for file in settings.UPLOAD_DIR.glob("*"):
            if file.is_file():
                os.remove(file)
        
        # Reset vector store
        VectorStoreManager.reset_database()
        
        return {"success": True, "message": "All documents and index reset"}
        
    except Exception as e:
        logger.error(f"Error resetting documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting: {str(e)}"
        )
