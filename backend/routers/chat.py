from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.config import OPENROUTER_MODEL_DEFAULT
from backend.database import get_db
from backend.models import ChatMessage, ChatSession
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.auth import get_current_user
from backend.services.openrouter import OpenRouterConfigError, generate_reply, stream_reply


router = APIRouter()


def _generate_title(user_message: str) -> str:
    """Gera título automático a partir da primeira mensagem do usuário."""
    title = user_message.strip()[:60]
    if len(user_message) > 60:
        title += "..."
    return title


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ChatResponse:
    session = _resolve_session(payload.session_id, current_user.id, db)

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

    _persist_messages(db, session.id, payload.message, reply, resolved_model)
    _auto_title(db, session, payload.message)

    return ChatResponse(reply=reply, model=resolved_model)


@router.post("/api/chat/stream")
async def chat_stream(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> StreamingResponse:
    session = _resolve_session(payload.session_id, current_user.id, db)
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
            _persist_messages(db, session.id, payload.message, full_reply, resolved_model)
            _auto_title(db, session, payload.message)

        yield f"data: {json.dumps({'done': True}, ensure_ascii=True)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


def _resolve_session(session_id: int | None, user_id: int, db: Session) -> ChatSession:
    """Resolve a sessão: usa a existente ou cria uma nova."""
    if session_id:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        if session.user_id != user_id:
            raise HTTPException(status_code=403, detail="Acesso negado a esta sessão")
        return session

    session = ChatSession(user_id=user_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _persist_messages(db: Session, session_id: int, user_msg: str, reply: str, model: str) -> None:
    db.add(ChatMessage(session_id=session_id, role="user", content=user_msg, model=model))
    db.add(ChatMessage(session_id=session_id, role="assistant", content=reply, model=model))
    db.commit()


def _auto_title(db: Session, session: ChatSession, user_message: str) -> None:
    """Define título automático se a sessão ainda não tiver um."""
    if session.title:
        return
    session.title = _generate_title(user_message)
    db.commit()
