"""add scheduled_tasks table

Revision ID: a4b8c2d1e3f6
Revises: 3f7222350efb
Create Date: 2026-02-13 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4b8c2d1e3f6'
down_revision: Union[str, None] = '3f7222350efb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('scheduled_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_type', sa.Enum('reminder', 'recurring', 'follow_up', 'contract_check', name='tasktype'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'cancelled', 'failed', name='taskstatus'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('repeat_interval_hours', sa.Integer(), nullable=True),
        sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('property_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=True),
        sa.Column('action_params', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_scheduled_tasks_id'), 'scheduled_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_scheduled_tasks_status'), 'scheduled_tasks', ['status'], unique=False)
    op.create_index(op.f('ix_scheduled_tasks_scheduled_at'), 'scheduled_tasks', ['scheduled_at'], unique=False)
    op.create_index(op.f('ix_scheduled_tasks_property_id'), 'scheduled_tasks', ['property_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_scheduled_tasks_property_id'), table_name='scheduled_tasks')
    op.drop_index(op.f('ix_scheduled_tasks_scheduled_at'), table_name='scheduled_tasks')
    op.drop_index(op.f('ix_scheduled_tasks_status'), table_name='scheduled_tasks')
    op.drop_index(op.f('ix_scheduled_tasks_id'), table_name='scheduled_tasks')
    op.drop_table('scheduled_tasks')
