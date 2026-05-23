from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None = None
    is_active: bool
    is_admin: bool
    auto_send_enabled: bool = False
    auto_send_threshold: float = 0.85
    created_at: datetime


class UserSettingsUpdate(BaseModel):
    auto_send_enabled: bool | None = None
    auto_send_threshold: float | None = Field(None, ge=0.0, le=1.0)
