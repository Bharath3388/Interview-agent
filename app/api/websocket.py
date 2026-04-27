"""WebSocket handler for real-time interview interaction."""

import base64
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.tts import KokoroTTS
from app.agents.graph import InterviewGraph
from app.api.routes import sessions
from app.db.crud import save_completed_interview

logger = logging.getLogger(__name__)

ws_router = APIRouter()

_tts = None


def _get_tts():
    global _tts
    if _tts is None:
        _tts = KokoroTTS()
    return _tts


@ws_router.websocket("/ws/{session_id}")
async def interview_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()

    if session_id not in sessions:
        await websocket.send_json({"type": "error", "message": "Invalid session"})
        await websocket.close()
        return

    session = sessions[session_id]
    graph: InterviewGraph = session["graph"]
    user_id: int = session.get("user_id")

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            action = message.get("action")

            if action == "text":
                # Accept typed text directly
                text = message.get("text", "").strip()
                if not text:
                    continue

                response = await graph.process_answer(text)

                audio_bytes = await _get_tts().synthesize(response["question_text"])
                audio_b64_out = base64.b64encode(audio_bytes).decode() if audio_bytes else ""

                await websocket.send_json({
                    "type": "question",
                    "text": response["question_text"],
                    "question_number": response.get("question_number", 0),
                    "total_questions": response.get("total_questions", 0),
                    "topic_phase": response.get("topic_phase", ""),
                    "evaluation": response.get("evaluation", {}),
                    "audio": audio_b64_out,
                    "is_complete": response.get("is_complete", False),
                    "progress": graph.get_progress(),
                })

                if response.get("is_complete"):
                    report = response.get("report", {})
                    if user_id:
                        save_completed_interview(session_id, user_id, graph.state, report)
                    await websocket.send_json({
                        "type": "report",
                        "report": report,
                    })
                    sessions.pop(session_id, None)
                    break

            elif action == "end":
                graph.state.is_complete = True
                report = await graph.generate_report()
                if user_id:
                    save_completed_interview(session_id, user_id, graph.state, report)
                await websocket.send_json({"type": "report", "report": report})
                sessions.pop(session_id, None)
                break

    except WebSocketDisconnect:
        logger.info("Client disconnected: session %s", session_id)
    except Exception:
        logger.exception("WebSocket error for session %s", session_id)
        try:
            await websocket.send_json({"type": "error", "message": "An internal error occurred"})
        except Exception:
            pass
