from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models import ActivityLog, User
from app.schemas.activity import ActivityLogOut

router = APIRouter()


@router.get("", response_model=list[ActivityLogOut])
async def list_activity_logs(
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ActivityLogOut]:
    rows = await db.scalars(
        select(ActivityLog)
        .where(ActivityLog.user_id == user.id)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
    )
    return [ActivityLogOut.model_validate(r) for r in rows.all()]
