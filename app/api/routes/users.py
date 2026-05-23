from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models import User
from app.schemas.user import UserOut, UserSettingsUpdate

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)


@router.put("/me/settings", response_model=UserOut)
async def update_settings(
    body: UserSettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    if body.auto_send_enabled is not None:
        user.auto_send_enabled = body.auto_send_enabled
    if body.auto_send_threshold is not None:
        user.auto_send_threshold = body.auto_send_threshold
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)
