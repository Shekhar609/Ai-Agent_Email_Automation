from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EmailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    message_id: str
    thread_id: str | None = None
    sender: str
    recipient: str
    subject: str | None = None
    body_plain: str | None = None
    received_at: datetime | None = None
    category: str | None = None
    intent: str | None = None
    urgency: str | None = None
    created_at: datetime


class SyncResponse(BaseModel):
    fetched: int
    created: int
    skipped: int
