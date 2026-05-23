from pydantic import BaseModel, Field


class StatsSummary(BaseModel):
    emails_last_7d: int
    emails_total: int
    drafts_pending: int
    drafts_sent_last_7d: int
    followups_scheduled: int
    categories: dict[str, int] = Field(default_factory=dict)
