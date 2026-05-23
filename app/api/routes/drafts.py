from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.workflow import resume_workflow
from app.api.deps import get_current_user, get_db
from app.db.models import Draft, User
from app.schemas.draft import (
    DraftActionResponse,
    DraftOut,
    DraftUpdate,
    RejectRequest,
)

router = APIRouter()


@router.get("", response_model=list[DraftOut])
async def list_drafts(
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DraftOut]:
    stmt = (
        select(Draft)
        .where(Draft.user_id == user.id)
        .order_by(Draft.created_at.desc())
        .limit(limit)
    )
    if status_filter:
        stmt = stmt.where(Draft.status == status_filter)
    rows = await db.scalars(stmt)
    return [DraftOut.model_validate(d) for d in rows.all()]


@router.get("/{draft_id}", response_model=DraftOut)
async def get_draft(
    draft_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DraftOut:
    draft = await db.get(Draft, draft_id)
    if draft is None or draft.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "draft not found")
    return DraftOut.model_validate(draft)


@router.put("/{draft_id}", response_model=DraftOut)
async def update_draft(
    draft_id: UUID,
    body: DraftUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DraftOut:
    draft = await db.get(Draft, draft_id)
    if draft is None or draft.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "draft not found")
    if draft.status != "pending_approval":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"cannot edit draft in status '{draft.status}'",
        )
    if body.subject is not None:
        draft.subject = body.subject
    if body.body is not None:
        draft.body = body.body
    if body.tone is not None:
        draft.tone = body.tone
    await db.commit()
    await db.refresh(draft)
    return DraftOut.model_validate(draft)


@router.post("/{draft_id}/approve", response_model=DraftActionResponse)
async def approve_draft(
    draft_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DraftActionResponse:
    draft = await db.get(Draft, draft_id)
    if draft is None or draft.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "draft not found")
    if draft.status != "pending_approval":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"cannot approve draft in status '{draft.status}'",
        )

    draft.approved = True
    draft.status = "approved"
    email_id = str(draft.email_id)
    await db.commit()

    result = await resume_workflow(email_id, approved=True)
    return DraftActionResponse(draft_id=str(draft.id), **result)


@router.post("/{draft_id}/reject", response_model=DraftActionResponse)
async def reject_draft(
    draft_id: UUID,
    body: RejectRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DraftActionResponse:
    draft = await db.get(Draft, draft_id)
    if draft is None or draft.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "draft not found")
    if draft.status != "pending_approval":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"cannot reject draft in status '{draft.status}'",
        )

    draft.status = "rejected"
    email_id = str(draft.email_id)
    await db.commit()

    result = await resume_workflow(email_id, approved=False, reason=body.reason)
    return DraftActionResponse(draft_id=str(draft.id), **result)
