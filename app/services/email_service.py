"""Email Service using Resend API."""

import os
from typing import List, Optional
import resend
from datetime import datetime, timezone

from app.config import settings


class EmailService:
    """Service for sending emails via Resend."""

    def __init__(self):
        """Initialize Resend client with API key from settings."""
        api_key = getattr(settings, 'resend_api_key', None) or os.getenv("RESEND_API_KEY")
        if not api_key:
            print("⚠️ RESEND_API_KEY not set - emails will be disabled")
            self.enabled = False
        else:
            resend.api_key = api_key
            self.enabled = True
            print(f"✓ Resend email service initialized")

    def send_email(
        self,
        to: str | List[str],
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        tags: Optional[List[dict]] = None
    ) -> bool:
        """
        Send an email via Resend.

        Args:
            to: Recipient email address or list of addresses
            subject: Email subject line
            html_content: HTML email body
            from_email: Sender email (must be verified in Resend)
            from_name: Sender display name
            reply_to: Reply-to address
            tags: Email tags for tracking [{"name": "category", "value": "alert"}]

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            print(f"📧 Email disabled: {subject}")
            return False

        try:
            # Default sender from settings
            if not from_email:
                from_email = getattr(settings, 'resend_from_email', None) or os.getenv("RESEND_FROM_EMAIL", "notifications@ai-realtor.com")

            # Build sender name
            if from_name:
                from_address = f"{from_name} <{from_email}>"
            else:
                from_address = from_email

            # Normalize recipients to list
            if isinstance(to, str):
                to = [to]

            params = {
                "from": from_address,
                "to": to,
                "subject": subject,
                "html": html_content,
            }

            # Optional reply-to
            if reply_to:
                params["reply_to"] = reply_to

            # Optional tags
            if tags:
                params["tags"] = tags

            # Send email
            response = resend.Emails.send(params)

            if response.get("id"):
                print(f"✓ Email sent: {subject} -> {', '.join(to)} (ID: {response['id']})")
                return True
            else:
                print(f"❌ Email failed: {response}")
                return False

        except Exception as e:
            print(f"❌ Email error: {e}")
            return False

    def send_alert_notification(
        self,
        to: str | List[str],
        alert_name: str,
        alert_message: str,
        metric_name: str,
        metric_value: int,
        severity: str = "medium",
        additional_context: Optional[dict] = None
    ) -> bool:
        """
        Send an analytics alert notification email.

        Args:
            to: Recipient email(s)
            alert_name: Name of the alert that triggered
            alert_message: Human-readable alert message
            metric_name: Metric that triggered the alert
            metric_value: Current value of the metric
            severity: Alert severity (low, medium, high, critical)
            additional_context: Optional extra context dict

        Returns:
            True if sent successfully
        """
        # Color coding by severity
        severity_colors = {
            "low": "#3b82f6",      # blue
            "medium": "#f59e0b",   # amber
            "high": "#ef4444",     # red
            "critical": "#dc2626"  # dark red
        }
        color = severity_colors.get(severity, "#f59e0b")

        # Build HTML email
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ border-left: 4px solid {color}; padding-left: 16px; margin-bottom: 24px; }}
        .alert-name {{ font-size: 24px; font-weight: bold; margin: 0 0 8px 0; }}
        .severity {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; text-transform: uppercase; background: {color}; color: white; }}
        .message {{ font-size: 16px; line-height: 1.6; color: #374151; margin-bottom: 24px; }}
        .metric-box {{ background: #f9fafb; border-radius: 8px; padding: 16px; margin-bottom: 16px; }}
        .metric-label {{ font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; }}
        .metric-value {{ font-size: 32px; font-weight: bold; color: #111827; }}
        .footer {{ font-size: 12px; color: #9ca3af; margin-top: 32px; padding-top: 16px; border-top: 1px solid #e5e7eb; }}
        .btn {{ display: inline-block; padding: 12px 24px; background: {color}; color: white; text-decoration: none; border-radius: 6px; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="alert-name">{alert_name}</h1>
            <span class="severity">{severity}</span>
        </div>

        <div class="message">
            {alert_message.replace(chr(10), '<br>')}
        </div>

        <div class="metric-box">
            <div class="metric-label">Current {metric_name.replace('_', ' ').title()}</div>
            <div class="metric-value">{metric_value:,}</div>
        </div>
        """

        # Add additional context if provided
        if additional_context:
            html += """
        <div class="metric-box">
            <div class="metric-label">Additional Context</div>
            <div style="font-size: 14px; color: #4b5563;">
            """
            for key, value in additional_context.items():
                html += f"<div><strong>{key.replace('_', ' ').title()}:</strong> {value}</div>"
            html += "</div></div>"

        # Add footer
        html += f"""
        <div class="footer">
            <p>Triggered at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            <p>AI Realtor Analytics Alerts</p>
        </div>
    </div>
</body>
</html>
"""

        subject = f"🚨 {alert_name}"

        # Add tags for tracking
        tags = [
            {"name": "alert_type", "value": "analytics"},
            {"name": "severity", "value": severity},
            {"name": "metric", "value": metric_name}
        ]

        return self.send_email(
            to=to,
            subject=subject,
            html_content=html,
            tags=tags
        )

    def send_daily_summary(
        self,
        to: str | List[str],
        agent_name: str,
        summary: dict
    ) -> bool:
        """
        Send daily analytics summary email.

        Args:
            to: Recipient email(s)
            agent_name: Agent's name
            summary: Daily summary dict with overview, trends, etc.

        Returns:
            True if sent successfully
        """
        overview = summary.get("overview", {})
        trend = summary.get("trend", {})

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 32px; }}
        .header h1 {{ color: #111827; margin: 0; }}
        .date {{ color: #6b7280; font-size: 14px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 24px; }}
        .stat-box {{ background: #f9fafb; border-radius: 8px; padding: 16px; text-align: center; }}
        .stat-label {{ font-size: 12px; color: #6b7280; text-transform: uppercase; }}
        .stat-value {{ font-size: 28px; font-weight: bold; color: #111827; }}
        .footer {{ text-align: center; font-size: 12px; color: #9ca3af; margin-top: 32px; padding-top: 16px; border-top: 1px solid #e5e7eb; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Daily Analytics Summary</h1>
            <p class="date">{datetime.now(timezone.utc).strftime('%A, %B %d, %Y')}</p>
        </div>

        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-label">Property Views</div>
                <div class="stat-value">{overview.get('property_views', 0):,}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Leads Created</div>
                <div class="stat-value">{overview.get('leads_created', 0):,}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Conversions</div>
                <div class="stat-value">{overview.get('conversions', 0):,}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Conversion Rate</div>
                <div class="stat-value">{overview.get('conversion_rate', 0):.1f}%</div>
            </div>
        </div>

        <div class="footer">
            <p>Daily summary for {agent_name}</p>
            <p>AI Realtor Analytics</p>
        </div>
    </div>
</body>
</html>
"""

        return self.send_email(
            to=to,
            subject=f"📊 Daily Analytics Summary - {summary.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))}",
            html_content=html,
            tags=[{"name": "alert_type", "value": "daily_summary"}]
        )

    def send_weekly_summary(
        self,
        to: str | List[str],
        agent_name: str,
        summary: dict
    ) -> bool:
        """
        Send weekly analytics summary email.

        Args:
            to: Recipient email(s)
            agent_name: Agent's name
            summary: Weekly summary dict

        Returns:
            True if sent successfully
        """
        overview = summary.get("overview", {})
        week_change = summary.get("week_over_week_change", {})

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 32px; }}
        .header h1 {{ color: #111827; margin: 0; }}
        .date {{ color: #6b7280; font-size: 14px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 24px; }}
        .stat-box {{ background: #f9fafb; border-radius: 8px; padding: 16px; text-align: center; }}
        .stat-label {{ font-size: 11px; color: #6b7280; text-transform: uppercase; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #111827; }}
        .change {{ font-size: 12px; margin-top: 4px; }}
        .change.positive {{ color: #10b981; }}
        .change.negative {{ color: #ef4444; }}
        .footer {{ text-align: center; font-size: 12px; color: #9ca3af; margin-top: 32px; padding-top: 16px; border-top: 1px solid #e5e7eb; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 Weekly Analytics Report</h1>
            <p class="date">{summary.get('week_start', '')} to {summary.get('week_end', '')}</p>
        </div>

        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-label">Property Views</div>
                <div class="stat-value">{overview.get('property_views', 0):,}</div>
                <div class="change {'positive' if week_change.get('property_views_change_percent', 0) >= 0 else 'negative'}">
                    {week_change.get('property_views_change_percent', 0):+d}%
                </div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Leads Created</div>
                <div class="stat-value">{overview.get('leads_created', 0):,}</div>
                <div class="change {'positive' if week_change.get('leads_created_change_percent', 0) >= 0 else 'negative'}">
                    {week_change.get('leads_created_change_percent', 0):+d}%
                </div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Conversions</div>
                <div class="stat-value">{overview.get('conversions', 0):,}</div>
                <div class="change {'positive' if week_change.get('conversions_change_percent', 0) >= 0 else 'negative'}">
                    {week_change.get('conversions_change_percent', 0):+d}%
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Weekly report for {agent_name}</p>
            <p>AI Realtor Analytics</p>
        </div>
    </div>
</body>
</html>
"""

        return self.send_email(
            to=to,
            subject=f"📈 Weekly Analytics Report - {summary.get('week_end', datetime.now(timezone.utc).strftime('%Y-%m-%d'))}",
            html_content=html,
            tags=[{"name": "alert_type", "value": "weekly_summary"}]
        )


# Singleton instance
email_service = EmailService()
