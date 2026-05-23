from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.rate_limit import limiter
from app.db.models import Email, User
from app.schemas.email import EmailOut, SyncResponse
from app.services.email_sync import sync_inbox

router = APIRouter()


@router.post("/sync", response_model=SyncResponse)
@limiter.limit("5/minute")
async def sync(
    request: Request,
    max_results: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SyncResponse:
    try:
        result = await sync_inbox(db, user, max_results=max_results)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return SyncResponse(**result)


@router.get("", response_model=list[EmailOut])
async def list_emails(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[EmailOut]:
    rows = await db.scalars(
        select(Email)
        .where(Email.user_id == user.id)
        .order_by(Email.received_at.desc().nullslast())
        .limit(limit)
    )
    return [EmailOut.model_validate(e) for e in rows.all()]


@router.get("/{email_id}", response_model=EmailOut)
async def get_email(
    email_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EmailOut:
    email = await db.get(Email, email_id)
    if email is None or email.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "email not found")
    return EmailOut.model_validate(email)
