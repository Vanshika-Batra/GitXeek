from fastapi import APIRouter

from app.api.v1.endpoints import auth, github, health, repositories, chat

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(github.router, tags=["github"])
api_router.include_router(repositories.router, tags=["repositories"])
api_router.include_router(chat.router, tags=["chat"])
