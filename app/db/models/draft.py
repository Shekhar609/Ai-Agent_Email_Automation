from uuid import UUID

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey


class Draft(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "drafts"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email_id: Mapped[UUID] = mapped_column(
        ForeignKey("emails.id", ondelete="CASCADE"), nullable=False, index=True
    )

    subject: Mapped[str | None] = mapped_column(String(1024))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    tone: Mapped[str | None] = mapped_column(String(32))

    status: Mapped[str] = mapped_column(
        String(32), default="pending_approval", nullable=False, index=True
    )
    confidence_score: Mapped[float | None] = mapped_column(Float)

    approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="drafts")
    email = relationship("Email", back_populates="drafts")
