"""Add property_video_jobs table

Revision ID: b7d4e2f38a16
Revises: a3c9f1e28d47
Create Date: 2026-03-04
"""
from alembic import op
import sqlalchemy as sa

revision = 'b7d4e2f38a16'
down_revision = 'a3c9f1e28d47'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'property_video_jobs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_id', sa.Integer(), sa.ForeignKey('agents.id'), nullable=False, index=True),
        sa.Column('property_id', sa.Integer(), sa.ForeignKey('properties.id'), nullable=False, index=True),
        sa.Column('script', sa.Text(), nullable=True),
        sa.Column('style', sa.String(50), nullable=False, server_default='luxury'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('shotstack_render_id', sa.String(100), nullable=True),
        sa.Column('video_url', sa.String(500), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('stock_videos_used', sa.JSON(), nullable=True),
        sa.Column('timeline_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('property_video_jobs')
