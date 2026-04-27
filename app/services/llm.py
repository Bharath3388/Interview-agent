import json
import logging
import re
from typing import Any, Dict, List

from groq import AsyncGroq

from app.config import settings

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> Dict[str, Any]:
    """Extract JSON from an LLM response that may contain markdown fences."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    logger.warning("Could not parse JSON from LLM response, returning raw text")
    return {"raw_text": text}


class GroqLLM:
    """Drop-in replacement for GeminiLLM using Groq API."""

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    async def _chat(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048,
        )
        return response.choices[0].message.content or ""

    async def generate_question(
        self,
        resume_text: str,
        jd_text: str,
        history: List[Dict],
        topic: str,
        follow_up: bool = False,
    ) -> Dict:
        history_str = json.dumps(history[-10:], indent=2) if history else "[]"

        if follow_up:
            prompt = f"""You are an expert technical interviewer conducting a live interview.

RESUME:
{resume_text or "Not provided"}

JOB DESCRIPTION / TOPIC:
{jd_text}

CONVERSATION HISTORY (recent):
{history_str}

The candidate's last answer was vague or incomplete. Ask a specific follow-up question to probe deeper on the same topic.

Return ONLY valid JSON:
{{
  "question_text": "Your follow-up question here",
  "question_type": "follow_up",
  "expected_skills": ["skill1", "skill2"],
  "follow_up_hints": "What to look for in the answer"
}}"""
        else:
            prompt = f"""You are an expert technical interviewer conducting a live interview.

RESUME:
{resume_text or "Not provided"}

JOB DESCRIPTION / TOPIC:
{jd_text}

CONVERSATION HISTORY (recent):
{history_str}

CURRENT TOPIC PHASE: {topic}

Generate the next interview question appropriate for this phase:
- introduction: Warm-up, ask about background and motivation
- technical: Deep technical questions on skills from resume/JD
- experience: Project experience, challenges faced, problem-solving
- behavioral: Teamwork, leadership, conflict resolution
- closing: Final questions, candidate questions, wrap-up

Be conversational and professional. Probe depth, not just surface knowledge.

Return ONLY valid JSON:
{{
  "question_text": "Your question here",
  "question_type": "{topic}",
  "expected_skills": ["skill1", "skill2"],
  "follow_up_hints": "What to look for in the answer"
}}"""

        try:
            text = await self._chat(prompt)
            return _extract_json(text)
        except Exception as e:
            logger.error("Groq generate_question error: %s", e)
            return {
                "question_text": "Could you tell me more about your experience?",
                "question_type": topic,
                "expected_skills": [],
                "follow_up_hints": "",
            }

    async def evaluate_answer(
        self,
        question: str,
        answer: str,
        jd_text: str,
    ) -> Dict:
        prompt = f"""Evaluate this interview response concisely.

QUESTION: {question}
CANDIDATE'S ANSWER: {answer}
JOB CONTEXT: {jd_text[:1000]}

Score each from 0-100:
1. technical_accuracy
2. communication_clarity
3. depth_of_knowledge
4. relevance_to_role

Also decide: needs_follow_up (true if answer is vague, shallow, or incomplete).

Return ONLY valid JSON:
{{
  "technical_accuracy": 75,
  "communication_clarity": 80,
  "depth_of_knowledge": 70,
  "relevance_to_role": 85,
  "needs_follow_up": false,
  "brief_feedback": "One-line internal note"
}}"""

        try:
            text = await self._chat(prompt)
            result = _extract_json(text)
            result["needs_follow_up"] = bool(result.get("needs_follow_up", False))
            return result
        except Exception as e:
            logger.error("Groq evaluate_answer error: %s", e)
            return {
                "technical_accuracy": 50,
                "communication_clarity": 50,
                "depth_of_knowledge": 50,
                "relevance_to_role": 50,
                "needs_follow_up": False,
                "brief_feedback": "Evaluation unavailable",
            }

    async def generate_final_report(
        self,
        history: List[Dict],
        scores: List[Dict],
        jd_text: str,
    ) -> Dict:
        prompt = f"""Generate a comprehensive interview assessment report.

FULL TRANSCRIPT:
{json.dumps(history, indent=2)}

PER-QUESTION SCORES:
{json.dumps(scores, indent=2)}

JOB DESCRIPTION:
{jd_text[:2000]}

Return ONLY valid JSON:
{{
  "overall_score": 78,
  "cracking_probability": 65,
  "technical_strengths": ["strength1", "strength2"],
  "areas_for_improvement": ["area1", "area2"],
  "specific_recommendations": ["rec1", "rec2"],
  "hiring_recommendation": "Yes",
  "summary": "2-3 sentence executive summary",
  "topic_scores": {{
    "technical": 75,
    "communication": 80,
    "experience": 70,
    "behavioral": 85
  }}
}}

hiring_recommendation must be one of: Strong No, No, Maybe, Yes, Strong Yes"""

        try:
            text = await self._chat(prompt)
            return _extract_json(text)
        except Exception as e:
            logger.error("Groq generate_report error: %s", e)
            return {
                "overall_score": 0,
                "cracking_probability": 0,
                "technical_strengths": [],
                "areas_for_improvement": ["Report generation failed"],
                "specific_recommendations": [],
                "hiring_recommendation": "N/A",
                "summary": "Report generation encountered an error.",
                "topic_scores": {},
            }
