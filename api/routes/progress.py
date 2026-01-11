"""
Progress tracking routes for learning analytics.
"""
from fastapi import APIRouter, HTTPException
from api.models import ProgressStats
from api.progress import get_progress_tracker
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/progress", tags=["Progress"])


@router.get("/stats", response_model=ProgressStats)
async def get_progress_stats():
    """
    Get overall learning progress statistics.
    
    Returns:
    - Total questions asked
    - Total quizzes taken
    - Average quiz score
    - Topics studied
    - Weak and strong areas
    - Recent activity
    """
    tracker = get_progress_tracker()
    stats = tracker.get_progress_stats()
    
    return ProgressStats(
        total_sessions=stats["total_sessions"],
        total_questions_asked=stats["total_questions_asked"],
        total_quizzes_taken=stats["total_quizzes_taken"],
        average_quiz_score=stats["average_quiz_score"],
        topics_studied=stats["topics_studied"],
        weak_areas=stats["weak_areas"],
        strong_areas=stats["strong_areas"],
        recent_activity=stats["recent_activity"]
    )


@router.get("/topic/{topic}")
async def get_topic_progress(topic: str):
    """Get progress statistics for a specific topic."""
    tracker = get_progress_tracker()
    stats = tracker.get_topic_stats(topic)
    
    if stats is None:
        raise HTTPException(
            status_code=404,
            detail=f"No progress data found for topic: {topic}"
        )
    
    return stats


@router.post("/reset")
async def reset_progress():
    """Reset all progress data."""
    tracker = get_progress_tracker()
    tracker.reset_progress()
    return {"success": True, "message": "Progress data reset successfully"}


@router.get("/recommendations")
async def get_study_recommendations():
    """
    Get personalized study recommendations based on progress.
    
    Analyzes weak areas and suggests topics to focus on.
    """
    tracker = get_progress_tracker()
    stats = tracker.get_progress_stats()
    
    recommendations = []
    
    # Recommend weak areas
    for area in stats["weak_areas"]:
        recommendations.append({
            "type": "focus_area",
            "topic": area["topic"],
            "reason": f"Your average score is {area['average_score']:.1f}%",
            "action": "Review this topic and take more practice quizzes"
        })
    
    # If no quizzes taken yet
    if stats["total_quizzes_taken"] == 0:
        recommendations.append({
            "type": "get_started",
            "topic": "General",
            "reason": "You haven't taken any quizzes yet",
            "action": "Start with a quiz on your main study topic"
        })
    
    # If few questions asked
    if stats["total_questions_asked"] < 5:
        recommendations.append({
            "type": "explore",
            "topic": "General",
            "reason": "Try asking more questions about your materials",
            "action": "Use the chat to explore concepts you're unsure about"
        })
    
    # Celebrate strong areas
    for area in stats["strong_areas"][:2]:
        recommendations.append({
            "type": "strength",
            "topic": area["topic"],
            "reason": f"Great job! Your average score is {area['average_score']:.1f}%",
            "action": "Keep reviewing to maintain your knowledge"
        })
    
    return {
        "recommendations": recommendations,
        "summary": {
            "weak_topics": len(stats["weak_areas"]),
            "strong_topics": len(stats["strong_areas"]),
            "total_topics": len(stats["topics_studied"])
        }
    }
