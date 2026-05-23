"""Rate limiter wiring.

Uses slowapi. Storage URI:
- In production: Redis (so multiple uvicorn workers share the counter).
- Elsewhere: memory:// (single-process; sufficient for dev and tests).

Disable entirely with `RATE_LIMIT_ENABLED=false` — the decorators become no-ops.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings

_settings = get_settings()

_storage_uri = (
    _settings.redis_url if _settings.is_production else "memory://"
)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_storage_uri,
    enabled=_settings.rate_limit_enabled,
    default_limits=[],
    headers_enabled=True,
)
