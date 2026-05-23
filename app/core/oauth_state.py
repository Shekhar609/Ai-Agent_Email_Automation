"""OAuth CSRF state store.

Uses Redis with TTL when reachable; falls back to an in-process dict so that
unit tests and local dev work without a running Redis. Production deployments
should always have Redis available — the warning log line on fallback is the
operator's signal that something is misconfigured.
"""
import secrets
import time
from typing import Any

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

STATE_TTL_SECONDS = 600  # 10 minutes
_KEY_PREFIX = "oauth_state:"

_redis: Any = None
_redis_unavailable = False
_memory_store: dict[str, float] = {}


async def _get_redis():
    global _redis, _redis_unavailable
    if _redis_unavailable:
        return None
    if _redis is None:
        try:
            from redis.asyncio import Redis

            client = Redis.from_url(get_settings().redis_url, decode_responses=True)
            await client.ping()
            _redis = client
        except Exception as exc:
            logger.warning(
                "oauth_state.redis_unavailable_fallback_memory", error=str(exc)
            )
            _redis_unavailable = True
            return None
    return _redis


def _gc_memory(now: float) -> None:
    expired = [k for k, exp in _memory_store.items() if exp < now]
    for k in expired:
        _memory_store.pop(k, None)


async def generate_state() -> str:
    state = secrets.token_urlsafe(32)
    r = await _get_redis()
    if r is not None:
        await r.set(f"{_KEY_PREFIX}{state}", "1", ex=STATE_TTL_SECONDS)
    else:
        now = time.time()
        _gc_memory(now)
        _memory_store[state] = now + STATE_TTL_SECONDS
    return state


async def consume_state(state: str) -> bool:
    """Atomically consume a state token. Returns True if it existed."""
    r = await _get_redis()
    if r is not None:
        return (await r.getdel(f"{_KEY_PREFIX}{state}")) is not None

    now = time.time()
    _gc_memory(now)
    exp = _memory_store.pop(state, None)
    return exp is not None and exp >= now
