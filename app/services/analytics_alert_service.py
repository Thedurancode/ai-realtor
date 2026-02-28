"""
Analytics Alert Service

Monitors analytics metrics and triggers alerts based on configured rules.
Supports email, Slack, and webhook notifications.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import httpx
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from app.models.analytics_alert import (
    AnalyticsAlertRule,
    AnalyticsAlertTrigger,
    AlertType,
    AlertStatus,
    AlertOperator,
)
from app.models.analytics_event import AnalyticsEvent
from app.models.property import Property
from app.services.analytics_service import AnalyticsService


class AnalyticsAlertService:
    """Monitor analytics and trigger alerts"""

    def __init__(self, db: Session):
        self.db = db

    def check_alert_rules(self, agent_id: Optional[int] = None) -> List[AnalyticsAlertTrigger]:
        """
        Check all enabled alert rules and trigger if conditions are met.

        Args:
            agent_id: Optional agent ID to filter rules. If None, checks all agents.

        Returns:
            List of triggered alerts
        """
        # Get enabled rules
        query = self.db.query(AnalyticsAlertRule).filter(
            and_(
                AnalyticsAlertRule.enabled == True,
                or_(
                    AnalyticsAlertRule.status == AlertStatus.pending,
                    AnalyticsAlertRule.status == AlertStatus.resolved,
                    AnalyticsAlertRule.status == AlertStatus.triggered,
                )
            )
        )

        if agent_id:
            query = query.filter(AnalyticsAlertRule.agent_id == agent_id)

        rules = query.all()
        triggered_alerts = []

        for rule in rules:
            # Skip if recently triggered (within cooldown)
            if rule.status == AlertStatus.triggered and rule.last_triggered_at:
                cooldown_end = rule.last_triggered_at + timedelta(minutes=rule.notification_cooldown_minutes)
                if datetime.now(timezone.utc) < cooldown_end:
                    continue

            trigger = self._check_rule(rule)
            if trigger:
                triggered_alerts.append(trigger)
                self.db.add(trigger)

        self.db.commit()
        return triggered_alerts

    def _check_rule(self, rule: AnalyticsAlertRule) -> Optional[AnalyticsAlertTrigger]:
        """Check if a single rule should trigger"""

        # Skip if recently triggered (within cooldown)
        if rule.last_triggered_at:
            cooldown_end = rule.last_triggered_at + timedelta(minutes=rule.notification_cooldown_minutes)
            if datetime.now(timezone.utc) < cooldown_end:
                return None

        # Calculate metric values
        current_value, previous_value = self._get_metric_values(rule)

        if current_value is None:
            return None

        # Check if condition is met
        should_trigger, deviation = self._evaluate_condition(rule, current_value, previous_value)

        if should_trigger:
            # Create trigger record
            trigger = AnalyticsAlertTrigger(
                alert_rule_id=rule.id,
                status=AlertStatus.triggered,
                metric_value=current_value,
                threshold_value=rule.threshold_value or rule.threshold_percent or 0,
                deviation_percent=deviation,
                message=self._build_alert_message(rule, current_value, deviation),
                context={
                    "current_value": current_value,
                    "previous_value": previous_value,
                    "rule_name": rule.name,
                    "metric_name": rule.metric_name,
                },
                created_at=datetime.now(timezone.utc),
            )

            # Update rule state
            rule.last_triggered_at = datetime.now(timezone.utc)
            rule.status = AlertStatus.triggered

            # Send notifications
            self._send_notifications(rule, trigger)

            return trigger

        return None

    def _get_metric_values(self, rule: AnalyticsAlertRule) -> tuple[Optional[int], Optional[int]]:
        """
        Get current and previous metric values for comparison.

        Returns:
            (current_value, previous_value)
        """
        time_window = timedelta(minutes=rule.time_window_minutes)
        now = datetime.now(timezone.utc)
        current_start = now - time_window
        previous_start = current_start - time_window

        if rule.metric_name == "property_views":
            current = self.db.query(func.count(AnalyticsEvent.id)).filter(
                and_(
                    AnalyticsEvent.agent_id == rule.agent_id,
                    AnalyticsEvent.event_type == "property_view",
                    AnalyticsEvent.created_at >= current_start
                )
            ).scalar()

            previous = self.db.query(func.count(AnalyticsEvent.id)).filter(
                and_(
                    AnalyticsEvent.agent_id == rule.agent_id,
                    AnalyticsEvent.event_type == "property_view",
                    AnalyticsEvent.created_at >= previous_start,
                    AnalyticsEvent.created_at < current_start
                )
            ).scalar()

            return current or 0, previous or 0

        elif rule.metric_name == "conversion_rate":
            # Get from analytics service
            analytics = AnalyticsService()
            current_data = analytics.get_dashboard_overview(self.db, rule.agent_id, days=1)
            previous_data = analytics.get_dashboard_overview(self.db, rule.agent_id, days=2)

            current_rate = current_data.get("conversion_rate", 0)
            previous_rate = previous_data.get("conversion_rate", 0)

            return int(current_rate), int(previous_rate)

        elif rule.metric_name == "leads_created":
            current = self.db.query(func.count(AnalyticsEvent.id)).filter(
                and_(
                    AnalyticsEvent.agent_id == rule.agent_id,
                    AnalyticsEvent.event_type == "lead_created",
                    AnalyticsEvent.created_at >= current_start
                )
            ).scalar()

            previous = self.db.query(func.count(AnalyticsEvent.id)).filter(
                and_(
                    AnalyticsEvent.agent_id == rule.agent_id,
                    AnalyticsEvent.event_type == "lead_created",
                    AnalyticsEvent.created_at >= previous_start,
                    AnalyticsEvent.created_at < current_start
                )
            ).scalar()

            return current or 0, previous or 0

        elif rule.metric_name == "active_properties":
            current = self.db.query(func.count(Property.id)).filter(
                and_(
                    Property.agent_id == rule.agent_id,
                    Property.status != "complete"
                )
            ).scalar()

            return current or 0, None  # No previous value for this metric

        return None, None

    def _evaluate_condition(
        self,
        rule: AnalyticsAlertRule,
        current_value: int,
        previous_value: Optional[int]
    ) -> tuple[bool, Optional[int]]:
        """
        Evaluate if alert condition is met.

        Returns:
            (should_trigger, deviation_percent)
        """
        if previous_value is None or previous_value == 0:
            # No previous value or division by zero
            if rule.operator in [AlertOperator.greater_than, AlertOperator.less_than]:
                return self._evaluate_absolute(rule, current_value), None
            return False, None

        deviation = int((current_value - previous_value) / previous_value * 100)

        if rule.operator == AlertOperator.percentage_drop:
            return deviation <= -rule.threshold_percent, deviation
        elif rule.operator == AlertOperator.percentage_increase:
            return deviation >= rule.threshold_percent, deviation
        elif rule.operator == AlertOperator.percentage_change:
            return abs(deviation) >= rule.threshold_percent, deviation
        elif rule.operator == AlertOperator.greater_than:
            return current_value > rule.threshold_value, None
        elif rule.operator == AlertOperator.less_than:
            return current_value < rule.threshold_value, None
        elif rule.operator == AlertOperator.equals:
            return current_value == rule.threshold_value, None

        return False, None

    def _evaluate_absolute(self, rule: AnalyticsAlertRule, current_value: int) -> bool:
        """Evaluate absolute threshold conditions"""
        if rule.operator == AlertOperator.greater_than:
            return current_value > rule.threshold_value
        elif rule.operator == AlertOperator.less_than:
            return current_value < rule.threshold_value
        elif rule.operator == AlertOperator.equals:
            return current_value == rule.threshold_value
        return False

    def _build_alert_message(self, rule: AnalyticsAlertRule, current_value: int, deviation: Optional[int]) -> str:
        """Build human-readable alert message"""
        if deviation is not None:
            direction = "decreased" if deviation < 0 else "increased"
            return (
                f"Alert: {rule.name}\n"
                f"Your {rule.metric_name} has {direction} by {abs(deviation)}% "
                f"(current: {current_value})."
            )
        else:
            return (
                f"Alert: {rule.name}\n"
                f"Your {rule.metric_name} is {current_value} "
                f"(threshold: {rule.threshold_value})."
            )

    def _send_notifications(self, rule: AnalyticsAlertRule, trigger: AnalyticsAlertTrigger):
        """Send notifications via configured channels"""
        notifications_sent = {}

        for channel in rule.notification_channels:
            try:
                if channel == "email":
                    success = self._send_email_notification(rule, trigger)
                elif channel == "slack":
                    success = self._send_slack_notification(rule, trigger)
                elif channel == "webhook":
                    success = self._send_webhook_notification(rule, trigger)
                else:
                    success = False

                notifications_sent[channel] = success

                if success:
                    trigger.notification_sent_at = datetime.now(timezone.utc)

            except Exception as e:
                notifications_sent[channel] = f"error: {str(e)}"

        trigger.notifications_sent = notifications_sent

    def _send_email_notification(self, rule: AnalyticsAlertRule, trigger: AnalyticsAlertTrigger) -> bool:
        """Send email notification via Resend"""
        from app.services.email_service import email_service

        # Get email recipients from notification_recipients
        if not rule.notification_recipients:
            print("⚠️ No email recipients configured")
            return False

        recipients = rule.notification_recipients.get("email")
        if not recipients:
            print("⚠️ No email recipients in notification_recipients.email")
            return False

        # Normalize to list
        if isinstance(recipients, str):
            recipients = [recipients]

        # Get additional context for the email
        additional_context = trigger.context.copy() if trigger.context else None
        additional_context["rule_id"] = rule.id
        additional_context["threshold"] = rule.threshold_value or rule.threshold_percent

        # Send the alert email
        return email_service.send_alert_notification(
            to=recipients,
            alert_name=rule.name,
            alert_message=trigger.message,
            metric_name=rule.metric_name,
            metric_value=trigger.metric_value,
            severity=rule.severity,
            additional_context=additional_context
        )

    def _send_slack_notification(self, rule: AnalyticsAlertRule, trigger: AnalyticsAlertTrigger) -> bool:
        """Send Slack notification"""
        webhook_url = rule.notification_recipients.get("slack") if rule.notification_recipients else None

        if not webhook_url:
            return False

        message = {
            "text": f"🚨 *{rule.name}*",
            "attachments": [{
                "color": "danger" if rule.severity == "critical" else "warning",
                "title": rule.name,
                "text": trigger.message,
                "fields": [
                    {"title": "Metric", "value": rule.metric_name, "short": True},
                    {"title": "Current Value", "value": str(trigger.metric_value), "short": True},
                    {"title": "Severity", "value": rule.severity, "short": True},
                ],
                "footer": "AI Realtor Analytics",
                "ts": int(datetime.now(timezone.utc).timestamp())
            }]
        }

        try:
            response = httpx.post(webhook_url, json=message, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Slack notification failed: {e}")
            return False

    def _send_webhook_notification(self, rule: AnalyticsAlertRule, trigger: AnalyticsAlertTrigger) -> bool:
        """Send webhook notification"""
        webhook_url = rule.webhook_url
        if not webhook_url:
            return False

        payload = {
            "alert_id": trigger.id,
            "rule_id": rule.id,
            "rule_name": rule.name,
            "alert_type": rule.alert_type.value,
            "severity": rule.severity,
            "metric_name": rule.metric_name,
            "metric_value": trigger.metric_value,
            "threshold_value": trigger.threshold_value,
            "deviation_percent": trigger.deviation_percent,
            "message": trigger.message,
            "context": trigger.context,
            "triggered_at": datetime.now(timezone.utc).isoformat(),
        }

        headers = rule.webhook_headers or {}

        try:
            response = httpx.post(webhook_url, json=payload, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Webhook notification failed: {e}")
            return False

    def generate_daily_summary(self, agent_id: int) -> Dict[str, Any]:
        """Generate daily analytics summary for notifications"""
        analytics = AnalyticsService()
        overview = analytics.get_dashboard_overview(self.db, agent_id, days=1)
        trend = analytics.get_events_trend(self.db, agent_id, days=7)

        return {
            "agent_id": agent_id,
            "date": datetime.now(timezone.utc).date().isoformat(),
            "overview": overview,
            "trend": trend,
            "top_properties": analytics.get_top_properties(self.db, agent_id, days=1, limit=5),
            "traffic_sources": analytics.get_traffic_sources(self.db, agent_id, days=1)[:5],
        }

    def generate_weekly_summary(self, agent_id: int) -> Dict[str, Any]:
        """Generate weekly analytics summary for notifications"""
        analytics = AnalyticsService()
        overview = analytics.get_dashboard_overview(self.db, agent_id, days=7)
        previous_overview = analytics.get_dashboard_overview(self.db, agent_id, days=14)

        week_change = {}
        for key in ["property_views", "leads_created", "conversions"]:
            current = overview.get(key, 0)
            previous = previous_overview.get(key, 0)
            if previous > 0:
                change = int((current - previous) / previous * 100)
                week_change[f"{key}_change_percent"] = change

        return {
            "agent_id": agent_id,
            "week_start": (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat(),
            "week_end": datetime.now(timezone.utc).date().isoformat(),
            "overview": overview,
            "week_over_week_change": week_change,
            "top_properties": analytics.get_top_properties(self.db, agent_id, days=7, limit=10),
            "traffic_sources": analytics.get_traffic_sources(self.db, agent_id, days=7),
            "geo_distribution": analytics.get_geo_distribution(self.db, agent_id, days=7)[:10],
        }

    def send_daily_summary_email(
        self,
        agent_id: int,
        recipient_email: str,
        agent_name: Optional[str] = None
    ) -> bool:
        """
        Generate and send daily analytics summary email.

        Args:
            agent_id: Agent ID to generate summary for
            recipient_email: Email address to send summary to
            agent_name: Agent's name (optional, will query if not provided)

        Returns:
            True if sent successfully
        """
        from app.services.email_service import email_service
        from app.models.agent import Agent

        # Get agent name if not provided
        if not agent_name:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            agent_name = agent.name if agent else "Agent"

        # Generate summary
        summary = self.generate_daily_summary(agent_id)

        # Send email
        return email_service.send_daily_summary(
            to=recipient_email,
            agent_name=agent_name,
            summary=summary
        )

    def send_weekly_summary_email(
        self,
        agent_id: int,
        recipient_email: str,
        agent_name: Optional[str] = None
    ) -> bool:
        """
        Generate and send weekly analytics summary email.

        Args:
            agent_id: Agent ID to generate summary for
            recipient_email: Email address to send summary to
            agent_name: Agent's name (optional, will query if not provided)

        Returns:
            True if sent successfully
        """
        from app.services.email_service import email_service
        from app.models.agent import Agent

        # Get agent name if not provided
        if not agent_name:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            agent_name = agent.name if agent else "Agent"

        # Generate summary
        summary = self.generate_weekly_summary(agent_id)

        # Send email
        return email_service.send_weekly_summary(
            to=recipient_email,
            agent_name=agent_name,
            summary=summary
        )

    def create_default_alerts(self, agent_id: int) -> List[AnalyticsAlertRule]:
        """Create default alert rules for a new agent"""
        defaults = [
            AnalyticsAlertRule(
                agent_id=agent_id,
                name="Traffic Drop Alert",
                description="Alert when property views drop by 50% or more",
                alert_type=AlertType.traffic_drop,
                metric_name="property_views",
                operator=AlertOperator.percentage_drop,
                threshold_percent=50,
                time_window_minutes=60,
                notification_channels=["email"],
                severity="high",
                tags=["traffic", "urgent"],
            ),
            AnalyticsAlertRule(
                agent_id=agent_id,
                name="Conversion Rate Alert",
                description="Alert when conversion rate drops below 2%",
                alert_type=AlertType.conversion_drop,
                metric_name="conversion_rate",
                operator=AlertOperator.less_than,
                threshold_value=2,
                time_window_minutes=60,
                notification_channels=["email"],
                severity="medium",
                tags=["conversions"],
            ),
            AnalyticsAlertRule(
                agent_id=agent_id,
                name="Daily Summary",
                description="Daily analytics summary at 9 AM",
                alert_type=AlertType.daily_summary,
                metric_name="property_views",
                operator=AlertOperator.greater_than,
                threshold_value=0,
                time_window_minutes=1440,  # 24 hours
                notification_channels=["email"],
                severity="low",
                tags=["summary", "scheduled"],
            ),
        ]

        for rule in defaults:
            self.db.add(rule)

        self.db.commit()
        return defaults
