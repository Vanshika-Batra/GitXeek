from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.session import engine
from app.processing.scheduler import PriorityScheduler
from app.integrations.cognee_client import cognee_client
settings = get_settings()

@asynccontextmanager
async def lifespan(_app: FastAPI):
    await cognee_client.initialize()
    await PriorityScheduler.get().start()
    yield
    await PriorityScheduler.get().stop()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    return app


app = create_app()
