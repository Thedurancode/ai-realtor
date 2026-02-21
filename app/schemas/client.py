from datetime import datetime

from pydantic import BaseModel, Field


class ClientCreate(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    client_type: str = "buyer"
    source: str | None = None
    notes: str | None = None
    preferred_locations: list[str] = Field(default_factory=list)
    budget_min: float | None = None
    budget_max: float | None = None
    bedrooms_min: int | None = None
    bathrooms_min: float | None = None
    sqft_min: int | None = None
    property_types: list[str] = Field(default_factory=list)
    must_haves: list[str] = Field(default_factory=list)
    deal_breakers: list[str] = Field(default_factory=list)


class ClientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    client_type: str | None = None
    status: str | None = None
    source: str | None = None
    notes: str | None = None
    preferred_locations: list[str] | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    bedrooms_min: int | None = None
    bathrooms_min: float | None = None
    sqft_min: int | None = None
    property_types: list[str] | None = None
    must_haves: list[str] | None = None
    deal_breakers: list[str] | None = None


class ClientPreferencesUpdate(BaseModel):
    preferred_locations: list[str] | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    bedrooms_min: int | None = None
    bathrooms_min: float | None = None
    sqft_min: int | None = None
    property_types: list[str] | None = None
    must_haves: list[str] | None = None
    deal_breakers: list[str] | None = None


class ClientResponse(BaseModel):
    id: int
    agent_id: int
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    client_type: str
    status: str
    source: str | None = None
    notes: str | None = None
    preferred_locations: list[str] = Field(default_factory=list)
    budget_min: float | None = None
    budget_max: float | None = None
    bedrooms_min: int | None = None
    bathrooms_min: float | None = None
    sqft_min: int | None = None
    property_types: list[str] = Field(default_factory=list)
    must_haves: list[str] = Field(default_factory=list)
    deal_breakers: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ClientMatchResponse(BaseModel):
    client: ClientResponse
    matching_properties: list[dict] = Field(default_factory=list)
    match_count: int = 0
