"""add enabled to scheduled_tasks

Revision ID: 20260227_add_enabled_to_scheduled_tasks
Revises: a4b8c2d1e3f6
Create Date: 2026-02-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260227_add_enabled_to_scheduled_tasks'
down_revision = 'a4b8c2d1e3f6'


def upgrade() -> None:
    # Add enabled column with default True for existing rows
    # Use Boolean type to match what cron_scheduler expects
    op.add_column('scheduled_tasks', sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1'))


def downgrade() -> None:
    # Remove enabled column
    op.drop_column('scheduled_tasks', 'enabled')
