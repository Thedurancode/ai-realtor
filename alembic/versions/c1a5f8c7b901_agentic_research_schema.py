"""agentic research schema

Revision ID: c1a5f8c7b901
Revises: f838d6185616
Create Date: 2026-02-06 11:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c1a5f8c7b901"
down_revision: Union[str, None] = "f838d6185616"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


agentic_job_status = postgresql.ENUM(
    "PENDING",
    "IN_PROGRESS",
    "COMPLETED",
    "FAILED",
    name="agenticjobstatus",
    create_type=False,
)


def upgrade() -> None:
    postgresql.ENUM(
        "PENDING",
        "IN_PROGRESS",
        "COMPLETED",
        "FAILED",
        name="agenticjobstatus",
        create_type=True,
    ).create(op.get_bind(), checkfirst=True)

    op.create_table(
        "portal_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("url_hash", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("raw_html", sa.Text(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_portal_cache_id"), "portal_cache", ["id"], unique=False)
    op.create_index(op.f("ix_portal_cache_url_hash"), "portal_cache", ["url_hash"], unique=True)

    op.create_table(
        "research_properties",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stable_key", sa.String(length=128), nullable=False),
        sa.Column("raw_address", sa.String(), nullable=False),
        sa.Column("normalized_address", sa.String(), nullable=False),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("state", sa.String(length=2), nullable=True),
        sa.Column("zip_code", sa.String(length=10), nullable=True),
        sa.Column("apn", sa.String(), nullable=True),
        sa.Column("geo_lat", sa.Float(), nullable=True),
        sa.Column("geo_lng", sa.Float(), nullable=True),
        sa.Column("latest_profile", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_research_properties_id"), "research_properties", ["id"], unique=False)
    op.create_index(op.f("ix_research_properties_stable_key"), "research_properties", ["stable_key"], unique=True)

    op.create_table(
        "agentic_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=False),
        sa.Column("research_property_id", sa.Integer(), nullable=False),
        sa.Column("status", agentic_job_status, nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("current_step", sa.String(length=255), nullable=True),
        sa.Column("strategy", sa.String(length=32), nullable=False),
        sa.Column("assumptions", sa.JSON(), nullable=True),
        sa.Column("limits", sa.JSON(), nullable=True),
        sa.Column("results", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["research_property_id"], ["research_properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agentic_jobs_id"), "agentic_jobs", ["id"], unique=False)
    op.create_index(op.f("ix_agentic_jobs_trace_id"), "agentic_jobs", ["trace_id"], unique=True)
    op.create_index(op.f("ix_agentic_jobs_research_property_id"), "agentic_jobs", ["research_property_id"], unique=False)

    op.create_table(
        "evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("research_property_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("claim", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_excerpt", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["agentic_jobs.id"]),
        sa.ForeignKeyConstraint(["research_property_id"], ["research_properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evidence_id"), "evidence", ["id"], unique=False)
    op.create_index(op.f("ix_evidence_job_id"), "evidence", ["job_id"], unique=False)
    op.create_index(op.f("ix_evidence_research_property_id"), "evidence", ["research_property_id"], unique=False)
    op.create_index(op.f("ix_evidence_hash"), "evidence", ["hash"], unique=True)

    op.create_table(
        "comps_sales",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("research_property_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("distance_mi", sa.Float(), nullable=True),
        sa.Column("sale_date", sa.Date(), nullable=True),
        sa.Column("sale_price", sa.Float(), nullable=True),
        sa.Column("sqft", sa.Integer(), nullable=True),
        sa.Column("beds", sa.Integer(), nullable=True),
        sa.Column("baths", sa.Float(), nullable=True),
        sa.Column("year_built", sa.Integer(), nullable=True),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["agentic_jobs.id"]),
        sa.ForeignKeyConstraint(["research_property_id"], ["research_properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_comps_sales_id"), "comps_sales", ["id"], unique=False)
    op.create_index(op.f("ix_comps_sales_job_id"), "comps_sales", ["job_id"], unique=False)
    op.create_index(op.f("ix_comps_sales_research_property_id"), "comps_sales", ["research_property_id"], unique=False)

    op.create_table(
        "comps_rentals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("research_property_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("distance_mi", sa.Float(), nullable=True),
        sa.Column("rent", sa.Float(), nullable=True),
        sa.Column("date_listed", sa.Date(), nullable=True),
        sa.Column("sqft", sa.Integer(), nullable=True),
        sa.Column("beds", sa.Integer(), nullable=True),
        sa.Column("baths", sa.Float(), nullable=True),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["agentic_jobs.id"]),
        sa.ForeignKeyConstraint(["research_property_id"], ["research_properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_comps_rentals_id"), "comps_rentals", ["id"], unique=False)
    op.create_index(op.f("ix_comps_rentals_job_id"), "comps_rentals", ["job_id"], unique=False)
    op.create_index(op.f("ix_comps_rentals_research_property_id"), "comps_rentals", ["research_property_id"], unique=False)

    op.create_table(
        "underwriting",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("research_property_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("strategy", sa.String(length=32), nullable=False),
        sa.Column("assumptions", sa.JSON(), nullable=True),
        sa.Column("arv_low", sa.Float(), nullable=True),
        sa.Column("arv_base", sa.Float(), nullable=True),
        sa.Column("arv_high", sa.Float(), nullable=True),
        sa.Column("rent_low", sa.Float(), nullable=True),
        sa.Column("rent_base", sa.Float(), nullable=True),
        sa.Column("rent_high", sa.Float(), nullable=True),
        sa.Column("rehab_tier", sa.String(length=16), nullable=False),
        sa.Column("rehab_low", sa.Float(), nullable=True),
        sa.Column("rehab_high", sa.Float(), nullable=True),
        sa.Column("offer_low", sa.Float(), nullable=True),
        sa.Column("offer_base", sa.Float(), nullable=True),
        sa.Column("offer_high", sa.Float(), nullable=True),
        sa.Column("fees", sa.JSON(), nullable=True),
        sa.Column("sensitivity", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["agentic_jobs.id"]),
        sa.ForeignKeyConstraint(["research_property_id"], ["research_properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_underwriting_id"), "underwriting", ["id"], unique=False)
    op.create_index(op.f("ix_underwriting_job_id"), "underwriting", ["job_id"], unique=False)
    op.create_index(op.f("ix_underwriting_research_property_id"), "underwriting", ["research_property_id"], unique=False)

    op.create_table(
        "risk_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("research_property_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("title_risk", sa.Float(), nullable=True),
        sa.Column("data_confidence", sa.Float(), nullable=True),
        sa.Column("compliance_flags", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["agentic_jobs.id"]),
        sa.ForeignKeyConstraint(["research_property_id"], ["research_properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_risk_scores_id"), "risk_scores", ["id"], unique=False)
    op.create_index(op.f("ix_risk_scores_job_id"), "risk_scores", ["job_id"], unique=False)
    op.create_index(op.f("ix_risk_scores_research_property_id"), "risk_scores", ["research_property_id"], unique=False)

    op.create_table(
        "dossiers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("research_property_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("markdown", sa.Text(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["agentic_jobs.id"]),
        sa.ForeignKeyConstraint(["research_property_id"], ["research_properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_dossiers_id"), "dossiers", ["id"], unique=False)
    op.create_index(op.f("ix_dossiers_job_id"), "dossiers", ["job_id"], unique=False)
    op.create_index(op.f("ix_dossiers_research_property_id"), "dossiers", ["research_property_id"], unique=False)

    op.create_table(
        "worker_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("worker_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("runtime_ms", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Float(), nullable=False),
        sa.Column("web_calls", sa.Integer(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("unknowns", sa.JSON(), nullable=True),
        sa.Column("errors", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["agentic_jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_worker_runs_id"), "worker_runs", ["id"], unique=False)
    op.create_index(op.f("ix_worker_runs_job_id"), "worker_runs", ["job_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_worker_runs_job_id"), table_name="worker_runs")
    op.drop_index(op.f("ix_worker_runs_id"), table_name="worker_runs")
    op.drop_table("worker_runs")

    op.drop_index(op.f("ix_dossiers_research_property_id"), table_name="dossiers")
    op.drop_index(op.f("ix_dossiers_job_id"), table_name="dossiers")
    op.drop_index(op.f("ix_dossiers_id"), table_name="dossiers")
    op.drop_table("dossiers")

    op.drop_index(op.f("ix_risk_scores_research_property_id"), table_name="risk_scores")
    op.drop_index(op.f("ix_risk_scores_job_id"), table_name="risk_scores")
    op.drop_index(op.f("ix_risk_scores_id"), table_name="risk_scores")
    op.drop_table("risk_scores")

    op.drop_index(op.f("ix_underwriting_research_property_id"), table_name="underwriting")
    op.drop_index(op.f("ix_underwriting_job_id"), table_name="underwriting")
    op.drop_index(op.f("ix_underwriting_id"), table_name="underwriting")
    op.drop_table("underwriting")

    op.drop_index(op.f("ix_comps_rentals_research_property_id"), table_name="comps_rentals")
    op.drop_index(op.f("ix_comps_rentals_job_id"), table_name="comps_rentals")
    op.drop_index(op.f("ix_comps_rentals_id"), table_name="comps_rentals")
    op.drop_table("comps_rentals")

    op.drop_index(op.f("ix_comps_sales_research_property_id"), table_name="comps_sales")
    op.drop_index(op.f("ix_comps_sales_job_id"), table_name="comps_sales")
    op.drop_index(op.f("ix_comps_sales_id"), table_name="comps_sales")
    op.drop_table("comps_sales")

    op.drop_index(op.f("ix_evidence_hash"), table_name="evidence")
    op.drop_index(op.f("ix_evidence_research_property_id"), table_name="evidence")
    op.drop_index(op.f("ix_evidence_job_id"), table_name="evidence")
    op.drop_index(op.f("ix_evidence_id"), table_name="evidence")
    op.drop_table("evidence")

    op.drop_index(op.f("ix_agentic_jobs_research_property_id"), table_name="agentic_jobs")
    op.drop_index(op.f("ix_agentic_jobs_trace_id"), table_name="agentic_jobs")
    op.drop_index(op.f("ix_agentic_jobs_id"), table_name="agentic_jobs")
    op.drop_table("agentic_jobs")

    op.drop_index(op.f("ix_research_properties_stable_key"), table_name="research_properties")
    op.drop_index(op.f("ix_research_properties_id"), table_name="research_properties")
    op.drop_table("research_properties")

    op.drop_index(op.f("ix_portal_cache_url_hash"), table_name="portal_cache")
    op.drop_index(op.f("ix_portal_cache_id"), table_name="portal_cache")
    op.drop_table("portal_cache")

    postgresql.ENUM(
        "PENDING",
        "IN_PROGRESS",
        "COMPLETED",
        "FAILED",
        name="agenticjobstatus",
        create_type=True,
    ).drop(op.get_bind(), checkfirst=True)
