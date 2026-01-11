from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.retrievers import BM25Retriever
from rag.vector_store import VectorStoreManager
from rag.llm import get_llm
from rag.prompts import QA_PROMPT, QUIZ_PROMPT, SUMMARY_PROMPT, EXPLAIN_PROMPT
from config.settings import settings
import json
import logging
import re

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Main RAG pipeline with hybrid retrieval (BM25 + Vector similarity)."""
    
    def __init__(self, collection_name: str = "study_documents"):
        self.collection_name = collection_name
        self.llm = get_llm()
        self.output_parser = StrOutputParser()
        self.bm25_retriever: Optional[BM25Retriever] = None
        self.use_hybrid = settings.USE_HYBRID_RETRIEVAL
        self._documents_cache: List[Document] = []
    
    def _format_docs(self, docs: List[Document]) -> str:
        """Format retrieved documents into a single context string with explicit page numbers."""
        formatted_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "")
            page_info = f" (Page {page + 1})" if page != "" else ""  # page +1 because pdf stores page number as 0 indexed
            
            # Add clear page number markers for hallucination detection
            page_label = f"PAGE {page + 1}" if page != "" else "PAGE UNKNOWN"
            
            formatted_parts.append(
                f"[Source {i}: {source}{page_info}]\n[{page_label}]\n{doc.page_content}"
            )
        return "\n\n---\n\n".join(formatted_parts)
    
    def update_bm25_index(self, documents: List[Document]):
        """Update the BM25 retriever with new documents."""
        if not documents:
            return
        
        self._documents_cache.extend(documents)
        
        if self.use_hybrid:
            logger.info(f"Updating BM25 index with {len(documents)} documents")
            self.bm25_retriever = BM25Retriever.from_documents(
                self._documents_cache,
                k=settings.TOP_K_RESULTS
            )
    
    def _retrieve_bm25(self, query: str, k: int = None) -> List[Document]:
        """Retrieve using BM25 (sparse retrieval)."""
        if self.bm25_retriever is None:
            return []
        
        k = k or settings.TOP_K_RESULTS
        self.bm25_retriever.k = k
        
        try:
            results = self.bm25_retriever.invoke(query)
            logger.info(f"BM25 retrieved {len(results)} documents")
            return results
        except Exception as e:
            logger.error(f"BM25 retrieval error: {e}")
            return []
    
    def _retrieve_vector(self, query: str, k: int = None) -> List[Document]:
        """Retrieve using vector similarity (dense retrieval)."""
        k = k or settings.TOP_K_RESULTS
        return VectorStoreManager.similarity_search(
            query=query,
            k=k,
            collection_name=self.collection_name
        )
    
    def _retrieve(self, query: str, k: int = None) -> List[Document]:
        """
        Hybrid retrieval: combines BM25 and vector similarity results.
        BM25 excels at keyword matching, vector at semantic similarity.
        """
        k = k or settings.TOP_K_RESULTS
        
        if self.use_hybrid and self.bm25_retriever is not None:
            # Get results from both retrievers
            bm25_docs = self._retrieve_bm25(query, k)
            vector_docs = self._retrieve_vector(query, k)
            
            # Combine and deduplicate results
            seen_content = set()
            combined_docs = []
            
            # Interleave results for diversity (vector first, then bm25)
            for doc in vector_docs + bm25_docs:
                content_hash = hash(doc.page_content[:200])
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    combined_docs.append(doc)
                    if len(combined_docs) >= k:
                        break
            
            logger.info(f"Hybrid retrieval: {len(combined_docs)} unique documents")
            return combined_docs
        else:
            # Fallback to vector-only retrieval
            return self._retrieve_vector(query, k)
    
    def answer_question(
        self,
        question: str,
        k: int = None,
        return_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG.
        
        Args:
            question: The user's question
            k: Number of documents to retrieve
            return_sources: Whether to include source documents in response
            
        Returns:
            Dictionary with answer and optional sources
        """
        logger.info(f"Processing question: {question[:100]}...")
        
        # Retrieve relevant documents
        docs = self._retrieve(question, k)
        
        if not docs:
            return {
                "answer": "I couldn't find any relevant information in your study materials. Please make sure you've uploaded documents related to this topic.",
                "sources": []
            }
        
        # Format context
        context = self._format_docs(docs)
        
        # Generate answer
        chain = QA_PROMPT | self.llm | self.output_parser
        answer = chain.invoke({
            "context": context,
            "question": question
        })
        
        result = {"answer": answer}
        
        if return_sources:
            result["sources"] = [
                {
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "source": doc.metadata.get("source", "Unknown"),
                    "page": doc.metadata.get("page", None)
                }
                for doc in docs
            ]
        
        return result
    
    def generate_quiz(
        self,
        topic: str,
        num_questions: int = None,
        question_type: str = "mixed",
        k: int = None
    ) -> Dict[str, Any]:
        """
        Generate quiz questions on a topic.
        
        Args:
            topic: Topic to generate questions about
            num_questions: Number of questions to generate
            question_type: Type of questions (mcq, short_answer, mixed)
            k: Number of documents to retrieve for context
            
        Returns:
            Dictionary with generated questions
        """
        num_questions = num_questions or settings.DEFAULT_QUIZ_QUESTIONS
        num_questions = min(num_questions, settings.MAX_QUIZ_QUESTIONS)
        
        logger.info(f"Generating {num_questions} {question_type} questions on: {topic}")
        
        # Retrieve relevant documents
        docs = self._retrieve(topic, k or 10)
        
        if not docs:
            return {
                "success": False,
                "error": "No relevant content found for this topic",
                "questions": []
            }
        
        context = self._format_docs(docs)
        
        # Generate questions
        chain = QUIZ_PROMPT | self.llm | self.output_parser
        response = chain.invoke({
            "context": context,
            "topic": topic,
            "num_questions": num_questions,
            "question_type": question_type
        })
        
        # Parse JSON response
        try:
            # Extract JSON from response (handle potential markdown code blocks)
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                questions = json.loads(json_match.group())
            else:
                questions = json.loads(response)
            
            return {
                "success": True,
                "topic": topic,
                "questions": questions
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse quiz response: {e}")
            return {
                "success": False,
                "error": "Failed to generate properly formatted questions",
                "raw_response": response
            }
    
    def summarize_topic(
        self,
        topic: str,
        focus_area: str = "all key concepts",
        k: int = None
    ) -> Dict[str, Any]:
        logger.info(f"Generating summary for: {topic}")
        
        docs = self._retrieve(topic, k or 8)
        
        if not docs:
            return {
                "success": False,
                "error": "No relevant content found for this topic",
                "summary": ""
            }
        
        context = self._format_docs(docs)
        
        chain = SUMMARY_PROMPT | self.llm | self.output_parser
        summary = chain.invoke({
            "context": context,
            "focus_area": focus_area
        })
        
        return {
            "success": True,
            "topic": topic,
            "summary": summary,
            "sources_used": len(docs)
        }
    
    def explain_concept(
        self,
        concept: str,
        k: int = None
    ) -> Dict[str, Any]:
        logger.info(f"Explaining concept: {concept}")
        
        docs = self._retrieve(concept, k)
        
        if not docs:
            return {
                "success": False,
                "error": "No relevant content found for this concept",
                "explanation": ""
            }
        
        context = self._format_docs(docs)
        
        chain = EXPLAIN_PROMPT | self.llm | self.output_parser
        explanation = chain.invoke({
            "context": context,
            "concept": concept
        })
        
        return {
            "success": True,
            "concept": concept,
            "explanation": explanation
        }


# Singleton instance
_pipeline_instance: Optional[RAGPipeline] = None


def get_rag_pipeline(collection_name: str = "study_documents") -> RAGPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = RAGPipeline(collection_name)
    return _pipeline_instance


def reset_pipeline():
    """Reset the pipeline instance."""
    global _pipeline_instance
    _pipeline_instance = None
