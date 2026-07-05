from datetime import datetime

from pydantic import BaseModel, Field

from app.models.chat import Role


class ChatQueryRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class ChatQueryResponse(BaseModel):
    answer: str
    conversation_id: int
    understanding_percentage: int
    processing_status: str
    is_partial: bool = False
    prioritized: list[str] = Field(default_factory=list)


class MessageResponse(BaseModel):
    id: int
    content: str
    role: Role
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: int
    repository_id: int
    messages: list[MessageResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}
