"""add_missing_performance_indexes

Revision ID: d395fd06467d
Revises: add_analytics_alerts
Create Date: 2026-02-28 00:34:39.357307

Adds missing performance indexes for common queries:
- Properties: price, city+state+type composite for filtering
- Contacts: email for login lookups, property+email for duplicate detection
- Conversation history: property_id for activity lookups
- Analytics events: property_id+created_at for time-series queries
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd395fd06467d'
down_revision: Union[str, None] = 'add_analytics_alerts'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns_exist(table_name: str, columns: list) -> bool:
    conn = op.get_bind()
    for col in columns:
        result = conn.execute(
            sa.text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                "WHERE table_name = :t AND column_name = :c)"
            ),
            {"t": table_name, "c": col}
        )
        if not result.scalar():
            return False
    return True


def _safe_create_index(name, table, columns):
    if _columns_exist(table, columns):
        op.create_index(name, table, columns)


def upgrade() -> None:
    _safe_create_index("ix_properties_city_state_type", "properties", ["city", "state", "property_type"])
    _safe_create_index("ix_properties_price", "properties", ["price"])
    _safe_create_index("ix_contacts_email", "contacts", ["email"])
    _safe_create_index("ix_contacts_property_email", "contacts", ["property_id", "email"])
    _safe_create_index("ix_conversation_history_property_created", "conversation_history", ["property_id", "created_at"])
    _safe_create_index("ix_analytics_events_property_type_created", "analytics_events", ["property_id", "event_type", "created_at"])
    _safe_create_index("ix_scheduled_tasks_agent_status", "scheduled_tasks", ["agent_id", "status"])
    _safe_create_index("ix_notifications_agent_read", "notifications", ["agent_id", "is_read"])


def downgrade() -> None:
    for name, table in [
        ("ix_notifications_agent_read", "notifications"),
        ("ix_scheduled_tasks_agent_status", "scheduled_tasks"),
        ("ix_analytics_events_property_type_created", "analytics_events"),
        ("ix_conversation_history_property_created", "conversation_history"),
        ("ix_contacts_property_email", "contacts"),
        ("ix_contacts_email", "contacts"),
        ("ix_properties_price", "properties"),
        ("ix_properties_city_state_type", "properties"),
    ]:
        try:
            op.drop_index(name, table)
        except Exception:
            pass
