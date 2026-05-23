from sqlalchemy import Boolean, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey


class User(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # OAuth refresh token (encrypted, populated in phase 2)
    google_refresh_token: Mapped[str | None] = mapped_column(String(2048))

    # Auto-send settings (phase 4): if enabled, drafts with confidence_score
    # >= threshold bypass human approval and are sent directly.
    auto_send_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_send_threshold: Mapped[float] = mapped_column(Float, default=0.85, nullable=False)

    emails = relationship("Email", back_populates="user", cascade="all, delete-orphan")
    drafts = relationship("Draft", back_populates="user", cascade="all, delete-orphan")
