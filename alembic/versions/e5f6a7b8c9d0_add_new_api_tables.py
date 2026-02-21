"""Add showings, clients, transactions, property_media, commissions, messages, listings tables

Revision ID: e5f6a7b8c9d0
Revises: d1e2f3a4b5c6
Create Date: 2026-02-21

Adds 9 new tables to support showings/appointments, client CRM, transaction
closing tracker, property media management, commission tracking, messaging
log, and listing syndication.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- clients (must come before showings, transactions, messages, commissions) ---
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("company", sa.String(), nullable=True),
        sa.Column("client_type", sa.Enum("BUYER", "SELLER", "INVESTOR", "TENANT", "LANDLORD", name="clienttype"), nullable=False),
        sa.Column("status", sa.Enum("LEAD", "CONTACTED", "QUALIFIED", "ACTIVE", "UNDER_CONTRACT", "CLOSED", "INACTIVE", name="clientstatus"), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("preferred_locations", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("budget_min", sa.Float(), nullable=True),
        sa.Column("budget_max", sa.Float(), nullable=True),
        sa.Column("bedrooms_min", sa.Integer(), nullable=True),
        sa.Column("bathrooms_min", sa.Float(), nullable=True),
        sa.Column("sqft_min", sa.Integer(), nullable=True),
        sa.Column("property_types", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("must_haves", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("deal_breakers", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_clients_id", "clients", ["id"], unique=False)
    op.create_index("ix_clients_agent_id", "clients", ["agent_id"], unique=False)
    op.create_index("ix_clients_status", "clients", ["status"], unique=False)
    op.create_index("ix_clients_type", "clients", ["client_type"], unique=False)

    # --- showings ---
    op.create_table(
        "showings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("showing_type", sa.Enum("IN_PERSON", "VIRTUAL", "OPEN_HOUSE", name="showingtype"), nullable=True),
        sa.Column("status", sa.Enum("SCHEDULED", "CONFIRMED", "COMPLETED", "CANCELLED", "NO_SHOW", name="showingstatus"), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("attendee_name", sa.String(), nullable=True),
        sa.Column("attendee_phone", sa.String(), nullable=True),
        sa.Column("attendee_email", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_showings_id", "showings", ["id"], unique=False)
    op.create_index("ix_showings_property_id", "showings", ["property_id"], unique=False)
    op.create_index("ix_showings_status", "showings", ["status"], unique=False)
    op.create_index("ix_showings_scheduled_at", "showings", ["scheduled_at"], unique=False)
    op.create_index("ix_showings_agent_id", "showings", ["agent_id"], unique=False)

    # --- transactions ---
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("offer_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.Enum("PENDING", "UNDER_CONTRACT", "INSPECTION", "APPRAISAL", "TITLE_REVIEW", "FINANCING", "CLOSING_SCHEDULED", "CLOSED", "FELL_THROUGH", name="transactionstatus"), nullable=True),
        sa.Column("sale_price", sa.Float(), nullable=True),
        sa.Column("closing_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("earnest_money", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("escrow_company", sa.String(), nullable=True),
        sa.Column("title_company", sa.String(), nullable=True),
        sa.Column("lender_name", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["offer_id"], ["offers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_transactions_id", "transactions", ["id"], unique=False)
    op.create_index("ix_transactions_property_id", "transactions", ["property_id"], unique=False)
    op.create_index("ix_transactions_status", "transactions", ["status"], unique=False)
    op.create_index("ix_transactions_agent_id", "transactions", ["agent_id"], unique=False)
    op.create_index("ix_transactions_closing_date", "transactions", ["closing_date"], unique=False)

    # --- transaction_milestones ---
    op.create_table(
        "transaction_milestones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("PENDING", "IN_PROGRESS", "COMPLETED", "WAIVED", "FAILED", name="milestonestatus"), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_milestones_id", "transaction_milestones", ["id"], unique=False)
    op.create_index("ix_milestones_transaction_id", "transaction_milestones", ["transaction_id"], unique=False)

    # --- property_media ---
    op.create_table(
        "property_media",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("media_type", sa.Enum("PHOTO", "VIDEO", "FLOOR_PLAN", "VIRTUAL_TOUR", "DOCUMENT", name="mediatype"), nullable=True),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("is_primary", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_property_media_id", "property_media", ["id"], unique=False)
    op.create_index("ix_property_media_property_id", "property_media", ["property_id"], unique=False)
    op.create_index("ix_property_media_type", "property_media", ["media_type"], unique=False)

    # --- commissions ---
    op.create_table(
        "commissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=True),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("sale_price", sa.Float(), nullable=True),
        sa.Column("commission_rate", sa.Float(), nullable=True),
        sa.Column("commission_amount", sa.Float(), nullable=True),
        sa.Column("split_percentage", sa.Float(), nullable=True),
        sa.Column("net_amount", sa.Float(), nullable=True),
        sa.Column("status", sa.Enum("PROJECTED", "PENDING", "INVOICED", "PAID", name="commissionstatus"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_commissions_id", "commissions", ["id"], unique=False)
    op.create_index("ix_commissions_agent_id", "commissions", ["agent_id"], unique=False)
    op.create_index("ix_commissions_status", "commissions", ["status"], unique=False)
    op.create_index("ix_commissions_property_id", "commissions", ["property_id"], unique=False)

    # --- messages ---
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("property_id", sa.Integer(), nullable=True),
        sa.Column("channel", sa.Enum("EMAIL", "SMS", "PHONE_CALL", "IN_PERSON", "NOTE", name="messagechannel"), nullable=False),
        sa.Column("direction", sa.Enum("OUTBOUND", "INBOUND", name="messagedirection"), nullable=True),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("recipient", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messages_id", "messages", ["id"], unique=False)
    op.create_index("ix_messages_client_id", "messages", ["client_id"], unique=False)
    op.create_index("ix_messages_property_id", "messages", ["property_id"], unique=False)
    op.create_index("ix_messages_channel", "messages", ["channel"], unique=False)
    op.create_index("ix_messages_created_at", "messages", ["created_at"], unique=False)

    # --- listings ---
    op.create_table(
        "listings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("DRAFT", "ACTIVE", "PENDING", "SOLD", "WITHDRAWN", "EXPIRED", name="listingstatus"), nullable=True),
        sa.Column("list_price", sa.Float(), nullable=False),
        sa.Column("original_price", sa.Float(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("mls_number", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sold_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sold_price", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_listings_id", "listings", ["id"], unique=False)
    op.create_index("ix_listings_property_id", "listings", ["property_id"], unique=False)
    op.create_index("ix_listings_status", "listings", ["status"], unique=False)
    op.create_index("ix_listings_agent_id", "listings", ["agent_id"], unique=False)

    # --- listing_price_changes ---
    op.create_table(
        "listing_price_changes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("old_price", sa.Float(), nullable=False),
        sa.Column("new_price", sa.Float(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_listing_price_changes_id", "listing_price_changes", ["id"], unique=False)
    op.create_index("ix_listing_price_changes_listing_id", "listing_price_changes", ["listing_id"], unique=False)


def downgrade() -> None:
    op.drop_table("listing_price_changes")
    op.drop_table("listings")
    op.drop_table("messages")
    op.drop_table("commissions")
    op.drop_table("property_media")
    op.drop_table("transaction_milestones")
    op.drop_table("transactions")
    op.drop_table("showings")
    op.drop_table("clients")
