"""Pydantic schemas for Transaction Coordinator."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class PartySchema(BaseModel):
    name: str
    role: str
    email: Optional[str] = None
    phone: Optional[str] = None


class TransactionCreate(BaseModel):
    property_id: int
    offer_id: Optional[int] = None
    title: Optional[str] = None
    accepted_date: Optional[datetime] = None
    closing_date: Optional[datetime] = None
    sale_price: Optional[float] = None
    earnest_money: Optional[float] = None
    commission_rate: Optional[float] = None
    financing_type: Optional[str] = None
    parties: Optional[List[PartySchema]] = []
    notes: Optional[str] = None
    # Deadline overrides (if not provided, auto-calculated from accepted_date)
    attorney_review_deadline: Optional[datetime] = None
    inspection_deadline: Optional[datetime] = None
    appraisal_deadline: Optional[datetime] = None
    mortgage_contingency_date: Optional[datetime] = None


class MilestoneCreate(BaseModel):
    name: str
    description: Optional[str] = None
    assigned_role: Optional[str] = None
    assigned_name: Optional[str] = None
    assigned_contact: Optional[str] = None
    due_date: Optional[datetime] = None


class MilestoneUpdate(BaseModel):
    status: Optional[str] = None
    outcome_notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    assigned_name: Optional[str] = None
    assigned_contact: Optional[str] = None


class MilestoneResponse(BaseModel):
    id: int
    transaction_id: int
    name: str
    description: Optional[str] = None
    status: str
    assigned_role: Optional[str] = None
    assigned_name: Optional[str] = None
    assigned_contact: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    reminder_sent: bool
    outcome_notes: Optional[str] = None
    documents: list = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TransactionResponse(BaseModel):
    id: int
    property_id: int
    offer_id: Optional[int] = None
    status: str
    title: str
    accepted_date: Optional[datetime] = None
    attorney_review_deadline: Optional[datetime] = None
    inspection_deadline: Optional[datetime] = None
    appraisal_deadline: Optional[datetime] = None
    mortgage_contingency_date: Optional[datetime] = None
    title_clear_date: Optional[datetime] = None
    final_walkthrough_date: Optional[datetime] = None
    closing_date: Optional[datetime] = None
    sale_price: Optional[float] = None
    earnest_money: Optional[float] = None
    commission_rate: Optional[float] = None
    financing_type: Optional[str] = None
    parties: list = []
    notes: Optional[str] = None
    risk_flags: list = []
    milestones: List[MilestoneResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TransactionSummary(BaseModel):
    id: int
    property_id: int
    status: str
    title: str
    closing_date: Optional[datetime] = None
    sale_price: Optional[float] = None
    days_to_close: Optional[int] = None
    milestones_completed: int = 0
    milestones_total: int = 0
    overdue_milestones: int = 0
    risk_flags: list = []

    model_config = {"from_attributes": True}
