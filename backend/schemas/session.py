from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SessionCreate(BaseModel):
    pass


class SessionRename(BaseModel):
    title: str


class SessionOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    model: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionListOut(BaseModel):
    sessions: list[SessionOut]