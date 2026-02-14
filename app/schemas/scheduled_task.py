"""Pydantic schemas for scheduled tasks."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ScheduledTaskCreate(BaseModel):
    task_type: str = "reminder"
    title: str
    description: Optional[str] = None
    scheduled_at: datetime
    repeat_interval_hours: Optional[int] = None
    property_id: Optional[int] = None
    action: Optional[str] = None
    action_params: Optional[dict] = None
    created_by: str = "voice"


class ScheduledTaskResponse(BaseModel):
    id: int
    task_type: str
    status: str
    title: str
    description: Optional[str] = None
    scheduled_at: datetime
    repeat_interval_hours: Optional[int] = None
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    property_id: Optional[int] = None
    action: Optional[str] = None
    action_params: Optional[dict] = None
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
