"""
Notification service for real-time alerts via WebSocket
"""
from typing import Optional, Dict, Any
from datetime import datetime
import json
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType, NotificationPriority


class NotificationService:
    """Service for creating and broadcasting notifications"""

    def __init__(self):
        pass

    def create_notification(
        self,
        db: Session,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        property_id: Optional[int] = None,
        contact_id: Optional[int] = None,
        contract_id: Optional[int] = None,
        agent_id: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None,
        icon: Optional[str] = None,
        action_url: Optional[str] = None,
        auto_dismiss_seconds: Optional[int] = None
    ) -> Notification:
        """Create a notification in the database"""
        notification = Notification(
            type=notification_type,
            priority=priority,
            title=title,
            message=message,
            property_id=property_id,
            contact_id=contact_id,
            contract_id=contract_id,
            agent_id=agent_id,
            data=json.dumps(data) if data else None,
            icon=icon,
            action_url=action_url,
            auto_dismiss_seconds=auto_dismiss_seconds
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    def get_websocket_payload(self, notification: Notification) -> dict:
        """Convert notification to WebSocket payload"""
        return {
            "action": "notification",
            "notification": {
                "id": notification.id,
                "type": notification.type.value,
                "priority": notification.priority.value,
                "title": notification.title,
                "message": notification.message,
                "property_id": notification.property_id,
                "contact_id": notification.contact_id,
                "contract_id": notification.contract_id,
                "agent_id": notification.agent_id,
                "data": json.loads(notification.data) if notification.data else None,
                "icon": notification.icon,
                "action_url": notification.action_url,
                "created_at": notification.created_at.isoformat() if notification.created_at else None,
                "auto_dismiss_seconds": notification.auto_dismiss_seconds
            }
        }

    async def notify_contract_signed(
        self,
        db: Session,
        manager,
        contract_id: int,
        contract_name: str,
        signer_name: str,
        property_address: str,
        remaining_signers: int = 0
    ):
        """Send contract signed notification"""
        if remaining_signers > 0:
            title = f"📝 Contract Partially Signed"
            message = f"{signer_name} signed {contract_name} for {property_address}. {remaining_signers} signer(s) remaining."
            priority = NotificationPriority.MEDIUM
        else:
            title = f"✅ Contract Fully Signed!"
            message = f"All parties signed {contract_name} for {property_address}"
            priority = NotificationPriority.HIGH

        notification = self.create_notification(
            db=db,
            notification_type=NotificationType.CONTRACT_SIGNED,
            title=title,
            message=message,
            priority=priority,
            contract_id=contract_id,
            icon="📝" if remaining_signers > 0 else "✅",
            data={
                "contract_name": contract_name,
                "signer_name": signer_name,
                "property_address": property_address,
                "remaining_signers": remaining_signers,
                "fully_signed": remaining_signers == 0
            },
            auto_dismiss_seconds=10
        )

        # Broadcast via WebSocket
        if manager:
            await manager.broadcast(self.get_websocket_payload(notification))

        return notification

    async def notify_new_lead(
        self,
        db: Session,
        manager,
        contact_id: int,
        contact_name: str,
        contact_email: Optional[str],
        contact_phone: Optional[str],
        property_address: Optional[str] = None,
        property_id: Optional[int] = None,
        lead_source: str = "website"
    ):
        """Send new lead notification"""
        title = f"🎯 New Lead: {contact_name}"

        details = []
        if contact_email:
            details.append(f"📧 {contact_email}")
        if contact_phone:
            details.append(f"📱 {contact_phone}")
        if property_address:
            details.append(f"🏠 Interested in {property_address}")

        message = " | ".join(details) if details else f"New lead from {lead_source}"

        notification = self.create_notification(
            db=db,
            notification_type=NotificationType.NEW_LEAD,
            title=title,
            message=message,
            priority=NotificationPriority.HIGH,
            contact_id=contact_id,
            property_id=property_id,
            icon="🎯",
            data={
                "contact_name": contact_name,
                "contact_email": contact_email,
                "contact_phone": contact_phone,
                "property_address": property_address,
                "lead_source": lead_source
            },
            auto_dismiss_seconds=15
        )

        if manager:
            await manager.broadcast(self.get_websocket_payload(notification))

        return notification

    async def notify_property_price_change(
        self,
        db: Session,
        manager,
        property_id: int,
        property_address: str,
        old_price: float,
        new_price: float,
        agent_id: Optional[int] = None
    ):
        """Send property price change notification"""
        price_diff = new_price - old_price
        if price_diff > 0:
            title = f"📈 Price Increase: {property_address}"
            icon = "📈"
        else:
            title = f"📉 Price Reduction: {property_address}"
            icon = "📉"

        message = f"Price changed from ${old_price:,.0f} to ${new_price:,.0f} (${abs(price_diff):,.0f} {'increase' if price_diff > 0 else 'decrease'})"

        notification = self.create_notification(
            db=db,
            notification_type=NotificationType.PROPERTY_PRICE_CHANGE,
            title=title,
            message=message,
            priority=NotificationPriority.MEDIUM,
            property_id=property_id,
            agent_id=agent_id,
            icon=icon,
            data={
                "property_address": property_address,
                "old_price": old_price,
                "new_price": new_price,
                "price_diff": price_diff,
                "percentage_change": ((new_price - old_price) / old_price * 100)
            },
            auto_dismiss_seconds=12
        )

        if manager:
            await manager.broadcast(self.get_websocket_payload(notification))

        return notification

    async def notify_property_status_change(
        self,
        db: Session,
        manager,
        property_id: int,
        property_address: str,
        old_status: str,
        new_status: str,
        agent_id: Optional[int] = None
    ):
        """Send property status change notification"""
        status_icons = {
            "new_property": "🟢",
            "enriched": "🟡",
            "researched": "🔵",
            "waiting_for_contracts": "🟠",
            "complete": "🔴",
        }

        title = f"{status_icons.get(new_status, '🏠')} Status Change: {property_address}"
        message = f"Status changed from '{old_status}' to '{new_status}'"

        priority = NotificationPriority.HIGH if new_status in ["complete", "waiting_for_contracts"] else NotificationPriority.MEDIUM

        notification = self.create_notification(
            db=db,
            notification_type=NotificationType.PROPERTY_STATUS_CHANGE,
            title=title,
            message=message,
            priority=priority,
            property_id=property_id,
            agent_id=agent_id,
            icon=status_icons.get(new_status, "🏠"),
            data={
                "property_address": property_address,
                "old_status": old_status,
                "new_status": new_status
            },
            auto_dismiss_seconds=10
        )

        if manager:
            await manager.broadcast(self.get_websocket_payload(notification))

        return notification

    async def notify_appointment_reminder(
        self,
        db: Session,
        manager,
        appointment_type: str,
        appointment_time: str,
        property_address: str,
        property_id: int,
        client_name: str,
        minutes_until: int,
        agent_id: Optional[int] = None
    ):
        """Send appointment reminder notification"""
        title = f"⏰ Upcoming {appointment_type}: {property_address}"
        message = f"Meeting with {client_name} in {minutes_until} minutes at {appointment_time}"

        priority = NotificationPriority.URGENT if minutes_until <= 15 else NotificationPriority.HIGH

        notification = self.create_notification(
            db=db,
            notification_type=NotificationType.APPOINTMENT_REMINDER,
            title=title,
            message=message,
            priority=priority,
            property_id=property_id,
            agent_id=agent_id,
            icon="⏰",
            data={
                "appointment_type": appointment_type,
                "appointment_time": appointment_time,
                "property_address": property_address,
                "client_name": client_name,
                "minutes_until": minutes_until
            },
            auto_dismiss_seconds=20
        )

        if manager:
            await manager.broadcast(self.get_websocket_payload(notification))

        return notification

    async def notify_skip_trace_complete(
        self,
        db: Session,
        manager,
        property_id: int,
        property_address: str,
        owner_name: Optional[str] = None,
        phone_count: int = 0,
        email_count: int = 0
    ):
        """Send skip trace completion notification"""
        title = f"🔍 Skip Trace Complete: {property_address}"

        details = []
        if owner_name:
            details.append(f"Owner: {owner_name}")
        if phone_count > 0:
            details.append(f"{phone_count} phone(s)")
        if email_count > 0:
            details.append(f"{email_count} email(s)")

        message = " | ".join(details) if details else "Owner information found"

        notification = self.create_notification(
            db=db,
            notification_type=NotificationType.SKIP_TRACE_COMPLETE,
            title=title,
            message=message,
            priority=NotificationPriority.MEDIUM,
            property_id=property_id,
            icon="🔍",
            data={
                "property_address": property_address,
                "owner_name": owner_name,
                "phone_count": phone_count,
                "email_count": email_count
            },
            auto_dismiss_seconds=10
        )

        if manager:
            await manager.broadcast(self.get_websocket_payload(notification))

        return notification

    async def notify_enrichment_complete(
        self,
        db: Session,
        manager,
        property_id: int,
        property_address: str,
        zestimate: Optional[float] = None,
        photo_count: int = 0
    ):
        """Send enrichment completion notification"""
        title = f"✨ Enrichment Complete: {property_address}"

        details = []
        if zestimate:
            details.append(f"Zestimate: ${zestimate:,.0f}")
        if photo_count > 0:
            details.append(f"{photo_count} photos")

        message = " | ".join(details) if details else "Property data enriched with Zillow information"

        notification = self.create_notification(
            db=db,
            notification_type=NotificationType.ENRICHMENT_COMPLETE,
            title=title,
            message=message,
            priority=NotificationPriority.LOW,
            property_id=property_id,
            icon="✨",
            data={
                "property_address": property_address,
                "zestimate": zestimate,
                "photo_count": photo_count
            },
            auto_dismiss_seconds=8
        )

        if manager:
            await manager.broadcast(self.get_websocket_payload(notification))

        return notification

    def mark_as_read(self, db: Session, notification_id: int):
        """Mark notification as read"""
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.commit()
        return notification

    def mark_as_dismissed(self, db: Session, notification_id: int):
        """Mark notification as dismissed"""
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            notification.is_dismissed = True
            notification.dismissed_at = datetime.utcnow()
            db.commit()
        return notification

    async def notify_compliance_failed(
        self,
        db: Session,
        manager,
        property_id: int,
        property_address: str,
        failed_count: int,
        check_id: int,
        agent_id: Optional[int] = None
    ):
        """Send compliance check failed notification"""
        title = f"⚠️ Compliance Issues: {property_address}"
        message = f"Found {failed_count} compliance issue{'s' if failed_count != 1 else ''} that must be fixed before listing"

        notification = self.create_notification(
            db=db,
            notification_type=NotificationType.SYSTEM_ALERT,
            title=title,
            message=message,
            priority=NotificationPriority.HIGH,
            property_id=property_id,
            agent_id=agent_id,
            icon="⚠️",
            data={
                "property_address": property_address,
                "failed_count": failed_count,
                "check_id": check_id
            },
            action_url=f"/compliance/checks/{check_id}",
            auto_dismiss_seconds=15
        )

        if manager:
            await manager.broadcast(self.get_websocket_payload(notification))

        return notification


# Singleton instance
notification_service = NotificationService()
