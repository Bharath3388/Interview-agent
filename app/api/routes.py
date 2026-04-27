"""REST API routes for interview setup and audio serving."""

import base64
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.services.resume_parser import ResumeParser
from app.services.llm import GroqLLM
from app.services.tts import KokoroTTS
from app.models.state import InterviewState
from app.agents.graph import InterviewGraph
from app.db.database import get_db
from app.db import models
from app.db.crud import create_interview_session, save_completed_interview
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# Shared state across routes/ws — keyed by session_id
sessions: dict[str, dict] = {}

resume_parser = ResumeParser()


@router.post("/interview/start")
async def start_interview(
    resume: Optional[UploadFile] = File(None),
    job_description: str = Form(""),
    topic: str = Form(""),
    duration: int = Form(15),
    difficulty: str = Form("mid"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start a new interview session and return the first question + audio."""
    session_id = uuid.uuid4().hex[:12]

    # Parse resume
    resume_text = ""
    if resume and resume.filename:
        resume_text = await resume_parser.parse(resume)

    jd_text = job_description or topic or "General software engineering interview"

    # Build interview state
    state = InterviewState(
        session_id=session_id,
        resume_text=resume_text,
        jd_text=jd_text,
        duration=duration,
        difficulty=difficulty,
    )

    llm = GroqLLM()
    graph = InterviewGraph(llm=llm, state=state)

    # Generate first question
    first_q = await graph.start()

    # Generate TTS
    tts = KokoroTTS()
    audio_bytes = await tts.synthesize(first_q["question_text"])
    audio_b64 = base64.b64encode(audio_bytes).decode() if audio_bytes else ""

    # Store session
    sessions[session_id] = {
        "graph": graph,
        "state": state,
        "llm": llm,
        "user_id": current_user.id,
    }

    # Persist session record in DB
    create_interview_session(
        session_id=session_id,
        user_id=current_user.id,
        jd_text=jd_text,
        resume_text=resume_text,
        difficulty=difficulty,
        duration=duration,
    )

    return {
        "session_id": session_id,
        "first_question": first_q,
        "audio": audio_b64,
        "progress": graph.get_progress(),
    }


@router.get("/interview/{session_id}/progress")
async def get_progress(session_id: str):
    if session_id not in sessions:
        return JSONResponse({"error": "Session not found"}, status_code=404)
    return sessions[session_id]["graph"].get_progress()


@router.post("/interview/{session_id}/end")
async def end_interview(session_id: str):
    """Force-end an interview and get the report."""
    if session_id not in sessions:
        return JSONResponse({"error": "Session not found"}, status_code=404)

    graph: InterviewGraph = sessions[session_id]["graph"]
    user_id: int = sessions[session_id].get("user_id")
    graph.state.is_complete = True
    report = await graph.generate_report()

    if user_id:
        save_completed_interview(session_id, user_id, graph.state, report)

    del sessions[session_id]
    return {"report": report}


@router.get("/health")
async def health():
    return {"status": "healthy", "sessions_active": len(sessions)}
