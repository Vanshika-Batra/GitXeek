from datetime import datetime
from pathlib import Path

from app.processing.progress import init_progress
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.repository import GitHubRepoResponse, RepositoryCreateRequest, RepositoryResponse
from app.core.config import get_settings
from app.core.exceptions import bad_request, conflict
from app.integrations.git import clone_repository
from app.integrations.github_client import GitHubClient
from app.models.repository import Repository, Status, Visibility, ProcessingStatus
from app.processing.scheduler import PriorityScheduler
from app.models.user import User


async def list_github_repositories(user: User) -> list[GitHubRepoResponse]:
    if not user.github_token:
        raise bad_request("GitHub account is not connected")

    client = GitHubClient(access_token=user.github_token)
    github_user = await client.get_authenticated_user()
    user_login = github_user["login"]
    repos = await client.list_repositories()
    return [
        GitHubRepoResponse(
            github_repo_id=str(repo["id"]),
            name=repo["name"],
            full_name=repo["full_name"],
            url=repo["html_url"],
            clone_url=repo["clone_url"],
            default_branch=repo.get("default_branch"),
            visibility=Visibility.PRIVATE if repo["private"] else Visibility.PUBLIC,
            is_owner=repo.get("owner", {}).get("login") == user_login,
        )
        for repo in repos
    ]


async def list_user_repositories(db: AsyncSession, user: User) -> list[RepositoryResponse]:
    result = await db.execute(
        select(Repository).where(Repository.user_id == user.id).order_by(Repository.updated_at.desc())
    )
    return [_to_response(repo) for repo in result.scalars().all()]


async def activate_repository(
    db: AsyncSession, user: User, request: RepositoryCreateRequest
) -> RepositoryResponse:
    if not user.github_token:
        raise bad_request("GitHub account is not connected")

    client = GitHubClient(access_token=user.github_token)
    owner, repo_name = request.full_name.split("/", 1)
    github_repo = await client.get_repository(owner, repo_name)

    github_repo_id = str(github_repo["id"])
    existing = await _get_by_github_repo_id(db, user.id, github_repo_id)
    if existing:
        raise conflict("Repository already added")

    await db.execute(
        update(Repository)
        .where(Repository.user_id == user.id, Repository.status == Status.ACTIVE)
        .values(status=Status.INACTIVE)
    )

    settings = get_settings()
    clone_path = Path(settings.REPOS_CLONE_DIR) / str(user.id) / github_repo["name"]
    default_branch = github_repo.get("default_branch")
    clone_url = _authenticated_clone_url(github_repo["clone_url"], user.github_token)

    try:
        await clone_repository(clone_url, clone_path, default_branch)
    except RuntimeError as exc:
        raise bad_request(f"Failed to clone repository: {exc}") from exc

    repo_owner_login = github_repo.get("owner", {}).get("login", "")
    repository = Repository(
        name=github_repo["name"],
        full_name=github_repo["full_name"],
        github_repo_id=github_repo_id,
        user_id=user.id,
        is_owner=repo_owner_login == owner,
        url=github_repo["html_url"],
        clone_path=str(clone_path),
        status=Status.ACTIVE,
        visibility=Visibility.PRIVATE if github_repo["private"] else Visibility.PUBLIC,
        default_branch=default_branch,
        current_branch=default_branch,
        last_synced_at=datetime.now(),
        processing_status=ProcessingStatus.PENDING,
        processing_progress = init_progress()
    )
    db.add(repository)
    await db.commit()
    await db.refresh(repository)

    await PriorityScheduler.get().enqueue_repository(repository.id)

    return _to_response(repository)


async def _get_by_github_repo_id(
    db: AsyncSession, user_id: int, github_repo_id: str
) -> Repository | None:
    result = await db.execute(
        select(Repository).where(
            Repository.user_id == user_id,
            Repository.github_repo_id == github_repo_id,
        )
    )
    return result.scalar_one_or_none()


def _to_response(repo: Repository) -> RepositoryResponse:
    return RepositoryResponse(
        id=repo.id,
        name=repo.name,
        full_name=repo.full_name,
        github_repo_id=repo.github_repo_id,
        url=repo.url,
        status=repo.status,
        visibility=repo.visibility,
        default_branch=repo.default_branch,
        current_branch=repo.current_branch,
        is_owner=repo.is_owner,
        last_synced_at=repo.last_synced_at,
        created_at=repo.created_at,
        understanding_percentage=repo.understanding_percentage or 0,
        processing_status=repo.processing_status or ProcessingStatus.PENDING,
    )


def _authenticated_clone_url(clone_url: str, token: str) -> str:
    if clone_url.startswith("https://"):
        return clone_url.replace("https://", f"https://x-access-token:{token}@", 1)
    return clone_url
