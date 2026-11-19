"""Complete student and mentor profile fields."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("student_profiles", sa.Column("education", sa.Text()))
    op.add_column("student_profiles", sa.Column("interests", sa.Text()))
    op.add_column("mentor_profiles", sa.Column("organisation", sa.String(length=150)))
    op.add_column("mentor_profiles", sa.Column("skills", ARRAY(sa.Text())))

    # Existing text values may contain comma-separated skills and previous roles.
    for table, column in (
        ("student_profiles", "skills"),
        ("mentor_profiles", "past_roles"),
    ):
        op.alter_column(
            table,
            column,
            existing_type=sa.Text(),
            type_=ARRAY(sa.Text()),
            postgresql_using=(
                f"CASE WHEN btrim({column}) = '' THEN ARRAY[]::text[] "
                f"ELSE regexp_split_to_array(btrim({column}), '[[:space:]]*,[[:space:]]*') END"
            ),
        )

    op.create_index(
        "uq_guidance_areas_name_ci",
        "guidance_areas",
        [sa.text("lower(name)")],
        unique=True,
    )
    op.drop_constraint("uq_guidance_areas_name", "guidance_areas", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("uq_guidance_areas_name", "guidance_areas", ["name"])
    op.drop_index("uq_guidance_areas_name_ci", table_name="guidance_areas")

    for table, column in (
        ("student_profiles", "skills"),
        ("mentor_profiles", "past_roles"),
    ):
        op.alter_column(
            table,
            column,
            existing_type=ARRAY(sa.Text()),
            type_=sa.Text(),
            postgresql_using=f"array_to_string({column}, ', ')",
        )

    op.drop_column("mentor_profiles", "skills")
    op.drop_column("mentor_profiles", "organisation")
    op.drop_column("student_profiles", "interests")
    op.drop_column("student_profiles", "education")
