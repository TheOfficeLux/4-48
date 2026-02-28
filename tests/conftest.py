"""Pytest fixtures: test_app, db, mock_google_ai."""

import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import create_app
from app.models import Base

# Use in-memory SQLite for speed (optional: use postgres in CI)
DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_engine():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    async with factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def test_app():
    return create_app()


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


@pytest.fixture
async def async_client(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_google_embed():
    with patch("app.services.embeddings.EmbeddingService.embed", new_callable=AsyncMock) as m:
        m.return_value = [0.1] * 768
        yield m


@pytest.fixture
def mock_google_chat():
    with patch("app.services.rag.RAGPipeline._call_llm", new_callable=AsyncMock) as m:
        m.return_value = "This is a sample response."
        yield m
