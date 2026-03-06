"""Add voice_sample_url, voice_clone_id, voice_clone_status to agent_brands

Revision ID: 72444e81856b
Revises: None
Create Date: 2026-03-04
"""
from alembic import op
import sqlalchemy as sa

revision = '72444e81856b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('agent_brands', sa.Column('voice_sample_url', sa.String(500), nullable=True))
    op.add_column('agent_brands', sa.Column('voice_clone_id', sa.String(100), nullable=True))
    op.add_column('agent_brands', sa.Column('voice_clone_status', sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column('agent_brands', 'voice_clone_status')
    op.drop_column('agent_brands', 'voice_clone_id')
    op.drop_column('agent_brands', 'voice_sample_url')
