from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models import Draft, Email, FollowUp, User
from app.schemas.stats import StatsSummary

router = APIRouter()


@router.get("/summary", response_model=StatsSummary)
async def summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StatsSummary:
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    emails_last_7d = (
        await db.scalar(
            select(func.count(Email.id)).where(
                Email.user_id == user.id, Email.received_at >= week_ago
            )
        )
    ) or 0

    emails_total = (
        await db.scalar(select(func.count(Email.id)).where(Email.user_id == user.id))
    ) or 0

    drafts_pending = (
        await db.scalar(
            select(func.count(Draft.id)).where(
                Draft.user_id == user.id, Draft.status == "pending_approval"
            )
        )
    ) or 0

    drafts_sent_last_7d = (
        await db.scalar(
            select(func.count(Draft.id)).where(
                Draft.user_id == user.id,
                Draft.sent.is_(True),
                Draft.updated_at >= week_ago,
            )
        )
    ) or 0

    followups_scheduled = (
        await db.scalar(
            select(func.count(FollowUp.id)).where(
                FollowUp.user_id == user.id, FollowUp.status == "pending"
            )
        )
    ) or 0

    cat_rows = (
        await db.execute(
            select(Email.category, func.count(Email.id))
            .where(Email.user_id == user.id, Email.category.is_not(None))
            .group_by(Email.category)
        )
    ).all()

    return StatsSummary(
        emails_last_7d=emails_last_7d,
        emails_total=emails_total,
        drafts_pending=drafts_pending,
        drafts_sent_last_7d=drafts_sent_last_7d,
        followups_scheduled=followups_scheduled,
        categories={c: n for c, n in cat_rows},
    )
