"""add_status_column_indexes

Revision ID: 1ed987f5fee3
Revises: e58e55272f67
Create Date: 2026-03-10

Adds indexes to status columns that are frequently filtered but missing indexes:
- agent_brands.voice_clone_status
- direct_mails.mail_status
- photo_order_items.status
- photo_order_deliverables.processing_status
- calendar_connections.last_sync_status
- synced_calendar_events.sync_status
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1ed987f5fee3'
down_revision: Union[str, None] = 'e58e55272f67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _safe_create_index(index_name: str, table_name: str, columns: list) -> None:
    """Create an index only if the table and columns exist."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    try:
        table_columns = [c["name"] for c in inspector.get_columns(table_name)]
        if all(col in table_columns for col in columns):
            op.create_index(index_name, table_name, columns, if_not_exists=True)
    except Exception:
        pass  # Table doesn't exist yet


def _safe_drop_index(index_name: str, table_name: str) -> None:
    """Drop an index only if it exists."""
    try:
        op.drop_index(index_name, table_name=table_name)
    except Exception:
        pass


def upgrade() -> None:
    _safe_create_index("ix_agent_brands_voice_clone_status", "agent_brands", ["voice_clone_status"])
    _safe_create_index("ix_direct_mails_mail_status", "direct_mails", ["mail_status"])
    _safe_create_index("ix_photo_order_items_status", "photo_order_items", ["status"])
    _safe_create_index("ix_photo_order_deliverables_processing_status", "photo_order_deliverables", ["processing_status"])
    _safe_create_index("ix_calendar_connections_last_sync_status", "calendar_connections", ["last_sync_status"])
    _safe_create_index("ix_synced_calendar_events_sync_status", "synced_calendar_events", ["sync_status"])


def downgrade() -> None:
    _safe_drop_index("ix_synced_calendar_events_sync_status", "synced_calendar_events")
    _safe_drop_index("ix_calendar_connections_last_sync_status", "calendar_connections")
    _safe_drop_index("ix_photo_order_deliverables_processing_status", "photo_order_deliverables")
    _safe_drop_index("ix_photo_order_items_status", "photo_order_items")
    _safe_drop_index("ix_direct_mails_mail_status", "direct_mails")
    _safe_drop_index("ix_agent_brands_voice_clone_status", "agent_brands")
