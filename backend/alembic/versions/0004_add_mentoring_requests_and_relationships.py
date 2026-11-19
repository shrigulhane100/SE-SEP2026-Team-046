"""add mentoring requests and relationships

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-19 15:40:15.793641

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "mentoring_requests",
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("mentor_id", sa.Integer(), nullable=False),
        sa.Column("area_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("objective", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "ONE_TIME",
                "LONG_TERM",
                name="chk_request_type",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "ACCEPTED",
                "REJECTED",
                "EXPIRED",
                "CANCELLED",
                name="chk_mentoring_request_status",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reject_reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["guidance_areas.area_id"],
        ),
        sa.ForeignKeyConstraint(
            ["mentor_id"],
            ["users.user_id"],
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("request_id"),
    )
    op.create_index(
        "ix_requests_expiry", "mentoring_requests", ["expires_at"], unique=False
    )
    op.create_index(
        "ix_requests_mentor", "mentoring_requests", ["mentor_id"], unique=False
    )
    op.create_index(
        "ix_requests_status", "mentoring_requests", ["status"], unique=False
    )
    op.create_index(
        "ix_requests_student", "mentoring_requests", ["student_id"], unique=False
    )
    op.create_index(
        "uq_pending_request_pair",
        "mentoring_requests",
        ["student_id", "mentor_id"],
        unique=True,
        postgresql_where=sa.text("status = 'PENDING'"),
    )
    op.create_table(
        "mentoring_relationships",
        sa.Column("relationship_id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE",
                "PAUSED",
                "COMPLETED",
                "CLOSED",
                name="chk_relationship_status",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="ACTIVE",
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["mentoring_requests.request_id"],
        ),
        sa.PrimaryKeyConstraint("relationship_id"),
        sa.UniqueConstraint("request_id", name="uq_relationship_request"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("mentoring_relationships")
    op.drop_index(
        "uq_pending_request_pair",
        table_name="mentoring_requests",
        postgresql_where=sa.text("status = 'PENDING'"),
    )
    op.drop_index("ix_requests_student", table_name="mentoring_requests")
    op.drop_index("ix_requests_status", table_name="mentoring_requests")
    op.drop_index("ix_requests_mentor", table_name="mentoring_requests")
    op.drop_index("ix_requests_expiry", table_name="mentoring_requests")
    op.drop_table("mentoring_requests")
