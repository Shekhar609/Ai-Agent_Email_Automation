"""followups + user auto-send settings

Revision ID: 0003_followups_and_auto_send
Revises: 0002_activity_logs
Create Date: 2026-05-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_followups_and_auto_send"
down_revision: Union[str, Sequence[str], None] = "0002_activity_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "auto_send_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "auto_send_threshold",
            sa.Float(),
            nullable=False,
            server_default="0.85",
        ),
    )

    op.create_table(
        "followups",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "email_id",
            sa.Uuid(),
            sa.ForeignKey("emails.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("thread_id", sa.String(512), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(1024), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column(
            "draft_id",
            sa.Uuid(),
            sa.ForeignKey("drafts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_followups_user_id", "followups", ["user_id"])
    op.create_index("ix_followups_email_id", "followups", ["email_id"])
    op.create_index("ix_followups_thread_id", "followups", ["thread_id"])
    op.create_index("ix_followups_scheduled_for", "followups", ["scheduled_for"])
    op.create_index("ix_followups_status", "followups", ["status"])


def downgrade() -> None:
    op.drop_index("ix_followups_status", table_name="followups")
    op.drop_index("ix_followups_scheduled_for", table_name="followups")
    op.drop_index("ix_followups_thread_id", table_name="followups")
    op.drop_index("ix_followups_email_id", table_name="followups")
    op.drop_index("ix_followups_user_id", table_name="followups")
    op.drop_table("followups")

    op.drop_column("users", "auto_send_threshold")
    op.drop_column("users", "auto_send_enabled")
