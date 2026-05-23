"""LangGraph checkpointer factory.

Prefers `AsyncPostgresSaver` so workflows survive process restarts. Falls back
to `MemorySaver` if the postgres checkpoint package isn't installed or the
setup fails — useful for local dev and test environments.
"""
from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _psycopg_url() -> str:
    """Convert our SQLAlchemy/asyncpg DATABASE_URL into a psycopg-compatible
    connection string."""
    return get_settings().database_url.replace("+asyncpg", "")


async def get_checkpointer():
    """Return the best available checkpointer instance."""
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from psycopg_pool import AsyncConnectionPool

        pool = AsyncConnectionPool(
            conninfo=_psycopg_url(),
            open=False,
            max_size=10,
            kwargs={"autocommit": True, "prepare_threshold": 0},
        )
        await pool.open()
        saver = AsyncPostgresSaver(pool)
        await saver.setup()
        logger.info("checkpointer.postgres.ready")
        return saver
    except ImportError as exc:
        logger.warning(
            "checkpointer.postgres.unavailable",
            reason="langgraph-checkpoint-postgres or psycopg not installed",
            error=str(exc),
        )
    except Exception as exc:
        logger.warning("checkpointer.postgres.setup_failed", error=str(exc))

    from langgraph.checkpoint.memory import MemorySaver

    logger.info("checkpointer.memory.fallback")
    return MemorySaver()
