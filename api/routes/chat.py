"""
Chat routes for question answering using RAG.
"""
from fastapi import APIRouter, HTTPException
from api.models import ChatRequest, ChatResponse, SourceDocument, SummaryRequest, SummaryResponse, ExplanationRequest, ExplanationResponse
from rag.pipeline import get_rag_pipeline
from api.progress import get_progress_tracker
import time
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    """
    Ask a question about the study materials.
    
    The AI will search through uploaded documents and provide
    an answer grounded in your study materials.
    """
    start_time = time.time()
    
    try:
        pipeline = get_rag_pipeline()
        result = pipeline.answer_question(
            question=request.question,
            k=request.num_results,
            return_sources=request.include_sources
        )
        
        # Record the question for progress tracking
        tracker = get_progress_tracker()
        tracker.record_question(request.question)
        
        processing_time = time.time() - start_time
        
        # Convert sources to response model
        sources = [
            SourceDocument(
                content=s["content"],
                source=s["source"],
                page=s.get("page")
            )
            for s in result.get("sources", [])
        ]
        
        return ChatResponse(
            answer=result["answer"],
            sources=sources,
            processing_time=round(processing_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )


@router.post("/summarize", response_model=SummaryResponse)
async def summarize_topic(request: SummaryRequest):
    """
    Generate a summary of a topic from study materials.
    """
    try:
        pipeline = get_rag_pipeline()
        result = pipeline.summarize_topic(
            topic=request.topic,
            focus_area=request.focus_area
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=result.get("error", "Could not generate summary")
            )
        
        return SummaryResponse(
            success=True,
            topic=result["topic"],
            summary=result["summary"],
            sources_used=result["sources_used"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating summary: {str(e)}"
        )


@router.post("/explain", response_model=ExplanationResponse)
async def explain_concept(request: ExplanationRequest):
    """
    Get a detailed explanation of a concept.
    """
    try:
        pipeline = get_rag_pipeline()
        result = pipeline.explain_concept(concept=request.concept)
        
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=result.get("error", "Could not explain concept")
            )
        
        return ExplanationResponse(
            success=True,
            concept=result["concept"],
            explanation=result["explanation"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining concept: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error explaining concept: {str(e)}"
        )
