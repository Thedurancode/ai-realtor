"""add property websites

Revision ID: add_property_websites
Revises:
Create Date: 2026-02-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_property_websites'
down_revision = '20250227_add_onboarding'
branch_labels = None
depends_on = None


def upgrade():
    # Create property_websites table
    op.create_table(
        'property_websites',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('property_id', sa.Integer(), sa.ForeignKey('properties.id'), nullable=False),
        sa.Column('agent_id', sa.Integer(), sa.ForeignKey('agents.id'), nullable=False),
        sa.Column('website_name', sa.String(255), nullable=False),
        sa.Column('website_slug', sa.String(255), unique=True, nullable=False),
        sa.Column('website_type', sa.String(50), nullable=False, default='landing_page'),  # landing_page, single_page, full_site
        sa.Column('template', sa.String(100), nullable=False, default='modern'),
        sa.Column('theme', sa.JSON(), nullable=True),  # color scheme, fonts, layout preferences
        sa.Column('content', sa.JSON(), nullable=True),  # hero, sections, about, contact, etc
        sa.Column('custom_domain', sa.String(255), nullable=True),
        sa.Column('is_published', sa.Boolean(), default=False, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('published_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), onupdate=sa.text('NOW()'), nullable=False),
    )

    # Create indexes
    op.create_index('ix_property_websites_property_id', 'property_websites', ['property_id'])
    op.create_index('ix_property_websites_agent_id', 'property_websites', ['agent_id'])
    op.create_index('ix_property_websites_slug', 'property_websites', ['website_slug'])
    op.create_index('ix_property_websites_published', 'property_websites', ['is_published', 'is_active'])

    # Create website_analytics table (track visitors, leads)
    op.create_table(
        'website_analytics',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('website_id', sa.Integer(), sa.ForeignKey('property_websites.id'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),  # view, contact_form_submit, inquiry, click
        sa.Column('event_data', sa.JSON(), nullable=True),
        sa.Column('visitor_ip', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('referrer', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_index('ix_website_analytics_website_id', 'website_analytics', ['website_id'])
    op.create_index('ix_website_analytics_event_type', 'website_analytics', ['event_type'])
    op.create_index('ix_website_analytics_created_at', 'website_analytics', ['created_at'])


def downgrade():
    op.drop_index('ix_website_analytics_created_at', table='website_analytics')
    op.drop_index('ix_website_analytics_event_type', table='website_analytics')
    op.drop_index('ix_website_analytics_website_id', table='website_analytics')
    op.drop_table('website_analytics')

    op.drop_index('ix_property_websites_published', table='property_websites')
    op.drop_index('ix_property_websites_slug', table='property_websites')
    op.drop_index('ix_property_websites_agent_id', table='property_websites')
    op.drop_index('ix_property_websites_property_id', table='property_websites')
    op.drop_table('property_websites')
