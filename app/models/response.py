from pydantic import BaseModel
from typing import Optional
from enum import Enum


class ResponseType(str, Enum):
    QUERY = "query"
    CHAT = "chat"
    ERROR = "error"


class ChatResponse(BaseModel):
    session_id: str
    type: ResponseType
    content: str
    sql: Optional[str] = None


class HistoryMessage(BaseModel):
    role: str
    content: str
    sql: Optional[str] = None
    created_at: str


class HistoryResponse(BaseModel):
    session_id: str
    messages: list[HistoryMessage]
