"""
Pydantic models for API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class QuestionType(str, Enum):
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"
    MIXED = "mixed"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# Document Models
class DocumentInfo(BaseModel):
    """Information about an uploaded document."""
    id: str
    filename: str
    file_type: str
    upload_time: datetime
    chunk_count: int
    status: str = "processed"


class DocumentUploadResponse(BaseModel):
    """Response after document upload."""
    success: bool
    message: str
    document: Optional[DocumentInfo] = None
    error: Optional[str] = None


class DocumentListResponse(BaseModel):
    """Response for listing documents."""
    documents: List[DocumentInfo]
    total_count: int


# Chat Models
class ChatRequest(BaseModel):
    """Request for chat/question answering."""
    question: str = Field(..., min_length=1, max_length=2000)
    include_sources: bool = True
    num_results: int = Field(default=5, ge=1, le=20)


class SourceDocument(BaseModel):
    """A source document reference."""
    content: str
    source: str
    page: Optional[int] = None


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    answer: str
    sources: List[SourceDocument] = []
    processing_time: Optional[float] = None


# Quiz Models
class QuizRequest(BaseModel):
    """Request for quiz generation."""
    topic: str = Field(..., min_length=1, max_length=500)
    num_questions: int = Field(default=5, ge=1, le=20)
    question_type: QuestionType = QuestionType.MIXED


class QuizQuestion(BaseModel):
    """A single quiz question."""
    id: int
    question: str
    type: str
    difficulty: str
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: str


class QuizResponse(BaseModel):
    """Response from quiz generation."""
    success: bool
    topic: str
    questions: List[QuizQuestion] = []
    error: Optional[str] = None


class QuizAnswerRequest(BaseModel):
    """Request for submitting quiz answers."""
    quiz_id: str
    answers: Dict[int, str]  # question_id -> answer


class QuizResult(BaseModel):
    """Result of a quiz attempt."""
    quiz_id: str
    total_questions: int
    correct_answers: int
    score_percentage: float
    question_results: List[Dict[str, Any]]
    completed_at: datetime


# Summary Models
class SummaryRequest(BaseModel):
    """Request for topic summary."""
    topic: str = Field(..., min_length=1, max_length=500)
    focus_area: str = "all key concepts"


class SummaryResponse(BaseModel):
    """Response from summary endpoint."""
    success: bool
    topic: str
    summary: str
    sources_used: int
    error: Optional[str] = None


# Explanation Models
class ExplanationRequest(BaseModel):
    """Request for concept explanation."""
    concept: str = Field(..., min_length=1, max_length=500)


class ExplanationResponse(BaseModel):
    """Response from explanation endpoint."""
    success: bool
    concept: str
    explanation: str
    error: Optional[str] = None


# Progress Models
class StudySession(BaseModel):
    """A study session record."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    questions_asked: int = 0
    quizzes_taken: int = 0
    topics_studied: List[str] = []


class QuizAttempt(BaseModel):
    """A quiz attempt record."""
    attempt_id: str
    quiz_topic: str
    score: float
    total_questions: int
    correct_answers: int
    timestamp: datetime
    weak_areas: List[str] = []


class ProgressStats(BaseModel):
    """Overall progress statistics."""
    total_sessions: int
    total_questions_asked: int
    total_quizzes_taken: int
    average_quiz_score: float
    topics_studied: List[str]
    weak_areas: List[Dict[str, Any]]
    strong_areas: List[Dict[str, Any]]
    recent_activity: Dict[str, Any]  # Contains recent_quizzes and recent_questions


# System Models
class SystemStatus(BaseModel):
    """System health status."""
    status: str
    version: str
    documents_indexed: int
    llm_provider: str
    embedding_provider: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    status_code: int
