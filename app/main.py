"""FastAPI app factory, lifespan, middleware."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import async_session_factory, engine
from app.exceptions import LearningServiceUnavailableError
from app.middleware.logging import logging_middleware
from app.routers import admin, auth, children, learn, progress, sessions

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Create DB engine and Redis client; dispose on shutdown."""
    settings = get_settings()
    logger.info("Starting up", redis_url=settings.redis_url[:50] + "...")
    try:
        # Redis is created lazily in services that need it
        yield
    finally:
        await engine.dispose()
        logger.info("Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Adaptive Child Learning API",
        description="RAG-powered adaptive learning for neurodiverse and disabled children",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    @app.middleware("http")
    async def db_session_middleware(request: Request, call_next):
        async with async_session_factory() as session:
            request.state.db = session
            try:
                response = await call_next(request)
                await session.commit()
                return response
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    # Logging runs after DB so request is fully set up
    app.middleware("http")(logging_middleware)

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(children.router, prefix="/api/children", tags=["children"])
    app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
    app.include_router(learn.router, prefix="/api/learn", tags=["learn"])
    app.include_router(progress.router, prefix="/api/progress", tags=["progress"])
    app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

    @app.exception_handler(LearningServiceUnavailableError)
    async def learning_unavailable_handler(request: Request, exc: LearningServiceUnavailableError):
        return JSONResponse(
            status_code=503,
            content={"detail": exc.args[0] if exc.args else "Learning service temporarily unavailable. Please try again later."},
        )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/metrics")
    async def metrics():
        from fastapi.responses import Response
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
