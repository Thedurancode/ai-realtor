"""Add indexes, soft delete columns for research data

Revision ID: d1e2f3a4b5c6
Revises: c8d2e4f5a7b9
Create Date: 2026-02-21

Adds performance indexes to frequently queried tables (properties, contracts,
contacts, skip_traces, todos, offers, etc.) and adds is_current/superseded_at
columns to research data models for soft-delete support.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, None] = "c8d2e4f5a7b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Properties indexes ──
    op.create_index("ix_properties_agent_id", "properties", ["agent_id"])
    op.create_index("ix_properties_status", "properties", ["status"])
    op.create_index("ix_properties_pipeline_status", "properties", ["pipeline_status"])
    op.create_index("ix_properties_agent_status", "properties", ["agent_id", "status"])
    op.create_index("ix_properties_created_at", "properties", ["created_at"])
    op.create_index("ix_properties_state_city", "properties", ["state", "city"])

    # ── Contracts indexes ──
    op.create_index("ix_contracts_property_id", "contracts", ["property_id"])
    op.create_index("ix_contracts_status", "contracts", ["status"])
    op.create_index("ix_contracts_property_status", "contracts", ["property_id", "status"])
    op.create_index("ix_contracts_created_at", "contracts", ["created_at"])

    # ── Contacts indexes ──
    op.create_index("ix_contacts_property_id", "contacts", ["property_id"])
    op.create_index("ix_contacts_role", "contacts", ["role"])
    op.create_index("ix_contacts_property_role", "contacts", ["property_id", "role"])

    # ── Skip traces indexes ──
    op.create_index("ix_skip_traces_property_id", "skip_traces", ["property_id"])
    op.create_index("ix_skip_traces_created_at", "skip_traces", ["created_at"])

    # ── Todos indexes ──
    op.create_index("ix_todos_property_id", "todos", ["property_id"])
    op.create_index("ix_todos_status", "todos", ["status"])
    op.create_index("ix_todos_property_status", "todos", ["property_id", "status"])
    op.create_index("ix_todos_due_date", "todos", ["due_date"])
    op.create_index("ix_todos_priority_created", "todos", ["priority", "created_at"])

    # ── Offers indexes ──
    op.create_index("ix_offers_status", "offers", ["status"])
    op.create_index("ix_offers_property_status", "offers", ["property_id", "status"])

    # ── Zillow enrichments index ──
    op.create_index("ix_zillow_enrichments_property_id", "zillow_enrichments", ["property_id"])

    # ── Property notes indexes ──
    op.create_index("ix_property_notes_property_id", "property_notes", ["property_id"])
    op.create_index("ix_property_notes_created_at", "property_notes", ["created_at"])

    # ── Research indexes ──
    op.create_index("ix_research_property_id", "research", ["property_id"])
    op.create_index("ix_research_status", "research", ["status"])
    op.create_index("ix_research_agent_id", "research", ["agent_id"])

    # ── Agent conversations indexes ──
    op.create_index("ix_agent_conversations_property_id", "agent_conversations", ["property_id"])
    op.create_index("ix_agent_conversations_agent_id", "agent_conversations", ["agent_id"])
    op.create_index("ix_agent_conversations_status", "agent_conversations", ["status"])

    # ── Compliance checks index ──
    op.create_index("ix_compliance_checks_property_id", "compliance_checks", ["property_id"])

    # ── Contract submitters indexes ──
    op.create_index("ix_contract_submitters_contract_id", "contract_submitters", ["contract_id"])
    op.create_index("ix_contract_submitters_contact_id", "contract_submitters", ["contact_id"])

    # ── Soft delete columns for research data ──
    op.add_column("comps_sales", sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("comps_sales", sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_comps_sales_current", "comps_sales", ["job_id", "is_current"])

    op.add_column("comps_rentals", sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("comps_rentals", sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_comps_rentals_current", "comps_rentals", ["job_id", "is_current"])

    op.add_column("underwriting", sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("underwriting", sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_underwriting_current", "underwriting", ["job_id", "is_current"])

    op.add_column("risk_scores", sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("risk_scores", sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_risk_scores_current", "risk_scores", ["job_id", "is_current"])

    op.add_column("dossiers", sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("dossiers", sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_dossiers_current", "dossiers", ["job_id", "is_current"])


def downgrade() -> None:
    # ── Drop soft delete columns ──
    op.drop_index("ix_dossiers_current", "dossiers")
    op.drop_column("dossiers", "superseded_at")
    op.drop_column("dossiers", "is_current")

    op.drop_index("ix_risk_scores_current", "risk_scores")
    op.drop_column("risk_scores", "superseded_at")
    op.drop_column("risk_scores", "is_current")

    op.drop_index("ix_underwriting_current", "underwriting")
    op.drop_column("underwriting", "superseded_at")
    op.drop_column("underwriting", "is_current")

    op.drop_index("ix_comps_rentals_current", "comps_rentals")
    op.drop_column("comps_rentals", "superseded_at")
    op.drop_column("comps_rentals", "is_current")

    op.drop_index("ix_comps_sales_current", "comps_sales")
    op.drop_column("comps_sales", "superseded_at")
    op.drop_column("comps_sales", "is_current")

    # ── Drop contract submitters indexes ──
    op.drop_index("ix_contract_submitters_contact_id", "contract_submitters")
    op.drop_index("ix_contract_submitters_contract_id", "contract_submitters")

    # ── Drop compliance checks index ──
    op.drop_index("ix_compliance_checks_property_id", "compliance_checks")

    # ── Drop agent conversations indexes ──
    op.drop_index("ix_agent_conversations_status", "agent_conversations")
    op.drop_index("ix_agent_conversations_agent_id", "agent_conversations")
    op.drop_index("ix_agent_conversations_property_id", "agent_conversations")

    # ── Drop research indexes ──
    op.drop_index("ix_research_agent_id", "research")
    op.drop_index("ix_research_status", "research")
    op.drop_index("ix_research_property_id", "research")

    # ── Drop property notes indexes ──
    op.drop_index("ix_property_notes_created_at", "property_notes")
    op.drop_index("ix_property_notes_property_id", "property_notes")

    # ── Drop zillow enrichments index ──
    op.drop_index("ix_zillow_enrichments_property_id", "zillow_enrichments")

    # ── Drop offers indexes ──
    op.drop_index("ix_offers_property_status", "offers")
    op.drop_index("ix_offers_status", "offers")

    # ── Drop todos indexes ──
    op.drop_index("ix_todos_priority_created", "todos")
    op.drop_index("ix_todos_due_date", "todos")
    op.drop_index("ix_todos_property_status", "todos")
    op.drop_index("ix_todos_status", "todos")
    op.drop_index("ix_todos_property_id", "todos")

    # ── Drop skip traces indexes ──
    op.drop_index("ix_skip_traces_created_at", "skip_traces")
    op.drop_index("ix_skip_traces_property_id", "skip_traces")

    # ── Drop contacts indexes ──
    op.drop_index("ix_contacts_property_role", "contacts")
    op.drop_index("ix_contacts_role", "contacts")
    op.drop_index("ix_contacts_property_id", "contacts")

    # ── Drop contracts indexes ──
    op.drop_index("ix_contracts_created_at", "contracts")
    op.drop_index("ix_contracts_property_status", "contracts")
    op.drop_index("ix_contracts_status", "contracts")
    op.drop_index("ix_contracts_property_id", "contracts")

    # ── Drop properties indexes ──
    op.drop_index("ix_properties_state_city", "properties")
    op.drop_index("ix_properties_created_at", "properties")
    op.drop_index("ix_properties_agent_status", "properties")
    op.drop_index("ix_properties_pipeline_status", "properties")
    op.drop_index("ix_properties_status", "properties")
    op.drop_index("ix_properties_agent_id", "properties")
