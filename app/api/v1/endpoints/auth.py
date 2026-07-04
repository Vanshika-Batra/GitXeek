from fastapi import APIRouter

from app.api.deps import DbSession
from app.api.v1.schemas.auth import LoginRequest, LoginResponse
from app.api.v1.services import auth_service

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=LoginResponse)
async def register(request: LoginRequest, db: DbSession) -> LoginResponse:
    return await auth_service.register(db, request)


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: DbSession) -> LoginResponse:
    return await auth_service.login(db, request)
