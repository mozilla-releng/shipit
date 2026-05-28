"""Add nightly release

Revision ID: c7e2a5f8b9d3
Revises: bc175ac0c2c5
Create Date: 2026-05-22 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c7e2a5f8b9d3"
down_revision = "bc175ac0c2c5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "shipit_api_nightly_releases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product", sa.String(), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("buildid", sa.String(), nullable=False),
        sa.Column("locales", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product", "channel", "buildid", name="_nightly_release_uc"),
    )


def downgrade():
    op.drop_table("shipit_api_nightly_releases")
