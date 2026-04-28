from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class InterviewStartRequest(BaseModel):
    job_description: str = ""
    topic: str = ""
    duration: int = Field(default=15, ge=5, le=60)
    difficulty: str = Field(default="mid", pattern="^(easy|mid|hard)$")


class QuestionResponse(BaseModel):
    question_text: str
    question_type: str = "technical"
    question_number: int = 1
    total_questions: int = 7
    topic_phase: str = "introduction"


class EvaluationScore(BaseModel):
    technical_accuracy: int = 0
    communication_clarity: int = 0
    depth_of_knowledge: int = 0
    relevance_to_role: int = 0
    needs_follow_up: bool = False
    brief_feedback: str = ""


class InterviewReport(BaseModel):
    overall_score: int = 0
    cracking_probability: int = 0
    technical_strengths: List[str] = []
    areas_for_improvement: List[str] = []
    specific_recommendations: List[str] = []
    hiring_recommendation: str = "N/A"
    summary: str = ""
    topic_scores: Dict[str, int] = {}


class SessionInfo(BaseModel):
    session_id: str
    status: str = "active"
    questions_asked: int = 0
    total_questions: int = 7
    current_topic: str = "introduction"
    elapsed_seconds: int = 0
