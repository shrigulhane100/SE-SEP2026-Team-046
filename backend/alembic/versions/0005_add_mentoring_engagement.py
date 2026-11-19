"""add goals activities feedback notifications

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-19 15:46:43.287809

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "notifications",
        sa.Column("notification_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "notification_type",
            sa.Enum(
                "NEW_REQUEST",
                "REQUEST_ACCEPTED",
                "REQUEST_REJECTED",
                "REQUEST_CANCELLED",
                "REQUEST_EXPIRED",
                "RELATIONSHIP_UPDATED",
                "GOAL_ADDED",
                "ACTIVITY_LOGGED",
                "FEEDBACK_RECEIVED",
                name="chk_notification_type",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "reference_type",
            sa.Enum(
                "REQUEST",
                "RELATIONSHIP",
                name="chk_notification_reference_type",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("reference_id", sa.Integer(), nullable=False),
        sa.Column(
            "is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("reference_id > 0", name="chk_notification_reference_id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("notification_id"),
    )
    op.create_index(
        "ix_notifications_user_read",
        "notifications",
        ["user_id", "is_read"],
        unique=False,
    )
    op.create_table(
        "activities",
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.Column("relationship_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column(
            "activity_type",
            sa.Enum(
                "MEETING",
                "RESUME_REVIEW",
                "MOCK_INTERVIEW",
                "CHECK_IN",
                "OTHER",
                name="chk_activity_type",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("activity_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.user_id"],
        ),
        sa.ForeignKeyConstraint(
            ["relationship_id"],
            ["mentoring_relationships.relationship_id"],
        ),
        sa.PrimaryKeyConstraint("activity_id"),
    )
    op.create_index(
        "ix_activities_relationship", "activities", ["relationship_id"], unique=False
    )
    op.create_table(
        "feedback",
        sa.Column("feedback_id", sa.Integer(), nullable=False),
        sa.Column("relationship_id", sa.Integer(), nullable=False),
        sa.Column("given_by", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comments", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="chk_feedback_rating"),
        sa.ForeignKeyConstraint(
            ["given_by"],
            ["users.user_id"],
        ),
        sa.ForeignKeyConstraint(
            ["relationship_id"],
            ["mentoring_relationships.relationship_id"],
        ),
        sa.PrimaryKeyConstraint("feedback_id"),
        sa.UniqueConstraint("relationship_id", "given_by", name="uq_feedback_author"),
    )
    op.create_table(
        "goals",
        sa.Column("goal_id", sa.Integer(), nullable=False),
        sa.Column("relationship_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "TODO",
                "IN_PROGRESS",
                "DONE",
                name="chk_goal_status",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="TODO",
            nullable=False,
        ),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.user_id"],
        ),
        sa.ForeignKeyConstraint(
            ["relationship_id"],
            ["mentoring_relationships.relationship_id"],
        ),
        sa.PrimaryKeyConstraint("goal_id"),
    )
    op.create_index("ix_goals_relationship", "goals", ["relationship_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_goals_relationship", table_name="goals")
    op.drop_table("goals")
    op.drop_table("feedback")
    op.drop_index("ix_activities_relationship", table_name="activities")
    op.drop_table("activities")
    op.drop_index("ix_notifications_user_read", table_name="notifications")
    op.drop_table("notifications")
