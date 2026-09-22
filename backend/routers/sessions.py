from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ChatMessage, ChatSession, User
from backend.schemas.chat import SessionOut
from backend.services.auth import get_current_user


router = APIRouter(tags=["sessions"])


@router.get("/api/sessions", response_model=list[SessionOut])
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ChatSession]:
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    return sessions


@router.post("/api/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatSession:
    session = ChatSession(user_id=current_user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.delete("/api/sessions/{session_id}")
def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado a esta sessão")

    db.delete(session)
    db.commit()
    return {"ok": True}


@router.get("/api/sessions/{session_id}/messages", response_model=list[dict])
def get_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado a esta sessão")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [
        {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
        for m in messages
    ]


@router.get("/api/sessions/{session_id}/messages", response_model=list[dict])
def get_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado a esta sessão")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [
        {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
        for m in messages
    ]