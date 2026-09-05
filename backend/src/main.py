"""FastAPI application factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.auth import router as auth_router
from src.api.health import router as health_router
from src.api.projects import router as project_router
from src.config.logging import configure_logging
from src.config.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build a configured API application suitable for production and tests."""

    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
        configure_logging(app_settings.log_level)
        yield

    app = FastAPI(
        title="AI Coding Server",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in app_settings.cors_origins],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(auth_router)
    app.include_router(health_router)
    app.include_router(project_router)
    return app


app = create_app()
