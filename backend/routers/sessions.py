from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ChatMessage, ChatSession
from backend.routers.auth import get_current_user
from backend.schemas.session import MessageOut, SessionCreate, SessionOut, SessionRename
from backend.services.openrouter import generate_reply


router = APIRouter()


@router.get("/api/sessions", response_model=list[SessionOut])
def list_sessions(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista todas as sessões do usuário, da mais recente para a mais antiga."""
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    return sessions


@router.post("/api/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cria uma nova sessão para o usuário."""
    session = ChatSession(user_id=current_user.id, title="")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.patch("/api/sessions/{session_id}", response_model=SessionOut)
def rename_session(
    session_id: int,
    payload: SessionRename,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Renomeia uma sessão."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    session.title = payload.title
    db.commit()
    db.refresh(session)
    return session


@router.delete("/api/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exclui uma sessão e todas as suas mensagens."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    db.delete(session)
    db.commit()


@router.get("/api/sessions/{session_id}/messages", response_model=list[MessageOut])
def get_session_messages(
    session_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retorna todas as mensagens de uma sessão."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return messages