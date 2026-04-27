"""Interview orchestrator using the LangGraph-style state machine."""

import logging
from typing import Dict, Any, Optional

from app.models.state import InterviewState
from app.services.llm import GroqLLM
from app.agents.nodes import (
    generate_question_node,
    evaluate_answer_node,
    decide_next_node,
)

logger = logging.getLogger(__name__)


class InterviewGraph:
    """Orchestrates the interview flow: question -> answer -> evaluate -> decide."""

    def __init__(
        self,
        llm: GroqLLM,
        state: InterviewState,
    ):
        self.llm = llm
        self.state = state

    async def start(self) -> Dict[str, Any]:
        """Generate the first question and return it."""
        result = await generate_question_node(self.state, self.llm)
        return result

    async def process_answer(self, answer: str) -> Dict[str, Any]:
        """Accept user answer, evaluate, decide next, and return response."""

        # 1. Evaluate
        evaluation = await evaluate_answer_node(self.state, self.llm, answer)

        # 2. Decide
        decision = await decide_next_node(self.state)

        if decision == "end":
            self.state.is_complete = True
            report = await self.generate_report()
            return {
                "question_text": "Thank you for completing the interview! I'm generating your detailed report now.",
                "question_type": "closing",
                "question_number": self.state.questions_asked,
                "total_questions": self.state.max_questions,
                "topic_phase": "closing",
                "evaluation": evaluation,
                "is_complete": True,
                "report": report,
            }

        # 3. Generate next question (regular or follow-up)
        result = await generate_question_node(self.state, self.llm)

        result["evaluation"] = evaluation
        result["is_complete"] = False
        return result

    async def generate_report(self) -> Dict[str, Any]:
        """Generate the final interview report."""
        answered = [e for e in self.state.history if e.answer and e.answer.strip()]
        if not answered:
            return {
                "overall_score": 0,
                "cracking_probability": 0,
                "technical_strengths": [],
                "areas_for_improvement": [
                    "No answers were provided during the interview."
                ],
                "specific_recommendations": [
                    "Attempt all questions during the interview to receive a meaningful evaluation.",
                    "Complete a full session for actionable, personalised feedback.",
                ],
                "hiring_recommendation": "Strong No",
                "summary": (
                    "The interview was ended before any questions were answered. "
                    "No evaluation could be performed."
                ),
                "topic_scores": {},
            }

        history_data = [
            {"question": e.question, "answer": e.answer or "", "topic": e.topic}
            for e in self.state.history
        ]
        report = await self.llm.generate_final_report(
            history=history_data,
            scores=self.state.scores,
            jd_text=self.state.jd_text,
        )
        return report

    def get_progress(self) -> Dict[str, Any]:
        return {
            "questions_asked": self.state.questions_asked,
            "total_questions": self.state.max_questions,
            "current_topic": self.state.current_topic,
            "elapsed_seconds": self.state.elapsed_seconds,
            "is_complete": self.state.is_complete,
        }
