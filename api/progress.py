"""
Progress tracking service for monitoring student learning.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from pathlib import Path
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Tracks student progress, quiz results, and learning analytics."""
    
    def __init__(self, data_file: str = None):
        self.data_file = Path(data_file) if data_file else settings.BASE_DIR / "progress_data.json"
        self.data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """Load progress data from file."""
        if self.data_file.exists():
            try:
                with open(self.data_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading progress data: {e}")
        
        return {
            "sessions": [],
            "quiz_attempts": [],
            "questions_asked": [],
            "topic_scores": {},
            "total_stats": {
                "questions_asked": 0,
                "quizzes_taken": 0,
                "total_quiz_score": 0
            }
        }
    
    def _save_data(self):
        """Save progress data to file."""
        try:
            with open(self.data_file, "w") as f:
                json.dump(self.data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving progress data: {e}")
    
    def record_question(self, question: str, topic: str = "general"):
        """Record a question asked by the student."""
        self.data["questions_asked"].append({
            "question": question,
            "topic": topic,
            "timestamp": datetime.now().isoformat()
        })
        self.data["total_stats"]["questions_asked"] += 1
        
        # Update topic tracking
        if topic not in self.data["topic_scores"]:
            self.data["topic_scores"][topic] = {
                "questions": 0,
                "quizzes": 0,
                "total_score": 0,
                "attempts": 0
            }
        self.data["topic_scores"][topic]["questions"] += 1
        
        self._save_data()
    
    def record_quiz_attempt(
        self,
        topic: str,
        total_questions: int,
        correct_answers: int,
        question_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Record a quiz attempt and calculate weak areas."""
        score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        # Identify weak areas (questions answered incorrectly)
        weak_areas = [
            result["question"][:50] for result in question_results
            if not result.get("is_correct", False)
        ]
        
        attempt = {
            "attempt_id": f"quiz_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "topic": topic,
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "score_percentage": score_percentage,
            "weak_areas": weak_areas,
            "question_results": question_results,
            "timestamp": datetime.now().isoformat()
        }
        
        self.data["quiz_attempts"].append(attempt)
        self.data["total_stats"]["quizzes_taken"] += 1
        self.data["total_stats"]["total_quiz_score"] += score_percentage
        
        # Update topic scores
        if topic not in self.data["topic_scores"]:
            self.data["topic_scores"][topic] = {
                "questions": 0,
                "quizzes": 0,
                "total_score": 0,
                "attempts": 0
            }
        
        self.data["topic_scores"][topic]["quizzes"] += 1
        self.data["topic_scores"][topic]["total_score"] += score_percentage
        self.data["topic_scores"][topic]["attempts"] += 1
        
        self._save_data()
        
        return attempt
    
    def get_progress_stats(self) -> Dict[str, Any]:
        """Get overall progress statistics."""
        total_quizzes = self.data["total_stats"]["quizzes_taken"]
        
        # Calculate average score
        avg_score = 0
        if total_quizzes > 0:
            avg_score = self.data["total_stats"]["total_quiz_score"] / total_quizzes
        
        # Identify weak and strong areas
        weak_areas = []
        strong_areas = []
        
        for topic, scores in self.data["topic_scores"].items():
            if scores["attempts"] > 0:
                avg_topic_score = scores["total_score"] / scores["attempts"]
                topic_info = {
                    "topic": topic,
                    "average_score": avg_topic_score,
                    "attempts": scores["attempts"]
                }
                
                if avg_topic_score < 60:
                    weak_areas.append(topic_info)
                elif avg_topic_score >= 80:
                    strong_areas.append(topic_info)
        
        # Sort by score
        weak_areas.sort(key=lambda x: x["average_score"])
        strong_areas.sort(key=lambda x: x["average_score"], reverse=True)
        
        # Recent activity
        recent_quizzes = sorted(
            self.data["quiz_attempts"],
            key=lambda x: x["timestamp"],
            reverse=True
        )[:10]
        
        recent_questions = sorted(
            self.data["questions_asked"],
            key=lambda x: x["timestamp"],
            reverse=True
        )[:10]
        
        return {
            "total_sessions": len(set(
                q["timestamp"][:10] for q in self.data["questions_asked"]
            )),
            "total_questions_asked": self.data["total_stats"]["questions_asked"],
            "total_quizzes_taken": total_quizzes,
            "average_quiz_score": round(avg_score, 2),
            "topics_studied": list(self.data["topic_scores"].keys()),
            "weak_areas": weak_areas[:5],
            "strong_areas": strong_areas[:5],
            "recent_activity": {
                "recent_quizzes": recent_quizzes,
                "recent_questions": recent_questions
            }
        }
    
    def get_topic_stats(self, topic: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific topic."""
        if topic not in self.data["topic_scores"]:
            return None
        
        scores = self.data["topic_scores"][topic]
        avg_score = scores["total_score"] / scores["attempts"] if scores["attempts"] > 0 else 0
        
        # Get recent quiz attempts for this topic
        topic_quizzes = [
            q for q in self.data["quiz_attempts"]
            if q["topic"] == topic
        ]
        
        return {
            "topic": topic,
            "questions_asked": scores["questions"],
            "quizzes_taken": scores["quizzes"],
            "average_score": round(avg_score, 2),
            "recent_attempts": sorted(topic_quizzes, key=lambda x: x["timestamp"], reverse=True)[:5]
        }
    
    def reset_progress(self):
        """Reset all progress data."""
        self.data = {
            "sessions": [],
            "quiz_attempts": [],
            "questions_asked": [],
            "topic_scores": {},
            "total_stats": {
                "questions_asked": 0,
                "quizzes_taken": 0,
                "total_quiz_score": 0
            }
        }
        self._save_data()
        logger.info("Progress data reset")


# Singleton instance
_tracker_instance: Optional[ProgressTracker] = None


def get_progress_tracker() -> ProgressTracker:
    """Get or create progress tracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = ProgressTracker()
    return _tracker_instance
