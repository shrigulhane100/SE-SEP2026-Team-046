"""create account and profile foundation

Revision ID: 0001
Revises:
Create Date: 2026-11-18 17:30:52.391789

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "guidance_areas",
        sa.Column("area_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.PrimaryKeyConstraint("area_id"),
        sa.UniqueConstraint("name", name="uq_guidance_areas_name"),
    )
    op.create_table(
        "users",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "STUDENT",
                "MENTOR",
                "ADMIN",
                name="chk_users_role",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("staff_type", sa.String(length=100), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "mentor_profiles",
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("mentor_type", sa.String(length=100), nullable=True),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("current_role", sa.String(length=150), nullable=True),
        sa.Column("past_roles", sa.Text(), nullable=True),
        sa.Column("academic_background", sa.Text(), nullable=True),
        sa.Column("experience_years", sa.Integer(), server_default="0", nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("max_mentees", sa.Integer(), server_default="3", nullable=False),
        sa.Column(
            "is_accepting",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "verification_status",
            sa.Enum(
                "PENDING",
                "VERIFIED",
                "REJECTED",
                name="chk_mentor_verification",
                native_enum=False,
                create_constraint=True,
            ),
            server_default="PENDING",
            nullable=False,
        ),
        sa.CheckConstraint("experience_years >= 0", name="chk_mentor_experience"),
        sa.CheckConstraint("max_mentees >= 1", name="chk_mentor_capacity"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("profile_id"),
        sa.UniqueConstraint("user_id", name="uq_mentor_profiles_user"),
    )
    op.create_table(
        "student_profiles",
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("roll_number", sa.String(length=50), nullable=False),
        sa.Column("level", sa.String(length=100), nullable=True),
        sa.Column("career_stage", sa.String(length=100), nullable=True),
        sa.Column("skills", sa.Text(), nullable=True),
        sa.Column("goals_summary", sa.Text(), nullable=True),
        sa.Column("preferred_mode", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("profile_id"),
        sa.UniqueConstraint("roll_number", name="uq_student_profiles_roll"),
        sa.UniqueConstraint("user_id", name="uq_student_profiles_user"),
    )
    op.create_table(
        "mentor_guidance_areas",
        sa.Column("mentor_profile_id", sa.Integer(), nullable=False),
        sa.Column("area_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["guidance_areas.area_id"],
        ),
        sa.ForeignKeyConstraint(
            ["mentor_profile_id"],
            ["mentor_profiles.profile_id"],
        ),
        sa.PrimaryKeyConstraint("mentor_profile_id", "area_id"),
    )
    op.create_table(
        "student_guidance_areas",
        sa.Column("student_profile_id", sa.Integer(), nullable=False),
        sa.Column("area_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["area_id"],
            ["guidance_areas.area_id"],
        ),
        sa.ForeignKeyConstraint(
            ["student_profile_id"],
            ["student_profiles.profile_id"],
        ),
        sa.PrimaryKeyConstraint("student_profile_id", "area_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("student_guidance_areas")
    op.drop_table("mentor_guidance_areas")
    op.drop_table("student_profiles")
    op.drop_table("mentor_profiles")
    op.drop_table("users")
    op.drop_table("guidance_areas")
