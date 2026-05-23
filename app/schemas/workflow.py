from uuid import UUID

from pydantic import BaseModel


class RunRequest(BaseModel):
    email_id: UUID


class RunResponse(BaseModel):
    thread_id: str
    category: str | None = None
    is_spam: bool = False
    draft_id: str | None = None
    confidence_score: float | None = None
    status: str
