import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Per-request: generate/honor request_id, bind to structlog contextvars,
    log start + end, surface request_id back to the client in X-Request-ID."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        start = time.perf_counter()

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )
        log = get_logger("http")
        log.info("http.request.start")

        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            log.exception(
                "http.request.error",
                elapsed_ms=round(elapsed_ms, 2),
                error=str(exc),
            )
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        log.info(
            "http.request.end",
            status_code=response.status_code,
            elapsed_ms=round(elapsed_ms, 2),
        )
        return response
