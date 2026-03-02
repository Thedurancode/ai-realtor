"""Add Products and User Products for SaaS Platform with Coolify Auto-Provisioning

Revision ID: 20260302_add_products
Create Date: 2026-03-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20260302_add_products'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create tables for SaaS product management system"""

    # =========================================================================
    # PRODUCTS TABLE
    # =========================================================================
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price_monthly', sa.Float(precision=10, scale=2), nullable=True),
        sa.Column('price_downpayment', sa.Float(precision=10, scale=2), nullable=True),
        sa.Column('sku', sa.String(length=100), nullable=True),
        sa.Column('coolify_config', postgresql.JSON(), nullable=True),
        sa.Column('auto_provision', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for products
    op.create_index('ix_products_id', 'products', ['id'], unique=False)
    op.create_index('ix_products_name', 'products', ['name'], unique=False)
    op.create_index('ix_products_slug', 'products', ['slug'], unique=True)
    op.create_index('ix_products_auto_provision', 'products', ['auto_provision'], unique=False)
    op.create_index('ix_products_is_active', 'products', ['is_active'], unique=False)

    # =========================================================================
    # USER_PRODUCTS TABLE
    # =========================================================================
    op.create_table(
        'user_products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('purchase_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('coolify_instance_id', sa.String(length=255), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('subscription_cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('auto_renew', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for user_products
    op.create_index('ix_user_products_id', 'user_products', ['id'], unique=False)
    op.create_index('ix_user_products_user_id', 'user_products', ['user_id'], unique=False)
    op.create_index('ix_user_products_product_id', 'user_products', ['product_id'], unique=False)
    op.create_index('ix_user_products_status', 'user_products', ['status'], unique=False)
    op.create_index('ix_user_products_purchase_date', 'user_products', ['purchase_date'], unique=False)
    op.create_index('ix_user_products_coolify_instance_id', 'user_products', ['coolify_instance_id'], unique=False)


def downgrade():
    """Drop products and user_products tables"""

    # Drop tables in reverse order due to foreign keys
    op.drop_table('user_products')
    op.drop_table('products')
