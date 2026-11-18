"""add authentication sessions

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-18 17:48:01.722558

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "auth_sessions",
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_index(
        "ix_auth_sessions_user_expiry",
        "auth_sessions",
        ["user_id", "expires_at"],
        unique=False,
    )
    op.add_column(
        "student_profiles",
        sa.Column("career_objective", sa.String(length=30), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("student_profiles", "career_objective")
    op.drop_index("ix_auth_sessions_user_expiry", table_name="auth_sessions")
    op.drop_table("auth_sessions")
