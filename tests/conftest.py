import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("APP_SECRET_KEY", "test-secret-key-please-change-1234")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://emailagent:emailagent@localhost:5432/emailagent_test",
)
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")


@pytest.fixture
async def client():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
