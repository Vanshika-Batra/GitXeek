from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.auth import LoginRequest, LoginResponse
from app.api.v1.services import user_service
from app.core.security import create_access_token, create_refresh_token


async def register(db: AsyncSession, request: LoginRequest) -> LoginResponse:
    user = await user_service.create_user(db, request.email, request.password)
    return _build_login_response(user.id, user.email)


async def login(db: AsyncSession, request: LoginRequest) -> LoginResponse:
    user = await user_service.authenticate_user(db, request.email, request.password)
    return _build_login_response(user.id, user.email)


def _build_login_response(user_id: int, email: str) -> LoginResponse:
    return LoginResponse(
        user_id=user_id,
        email=email,
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )
