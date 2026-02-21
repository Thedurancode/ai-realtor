from pydantic import BaseModel, Field


class CMAResponse(BaseModel):
    property_id: int
    address: str
    suggested_price_low: float | None = None
    suggested_price_high: float | None = None
    average_comp_price: float | None = None
    median_comp_price: float | None = None
    price_per_sqft: float | None = None
    comparable_sales: list[dict] = Field(default_factory=list)
    comparable_rentals: list[dict] = Field(default_factory=list)
    market_trends: dict = Field(default_factory=dict)
    ai_analysis: str = ""
    voice_summary: str = ""
