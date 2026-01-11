import os
from pathlib import Path
from typing import List, Optional
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles document loading and chunking with Semantic or Recursive splitting."""
    
    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown"}
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        use_semantic: bool = None
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.use_semantic = use_semantic if use_semantic is not None else settings.USE_SEMANTIC_CHUNKING
        
        if self.use_semantic:
            # Initialize SemanticChunker with embeddings
            logger.info("Using SemanticChunker for intelligent document splitting")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=f"sentence-transformers/{settings.EMBEDDING_MODEL}"
            )
            self.text_splitter = SemanticChunker(
                embeddings=self.embeddings,
                breakpoint_threshold_type='gradient',
                breakpoint_threshold_amount=settings.SEMANTIC_THRESHOLD
            )
        else:
            # Use traditional RecursiveCharacterTextSplitter
            logger.info("Using RecursiveCharacterTextSplitter for document splitting")
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
    
    def _get_loader(self, file_path: str):
        """Get the appropriate loader based on file extension."""
        ext = Path(file_path).suffix.lower()
        
        if ext == ".pdf":
            return PyPDFLoader(file_path)
        elif ext == ".txt":
            return TextLoader(file_path, encoding="utf-8")
        elif ext in {".md", ".markdown"}:
            return UnstructuredMarkdownLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    def load_document(self, file_path: str) -> List[Document]:
        """Load a single document and return its content."""
        logger.info(f"Loading document: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        loader = self._get_loader(file_path)
        documents = loader.load()
        
        # Add metadata
        file_name = Path(file_path).name
        for doc in documents:
            doc.metadata["source"] = file_name
            doc.metadata["file_path"] = file_path
        
        logger.info(f"Loaded {len(documents)} pages/sections from {file_name}")
        return documents
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into smaller chunks for embedding."""
        logger.info(f"Chunking {len(documents)} documents")
        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"Created {len(chunks)} chunks")
        return chunks
    
    def process_file(self, file_path: str) -> List[Document]:
        """Load and chunk a single file."""
        documents = self.load_document(file_path)
        return self.chunk_documents(documents)
    
    def process_directory(self, directory: str) -> List[Document]:
        """Process all supported files in a directory."""
        all_chunks = []
        directory_path = Path(directory)
        
        for ext in self.SUPPORTED_EXTENSIONS:
            for file_path in directory_path.glob(f"*{ext}"):
                try:
                    chunks = self.process_file(str(file_path))
                    all_chunks.extend(chunks)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
        
        return all_chunks
    
    @staticmethod
    def is_supported_file(filename: str) -> bool:
        """Check if a file type is supported."""
        ext = Path(filename).suffix.lower()
        return ext in DocumentProcessor.SUPPORTED_EXTENSIONS
