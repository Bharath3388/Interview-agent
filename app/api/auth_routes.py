"""Authentication endpoints: register, login, me, and session history."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.db.crud import get_user_sessions, get_session_qas
from app.core.security import hash_password, verify_password, create_access_token
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/api/auth")


# ---- Request schemas ----

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        return v

    @field_validator("password")
    @classmethod
    def password_valid(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


# ---- Endpoints ----

@auth_router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == req.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(models.User).filter(models.User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = models.User(
        username=req.username,
        email=req.email.lower(),
        hashed_password=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    logger.info("New user registered: %s", user.username)
    return {"access_token": token, "token_type": "bearer", "username": user.username}


@auth_router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer", "username": user.username}


@auth_router.get("/me")
def me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
    }


# ---- History endpoints ----

@auth_router.get("/history")
def history(current_user: models.User = Depends(get_current_user)):
    """List all completed interview sessions for the logged-in user."""
    return get_user_sessions(current_user.id)


@auth_router.get("/history/{session_id}")
def session_detail(
    session_id: str,
    current_user: models.User = Depends(get_current_user),
):
    """Return Q&A detail for a specific session owned by the current user."""
    qas = get_session_qas(session_id, current_user.id)
    if qas is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "qas": qas}
