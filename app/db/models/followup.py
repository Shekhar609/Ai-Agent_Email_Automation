from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey


class FollowUp(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "followups"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("emails.id", ondelete="SET NULL"), nullable=True, index=True
    )
    thread_id: Mapped[str | None] = mapped_column(String(512), index=True)

    scheduled_for: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    reason: Mapped[str | None] = mapped_column(String(1024))

    # pending | processing | completed | cancelled | failed
    status: Mapped[str] = mapped_column(
        String(32), default="pending", nullable=False, index=True
    )

    draft_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("drafts.id", ondelete="SET NULL"), nullable=True
    )
    error: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
