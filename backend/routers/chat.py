from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.config import OPENROUTER_MODEL_DEFAULT
from backend.database import get_db
from backend.models import ChatMessage, ChatSession
from backend.routers.auth import get_current_user
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.openrouter import OpenRouterConfigError, generate_reply, stream_reply


router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    session_id: int | None = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
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

    # Se não veio session_id, usa a sessão mais recente ou cria uma
    if session_id is None:
        session = (
            db.query(ChatSession)
            .filter(ChatSession.user_id == current_user.id)
            .order_by(ChatSession.updated_at.desc())
            .first()
        )
        if not session:
            session = ChatSession(user_id=current_user.id, title="")
            db.add(session)
            db.flush()
    else:
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada.")

    # Gera título automático se ainda não tiver
    if not session.title.strip():
        title_prompt = (
            "Gere um título curto de no máximo 5 palavras para uma conversa "
            f"que começa com: \"{payload.message[:100]}\""
        )
        try:
            title_reply, _ = await generate_reply(
                user_message=title_prompt,
                history=[],
                model=payload.model,
            )
            session.title = title_reply.strip().strip('"').strip("'")[:100]
        except Exception:
            session.title = payload.message[:50]

    db.add(ChatMessage(session_id=session.id, role="user", content=payload.message, model=resolved_model))
    db.add(ChatMessage(session_id=session.id, role="assistant", content=reply, model=resolved_model))
    session.updated_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(tzinfo=None)
    db.commit()

    return ChatResponse(reply=reply, model=resolved_model)


@router.post("/api/chat/stream")
async def chat_stream(
    payload: ChatRequest,
    session_id: int | None = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
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
            # Garante sessão
            if session_id is None:
                session = (
                    db.query(ChatSession)
                    .filter(ChatSession.user_id == current_user.id)
                    .order_by(ChatSession.updated_at.desc())
                    .first()
                )
                if not session:
                    session = ChatSession(user_id=current_user.id, title="")
                    db.add(session)
                    db.flush()
            else:
                session = db.query(ChatSession).filter(
                    ChatSession.id == session_id,
                    ChatSession.user_id == current_user.id,
                ).first()
                if not session:
                    yield f"data: {json.dumps({'error': 'Sessão não encontrada.'}, ensure_ascii=True)}\n\n"
                    return

            # Gera título automático se ainda não tiver
            if not session.title.strip():
                title_prompt = (
                    "Gere um título curto de no máximo 5 palavras para uma conversa "
                    f"que começa com: \"{payload.message[:100]}\""
                )
                try:
                    title_reply, _ = await generate_reply(
                        user_message=title_prompt,
                        history=[],
                        model=payload.model,
                    )
                    session.title = title_reply.strip().strip('"').strip("'")[:100]
                except Exception:
                    session.title = payload.message[:50]

            db.add(
                ChatMessage(
                    session_id=session.id,
                    role="user",
                    content=payload.message,
                    model=resolved_model,
                )
            )
            db.add(
                ChatMessage(
                    session_id=session.id,
                    role="assistant",
                    content=full_reply,
                    model=resolved_model,
                )
            )
            session.updated_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).replace(tzinfo=None)
            db.commit()

        yield f"data: {json.dumps({'done': True}, ensure_ascii=True)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
