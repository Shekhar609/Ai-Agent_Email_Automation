"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("google_refresh_token", sa.String(2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "emails",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message_id", sa.String(512), nullable=False),
        sa.Column("thread_id", sa.String(512), nullable=True),
        sa.Column("sender", sa.String(320), nullable=False),
        sa.Column("recipient", sa.String(320), nullable=False),
        sa.Column("subject", sa.String(1024), nullable=True),
        sa.Column("body_plain", sa.Text(), nullable=True),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column("intent", sa.String(255), nullable=True),
        sa.Column("urgency", sa.String(32), nullable=True),
        sa.Column("entities", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("message_id", name="uq_emails_message_id"),
    )
    op.create_index("ix_emails_user_id", "emails", ["user_id"])
    op.create_index("ix_emails_message_id", "emails", ["message_id"])
    op.create_index("ix_emails_thread_id", "emails", ["thread_id"])
    op.create_index("ix_emails_category", "emails", ["category"])
    op.create_index("ix_emails_received_at", "emails", ["received_at"])
    op.create_index("ix_emails_user_received", "emails", ["user_id", "received_at"])

    op.create_table(
        "drafts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email_id", sa.Uuid(), sa.ForeignKey("emails.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject", sa.String(1024), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("tone", sa.String(32), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending_approval"),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_drafts_user_id", "drafts", ["user_id"])
    op.create_index("ix_drafts_email_id", "drafts", ["email_id"])
    op.create_index("ix_drafts_status", "drafts", ["status"])


def downgrade() -> None:
    op.drop_index("ix_drafts_status", table_name="drafts")
    op.drop_index("ix_drafts_email_id", table_name="drafts")
    op.drop_index("ix_drafts_user_id", table_name="drafts")
    op.drop_table("drafts")

    op.drop_index("ix_emails_user_received", table_name="emails")
    op.drop_index("ix_emails_received_at", table_name="emails")
    op.drop_index("ix_emails_category", table_name="emails")
    op.drop_index("ix_emails_thread_id", table_name="emails")
    op.drop_index("ix_emails_message_id", table_name="emails")
    op.drop_index("ix_emails_user_id", table_name="emails")
    op.drop_table("emails")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
