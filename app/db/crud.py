"""CRUD helpers for interview persistence.

These functions use SessionLocal directly (not FastAPI Depends)
so they can be called from WebSocket handlers and background tasks.
"""

import datetime
import json
import logging

from app.db.database import SessionLocal
from app.db import models

logger = logging.getLogger(__name__)


def create_interview_session(
    session_id: str,
    user_id: int,
    jd_text: str,
    resume_text: str,
    difficulty: str,
    duration: int,
) -> None:
    """Insert a new InterviewSession row when the interview starts."""
    db = SessionLocal()
    try:
        record = models.InterviewSession(
            session_id=session_id,
            user_id=user_id,
            job_description=jd_text,
            resume_text=resume_text,
            difficulty=difficulty,
            duration=duration,
        )
        db.add(record)
        db.commit()
    except Exception:
        logger.exception("Failed to create interview session %s", session_id)
        db.rollback()
    finally:
        db.close()


def save_completed_interview(
    session_id: str,
    user_id: int,
    state,          # InterviewState dataclass
    report: dict,
) -> None:
    """Update the session row with results and persist all Q&A entries."""
    db = SessionLocal()
    try:
        db_session = (
            db.query(models.InterviewSession)
            .filter(models.InterviewSession.session_id == session_id)
            .first()
        )
        if not db_session:
            logger.warning("No DB session found for session_id %s — skipping save", session_id)
            return

        db_session.is_complete = True
        db_session.completed_at = datetime.datetime.utcnow()
        db_session.overall_score = int(report.get("overall_score") or 0)
        db_session.cracking_probability = int(report.get("cracking_probability") or 0)
        db_session.hiring_recommendation = report.get("hiring_recommendation") or ""
        db_session.summary = report.get("summary") or ""
        db_session.report_json = json.dumps(report)

        # Persist Q&A entries (only those with a real answer)
        for i, entry in enumerate(state.history):
            qa = models.InterviewQA(
                session_db_id=db_session.id,
                question_number=i + 1,
                topic=entry.topic or "",
                question=entry.question or "",
                answer=entry.answer or "",
                evaluation_json=json.dumps(entry.evaluation or {}),
            )
            db.add(qa)

        db.commit()
        logger.info("Saved completed interview %s for user %s", session_id, user_id)
    except Exception:
        logger.exception("Failed to save interview %s", session_id)
        db.rollback()
    finally:
        db.close()


def get_user_sessions(user_id: int) -> list:
    """Return all completed sessions for a user, newest first."""
    db = SessionLocal()
    try:
        rows = (
            db.query(models.InterviewSession)
            .filter(
                models.InterviewSession.user_id == user_id,
                models.InterviewSession.is_complete == True,  # noqa: E712
            )
            .order_by(models.InterviewSession.started_at.desc())
            .all()
        )
        return [
            {
                "session_id": r.session_id,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "difficulty": r.difficulty,
                "duration": r.duration,
                "overall_score": r.overall_score,
                "cracking_probability": r.cracking_probability,
                "hiring_recommendation": r.hiring_recommendation,
                "summary": r.summary,
                "job_description": r.job_description,
            }
            for r in rows
        ]
    finally:
        db.close()


def get_session_qas(session_id: str, user_id: int) -> list | None:
    """Return Q&A list for a session (returns None if session doesn't belong to user)."""
    db = SessionLocal()
    try:
        db_session = (
            db.query(models.InterviewSession)
            .filter(
                models.InterviewSession.session_id == session_id,
                models.InterviewSession.user_id == user_id,
            )
            .first()
        )
        if not db_session:
            return None
        return [
            {
                "question_number": qa.question_number,
                "topic": qa.topic,
                "question": qa.question,
                "answer": qa.answer,
                "evaluation": json.loads(qa.evaluation_json or "{}"),
            }
            for qa in db_session.qas
        ]
    finally:
        db.close()
