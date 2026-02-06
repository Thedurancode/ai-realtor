from pydantic import BaseModel
from typing import Optional
from datetime import datetime


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
