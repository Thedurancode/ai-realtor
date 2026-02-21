from datetime import datetime

from pydantic import BaseModel, Field


class ListingCreate(BaseModel):
    property_id: int
    list_price: float
    description: str | None = None
    mls_number: str | None = None
    expires_at: datetime | None = None


class ListingUpdate(BaseModel):
    list_price: float | None = None
    description: str | None = None
    mls_number: str | None = None
    expires_at: datetime | None = None


class PriceChangeResponse(BaseModel):
    id: int
    listing_id: int
    old_price: float
    new_price: float
    reason: str | None = None
    changed_at: datetime

    class Config:
        from_attributes = True


class ListingResponse(BaseModel):
    id: int
    property_id: int
    agent_id: int
    status: str
    list_price: float
    original_price: float | None = None
    description: str | None = None
    mls_number: str | None = None
    published_at: datetime | None = None
    expires_at: datetime | None = None
    sold_at: datetime | None = None
    sold_price: float | None = None
    price_history: list[PriceChangeResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
