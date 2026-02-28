"""add analytics alerts

Revision ID: 20260228_add_analytics_alerts
Revises: add_analytics_dashboard
Create Date: 2026-02-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'add_analytics_alerts'
down_revision = 'add_analytics_dashboard'


def upgrade() -> None:
    # Create analytics_alert_rules table
    op.create_table(
        'analytics_alert_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('alert_type', sa.Enum('traffic_drop', 'traffic_spike', 'conversion_drop', 'goal_achieved', 'goal_missed', 'custom_metric', 'daily_summary', 'weekly_summary', name='alerttype'), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_dimension', sa.String(length=100), nullable=True),
        sa.Column('operator', sa.Enum('greater_than', 'less_than', 'equals', 'percentage_change', 'percentage_drop', 'percentage_increase', name='alertoperator'), nullable=False),
        sa.Column('threshold_value', sa.Integer(), nullable=True),
        sa.Column('threshold_percent', sa.Integer(), nullable=True),
        sa.Column('time_window_minutes', sa.Integer(), nullable=False),
        sa.Column('goal_target', sa.Integer(), nullable=True),
        sa.Column('goal_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('pending', 'triggered', 'resolved', 'snoozed', 'disabled', name='alertstatus'), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notification_channels', postgresql.JSON(), nullable=False),
        sa.Column('notification_cooldown_minutes', sa.Integer(), nullable=False),
        sa.Column('notification_recipients', postgresql.JSON(), nullable=True),
        sa.Column('webhook_url', sa.String(length=500), nullable=True),
        sa.Column('webhook_headers', postgresql.JSON(), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alert_rules_agent_id', 'analytics_alert_rules', ['agent_id'], unique=False)
    op.create_index('ix_alert_rules_enabled', 'analytics_alert_rules', ['enabled'], unique=False)
    op.create_index('ix_alert_rules_status', 'analytics_alert_rules', ['status'], unique=False)
    op.create_index('ix_alert_rules_type', 'analytics_alert_rules', ['alert_type'], unique=False)

    # Create analytics_alert_triggers table
    op.create_table(
        'analytics_alert_triggers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_rule_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'triggered', 'resolved', 'snoozed', 'disabled', name='alertstatus'), nullable=True),
        sa.Column('metric_value', sa.Integer(), nullable=False),
        sa.Column('threshold_value', sa.Integer(), nullable=False),
        sa.Column('deviation_percent', sa.Integer(), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('context', postgresql.JSON(), nullable=True),
        sa.Column('comparison_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('comparison_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notifications_sent', postgresql.JSON(), nullable=True),
        sa.Column('notification_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['alert_rule_id'], ['analytics_alert_rules.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alert_triggers_created_at', 'analytics_alert_triggers', ['created_at'], unique=False)
    op.create_index('ix_alert_triggers_rule_id', 'analytics_alert_triggers', ['alert_rule_id'], unique=False)
    op.create_index('ix_alert_triggers_status', 'analytics_alert_triggers', ['status'], unique=False)

    # Create alert_subscriptions table
    op.create_table(
        'alert_subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('destination', sa.String(length=500), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('alert_types', postgresql.JSON(), nullable=True),
        sa.Column('min_severity', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alert_subscriptions_agent_id', 'alert_subscriptions', ['agent_id'], unique=False)
    op.create_index('ix_alert_subscriptions_channel', 'alert_subscriptions', ['channel'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_index('ix_alert_subscriptions_channel', 'alert_subscriptions')
    op.drop_index('ix_alert_subscriptions_agent_id', 'alert_subscriptions')
    op.drop_table('alert_subscriptions')

    op.drop_index('ix_alert_triggers_status', 'analytics_alert_triggers')
    op.drop_index('ix_alert_triggers_rule_id', 'analytics_alert_triggers')
    op.drop_index('ix_alert_triggers_created_at', 'analytics_alert_triggers')
    op.drop_table('analytics_alert_triggers')

    op.drop_index('ix_alert_rules_type', 'analytics_alert_rules')
    op.drop_index('ix_alert_rules_status', 'analytics_alert_rules')
    op.drop_index('ix_alert_rules_enabled', 'analytics_alert_rules')
    op.drop_index('ix_alert_rules_agent_id', 'analytics_alert_rules')
    op.drop_table('analytics_alert_rules')
