from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.schemas.chat import ChatQueryRequest, ChatQueryResponse, ConversationResponse, MessageResponse
from app.core.exceptions import bad_request, not_found
from app.integrations.cognee_client import cognee_client, search_stored_artifacts
from app.models.artifact import ArtifactStatus, RepositoryArtifact
from app.models.chat import Conversation, Message, Role
from app.models.repository import Repository, Status
from app.models.user import User
from app.processing.scheduler import PriorityScheduler


async def query_repository(
    db: AsyncSession,
    user: User,
    repository_id: int,
    request: ChatQueryRequest,
) -> ChatQueryResponse:
    repo = await _get_user_repo(db, user, repository_id)
    scheduler = PriorityScheduler.get()
    prioritized = await scheduler.boost_for_query(repository_id, request.message)

    conversation = await _get_or_create_conversation(db, user, repo)
    db.add(Message(conversation_id=conversation.id, user_id=user.id, content=request.message, role=Role.USER))
    await db.commit()

    cognee = cognee_client
    context = await cognee.recall_context(repository_id, request.message)
    print("context from cognee....: ", context)
    if not context:
        result = await db.execute(
            select(RepositoryArtifact).where(
                RepositoryArtifact.repository_id == repository_id,
                RepositoryArtifact.status == ArtifactStatus.INDEXED,
            )
        )
        context = await search_stored_artifacts(list(result.scalars().all()), request.message)
        print("stored context....: ", context)
    understanding = repo.understanding_percentage or 0
    is_partial = understanding < 35 or len(context) < 2
    print("understanding: ", understanding)
    print("len(context: ): ", len(context))
    print("is partial: ", is_partial)

    print("cognee.enabled: ;;; ", cognee.enabled)
    # if is_partial:
    #     answer = _partial_answer(prioritized)
    # elif cognee.enabled:
    #     answer = await cognee.answer(
    #         repository_id,
    #         user.id,
    #         request.message,
    #         repo_name=repo.full_name,
    #         understanding_pct=understanding,
    #     )
    #     if not answer:
    #         answer = _fallback_answer(request.message, context, repo.full_name, understanding)
    # else:
    #     answer = _fallback_answer(request.message, context, repo.full_name, understanding)

    if cognee.enabled and context:
        answer = await cognee.answer(
            repository_id,
            user.id,
            request.message,
            repo_name=repo.full_name,
            understanding_pct=understanding,
        )

        if not answer:
            answer = _fallback_answer(
                request.message,
                context,
                repo.full_name,
                understanding,
            )

    else:
        answer = _partial_answer(prioritized)
        
    db.add(Message(conversation_id=conversation.id, user_id=user.id, content=answer, role=Role.SYSTEM))
    await db.commit()

    return ChatQueryResponse(
        answer=answer,
        conversation_id=conversation.id,
        understanding_percentage=understanding,
        processing_status=repo.processing_status.value,
        is_partial=is_partial,
        prioritized=prioritized[:5],
    )


async def get_conversation(
    db: AsyncSession, user: User, repository_id: int
) -> ConversationResponse:
    repo = await _get_user_repo(db, user, repository_id)
    conversation = await _get_or_create_conversation(db, user, repo)
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation.id)
    )
    loaded = result.scalar_one()
    return ConversationResponse(
        id=loaded.id,
        repository_id=loaded.repository_id,
        messages=[MessageResponse.model_validate(m) for m in loaded.messages],
    )


async def _get_user_repo(db: AsyncSession, user: User, repository_id: int) -> Repository:
    repo = await db.get(Repository, repository_id)
    if not repo or repo.user_id != user.id:
        raise not_found("Repository")
    if repo.status != Status.ACTIVE:
        raise bad_request("Repository is not active")
    return repo


async def _get_or_create_conversation(db: AsyncSession, user: User, repo: Repository) -> Conversation:
    result = await db.execute(
        select(Conversation).where(
            Conversation.repository_id == repo.id,
            Conversation.user_id == user.id,
        )
    )
    conversation = result.scalar_one_or_none()
    if conversation:
        return conversation
    conversation = Conversation(repository_id=repo.id, user_id=user.id)
    db.add(conversation)
    await db.flush()
    return conversation


def _partial_answer(prioritized: list[str]) -> str:
    labels = prioritized[:3] or ["README", "PRs", "Commits"]
    checklist = "\n".join(f"✓ {label}" for label in labels)
    return (
        "I found relevant artifacts, but they're still being analyzed.\n\n"
        f"I'm prioritizing:\n{checklist}\n\n"
        "Try again in a few seconds — your question jumped the queue."
    )


def _fallback_answer(query: str, context: list[str], repo_name: str, understanding: int) -> str:
    snippet = context[0][:400] if context else "Still indexing this repo."
    return (
        f"**{repo_name}** ({understanding}% understood)\n\n"
        f"On *{query}* — here's what I've got so far:\n{snippet}"
    )
