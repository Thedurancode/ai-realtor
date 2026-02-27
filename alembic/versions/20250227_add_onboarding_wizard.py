"""add onboarding wizard and city field

Revision ID: 20250227_add_onboarding
Revises: c8d2e4f5a7b9
Create Date: 2025-02-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250227_add_onboarding'
down_revision = 'c8d2e4f5a7b9'
branch_labels = None
depends_on = None


def upgrade():
    # Add city column to agents table
    op.add_column('agents', sa.Column('city', sa.String(), nullable=True))

    # Create agent_onboarding table
    op.create_table(
        'agent_onboarding',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('license_number', sa.String(length=100), nullable=True),
        sa.Column('business_name', sa.String(length=255), nullable=True),
        sa.Column('business_card_image', sa.Text(), nullable=True),
        sa.Column('logo_url', sa.Text(), nullable=True),
        sa.Column('colors', postgresql.JSON(), nullable=True),
        sa.Column('schedule', postgresql.JSON(), nullable=True),
        sa.Column('weekend_schedule', postgresql.JSON(), nullable=True),
        sa.Column('contacts_uploaded', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('social_media', postgresql.JSON(), nullable=True),
        sa.Column('music_preferences', postgresql.JSON(), nullable=True),
        sa.Column('contracts_used', postgresql.JSON(), nullable=True),
        sa.Column('calendar_connected', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('primary_market', sa.String(length=255), nullable=True),
        sa.Column('secondary_markets', sa.Text(), nullable=True),
        sa.Column('service_radius', sa.String(length=100), nullable=True),
        sa.Column('office_locations', sa.Text(), nullable=True),
        sa.Column('assistant_name', sa.String(length=100), nullable=True),
        sa.Column('assistant_style', sa.String(length=100), nullable=True),
        sa.Column('personality_traits', postgresql.JSON(), nullable=True),
        sa.Column('onboarded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('onboarding_complete', sa.Boolean(), nullable=True, server_default='false'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id')
    )
    op.create_index(op.f('ix_agent_onboarding_agent_id'), 'agent_onboarding', ['agent_id'], unique=True)


def downgrade():
    # Drop agent_onboarding table
    op.drop_index(op.f('ix_agent_onboarding_agent_id'), table_name='agent_onboarding')
    op.drop_table('agent_onboarding')

    # Remove city column from agents table
    op.drop_column('agents', 'city')
