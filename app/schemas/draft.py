from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DraftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    email_id: UUID
    subject: str | None = None
    body: str
    tone: str | None = None
    status: str
    confidence_score: float | None = None
    approved: bool
    sent: bool
    created_at: datetime


class DraftUpdate(BaseModel):
    subject: str | None = None
    body: str | None = None
    tone: str | None = None


class RejectRequest(BaseModel):
    reason: str | None = None


class DraftActionResponse(BaseModel):
    draft_id: str
    thread_id: str
    approval_status: str | None = None
    sent_message_id: str | None = None
    status: str
