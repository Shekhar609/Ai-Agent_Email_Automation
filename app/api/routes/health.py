import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import get_settings

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "env": settings.app_env,
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/db", status_code=status.HTTP_200_OK)
async def health_db(db: AsyncSession = Depends(get_db)) -> dict:
    try:
        result = await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "reachable", "result": result.scalar()}
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"database unreachable: {exc.__class__.__name__}",
        ) from exc


@router.get("/health/ready")
async def health_ready(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """Readiness probe — checks every external dependency. 200 if all OK, 503 if any down.
    Suitable for k8s readiness probes."""
    checks: dict[str, str] = {"api": "ok"}
    overall_ok = True

    try:
        await db.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as exc:
        checks["db"] = f"error: {type(exc).__name__}"
        overall_ok = False

    try:
        from redis.asyncio import Redis

        r = Redis.from_url(get_settings().redis_url, decode_responses=True)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {type(exc).__name__}"
        overall_ok = False

    try:
        from app.vectorstore import chroma_client

        await asyncio.to_thread(chroma_client.get_client().heartbeat)
        checks["chroma"] = "ok"
    except Exception as exc:
        checks["chroma"] = f"error: {type(exc).__name__}"
        overall_ok = False

    return JSONResponse(
        {"status": "ready" if overall_ok else "degraded", "checks": checks},
        status_code=status.HTTP_200_OK if overall_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
    )
