from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey


class Email(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "emails"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message_id: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    thread_id: Mapped[str | None] = mapped_column(String(512), index=True)

    sender: Mapped[str] = mapped_column(String(320))
    recipient: Mapped[str] = mapped_column(String(320))
    subject: Mapped[str | None] = mapped_column(String(1024))
    body_plain: Mapped[str | None] = mapped_column(Text)
    body_html: Mapped[str | None] = mapped_column(Text)

    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    # Populated by classification agent (phase 3)
    category: Mapped[str | None] = mapped_column(String(64), index=True)
    intent: Mapped[str | None] = mapped_column(String(255))
    urgency: Mapped[str | None] = mapped_column(String(32))
    entities: Mapped[dict | None] = mapped_column(JSONB)

    user = relationship("User", back_populates="emails")
    drafts = relationship("Draft", back_populates="email", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_emails_user_received", "user_id", "received_at"),)
