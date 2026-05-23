from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey


class ActivityLog(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "activity_logs"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("emails.id", ondelete="SET NULL"), nullable=True, index=True
    )
    draft_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("drafts.id", ondelete="SET NULL"), nullable=True, index=True
    )

    category: Mapped[str | None] = mapped_column(String(64))
    approval_status: Mapped[str | None] = mapped_column(String(32))
    sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict | None] = mapped_column(JSONB)
