from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.api.v1.schemas.chat import ChatQueryRequest, ChatQueryResponse, ConversationResponse
from app.api.v1.services import chat_service

router = APIRouter()


@router.get("/repositories/{repository_id}/conversation", response_model=ConversationResponse)
async def get_conversation(
    repository_id: int, current_user: CurrentUser, db: DbSession
) -> ConversationResponse:
    return await chat_service.get_conversation(db, current_user, repository_id)


@router.post("/repositories/{repository_id}/query", response_model=ChatQueryResponse)
async def query_repository(
    repository_id: int,
    request: ChatQueryRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> ChatQueryResponse:
    return await chat_service.query_repository(db, current_user, repository_id, request)
