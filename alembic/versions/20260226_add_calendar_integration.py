"""add_calendar_integration

Revision ID: 004_add_calendar
Revises: 003_add_postiz
Create Date: 2026-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_add_calendar'
down_revision: Union[str, None] = '003_add_postiz'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create calendar_connections table
    op.create_table(
        'calendar_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('calendar_id', sa.String(length=255), nullable=True),
        sa.Column('calendar_name', sa.String(length=255), nullable=True),
        sa.Column('calendar_color', sa.String(length=20), nullable=True),
        sa.Column('sync_enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('sync_tasks', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('sync_follow_ups', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('sync_appointments', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('sync_contracts', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sync_status', sa.String(length=50), nullable=True),
        sa.Column('last_sync_error', sa.Text(), nullable=True),
        sa.Column('auto_create_events', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('event_duration_minutes', sa.Integer(), nullable=True, server_default='60'),
        sa.Column('reminder_minutes', sa.Integer(), nullable=True, server_default='15'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_calendar_connections_agent_id', 'calendar_connections', ['agent_id'])

    # Create synced_calendar_events table
    op.create_table(
        'synced_calendar_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('calendar_connection_id', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('external_event_id', sa.String(length=255), nullable=True),
        sa.Column('external_event_link', sa.String(length=500), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=500), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('all_day', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('reminder_minutes', sa.Integer(), nullable=True),
        sa.Column('sync_status', sa.String(length=50), nullable=False),
        sa.Column('sync_error', sa.Text(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['calendar_connection_id'], ['calendar_connections.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_synced_calendar_events_calendar_connection_id', 'synced_calendar_events', ['calendar_connection_id'])
    op.create_index('ix_synced_calendar_events_source_type_source_id', 'synced_calendar_events', ['source_type', 'source_id'])

    # Create calendar_events table
    op.create_table(
        'calendar_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=500), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('all_day', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('reminder_minutes', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('attendees', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='confirmed'),
        sa.Column('external_event_id', sa.String(length=255), nullable=True),
        sa.Column('external_calendar_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_calendar_events_agent_id', 'calendar_events', ['agent_id'])
    op.create_index('ix_calendar_events_property_id', 'calendar_events', ['property_id'])
    op.create_index('ix_calendar_events_start_time', 'calendar_events', ['start_time'])
    op.create_index('ix_calendar_events_event_type', 'calendar_events', ['event_type'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_calendar_events_event_type', table_name='calendar_events')
    op.drop_index('ix_calendar_events_start_time', table_name='calendar_events')
    op.drop_index('ix_calendar_events_property_id', table_name='calendar_events')
    op.drop_index('ix_calendar_events_agent_id', table_name='calendar_events')
    op.drop_index('ix_synced_calendar_events_source_type_source_id', table_name='synced_calendar_events')
    op.drop_index('ix_synced_calendar_events_calendar_connection_id', table_name='synced_calendar_events')
    op.drop_index('ix_calendar_connections_agent_id', table_name='calendar_connections')

    # Drop tables
    op.drop_table('calendar_events')
    op.drop_table('synced_calendar_events')
    op.drop_table('calendar_connections')
