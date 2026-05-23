from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import (
    activity,
    auth,
    drafts,
    emails,
    followups,
    health,
    stats,
    users,
    workflow,
)
from app.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware
from app.core.rate_limit import limiter

settings = get_settings()
configure_logging(level=settings.log_level, fmt=settings.log_format)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "app.startup",
        env=settings.app_env,
        name=settings.app_name,
        rate_limit_enabled=settings.rate_limit_enabled,
    )
    yield
    logger.info("app.shutdown")


app = FastAPI(
    title="Email Automation Agent",
    version="0.1.0",
    debug=settings.app_debug,
    lifespan=lifespan,
)

# Rate limiter (slowapi)
app.state.limiter = limiter


async def _rate_limit_handler(request, exc):  # type: ignore[no-untyped-def]
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=429,
        content={"detail": f"rate limit exceeded: {exc.detail}"},
    )


app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

# Request context (request_id, structured request logs)
app.add_middleware(RequestContextMiddleware)

# CORS — in production, restrict to configured origins.
if settings.is_production:
    if not settings.allowed_origins:
        logger.warning("cors.no_origins_configured_in_production")
    cors_origins = settings.allowed_origins
else:
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(emails.router, prefix="/api/emails", tags=["emails"])
app.include_router(workflow.router, prefix="/api/workflow", tags=["workflow"])
app.include_router(drafts.router, prefix="/api/drafts", tags=["drafts"])
app.include_router(followups.router, prefix="/api/followups", tags=["followups"])
app.include_router(activity.router, prefix="/api/activity-logs", tags=["activity"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])


@app.get("/")
async def root() -> dict:
    return {"name": settings.app_name, "version": "0.1.0", "status": "ok"}
