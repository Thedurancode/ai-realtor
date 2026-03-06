"""Add talking_head_videos table and heygen_avatar_id to agent_brands

Revision ID: 83a5f2d91e7c
Revises: 72444e81856b
Create Date: 2026-03-04
"""
from alembic import op
import sqlalchemy as sa

revision = '83a5f2d91e7c'
down_revision = '72444e81856b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'talking_head_videos',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_id', sa.Integer(), sa.ForeignKey('agents.id'), nullable=False, index=True),
        sa.Column('script', sa.Text(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('heygen_video_id', sa.String(100), nullable=True),
        sa.Column('heygen_avatar_id', sa.String(100), nullable=True),
        sa.Column('video_url', sa.String(500), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    op.add_column('agent_brands', sa.Column('heygen_avatar_id', sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column('agent_brands', 'heygen_avatar_id')
    op.drop_table('talking_head_videos')
