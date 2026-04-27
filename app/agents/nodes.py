"""LangGraph node functions for the interview workflow."""

import logging
from typing import Any, Dict

from app.models.state import InterviewState, InterviewEntry
from app.services.llm import GroqLLM
from app.config import settings

logger = logging.getLogger(__name__)


async def generate_question_node(
    state: InterviewState, llm: GroqLLM
) -> Dict[str, Any]:
    """Generate the next interview question."""
    is_follow_up = state.follow_up_count > 0

    question_data = await llm.generate_question(
        resume_text=state.resume_text,
        jd_text=state.jd_text,
        history=[
            {"question": e.question, "answer": e.answer or "", "topic": e.topic}
            for e in state.history[-8:]
        ],
        topic=state.current_topic,
        follow_up=is_follow_up,
    )

    question_text = question_data.get("question_text", "Could you elaborate?")

    # Record in history
    entry = InterviewEntry(
        question=question_text,
        topic=state.current_topic,
    )
    state.history.append(entry)

    return {
        "question_text": question_text,
        "question_type": question_data.get("question_type", state.current_topic),
        "question_number": state.questions_asked + 1,
        "total_questions": state.max_questions,
        "topic_phase": state.current_topic,
    }


async def evaluate_answer_node(
    state: InterviewState, llm: GroqLLM, answer: str
) -> Dict[str, Any]:
    """Evaluate the candidate's answer."""
    if not state.history:
        return {}

    # Store answer in the latest history entry
    state.history[-1].answer = answer

    last_question = state.history[-1].question

    evaluation = await llm.evaluate_answer(
        question=last_question,
        answer=answer,
        jd_text=state.jd_text,
    )

    state.history[-1].evaluation = evaluation
    state.scores.append(evaluation)

    # Manage follow-up logic
    if evaluation.get("needs_follow_up", False) and state.follow_up_count < settings.MAX_FOLLOW_UPS:
        state.follow_up_count += 1
    else:
        state.follow_up_count = 0

    return evaluation


async def decide_next_node(state: InterviewState) -> str:
    """Decide: continue, follow_up, or end."""
    if state.should_end():
        return "end"
    if state.follow_up_count > 0:
        return "follow_up"
    state.advance()
    return "continue"
