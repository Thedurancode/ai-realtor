from datetime import datetime

from pydantic import BaseModel, Field


class MilestoneCreate(BaseModel):
    title: str
    description: str | None = None
    due_date: datetime | None = None
    sort_order: int = 0


class MilestoneUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    due_date: datetime | None = None
    notes: str | None = None
    sort_order: int | None = None


class MilestoneResponse(BaseModel):
    id: int
    transaction_id: int
    title: str
    description: str | None = None
    status: str
    due_date: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None
    sort_order: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class TransactionCreate(BaseModel):
    property_id: int
    client_id: int | None = None
    offer_id: int | None = None
    sale_price: float | None = None
    closing_date: datetime | None = None
    earnest_money: float | None = None
    notes: str | None = None
    escrow_company: str | None = None
    title_company: str | None = None
    lender_name: str | None = None


class TransactionUpdate(BaseModel):
    status: str | None = None
    sale_price: float | None = None
    closing_date: datetime | None = None
    earnest_money: float | None = None
    notes: str | None = None
    escrow_company: str | None = None
    title_company: str | None = None
    lender_name: str | None = None


class TransactionResponse(BaseModel):
    id: int
    property_id: int
    agent_id: int
    client_id: int | None = None
    offer_id: int | None = None
    status: str
    sale_price: float | None = None
    closing_date: datetime | None = None
    earnest_money: float | None = None
    notes: str | None = None
    escrow_company: str | None = None
    title_company: str | None = None
    lender_name: str | None = None
    milestones: list[MilestoneResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
