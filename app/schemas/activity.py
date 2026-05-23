from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ActivityLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    email_id: UUID | None = None
    draft_id: UUID | None = None
    category: str | None = None
    approval_status: str | None = None
    sent: bool
    error: str | None = None
    payload: dict[str, Any] | None = None
    created_at: datetime
