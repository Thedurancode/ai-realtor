"""make generated_script nullable

Revision ID: make_generated_script_nullable
Revises:
Create Date: 2026-02-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'make_generated_script_nullable'
down_revision = None  # Standalone migration
branch_labels = None
depends_on = None


def upgrade():
    # Make generated_script nullable in property_videos table
    op.alter_column('property_videos', 'generated_script',
                    existing_type=sa.Text(),
                    nullable=True)


def downgrade():
    # Revert to not nullable
    op.alter_column('property_videos', 'generated_script',
                    existing_type=sa.Text(),
                    nullable=False)
