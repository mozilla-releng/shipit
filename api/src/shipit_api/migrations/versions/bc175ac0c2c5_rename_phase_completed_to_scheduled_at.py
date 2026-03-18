"""Rename phase completed to scheduled_at

Revision ID: bc175ac0c2c5
Revises: a91368f8211b
Create Date: 2026-03-18 09:08:26.406555

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "bc175ac0c2c5"
down_revision = "a91368f8211b"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("shipit_api_phases", "completed", new_column_name="scheduled_at")
    op.alter_column("shipit_api_phases", "completed_by", new_column_name="scheduled_by")
    op.alter_column("shipit_api_xpi_phases", "completed", new_column_name="scheduled_at")
    op.alter_column("shipit_api_xpi_phases", "completed_by", new_column_name="scheduled_by")


def downgrade():
    op.alter_column("shipit_api_phases", "scheduled_at", new_column_name="completed")
    op.alter_column("shipit_api_phases", "scheduled_by", new_column_name="completed_by")
    op.alter_column("shipit_api_xpi_phases", "scheduled_at", new_column_name="completed")
    op.alter_column("shipit_api_xpi_phases", "scheduled_by", new_column_name="completed_by")
