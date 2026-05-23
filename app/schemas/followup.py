from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FollowUpOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    email_id: UUID | None = None
    thread_id: str | None = None
    scheduled_for: datetime
    reason: str | None = None
    status: str
    draft_id: UUID | None = None
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class FollowUpCreate(BaseModel):
    email_id: UUID
    scheduled_for: datetime
    reason: str | None = None


class FollowUpCancelResponse(BaseModel):
    id: UUID
    status: str
