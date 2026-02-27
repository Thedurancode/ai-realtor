"""Add Direct Mail System for Lob.com Integration

Revision ID: 20260226_add_direct_mail
Revises: 20260226_add_photo_ordering
Create Date: 2026-02-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20260226_add_direct_mail'
down_revision = '20260226_add_photo_ordering'
branch_labels = None
depends_on = None


def upgrade():
    """Create tables for direct mail system"""

    # =========================================================================
    # DIRECT MAIL TABLE
    # =========================================================================
    op.create_table(
        'direct_mail',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=True),
        sa.Column('contact_id', sa.Integer(), nullable=True),

        # Mail details
        sa.Column('mail_type', sa.Enum('postcard', 'letter', 'check', name='mailtype'), nullable=False),
        sa.Column('mail_status', sa.Enum('draft', 'scheduled', 'processing', 'mailed', 'in_transit', 'delivered', 'cancelled', 'failed', name='mailstatus'), nullable=False),

        # Lob integration
        sa.Column('lob_mailpiece_id', sa.String(length=100), nullable=True),
        sa.Column('lob_object_id', sa.String(length=100), nullable=True),

        # Addresses
        sa.Column('to_address', postgresql.JSON(), nullable=False),
        sa.Column('from_address', postgresql.JSON(), nullable=False),

        # Content
        sa.Column('template_name', sa.String(length=100), nullable=True),
        sa.Column('front_html', sa.Text(), nullable=True),
        sa.Column('back_html', sa.Text(), nullable=True),
        sa.Column('file_url', sa.String(length=1000), nullable=True),
        sa.Column('merge_variables', postgresql.JSON(), nullable=True),

        # Mail options
        sa.Column('postcard_size', sa.Enum('4x6', '6x9', '6x11', name='postcardsize'), nullable=True),
        sa.Column('letter_size', sa.Enum('letter', 'legal', 'a4', name='lettersize'), nullable=True),
        sa.Column('color', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('double_sided', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('certified_mail', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('return_envelope', sa.Boolean(), nullable=False, server_default='false'),

        # Scheduling
        sa.Column('send_after', sa.DateTime(timezone=True), nullable=True),

        # Pricing
        sa.Column('estimated_cost', sa.Float(), nullable=True),
        sa.Column('actual_cost', sa.Float(), nullable=True),

        # Tracking
        sa.Column('expected_delivery_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tracking_events', postgresql.JSON(), nullable=True),
        sa.Column('tracking_url', sa.String(length=1000), nullable=True),

        # Campaign metadata
        sa.Column('campaign_name', sa.String(length=200), nullable=True),
        sa.Column('campaign_type', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for direct_mail
    op.create_index('ix_direct_mail_agent_id', 'direct_mail', ['agent_id'], unique=False)
    op.create_index('ix_direct_mail_property_id', 'direct_mail', ['property_id'], unique=False)
    op.create_index('ix_direct_mail_contact_id', 'direct_mail', ['contact_id'], unique=False)
    op.create_index('ix_direct_mail_mail_type', 'direct_mail', ['mail_type'], unique=False)
    op.create_index('ix_direct_mail_mail_status', 'direct_mail', ['mail_status'], unique=False)
    op.create_index('ix_direct_mail_lob_mailpiece_id', 'direct_mail', ['lob_mailpiece_id'], unique=True)
    op.create_index('ix_direct_mail_created_at', 'direct_mail', ['created_at'], unique=False)

    # =========================================================================
    # DIRECT MAIL TEMPLATES TABLE
    # =========================================================================
    op.create_table(
        'direct_mail_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),

        # Template details
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_type', sa.String(length=50), nullable=False),
        sa.Column('campaign_type', sa.String(length=50), nullable=True),

        # Content
        sa.Column('front_html_template', sa.Text(), nullable=False),
        sa.Column('back_html_template', sa.Text(), nullable=True),
        sa.Column('pdf_url_template', sa.String(length=1000), nullable=True),

        # Configuration
        sa.Column('default_postcard_size', sa.Enum('4x6', '6x9', '6x11', name='postcardsize'), nullable=True),
        sa.Column('default_color', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('default_double_sided', sa.Boolean(), nullable=False, server_default='true'),

        # Required variables
        sa.Column('required_variables', postgresql.JSON(), nullable=True),

        # Preview
        sa.Column('preview_image_url', sa.String(length=1000), nullable=True),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_system_template', sa.Boolean(), nullable=False, server_default='false'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for direct_mail_templates
    op.create_index('ix_direct_mail_templates_agent_id', 'direct_mail_templates', ['agent_id'], unique=False)
    op.create_index('ix_direct_mail_templates_template_type', 'direct_mail_templates', ['template_type'], unique=False)
    op.create_index('ix_direct_mail_templates_campaign_type', 'direct_mail_templates', ['campaign_type'], unique=False)
    op.create_index('ix_direct_mail_templates_is_active', 'direct_mail_templates', ['is_active'], unique=False)

    # =========================================================================
    # DIRECT MAIL CAMPAIGNS TABLE
    # =========================================================================
    op.create_table(
        'direct_mail_campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),

        # Campaign details
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('campaign_type', sa.String(length=50), nullable=True),

        # Targeting
        sa.Column('target_property_ids', postgresql.JSON(), nullable=True),
        sa.Column('target_contact_ids', postgresql.JSON(), nullable=True),
        sa.Column('filters', postgresql.JSON(), nullable=True),

        # Configuration
        sa.Column('mail_type', sa.Enum('postcard', 'letter', 'check', name='mailtype'), nullable=False),
        sa.Column('postcard_size', sa.Enum('4x6', '6x9', '6x11', name='postcardsize'), nullable=True),
        sa.Column('color', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('double_sided', sa.Boolean(), nullable=False, server_default='true'),

        # Scheduling
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=True),
        sa.Column('send_immediately', sa.Boolean(), nullable=False, server_default='false'),

        # Stats
        sa.Column('total_recipients', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sent_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('delivered_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_cost', sa.Float(), nullable=False, server_default='0.0'),

        # Status
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),

        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['template_id'], ['direct_mail_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for direct_mail_campaigns
    op.create_index('ix_direct_mail_campaigns_agent_id', 'direct_mail_campaigns', ['agent_id'], unique=False)
    op.create_index('ix_direct_mail_campaigns_template_id', 'direct_mail_campaigns', ['template_id'], unique=False)
    op.create_index('ix_direct_mail_campaigns_status', 'direct_mail_campaigns', ['status'], unique=False)
    op.create_index('ix_direct_mail_campaigns_created_at', 'direct_mail_campaigns', ['created_at'], unique=False)


def downgrade():
    """Drop direct mail tables"""

    # Drop tables in reverse order due to foreign keys
    op.drop_table('direct_mail_campaigns')
    op.drop_table('direct_mail_templates')
    op.drop_table('direct_mail')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS lettersize')
    op.execute('DROP TYPE IF EXISTS postcardsize')
    op.execute('DROP TYPE IF EXISTS mailstatus')
    op.execute('DROP TYPE IF EXISTS mailtype')
