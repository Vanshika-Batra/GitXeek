from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.services import user_service
from app.core.exceptions import bad_request
from app.core.security import create_oauth_state, verify_oauth_state
from app.integrations.github_client import GitHubClient
from app.models.user import User


def get_connect_url(user: User) -> str:
    state = create_oauth_state(user.id)
    return GitHubClient().get_authorize_url(state)


async def handle_oauth_callback(db: AsyncSession, code: str, state: str) -> User:
    try:
        user_id = verify_oauth_state(state)
    except Exception as exc:
        raise bad_request("Invalid or expired OAuth state") from exc

    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        raise bad_request("User not found for OAuth state")

    client = GitHubClient()
    access_token = await client.exchange_code_for_token(code)

    github_client = GitHubClient(access_token=access_token)
    github_user = await github_client.get_authenticated_user()
    github_id = str(github_user["id"])

    return await user_service.update_github_credentials(db, user, github_id, access_token)


async def disconnect(db: AsyncSession, user: User) -> User:
    if not user.github_connected:
        raise bad_request("GitHub account is not connected")
    return await user_service.disconnect_github(db, user)
