"""ORM models: User, InterviewSession, InterviewQA."""

import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey,
    Integer, String, Text,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(256), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    sessions = relationship("InterviewSession", back_populates="user")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(32), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Context
    job_description = Column(Text, default="")
    resume_text = Column(Text, default="")
    difficulty = Column(String(16), default="mid")
    duration = Column(Integer, default=15)

    # Results (populated when session ends)
    overall_score = Column(Integer, default=0)
    cracking_probability = Column(Integer, default=0)
    hiring_recommendation = Column(String(64), default="")
    summary = Column(Text, default="")
    report_json = Column(Text, default="{}")

    # Timestamps
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    is_complete = Column(Boolean, default=False)

    user = relationship("User", back_populates="sessions")
    qas = relationship("InterviewQA", back_populates="session", order_by="InterviewQA.question_number")


class InterviewQA(Base):
    __tablename__ = "interview_qas"

    id = Column(Integer, primary_key=True, index=True)
    session_db_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)

    question_number = Column(Integer, default=0)
    topic = Column(String(64), default="")
    question = Column(Text, default="")
    answer = Column(Text, default="")
    evaluation_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("InterviewSession", back_populates="qas")
