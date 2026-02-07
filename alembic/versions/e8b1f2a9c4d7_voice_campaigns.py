"""voice campaigns

Revision ID: e8b1f2a9c4d7
Revises: d4f9b2c1e8a7
Create Date: 2026-02-07 13:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e8b1f2a9c4d7"
down_revision: Union[str, None] = "d4f9b2c1e8a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "voice_campaigns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("call_purpose", sa.String(length=64), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=True),
        sa.Column("contact_roles", sa.JSON(), nullable=True),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("retry_delay_minutes", sa.Integer(), nullable=False),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=False),
        sa.Column("assistant_overrides", sa.JSON(), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_voice_campaigns_id"), "voice_campaigns", ["id"], unique=False)
    op.create_index(op.f("ix_voice_campaigns_property_id"), "voice_campaigns", ["property_id"], unique=False)
    op.create_index(op.f("ix_voice_campaigns_status"), "voice_campaigns", ["status"], unique=False)

    op.create_table(
        "voice_campaign_targets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=True),
        sa.Column("property_id", sa.Integer(), nullable=True),
        sa.Column("contact_name", sa.String(length=255), nullable=True),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempts_made", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_call_id", sa.String(length=128), nullable=True),
        sa.Column("last_call_status", sa.String(length=64), nullable=True),
        sa.Column("last_disposition", sa.String(length=64), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_webhook_payload", sa.JSON(), nullable=True),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["campaign_id"], ["voice_campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campaign_id", "phone_number", name="uq_campaign_target_phone"),
    )
    op.create_index(op.f("ix_voice_campaign_targets_id"), "voice_campaign_targets", ["id"], unique=False)
    op.create_index(op.f("ix_voice_campaign_targets_campaign_id"), "voice_campaign_targets", ["campaign_id"], unique=False)
    op.create_index(op.f("ix_voice_campaign_targets_contact_id"), "voice_campaign_targets", ["contact_id"], unique=False)
    op.create_index(op.f("ix_voice_campaign_targets_property_id"), "voice_campaign_targets", ["property_id"], unique=False)
    op.create_index(op.f("ix_voice_campaign_targets_status"), "voice_campaign_targets", ["status"], unique=False)
    op.create_index(op.f("ix_voice_campaign_targets_next_attempt_at"), "voice_campaign_targets", ["next_attempt_at"], unique=False)
    op.create_index(op.f("ix_voice_campaign_targets_last_call_id"), "voice_campaign_targets", ["last_call_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_voice_campaign_targets_last_call_id"), table_name="voice_campaign_targets")
    op.drop_index(op.f("ix_voice_campaign_targets_next_attempt_at"), table_name="voice_campaign_targets")
    op.drop_index(op.f("ix_voice_campaign_targets_status"), table_name="voice_campaign_targets")
    op.drop_index(op.f("ix_voice_campaign_targets_property_id"), table_name="voice_campaign_targets")
    op.drop_index(op.f("ix_voice_campaign_targets_contact_id"), table_name="voice_campaign_targets")
    op.drop_index(op.f("ix_voice_campaign_targets_campaign_id"), table_name="voice_campaign_targets")
    op.drop_index(op.f("ix_voice_campaign_targets_id"), table_name="voice_campaign_targets")
    op.drop_table("voice_campaign_targets")

    op.drop_index(op.f("ix_voice_campaigns_status"), table_name="voice_campaigns")
    op.drop_index(op.f("ix_voice_campaigns_property_id"), table_name="voice_campaigns")
    op.drop_index(op.f("ix_voice_campaigns_id"), table_name="voice_campaigns")
    op.drop_table("voice_campaigns")
