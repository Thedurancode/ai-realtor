from datetime import datetime

from pydantic import BaseModel, Field, computed_field


def format_datetime(dt: datetime | None) -> str | None:
    if not dt:
        return None
    return dt.strftime("%b %d, %Y at %I:%M %p")


def format_currency(amount: float | None) -> str:
    if amount is None:
        return "N/A"
    return f"${amount:,.0f}"


class OfferCreate(BaseModel):
    property_id: int
    offer_price: float
    buyer_contact_id: int | None = None
    earnest_money: float | None = None
    financing_type: str = "cash"
    closing_days: int | None = 30
    contingencies: list[str] = Field(default_factory=list)
    notes: str | None = None
    is_our_offer: bool = True
    expires_in_hours: int | None = 48


class CounterOfferCreate(BaseModel):
    offer_price: float
    earnest_money: float | None = None
    closing_days: int | None = None
    contingencies: list[str] | None = None
    notes: str | None = None
    expires_in_hours: int | None = 48


class OfferResponse(BaseModel):
    id: int
    property_id: int
    buyer_contact_id: int | None = None
    parent_offer_id: int | None = None
    offer_price: float
    earnest_money: float | None = None
    financing_type: str
    closing_days: int | None = None
    contingencies: list[str] = Field(default_factory=list)
    notes: str | None = None
    status: str
    is_our_offer: bool
    mao_low: float | None = None
    mao_base: float | None = None
    mao_high: float | None = None
    submitted_at: datetime | None = None
    expires_at: datetime | None = None
    responded_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

    @computed_field
    @property
    def offer_price_formatted(self) -> str:
        return format_currency(self.offer_price)

    @computed_field
    @property
    def submitted_at_formatted(self) -> str | None:
        return format_datetime(self.submitted_at)

    @computed_field
    @property
    def expires_at_formatted(self) -> str | None:
        return format_datetime(self.expires_at)

    class Config:
        from_attributes = True


class OfferSummary(BaseModel):
    property_id: int
    property_address: str
    total_offers: int
    active_offers: int
    highest_offer: float | None = None
    lowest_offer: float | None = None
    latest_status: str | None = None
    offers: list[OfferResponse] = Field(default_factory=list)
    voice_summary: str = ""


class TriRangeOut(BaseModel):
    low: float | None = None
    base: float | None = None
    high: float | None = None


class MAOResponse(BaseModel):
    property_id: int
    address: str
    arv: TriRangeOut | None = None
    offer_recommendation: TriRangeOut | None = None
    strategy: str = "wholesale"
    list_price: float | None = None
    zestimate: float | None = None
    explanation: str = ""
    voice_summary: str = ""


class OfferLetterRequest(BaseModel):
    offer_price: float
    financing_type: str = "cash"
    closing_days: int = 30
    contingencies: list[str] = Field(default_factory=list)
    earnest_money: float | None = None
    buyer_name: str | None = None
    buyer_email: str | None = None


class OfferLetterResponse(BaseModel):
    letter_text: str
    contract_id: int
    negotiation_strategy: str
    talking_points: list[str] = Field(default_factory=list)
    voice_summary: str
    docuseal_template_id: str | None = None
