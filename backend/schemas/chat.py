from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatMessageIn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    model: str | None = None
    history: list[ChatMessageIn] = Field(default_factory=list)
    session_id: int | None = None


class ChatResponse(BaseModel):
    reply: str
    model: str


class SessionCreate(BaseModel):
    pass


class SessionOut(BaseModel):
    id: int
    title: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
