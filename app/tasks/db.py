"""Task-side async DB plumbing.

Celery workers run each task in a fresh asyncio event loop via `asyncio.run`.
asyncpg connections bind to the loop they're created in, so we use NullPool
here: every session opens (and closes) a fresh connection in the current loop.
"""
import asyncio
from collections.abc import Awaitable
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings

_settings = get_settings()

task_engine = create_async_engine(
    _settings.database_url,
    poolclass=NullPool,
    echo=False,
)

TaskSessionLocal = async_sessionmaker(
    bind=task_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

T = TypeVar("T")


def run_async(coro: Awaitable[T]) -> T:
    """Run an async coroutine inside a Celery task body."""
    return asyncio.run(coro)
