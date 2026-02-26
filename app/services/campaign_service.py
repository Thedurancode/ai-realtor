"""Campaign Service - automated email/text drip campaigns."""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.contact import Contact
from app.models.property import Property
from app.models.notification import Notification, NotificationPriority, NotificationType

logger = logging.getLogger(__name__)


class CampaignService:
    """Automated email/text campaign management."""

    # Pre-defined campaign templates
    CAMPAIGN_TEMPLATES = {
        "lead_nurture": {
            "name": "Lead Nurture (7 touches over 30 days)",
            "touches": [
                {"day": 0, "message": "Thanks for your interest! Here are properties matching your criteria.", "type": "email"},
                {"day": 3, "message": "Have you had a chance to review the properties? I'd love to answer any questions.", "type": "sms"},
                {"day": 7, "message": "New properties just listed that match what you're looking for!", "type": "email"},
                {"day": 14, "message": "Market update: Prices in your area are trending {trend}. Now might be a great time to buy.", "type": "email"},
                {"day": 21, "message": "Just checking in - still looking for a property?", "type": "sms"},
                {"day": 28, "message": "Exclusive: Off-market opportunities coming soon. Want early access?", "type": "email"},
                {"day": 30, "message": "Last call - ready to schedule viewings?", "type": "sms"}
            ]
        },
        "contract_reminder": {
            "name": "Contract Deadline Reminder",
            "touches": [
                {"day": -3, "message": "Contract deadline approaching in 3 days. Please review and sign.", "type": "sms"},
                {"day": -1, "message": "URGENT: Contract deadline tomorrow. Action required.", "type": "sms"},
                {"day": 0, "message": "Contract due TODAY. Please sign immediately.", "type": "sms"}
            ]
        },
        "open_house": {
            "name": "Open House Reminder",
            "touches": [
                {"day": -7, "message": "Save the date! Open house coming up next week.", "type": "email"},
                {"day": -1, "message": "Open house tomorrow! Can't wait to show you around.", "type": "sms"},
                {"day": 0, "message": "Open house TODAY! Stop by anytime 2-4pm.", "type": "sms"}
            ]
        },
        "market_report": {
            "name": "Monthly Market Report",
            "touches": [
                {"day": 0, "message": "Your monthly market report is ready! {stats_summary}", "type": "email"}
            ]
        }
    }

    def __init__(self):
        pass

    def create_campaign(
        self,
        db: Session,
        agent_id: int,
        name: str,
        campaign_type: str,
        target_contacts: List[int],
        target_properties: List[int] = None,
        custom_message: str = None,
        start_date: datetime = None,
        channels: List[str] = None
    ) -> Dict[str, Any]:
        """Create a new campaign.

        Args:
            db: Database session
            agent_id: Agent creating campaign
            name: Campaign name
            campaign_type: Type of campaign (lead_nurture, contract_reminder, etc.)
            target_contacts: List of contact IDs to target
            target_properties: Optional list of property IDs
            custom_message: Custom message template
            start_date: When to start (default: now)
            channels: List of channels ["email", "sms"]

        Returns:
            Campaign creation result
        """
        if campaign_type not in self.CAMPAIGN_TEMPLATES:
            raise ValueError(f"Unknown campaign type: {campaign_type}")

        template = self.CAMPAIGN_TEMPLATES[campaign_type]
        start_date = start_date or datetime.now(timezone.utc)
        channels = channels or ["email"]

        # Validate contacts exist
        contacts = db.query(Contact).filter(
            Contact.id.in_(target_contacts)
        ).all()

        if len(contacts) != len(target_contacts):
            found_ids = [c.id for c in contacts]
            missing = set(target_contacts) - set(found_ids)
            logger.warning(f"Missing contact IDs: {missing}")

        # Create campaign summary (for now - could add Campaign table later)
        campaign_summary = {
            "id": f"campaign_{datetime.now(timezone.utc).timestamp()}",
            "agent_id": agent_id,
            "name": name,
            "type": campaign_type,
            "template_name": template["name"],
            "target_contacts": target_contacts,
            "target_properties": target_properties,
            "channels": channels,
            "total_touches": len(template["touches"]),
            "start_date": start_date.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        logger.info(f"Campaign created: {name} for {len(contacts)} contacts")

        return campaign_summary

    def send_campaign_touch(
        self,
        db: Session,
        agent_id: int,
        touch_type: str,
        contacts: List[int],
        message: str,
        channel: str = "email",
        property_id: int = None
    ) -> Dict[str, Any]:
        """Send a campaign touch to multiple contacts.

        Args:
            db: Database session
            agent_id: Agent sending
            touch_type: Type of touch (lead_nurture, reminder, etc.)
            contacts: List of contact IDs
            message: Message content
            channel: "email" or "sms"
            property_id: Optional property ID

        Returns:
            Send results
        """
        sent = 0
        failed = 0

        for contact_id in contacts:
            try:
                # For now, create notification (would integrate with Twilio/SendGrid in production)
                notification = Notification(
                    agent_id=agent_id,
                    type=NotificationType.SYSTEM,
                    priority=NotificationPriority.MEDIUM,
                    title=f"{channel.title()} Campaign: {touch_type}",
                    message=f"To: Contact {contact_id}\n\n{message}",
                    metadata={
                        "channel": channel,
                        "touch_type": touch_type,
                        "contact_id": contact_id,
                        "property_id": property_id,
                        "source": "campaign_service"
                    }
                )
                db.add(notification)
                sent += 1
            except Exception as e:
                logger.error(f"Failed to send {channel} to contact {contact_id}: {e}")
                failed += 1

        db.commit()

        return {
            "channel": channel,
            "sent": sent,
            "failed": failed,
            "total": sent + failed
        }

    def schedule_contract_reminders(
        self,
        db: Session,
        agent_id: int,
        contract_id: int,
        deadline: datetime,
        contact_id: int
    ) -> List[Dict[str, Any]]:
        """Schedule automatic contract deadline reminders.

        Args:
            db: Database session
            agent_id: Agent
            contract_id: Contract ID
            deadline: Deadline datetime
            contact_id: Contact to remind

        Returns:
            List of scheduled reminders
        """
        reminders = []

        # Calculate reminder dates
        reminder_days = [-3, -1, 0]  # 3 days before, 1 day before, day of

        for days_offset in reminder_days:
            reminder_date = deadline + timedelta(days=days_offset)

            # Create scheduled task for reminder
            from app.models.scheduled_task import ScheduledTask, TaskType, TaskStatus

            task = ScheduledTask(
                agent_id=agent_id,
                task_type=TaskType.REMINDER,
                status=TaskStatus.PENDING,
                title=f"Contract Reminder: {days_offset} days to deadline",
                description=f"Send contract deadline reminder to contact {contact_id} for contract {contract_id}",
                due_date=reminder_date,
                action="send_contract_reminder",
                metadata={
                    "contract_id": contract_id,
                    "contact_id": contact_id,
                    "days_offset": days_offset
                }
            )
            db.add(task)
            db.commit()
            db.refresh(task)

            reminders.append({
                "task_id": task.id,
                "scheduled_for": reminder_date.isoformat(),
                "days_offset": days_offset
            })

        logger.info(f"Scheduled {len(reminders)} contract reminders for deadline {deadline}")

        return reminders

    def send_market_report(
        self,
        db: Session,
        agent_id: int,
        contacts: List[int],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send monthly market report to contacts.

        Args:
            db: Database session
            agent_id: Agent
            contacts: List of contact IDs
            market_data: Market statistics

        Returns:
            Send results
        """
        # Generate market report summary
        stats_summary = self._generate_market_summary(market_data)

        message = f"""📊 Monthly Market Report

{stats_summary}

Let me know if you'd like more details about any specific area!

Best regards,
Your AI Realtor Assistant
"""

        return self.send_campaign_touch(
            db=db,
            agent_id=agent_id,
            touch_type="market_report",
            contacts=contacts,
            message=message,
            channel="email"
        )

    def _generate_market_summary(self, market_data: Dict[str, Any]) -> str:
        """Generate human-readable market summary.

        Args:
            market_data: Market statistics dict

        Returns:
            Formatted summary string
        """
        lines = []

        if market_data.get("median_price"):
            lines.append(f"Median Price: ${market_data['median_price']:,.0f}")

        if market_data.get("price_trend"):
            trend = market_data["price_trend"]
            emoji = "📈" if trend > 0 else "📉"
            lines.append(f"Price Trend: {emoji} {trend:+.1f}%")

        if market_data.get("inventory"):
            lines.append(f"Active Listings: {market_data['inventory']}")

        if market_data.get("avg_days_on_market"):
            lines.append(f"Avg Days on Market: {market_data['avg_days_on_market']:.0f}")

        return "\n".join(lines)

    def get_campaign_templates(self) -> Dict[str, Any]:
        """Get all available campaign templates.

        Returns:
            Dict of campaign templates
        """
        return {
            "templates": self.CAMPAIGN_TEMPLATES,
            "total": len(self.CAMPAIGN_TEMPLATES)
        }

    def estimate_campaign_cost(
        self,
        db: Session,
        contacts_count: int,
        touches_count: int,
        channels: List[str]
    ) -> Dict[str, Any]:
        """Estimate campaign cost.

        Args:
            db: Database session
            contacts_count: Number of contacts
            touches_count: Number of touches
            channels: List of channels

        Returns:
            Cost breakdown
        """
        # Pricing (example - would come from config)
        PRICING = {
            "sms": 0.0075,  # $0.0075 per SMS
            "email": 0.0001  # $0.0001 per email (SendGrid)
        }

        total_messages = contacts_count * touches_count
        cost_breakdown = {}
        total_cost = 0

        for channel in channels:
            if channel in PRICING:
                channel_cost = total_messages * PRICING[channel]
                cost_breakdown[channel] = {
                    "messages": total_messages,
                    "cost_per_message": PRICING[channel],
                    "total_cost": round(channel_cost, 2)
                }
                total_cost += channel_cost

        return {
            "contacts": contacts_count,
            "touches": touches_count,
            "total_messages": total_messages,
            "cost_breakdown": cost_breakdown,
            "estimated_total_cost": round(total_cost, 2)
        }


campaign_service = CampaignService()
