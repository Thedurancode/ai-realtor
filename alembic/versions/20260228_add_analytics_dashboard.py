"""add analytics dashboard

Revision ID: 20260228_add_analytics_dashboard
Revises: add_enhanced_video_generation
Create Date: 2026-02-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_analytics_dashboard'
down_revision = 'add_enhanced_video_generation'


def upgrade() -> None:
    # Create analytics_events table
    op.create_table(
        'analytics_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_name', sa.String(length=255), nullable=False),
        sa.Column('properties', sa.JSON(), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('referrer', sa.String(length=500), nullable=True),
        sa.Column('utm_source', sa.String(length=255), nullable=True),
        sa.Column('utm_medium', sa.String(length=255), nullable=True),
        sa.Column('utm_campaign', sa.String(length=255), nullable=True),
        sa.Column('utm_term', sa.String(length=255), nullable=True),
        sa.Column('utm_content', sa.String(length=255), nullable=True),
        sa.Column('property_id', sa.Integer(), nullable=True),
        sa.Column('value', sa.Integer(), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id']),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_analytics_events_agent_id', 'analytics_events', ['agent_id'], unique=False)
    op.create_index('ix_analytics_events_created_at', 'analytics_events', ['created_at'], unique=False)
    op.create_index('ix_analytics_events_event_type', 'analytics_events', ['event_type'], unique=False)
    op.create_index('ix_analytics_events_property_id', 'analytics_events', ['property_id'], unique=False)
    op.create_index('ix_analytics_events_session_id', 'analytics_events', ['session_id'], unique=False)

    # Create composite indexes for common queries
    op.create_index('idx_analytics_agent_created', 'analytics_events', ['agent_id', 'created_at'], unique=False)
    op.create_index('idx_analytics_type_created', 'analytics_events', ['event_type', 'created_at'], unique=False)
    op.create_index('idx_analytics_property_created', 'analytics_events', ['property_id', 'created_at'], unique=False)

    # Create dashboards table
    op.create_table(
        'dashboards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('layout', sa.JSON(), nullable=False),
        sa.Column('widgets', sa.JSON(), nullable=False),
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('auto_refresh', sa.Boolean(), nullable=False),
        sa.Column('refresh_interval_seconds', sa.Integer(), nullable=False),
        sa.Column('theme', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dashboards_agent_id', 'dashboards', ['agent_id'], unique=False)


def downgrade() -> None:
    # Drop dashboards table
    op.drop_index('ix_dashboards_agent_id', 'dashboards')
    op.drop_table('dashboards')

    # Drop analytics_events table
    op.drop_index('idx_analytics_property_created', 'analytics_events')
    op.drop_index('idx_analytics_type_created', 'analytics_events')
    op.drop_index('idx_analytics_agent_created', 'analytics_events')
    op.drop_index('ix_analytics_events_session_id', 'analytics_events')
    op.drop_index('ix_analytics_events_property_id', 'analytics_events')
    op.drop_index('ix_analytics_events_event_type', 'analytics_events')
    op.drop_index('ix_analytics_events_created_at', 'analytics_events')
    op.drop_index('ix_analytics_events_agent_id', 'analytics_events')
    op.drop_table('analytics_events')
