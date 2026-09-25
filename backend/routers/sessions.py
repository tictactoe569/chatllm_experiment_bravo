from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models import ChatMessage, Session, User
from backend.schemas.session import (
    ChatMessageResponse,
    SessionCreateResponse,
    SessionResponse,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionResponse])
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[SessionResponse]:
    """List all sessions for the authenticated user, most recently updated first."""
    sessions = (
        db.query(Session)
        .filter(Session.user_id == current_user.id)
        .order_by(Session.updated_at.desc())
        .all()
    )
    return sessions


@router.post("", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SessionCreateResponse:
    """Create a new session with a unique UUID session_key."""
    session_key = str(uuid.uuid4())
    session = Session(
        user_id=current_user.id,
        session_key=session_key,
    )
    db.add(session)
    db.commit()
    return SessionCreateResponse(session_key=session_key)


@router.delete("/{session_key}")
def delete_session(
    session_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a session and all its messages. Verifies ownership."""
    session = (
        db.query(Session)
        .filter(
            Session.session_key == session_key,
            Session.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão não encontrada",
        )

    db.query(ChatMessage).filter(
        ChatMessage.session_key == session_key,
        ChatMessage.user_id == current_user.id,
    ).delete(synchronize_session=False)

    db.delete(session)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{session_key}/messages", response_model=list[ChatMessageResponse])
def get_session_messages(
    session_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ChatMessageResponse]:
    """Get all messages for a session, ordered by creation time."""
    # Verify session exists and belongs to user
    session = (
        db.query(Session)
        .filter(
            Session.session_key == session_key,
            Session.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão não encontrada",
        )

    messages = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_key == session_key,
            ChatMessage.user_id == current_user.id,
        )
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return messages