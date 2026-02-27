"""Add Property Photo Ordering System

Revision ID: 20260226_add_photo_ordering
Revises: 20260226_add_phone_call_indexes
Create Date: 2026-02-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20260226_add_photo_ordering'
down_revision = '20260226_add_phone_call_indexes'
branch_labels = None
depends_on = None


def upgrade():
    """Create tables for property photo ordering system."""

    # =========================================================================
    # PHOTO ORDERS TABLE
    # =========================================================================
    op.create_table(
        'photo_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('property_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.Enum('proxypics', 'boxbrownie', 'photoup', 'manual', name='photoprovider'), nullable=False),
        sa.Column('provider_order_id', sa.String(length=100), nullable=True),
        sa.Column('order_status', sa.Enum('draft', 'pending', 'confirmed', 'in_progress', 'uploading', 'review', 'completed', 'cancelled', 'failed', name='photoorderstatus'), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('requested_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('time_slot_preference', sa.String(length=100), nullable=True),
        sa.Column('shoot_address', sa.String(length=500), nullable=False),
        sa.Column('shoot_city', sa.String(length=100), nullable=False),
        sa.Column('shoot_state', sa.String(length=50), nullable=False),
        sa.Column('shoot_zip', sa.String(length=20), nullable=False),
        sa.Column('shoot_lat', sa.Float(), nullable=True),
        sa.Column('shoot_lng', sa.Float(), nullable=True),
        sa.Column('special_instructions', sa.Text(), nullable=True),
        sa.Column('contact_name', sa.String(length=200), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('contact_email', sa.String(length=200), nullable=True),
        sa.Column('services_requested', sa.JSON(), nullable=True),
        sa.Column('rooms_count', sa.Integer(), nullable=True),
        sa.Column('square_footage', sa.Integer(), nullable=True),
        sa.Column('estimated_cost', sa.Float(), nullable=True),
        sa.Column('actual_cost', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=True, server_default='USD'),
        sa.Column('provider_response', sa.JSON(), nullable=True),
        sa.Column('photographer_assigned', sa.String(length=200), nullable=True),
        sa.Column('photographer_phone', sa.String(length=50), nullable=True),
        sa.Column('estimated_completion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivery_url', sa.String(length=1000), nullable=True),
        sa.Column('delivery_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('delivery_format', sa.String(length=50), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for photo_orders
    op.create_index('ix_photo_orders_property_id', 'photo_orders', ['property_id'], unique=False)
    op.create_index('ix_photo_orders_agent_id', 'photo_orders', ['agent_id'], unique=False)
    op.create_index('ix_photo_orders_status', 'photo_orders', ['order_status'], unique=False)
    op.create_index('ix_photo_orders_provider', 'photo_orders', ['provider'], unique=False)
    op.create_index('ix_photo_orders_scheduled_at', 'photo_orders', ['scheduled_at'], unique=False)
    op.create_index('ix_photo_orders_created_at', 'photo_orders', ['created_at'], unique=False)

    # =========================================================================
    # PHOTO ORDER ITEMS TABLE
    # =========================================================================
    op.create_table(
        'photo_order_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('service_type', sa.Enum('hdr_interior', 'exterior_day', 'exterior_twilight', 'aerial_drone', 'panoramic_360', 'virtual_tour_3d', 'walkthrough_video', 'aerial_video', 'virtual_staging', 'twilight_conversion', 'object_removal', 'sky_replacement', 'floor_plan', 'basic_editing', 'advanced_editing', name='photoservicetype'), nullable=False),
        sa.Column('service_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('room_name', sa.String(length=200), nullable=True),
        sa.Column('floor', sa.String(length=50), nullable=True),
        sa.Column('enhancement_options', sa.JSON(), nullable=True),
        sa.Column('unit_price', sa.Float(), nullable=True),
        sa.Column('total_price', sa.Float(), nullable=True),
        sa.Column('provider_item_id', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['photo_orders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_photo_order_items_order_id', 'photo_order_items', ['order_id'], unique=False)
    op.create_index('ix_photo_order_items_service_type', 'photo_order_items', ['service_type'], unique=False)

    # =========================================================================
    # PHOTO ORDER DELIVERABLES TABLE
    # =========================================================================
    op.create_table(
        'photo_order_deliverables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('order_item_id', sa.Integer(), nullable=True),
        sa.Column('file_name', sa.String(length=500), nullable=False),
        sa.Column('file_url', sa.String(length=1000), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('file_format', sa.String(length=20), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('room_name', sa.String(length=200), nullable=True),
        sa.Column('sequence', sa.Integer(), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=1000), nullable=True),
        sa.Column('preview_url', sa.String(length=1000), nullable=True),
        sa.Column('original_url', sa.String(length=1000), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_featured', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('processing_status', sa.String(length=50), nullable=True, server_default='pending'),
        sa.Column('provider_file_id', sa.String(length=200), nullable=True),
        sa.Column('provider_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['photo_orders.id'], ),
        sa.ForeignKeyConstraint(['order_item_id'], ['photo_order_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_photo_order_deliverables_order_id', 'photo_order_deliverables', ['order_id'], unique=False)
    op.create_index('ix_photo_order_deliverables_item_id', 'photo_order_deliverables', ['order_item_id'], unique=False)
    op.create_index('ix_photo_order_deliverables_type', 'photo_order_deliverables', ['file_type'], unique=False)

    # =========================================================================
    # PHOTO ORDER TEMPLATES TABLE
    # =========================================================================
    op.create_table(
        'photo_order_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('template_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('services', sa.JSON(), nullable=False),
        sa.Column('base_price', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=True, server_default='USD'),
        sa.Column('property_types', sa.JSON(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_photo_order_templates_agent_id', 'photo_order_templates', ['agent_id'], unique=False)
    op.create_index('ix_photo_order_templates_is_active', 'photo_order_templates', ['is_active'], unique=False)


def downgrade():
    """Drop photo ordering tables."""

    # Drop tables in reverse order due to foreign keys
    op.drop_table('photo_order_templates')
    op.drop_table('photo_order_deliverables')
    op.drop_table('photo_order_items')
    op.drop_table('photo_orders')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS photoservicetype')
    op.execute('DROP TYPE IF EXISTS photoorderstatus')
    op.execute('DROP TYPE IF EXISTS photoprovider')
