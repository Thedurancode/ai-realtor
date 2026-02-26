"""Add PhoneCall indexes for performance

Revision ID: 20260226_add_phone_call_indexes
Revises: c8d2e4f5a7b9
Create Date: 2026-02-26

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260226_add_phone_call_indexes'
down_revision = 'c8d2e4f5a7b9'
branch_labels = None
depends_on = None


def upgrade():
    """Add composite indexes to phone_calls table for common query patterns."""
    # For property call history (most recent first)
    op.create_index(
        'idx_phonecall_property_created',
        'phone_calls',
        ['property_id', 'created_at'],
        unique=False
    )

    # For agent's calls (most recent first)
    op.create_index(
        'idx_phonecall_agent_created',
        'phone_calls',
        ['agent_id', 'created_at'],
        unique=False
    )

    # For provider + status lookups (e.g., all completed Telnyx calls)
    op.create_index(
        'idx_phonecall_provider_status',
        'phone_calls',
        ['provider', 'status'],
        unique=False
    )

    # Add single column index on status if it doesn't exist
    # This improves filtering by status in general queries
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    indexes = inspector.get_indexes('phone_calls')
    status_index_exists = any(idx['name'] == 'ix_phone_calls_status' for idx in indexes)

    if not status_index_exists:
        op.create_index(
            'ix_phone_calls_status',
            'phone_calls',
            ['status'],
            unique=False
        )


def downgrade():
    """Remove the indexes added in upgrade."""
    op.drop_index('idx_phonecall_property_created', table_name='phone_calls')
    op.drop_index('idx_phonecall_agent_created', table_name='phone_calls')
    op.drop_index('idx_phonecall_provider_status', table_name='phone_calls')
    op.drop_index('ix_phone_calls_status', table_name='phone_calls')
