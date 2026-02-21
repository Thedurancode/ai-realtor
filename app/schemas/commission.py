from datetime import datetime

from pydantic import BaseModel, computed_field


class CommissionCreate(BaseModel):
    property_id: int
    transaction_id: int | None = None
    client_id: int | None = None
    sale_price: float | None = None
    commission_rate: float | None = None
    commission_amount: float | None = None
    split_percentage: float = 100.0
    notes: str | None = None


class CommissionUpdate(BaseModel):
    sale_price: float | None = None
    commission_rate: float | None = None
    commission_amount: float | None = None
    split_percentage: float | None = None
    status: str | None = None
    notes: str | None = None


class CommissionResponse(BaseModel):
    id: int
    agent_id: int
    property_id: int
    transaction_id: int | None = None
    client_id: int | None = None
    sale_price: float | None = None
    commission_rate: float | None = None
    commission_amount: float | None = None
    split_percentage: float
    net_amount: float | None = None
    status: str
    notes: str | None = None
    paid_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

    @computed_field
    @property
    def net_amount_formatted(self) -> str:
        if self.net_amount is None:
            return "N/A"
        return f"${self.net_amount:,.2f}"

    class Config:
        from_attributes = True


class CommissionSummaryResponse(BaseModel):
    total_earned: float = 0.0
    total_pending: float = 0.0
    total_projected: float = 0.0
    count_paid: int = 0
    count_pending: int = 0
    count_projected: int = 0
