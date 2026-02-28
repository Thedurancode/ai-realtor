"""Analytics Alert Models

Alert rules for monitoring analytics data and triggering notifications.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
import enum

from app.database import Base


class AlertType(str, enum.Enum):
    """Types of analytics alerts"""
    traffic_drop = "traffic_drop"
    traffic_spike = "traffic_spike"
    conversion_drop = "conversion_drop"
    goal_achieved = "goal_achieved"
    goal_missed = "goal_missed"
    custom_metric = "custom_metric"
    daily_summary = "daily_summary"
    weekly_summary = "weekly_summary"


class AlertStatus(str, enum.Enum):
    """Alert trigger status"""
    pending = "pending"
    triggered = "triggered"
    resolved = "resolved"
    snoozed = "snoozed"
    disabled = "disabled"


class AlertOperator(str, enum.Enum):
    """Comparison operators for alert conditions"""
    greater_than = "greater_than"
    less_than = "less_than"
    equals = "equals"
    percentage_change = "percentage_change"
    percentage_drop = "percentage_drop"
    percentage_increase = "percentage_increase"


class AnalyticsAlertRule(Base):
    """Alert rules for monitoring analytics metrics"""

    __tablename__ = "analytics_alert_rules"
    __table_args__ = (
        Index("ix_alert_rules_agent_id", "agent_id"),
        Index("ix_alert_rules_type", "alert_type"),
        Index("ix_alert_rules_status", "status"),
        Index("ix_alert_rules_enabled", "enabled"),
    )

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)

    # Alert configuration
    name = Column(String(255), nullable=False)
    description = Column(Text(), nullable=True)
    alert_type = Column(SQLEnum(AlertType), nullable=False, index=True)

    # Metric to monitor
    metric_name = Column(String(100), nullable=False)  # e.g., "property_views", "conversion_rate"
    metric_dimension = Column(String(100), nullable=True)  # e.g., "utm_source", "city"

    # Condition
    operator = Column(SQLEnum(AlertOperator), nullable=False)
    threshold_value = Column(Integer(), nullable=True)  # For absolute thresholds
    threshold_percent = Column(Integer(), nullable=True)  # For percentage thresholds
    time_window_minutes = Column(Integer(), nullable=False, default=60)  # Lookback period

    # Goals (for goal-related alerts)
    goal_target = Column(Integer(), nullable=True)
    goal_deadline = Column(DateTime(timezone=True), nullable=True)

    # State
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.pending, index=True)
    enabled = Column(Boolean(), default=True, index=True)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    last_resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Notification settings
    notification_channels = Column(JSON(), nullable=False)  # ["email", "slack", "webhook"]
    notification_cooldown_minutes = Column(Integer(), default=60)  # Don't spam
    notification_recipients = Column(JSON(), nullable=True)  # {"email": ["a@b.com"], "slack": "#channel"}

    # Webhook configuration
    webhook_url = Column(String(500), nullable=True)
    webhook_headers = Column(JSON(), nullable=True)

    # Metadata
    severity = Column(String(20), nullable=False, default="medium")  # low, medium, high, critical
    tags = Column(JSON(), nullable=True)  # ["marketing", "sales", "urgent"]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    agent = relationship("Agent", back_populates="analytics_alerts")
    trigger_history = relationship("AnalyticsAlertTrigger", back_populates="alert_rule", cascade="all, delete-orphan")


class AnalyticsAlertTrigger(Base):
    """History of triggered alerts"""

    __tablename__ = "analytics_alert_triggers"
    __table_args__ = (
        Index("ix_alert_triggers_rule_id", "alert_rule_id"),
        Index("ix_alert_triggers_created_at", "created_at"),
        Index("ix_alert_triggers_status", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    alert_rule_id = Column(Integer, ForeignKey("analytics_alert_rules.id"), nullable=False, index=True)

    # Trigger details
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.triggered, index=True)
    metric_value = Column(Integer(), nullable=False)
    threshold_value = Column(Integer(), nullable=False)
    deviation_percent = Column(Integer(), nullable=True)  # How much it deviated from threshold
    message = Column(Text(), nullable=False)  # Human-readable explanation

    # Context
    context = Column(JSON(), nullable=True)  # Additional data for debugging
    comparison_period_start = Column(DateTime(timezone=True), nullable=True)
    comparison_period_end = Column(DateTime(timezone=True), nullable=True)

    # Notification status
    notifications_sent = Column(JSON(), nullable=True)  # {"email": true, "slack": false, "webhook": "error: ..."}
    notification_sent_at = Column(DateTime(timezone=True), nullable=True)

    # Resolution
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_note = Column(Text(), nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    alert_rule = relationship("AnalyticsAlertRule", back_populates="trigger_history")


class AlertSubscription(Base):
    """Users subscribed to receive alerts"""

    __tablename__ = "alert_subscriptions"
    __table_args__ = (
        Index("ix_alert_subscriptions_agent_id", "agent_id"),
        Index("ix_alert_subscriptions_channel", "channel"),
    )

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)

    # Subscription details
    channel = Column(String(50), nullable=False, index=True)  # email, slack, webhook
    destination = Column(String(500), nullable=False)  # email@address.com, #slack-channel, https://webhook.url
    enabled = Column(Boolean(), default=True)

    # Filtering
    alert_types = Column(JSON(), nullable=True)  # Only subscribe to specific alert types
    min_severity = Column(String(20), nullable=True)  # Only receive medium+ alerts

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    agent = relationship("Agent", back_populates="alert_subscriptions")
