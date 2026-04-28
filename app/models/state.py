from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time


@dataclass
class InterviewEntry:
    question: str
    answer: Optional[str] = None
    topic: str = ""
    evaluation: Optional[Dict] = None


@dataclass
class InterviewState:
    """Mutable state for a single interview session."""

    session_id: str = ""
    resume_text: str = ""
    jd_text: str = ""
    duration: int = 15  # minutes
    difficulty: str = "mid"

    history: List[InterviewEntry] = field(default_factory=list)
    scores: List[Dict] = field(default_factory=list)

    current_topic: str = "introduction"
    topics_covered: List[str] = field(default_factory=list)
    follow_up_count: int = 0
    questions_asked: int = 0
    max_questions: int = 7
    is_complete: bool = False

    start_time: float = 0.0

    # Pre-computed topic sequence
    TOPIC_SEQUENCE: List[str] = field(
        default_factory=lambda: [
            "introduction",
            "technical",
            "technical",
            "experience",
            "technical",
            "behavioral",
            "closing",
        ]
    )

    def __post_init__(self):
        self.max_questions = min(self.duration // 2, 15)
        if len(self.TOPIC_SEQUENCE) < self.max_questions:
            # Pad with extra technical questions
            self.TOPIC_SEQUENCE.extend(
                ["technical"] * (self.max_questions - len(self.TOPIC_SEQUENCE))
            )
        if not self.start_time:
            self.start_time = time.time()

    @property
    def elapsed_seconds(self) -> int:
        return int(time.time() - self.start_time)

    @property
    def current_topic_for_next(self) -> str:
        idx = min(self.questions_asked, len(self.TOPIC_SEQUENCE) - 1)
        return self.TOPIC_SEQUENCE[idx]

    def advance(self):
        """Move to next question slot."""
        if self.follow_up_count == 0:
            topic = self.current_topic_for_next
            if topic != self.current_topic:
                self.topics_covered.append(self.current_topic)
            self.current_topic = topic
        self.questions_asked += 1

    def should_end(self) -> bool:
        if self.questions_asked >= self.max_questions:
            return True
        if self.elapsed_seconds >= self.duration * 60:
            return True
        return False
