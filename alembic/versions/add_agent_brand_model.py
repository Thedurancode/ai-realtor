"""add_agent_brand_model

Revision ID: 001_add_agent_brand
Revises:
Create Date: 2026-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_add_agent_brand'
down_revision: Union[str, None] = '20250222_add_intelligence'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create agent_brands table
    op.create_table(
        'agent_brands',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('tagline', sa.String(length=500), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('website_url', sa.String(length=500), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('about_us', sa.Text(), nullable=True),
        sa.Column('specialties', sa.JSON(), nullable=True),
        sa.Column('service_areas', sa.JSON(), nullable=True),
        sa.Column('languages', sa.JSON(), nullable=True),
        sa.Column('primary_color', sa.String(length=7), nullable=True),
        sa.Column('secondary_color', sa.String(length=7), nullable=True),
        sa.Column('accent_color', sa.String(length=7), nullable=True),
        sa.Column('background_color', sa.String(length=7), nullable=True),
        sa.Column('text_color', sa.String(length=7), nullable=True),
        sa.Column('social_media', sa.JSON(), nullable=True),
        sa.Column('display_phone', sa.String(length=50), nullable=True),
        sa.Column('display_email', sa.String(length=255), nullable=True),
        sa.Column('office_address', sa.String(length=500), nullable=True),
        sa.Column('office_phone', sa.String(length=50), nullable=True),
        sa.Column('license_display_name', sa.String(length=255), nullable=True),
        sa.Column('license_number', sa.String(length=100), nullable=True),
        sa.Column('license_states', sa.JSON(), nullable=True),
        sa.Column('show_profile', sa.Boolean(), nullable=True),
        sa.Column('show_contact_info', sa.Boolean(), nullable=True),
        sa.Column('show_social_media', sa.Boolean(), nullable=True),
        sa.Column('headshot_url', sa.String(length=500), nullable=True),
        sa.Column('banner_url', sa.String(length=500), nullable=True),
        sa.Column('company_badge_url', sa.String(length=500), nullable=True),
        sa.Column('email_template_style', sa.String(length=50), nullable=True),
        sa.Column('report_logo_placement', sa.String(length=20), nullable=True),
        sa.Column('meta_title', sa.String(length=255), nullable=True),
        sa.Column('meta_description', sa.Text(), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('google_analytics_id', sa.String(length=50), nullable=True),
        sa.Column('facebook_pixel_id', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index
    op.create_index('ix_agent_brands_agent_id', 'agent_brands', ['agent_id'])
    op.create_index('ix_agent_brands_company_name', 'agent_brands', ['company_name'])
    op.create_index('ix_agent_brands_show_profile', 'agent_brands', ['show_profile'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_agent_brands_show_profile', table_name='agent_brands')
    op.drop_index('ix_agent_brands_company_name', table_name='agent_brands')
    op.drop_index('ix_agent_brands_agent_id', table_name='agent_brands')

    # Drop table
    op.drop_table('agent_brands')
