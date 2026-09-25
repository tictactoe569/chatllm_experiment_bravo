from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.config import OPENROUTER_MODEL_DEFAULT
from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models import ChatMessage, Session, User
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.openrouter import OpenRouterConfigError, generate_reply, stream_reply


router = APIRouter()


def _resolve_session_key(
    payload_session_key: str | None,
    current_user: User,
    db: Session,
) -> str:
    """Return the session_key from payload or create a new Session."""
    if payload_session_key:
        # Verify session exists and belongs to user
        session = (
            db.query(Session)
            .filter(
                Session.session_key == payload_session_key,
                Session.user_id == current_user.id,
            )
            .first()
        )
        if session:
            return payload_session_key

    # Create a new session
    new_key = str(uuid.uuid4())
    db.add(Session(user_id=current_user.id, session_key=new_key))
    db.commit()
    return new_key


def _auto_title(reply: str) -> str | None:
    """Extract the first 5 words of the reply as a title."""
    words = reply.strip().split()
    if not words:
        return None
    title = " ".join(words[:5])
    # Truncate if too long
    if len(title) > 100:
        title = title[:100]
    return title


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    session_key = _resolve_session_key(payload.session_key, current_user, db)

    try:
        reply, model_name = await generate_reply(
            user_message=payload.message,
            history=[item.model_dump() for item in payload.history],
            model=payload.model,
        )
    except OpenRouterConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    resolved_model = payload.model or model_name or OPENROUTER_MODEL_DEFAULT

    db.add(
        ChatMessage(
            user_id=current_user.id,
            session_key=session_key,
            role="user",
            content=payload.message,
            model=resolved_model,
        )
    )
    db.add(
        ChatMessage(
            user_id=current_user.id,
            session_key=session_key,
            role="assistant",
            content=reply,
            model=resolved_model,
        )
    )

    # Auto-title if session has no title yet
    if reply.strip():
        session = (
            db.query(Session)
            .filter(Session.session_key == session_key)
            .first()
        )
        if session and not session.title:
            title = _auto_title(reply)
            if title:
                session.title = title
                session.updated_at = session.created_at  # keep original order

    db.commit()

    return ChatResponse(reply=reply, model=resolved_model)


@router.post("/api/chat/stream")
async def chat_stream(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    session_key = _resolve_session_key(payload.session_key, current_user, db)
    resolved_model = payload.model or OPENROUTER_MODEL_DEFAULT

    async def event_generator():
        full_reply = ""
        try:
            async for delta in stream_reply(
                user_message=payload.message,
                history=[item.model_dump() for item in payload.history],
                model=payload.model,
            ):
                full_reply += delta
                yield f"data: {json.dumps({'delta': delta}, ensure_ascii=True)}\n\n"
        except OpenRouterConfigError as exc:
            yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=True)}\n\n"
            return
        except RuntimeError as exc:
            yield f"data: {json.dumps({'error': str(exc)}, ensure_ascii=True)}\n\n"
            return

        if full_reply.strip():
            db.add(
                ChatMessage(
                    user_id=current_user.id,
                    session_key=session_key,
                    role="user",
                    content=payload.message,
                    model=resolved_model,
                )
            )
            db.add(
                ChatMessage(
                    user_id=current_user.id,
                    session_key=session_key,
                    role="assistant",
                    content=full_reply,
                    model=resolved_model,
                )
            )

            # Auto-title if session has no title yet
            session = (
                db.query(Session)
                .filter(Session.session_key == session_key)
                .first()
            )
            if session and not session.title:
                title = _auto_title(full_reply)
                if title:
                    session.title = title
                    session.updated_at = session.created_at

            db.commit()

        yield f"data: {json.dumps({'done': True, 'session_key': session_key}, ensure_ascii=True)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
