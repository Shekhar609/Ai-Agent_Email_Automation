from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models import Email, FollowUp, User
from app.schemas.followup import FollowUpCancelResponse, FollowUpCreate, FollowUpOut

router = APIRouter()


@router.get("", response_model=list[FollowUpOut])
async def list_followups(
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FollowUpOut]:
    stmt = (
        select(FollowUp)
        .where(FollowUp.user_id == user.id)
        .order_by(FollowUp.scheduled_for.asc())
        .limit(limit)
    )
    if status_filter:
        stmt = stmt.where(FollowUp.status == status_filter)
    rows = await db.scalars(stmt)
    return [FollowUpOut.model_validate(f) for f in rows.all()]


@router.post("", response_model=FollowUpOut, status_code=status.HTTP_201_CREATED)
async def create_followup(
    body: FollowUpCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FollowUpOut:
    email = await db.get(Email, body.email_id)
    if email is None or email.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "email not found")

    f = FollowUp(
        user_id=user.id,
        email_id=email.id,
        thread_id=email.thread_id,
        scheduled_for=body.scheduled_for,
        reason=body.reason,
        status="pending",
    )
    db.add(f)
    await db.commit()
    await db.refresh(f)
    return FollowUpOut.model_validate(f)


@router.delete("/{followup_id}", response_model=FollowUpCancelResponse)
async def cancel_followup(
    followup_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FollowUpCancelResponse:
    f = await db.get(FollowUp, followup_id)
    if f is None or f.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "follow-up not found")
    if f.status != "pending":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"cannot cancel follow-up in status '{f.status}'",
        )
    f.status = "cancelled"
    await db.commit()
    return FollowUpCancelResponse(id=f.id, status=f.status)
