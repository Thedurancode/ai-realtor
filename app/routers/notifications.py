"""
Notification endpoints for creating and managing real-time alerts
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.services.notification_service import notification_service


router = APIRouter(prefix="/notifications", tags=["notifications"])


# Helper function to get WebSocket manager
def get_ws_manager():
    """Get WebSocket manager from main module"""
    try:
        import sys
        if 'app.main' in sys.modules:
            return sys.modules['app.main'].manager
    except:
        pass
    return None


class NotificationCreate(BaseModel):
    """Create notification request"""
    type: str
    priority: str = "medium"
    title: str
    message: str
    property_id: Optional[int] = None
    contact_id: Optional[int] = None
    contract_id: Optional[int] = None
    agent_id: Optional[int] = None
    icon: Optional[str] = None
    auto_dismiss_seconds: Optional[int] = None


class NotificationResponse(BaseModel):
    """Notification response"""
    id: int
    type: str
    priority: str
    title: str
    message: str
    property_id: Optional[int]
    contact_id: Optional[int]
    contract_id: Optional[int]
    agent_id: Optional[int]
    icon: Optional[str]
    is_read: bool
    is_dismissed: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[NotificationResponse])
def list_notifications(
    limit: int = 50,
    unread_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    List recent notifications
    """
    query = db.query(Notification)

    if unread_only:
        query = query.filter(Notification.is_read == False)

    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()

    return [
        NotificationResponse(
            id=n.id,
            type=n.type.value,
            priority=n.priority.value,
            title=n.title,
            message=n.message,
            property_id=n.property_id,
            contact_id=n.contact_id,
            contract_id=n.contract_id,
            agent_id=n.agent_id,
            icon=n.icon,
            is_read=n.is_read,
            is_dismissed=n.is_dismissed,
            created_at=n.created_at
        )
        for n in notifications
    ]


@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a custom notification and broadcast via WebSocket
    """
    manager = get_ws_manager()

    try:
        notification_type = NotificationType[notification.type.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid notification type: {notification.type}")

    try:
        notification_priority = NotificationPriority[notification.priority.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid priority: {notification.priority}")

    new_notification = notification_service.create_notification(
        db=db,
        notification_type=notification_type,
        title=notification.title,
        message=notification.message,
        priority=notification_priority,
        property_id=notification.property_id,
        contact_id=notification.contact_id,
        contract_id=notification.contract_id,
        agent_id=notification.agent_id,
        icon=notification.icon,
        auto_dismiss_seconds=notification.auto_dismiss_seconds
    )

    # Broadcast via WebSocket
    if manager:
        await manager.broadcast(notification_service.get_websocket_payload(new_notification))

    return NotificationResponse(
        id=new_notification.id,
        type=new_notification.type.value,
        priority=new_notification.priority.value,
        title=new_notification.title,
        message=new_notification.message,
        property_id=new_notification.property_id,
        contact_id=new_notification.contact_id,
        contract_id=new_notification.contract_id,
        agent_id=new_notification.agent_id,
        icon=new_notification.icon,
        is_read=new_notification.is_read,
        is_dismissed=new_notification.is_dismissed,
        created_at=new_notification.created_at
    )


@router.post("/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    """Mark notification as read"""
    notification = notification_service.mark_as_read(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "marked_as_read", "notification_id": notification_id}


@router.post("/{notification_id}/dismiss")
def dismiss_notification(notification_id: int, db: Session = Depends(get_db)):
    """Dismiss notification"""
    notification = notification_service.mark_as_dismissed(db, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "dismissed", "notification_id": notification_id}


@router.delete("/{notification_id}")
def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    """Delete notification"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    db.delete(notification)
    db.commit()
    return {"status": "deleted", "notification_id": notification_id}


# Demo endpoint for testing notifications
@router.post("/demo/contract-signed")
async def demo_contract_signed(db: Session = Depends(get_db)):
    """Demo: Send a contract signed notification"""
    manager = get_ws_manager()
    await notification_service.notify_contract_signed(
        db=db,
        manager=manager,
        contract_id=1,
        contract_name="Purchase Agreement",
        signer_name="John Smith",
        property_address="123 Main Street",
        remaining_signers=0
    )
    return {"status": "notification_sent"}


@router.post("/demo/new-lead")
async def demo_new_lead(db: Session = Depends(get_db)):
    """Demo: Send a new lead notification"""
    manager = get_ws_manager()
    await notification_service.notify_new_lead(
        db=db,
        manager=manager,
        contact_id=1,
        contact_name="Sarah Johnson",
        contact_email="sarah@example.com",
        contact_phone="555-1234",
        property_address="456 Oak Avenue",
        lead_source="Website Form"
    )
    return {"status": "notification_sent"}


@router.post("/demo/price-change")
async def demo_price_change(db: Session = Depends(get_db)):
    """Demo: Send a price change notification"""
    manager = get_ws_manager()
    await notification_service.notify_property_price_change(
        db=db,
        manager=manager,
        property_id=1,
        property_address="789 Park Lane",
        old_price=500000,
        new_price=475000
    )
    return {"status": "notification_sent"}


@router.post("/demo/appointment")
async def demo_appointment(db: Session = Depends(get_db)):
    """Demo: Send an appointment reminder"""
    manager = get_ws_manager()
    await notification_service.notify_appointment_reminder(
        db=db,
        manager=manager,
        appointment_type="Property Showing",
        appointment_time="2:00 PM",
        property_address="321 Elm Street",
        property_id=1,
        client_name="Mike & Lisa Chen",
        minutes_until=15
    )
    return {"status": "notification_sent"}
