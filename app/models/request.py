from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="会话ID，用于多轮对话")
    user_id: str = Field(..., description="用户标识")
    question: str = Field(..., description="用户问题", min_length=1, max_length=1000)
