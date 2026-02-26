"""Add phone_numbers and phone_calls tables for AI Voice Assistant

Revision ID: 20250224_voice_assistant
Revises: 20250219_agent_brand_marketing
Create Date: 2026-02-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite, postgresql

# revision identifiers, used by Alembic.
revision = '20250224_voice_assistant'
down_revision = '003_add_postiz'
branch_labels = None
depends_on = None


def upgrade():
    """Create phone_numbers and phone_calls tables."""

    # Create phone_numbers table
    op.create_table(
        'phone_numbers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('phone_number', sa.String(), nullable=False),
        sa.Column('friendly_name', sa.String(), nullable=True),
        sa.Column('provider', sa.String(), nullable=False, server_default='vapi'),
        sa.Column('provider_phone_id', sa.String(), nullable=True),
        sa.Column('can_receive_calls', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('can_make_calls', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('can_receive_sms', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_send_sms', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('greeting_message', sa.Text(), nullable=True),
        sa.Column('ai_voice_id', sa.String(), nullable=True),
        sa.Column('ai_assistant_id', sa.String(), nullable=True),
        sa.Column('forward_to_number', sa.String(), nullable=True),
        sa.Column('forward_when', sa.String(), nullable=True),
        sa.Column('business_hours_start', sa.String(), nullable=True),
        sa.Column('business_hours_end', sa.String(), nullable=True),
        sa.Column('timezone', sa.String(), nullable=False, server_default='America/New_York'),
        sa.Column('total_calls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_minutes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_cost', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('last_call_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone_number')
    )
    op.create_index(op.f('ix_phone_numbers_agent_id'), 'phone_numbers', ['agent_id'], unique=False)
    op.create_index(op.f('ix_phone_numbers_phone_number'), 'phone_numbers', ['phone_number'], unique=True)

    # Create phone_calls table
    op.create_table(
        'phone_calls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('direction', sa.String(), nullable=False),
        sa.Column('phone_number', sa.String(), nullable=False),
        sa.Column('vapi_call_id', sa.String(), nullable=True),
        sa.Column('vapi_phone_number_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='initiated'),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('transcription', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('intent', sa.String(), nullable=True),
        sa.Column('property_id', sa.Integer(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('outcome', sa.String(), nullable=True),
        sa.Column('caller_name', sa.String(), nullable=True),
        sa.Column('caller_phone', sa.String(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('follow_up_created', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('recording_url', sa.String(), nullable=True),
        sa.Column('recording_transcribed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('vapi_call_id')
    )
    op.create_index(op.f('ix_phone_calls_agent_id'), 'phone_calls', ['agent_id'], unique=False)
    op.create_index(op.f('ix_phone_calls_property_id'), 'phone_calls', ['property_id'], unique=False)


def downgrade():
    """Drop phone_numbers and phone_calls tables."""

    op.drop_index(op.f('ix_phone_calls_property_id'), table_name='phone_calls')
    op.drop_index(op.f('ix_phone_calls_agent_id'), table_name='phone_calls')
    op.drop_table('phone_calls')

    op.drop_index(op.f('ix_phone_numbers_phone_number'), table_name='phone_numbers')
    op.drop_index(op.f('ix_phone_numbers_agent_id'), table_name='phone_numbers')
    op.drop_table('phone_numbers')
