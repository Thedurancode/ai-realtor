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


def upgrade() -> None:
    # Properties - composite index for common filtering patterns
    # Used by: search by city/state/type
    op.create_index(
        "ix_properties_city_state_type",
        "properties",
        ["city", "state", "property_type"]
    )

    # Properties - price index for range queries
    # Used by: price range filtering, max_price/min_price queries
    op.create_index(
        "ix_properties_price",
        "properties",
        ["price"]
    )

    # Contacts - email index for login/user lookups
    # Used by: email search, contact deduplication
    op.create_index(
        "ix_contacts_email",
        "contacts",
        ["email"]
    )

    # Contacts - property+email composite for duplicate detection
    # Used by: finding existing contacts for a property
    op.create_index(
        "ix_contacts_property_email",
        "contacts",
        ["property_id", "email"]
    )

    # Conversation history - property_id with created_at
    # Used by: activity timeline, stale property detection
    op.create_index(
        "ix_conversation_history_property_created",
        "conversation_history",
        ["property_id", "created_at"]
    )

    # Analytics events - property_id with event_type and created_at
    # Used by: activity analytics, event filtering by type
    op.create_index(
        "ix_analytics_events_property_type_created",
        "analytics_events",
        ["property_id", "event_type", "created_at"]
    )

    # Scheduled tasks - agent_id with status for pending tasks
    # Used by: task dashboard, scheduled task queries
    op.create_index(
        "ix_scheduled_tasks_agent_status",
        "scheduled_tasks",
        ["agent_id", "status"]
    )

    # Notifications - agent_id with is_read for unread counts
    # Used by: notification badge, unread filtering
    op.create_index(
        "ix_notifications_agent_read",
        "notifications",
        ["agent_id", "is_read"]
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_agent_read", "notifications")
    op.drop_index("ix_scheduled_tasks_agent_status", "scheduled_tasks")
    op.drop_index("ix_analytics_events_property_type_created", "analytics_events")
    op.drop_index("ix_conversation_history_property_created", "conversation_history")
    op.drop_index("ix_contacts_property_email", "contacts")
    op.drop_index("ix_contacts_email", "contacts")
    op.drop_index("ix_properties_price", "properties")
    op.drop_index("ix_properties_city_state_type", "properties")
