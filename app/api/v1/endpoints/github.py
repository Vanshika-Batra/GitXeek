from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from app.api.deps import CurrentUser, DbSession
from app.api.v1.schemas.github import GitHubConnectResponse
from app.api.v1.schemas.user import UserResponse
from app.api.v1.services import github_service
from app.core.config import get_settings

router = APIRouter(prefix="/auth/github")


@router.get("/connect", response_model=GitHubConnectResponse)
async def connect_github(current_user: CurrentUser) -> GitHubConnectResponse:
    authorize_url = github_service.get_connect_url(current_user)
    return GitHubConnectResponse(authorize_url=authorize_url)


@router.get("/callback")
async def github_callback(
    db: DbSession,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    settings = get_settings()
    if error or not code or not state:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}?github=error")
    try:
        await github_service.handle_oauth_callback(db, code, state)
        return RedirectResponse(url=f"{settings.FRONTEND_URL}?github=connected")
    except Exception:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}?github=error")


@router.delete("/disconnect", response_model=UserResponse)
async def disconnect_github(current_user: CurrentUser, db: DbSession) -> UserResponse:
    user = await github_service.disconnect(db, current_user)
    return UserResponse.model_validate(user)
