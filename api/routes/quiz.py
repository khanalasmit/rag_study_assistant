"""
Quiz routes for generating and evaluating practice questions.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from api.models import QuizRequest, QuizResponse, QuizQuestion, QuizAnswerRequest, QuizResult
from rag.pipeline import get_rag_pipeline
from api.progress import get_progress_tracker
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/quiz", tags=["Quiz"])

# In-memory quiz storage (in production, use a database)
quiz_storage: Dict[str, Dict[str, Any]] = {}


@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(request: QuizRequest):
    """
    Generate a quiz on a specific topic from study materials.
    
    Supports MCQ, short answer, or mixed question types.
    """
    try:
        pipeline = get_rag_pipeline()
        result = pipeline.generate_quiz(
            topic=request.topic,
            num_questions=request.num_questions,
            question_type=request.question_type.value
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to generate quiz")
            )
        
        # Generate quiz ID and store questions
        quiz_id = str(uuid.uuid4())
        
        # Format questions with IDs
        questions = []
        for i, q in enumerate(result["questions"], 1):
            question = QuizQuestion(
                id=i,
                question=q.get("question", ""),
                type=q.get("type", "mcq"),
                difficulty=q.get("difficulty", "medium"),
                options=q.get("options"),
                correct_answer=q.get("correct_answer", ""),
                explanation=q.get("explanation", "")
            )
            questions.append(question)
        
        # Store quiz for later evaluation
        quiz_storage[quiz_id] = {
            "topic": request.topic,
            "questions": [q.model_dump() for q in questions],
            "created_at": datetime.now().isoformat()
        }
        
        return QuizResponse(
            success=True,
            topic=request.topic,
            questions=questions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating quiz: {str(e)}"
        )


@router.post("/submit/{quiz_id}", response_model=QuizResult)
async def submit_quiz(quiz_id: str, request: QuizAnswerRequest):
    """
    Submit answers for a quiz and get results.
    """
    if quiz_id not in quiz_storage:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    quiz = quiz_storage[quiz_id]
    questions = quiz["questions"]
    
    # Evaluate answers
    correct_count = 0
    question_results = []
    
    for q in questions:
        user_answer = request.answers.get(q["id"], "")
        is_correct = user_answer.strip().lower() == q["correct_answer"].strip().lower()
        
        if is_correct:
            correct_count += 1
        
        question_results.append({
            "question_id": q["id"],
            "question": q["question"],
            "user_answer": user_answer,
            "correct_answer": q["correct_answer"],
            "is_correct": is_correct,
            "explanation": q["explanation"]
        })
    
    total_questions = len(questions)
    score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
    
    # Record quiz attempt for progress tracking
    tracker = get_progress_tracker()
    tracker.record_quiz_attempt(
        topic=quiz["topic"],
        total_questions=total_questions,
        correct_answers=correct_count,
        question_results=question_results
    )
    
    return QuizResult(
        quiz_id=quiz_id,
        total_questions=total_questions,
        correct_answers=correct_count,
        score_percentage=round(score_percentage, 2),
        question_results=question_results,
        completed_at=datetime.now()
    )


@router.get("/history")
async def get_quiz_history():
    """Get list of generated quizzes."""
    return {
        "quizzes": [
            {
                "quiz_id": qid,
                "topic": q["topic"],
                "question_count": len(q["questions"]),
                "created_at": q["created_at"]
            }
            for qid, q in quiz_storage.items()
        ]
    }


@router.get("/{quiz_id}")
async def get_quiz(quiz_id: str):
    """Get a specific quiz by ID."""
    if quiz_id not in quiz_storage:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    quiz = quiz_storage[quiz_id]
    
    # Return questions without correct answers for taking the quiz
    questions_for_student = []
    for q in quiz["questions"]:
        questions_for_student.append({
            "id": q["id"],
            "question": q["question"],
            "type": q["type"],
            "difficulty": q["difficulty"],
            "options": q.get("options")
        })
    
    return {
        "quiz_id": quiz_id,
        "topic": quiz["topic"],
        "questions": questions_for_student
    }
