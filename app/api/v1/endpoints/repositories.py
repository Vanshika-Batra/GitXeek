from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.api.v1.schemas.repository import (
    GitHubRepoResponse,
    RepositoryCreateRequest,
    RepositoryResponse,
)
from app.api.v1.services import repository_service

router = APIRouter(prefix="/repositories")


@router.get("/github", response_model=list[GitHubRepoResponse])
async def list_github_repos(current_user: CurrentUser) -> list[GitHubRepoResponse]:
    return await repository_service.list_github_repositories(current_user)


@router.get("", response_model=list[RepositoryResponse])
async def list_repositories(current_user: CurrentUser, db: DbSession) -> list[RepositoryResponse]:
    return await repository_service.list_user_repositories(db, current_user)


@router.post("", response_model=RepositoryResponse, status_code=201)
async def activate_repository(
    request: RepositoryCreateRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> RepositoryResponse:
    return await repository_service.activate_repository(db, current_user, request)
