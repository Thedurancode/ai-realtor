from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


Strategy = Literal["flip", "rental", "wholesale"]
ExecutionMode = Literal["pipeline", "orchestrated"]


class JobLimits(BaseModel):
    max_steps: int = 9
    max_web_calls: int = 30
    timeout_seconds_per_step: int = 20
    max_parallel_agents: int = 1


class ResearchInput(BaseModel):
    address: str
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    apn: str | None = None
    strategy: Strategy = "wholesale"
    mode: ExecutionMode = "pipeline"
    assumptions: dict[str, Any] = Field(default_factory=dict)
    limits: JobLimits = Field(default_factory=JobLimits)


class ParcelFacts(BaseModel):
    sqft: int | None = None
    lot: float | None = None
    beds: int | None = None
    baths: float | None = None
    year: int | None = None


class Geo(BaseModel):
    lat: float | None = None
    lng: float | None = None


class TransactionEvent(BaseModel):
    date: str | None = None
    event: str | None = None
    amount: float | None = None
    source_url: str | None = None


class EnrichmentStatus(BaseModel):
    has_crm_property_match: bool = False
    has_skip_trace_owner: bool = False
    has_zillow_enrichment: bool = False
    is_enriched: bool = False
    is_fresh: bool | None = None
    age_hours: float | None = None
    max_age_hours: int | None = None
    matched_property_id: int | None = None
    skip_trace_id: int | None = None
    zillow_enrichment_id: int | None = None
    missing: list[str] = Field(default_factory=list)
    last_enriched_at: datetime | None = None


class PropertyProfile(BaseModel):
    normalized_address: str
    geo: Geo
    apn: str | None = None
    parcel_facts: ParcelFacts
    zoning: str | None = None
    owner_names: list[str] = Field(default_factory=list)
    mailing_address: str | None = None
    assessed_values: dict[str, float | None] = Field(default_factory=dict)
    tax_status: str | None = None
    transaction_history: list[TransactionEvent] = Field(default_factory=list)
    enrichment_status: EnrichmentStatus | None = None


class EvidenceItemOut(BaseModel):
    id: int
    property_id: int
    category: str
    claim: str
    source_url: str
    captured_at: datetime
    raw_excerpt: str | None = None
    confidence: float | None = None
    hash: str


class CompSaleOut(BaseModel):
    address: str
    distance_mi: float | None = None
    sale_date: date | None = None
    sale_price: float | None = None
    sqft: int | None = None
    beds: int | None = None
    baths: float | None = None
    year_built: int | None = None
    similarity_score: float
    source_url: str


class CompRentalOut(BaseModel):
    address: str
    distance_mi: float | None = None
    rent: float | None = None
    date_listed: date | None = None
    sqft: int | None = None
    beds: int | None = None
    baths: float | None = None
    similarity_score: float
    source_url: str


class TriRange(BaseModel):
    low: float | None = None
    base: float | None = None
    high: float | None = None


class UnderwriteOut(BaseModel):
    arv_estimate: TriRange
    rent_estimate: TriRange
    rehab_tier: Literal["light", "medium", "heavy"]
    rehab_estimated_range: TriRange
    offer_price_recommendation: TriRange
    fees: dict[str, float] = Field(default_factory=dict)
    sensitivity_table: list[dict[str, Any]] = Field(default_factory=list)


class RiskScoreOut(BaseModel):
    title_risk: float | None = None
    data_confidence: float | None = None
    compliance_flags: list[str] = Field(default_factory=list)
    notes: str | None = None


class DossierOut(BaseModel):
    markdown: str


class WorkerRunOut(BaseModel):
    worker_name: str
    status: str
    runtime_ms: int
    cost_usd: float
    web_calls: int
    unknowns: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class NeighborhoodIntelOut(BaseModel):
    crime: list[dict[str, Any]] = Field(default_factory=list)
    schools: list[dict[str, Any]] = Field(default_factory=list)
    demographics: list[dict[str, Any]] = Field(default_factory=list)
    market_trends: list[dict[str, Any]] = Field(default_factory=list)
    walkability: list[dict[str, Any]] = Field(default_factory=list)
    ai_summary: str | None = None


class FloodZoneOut(BaseModel):
    flood_zone: str | None = None
    description: str | None = None
    in_floodplain: bool | None = None
    insurance_required: bool | None = None
    panel_number: str | None = None


class FullResearchOutput(BaseModel):
    property_profile: PropertyProfile
    evidence: list[EvidenceItemOut]
    comps_sales: list[CompSaleOut]
    comps_rentals: list[CompRentalOut]
    underwrite: UnderwriteOut
    risk_score: RiskScoreOut
    neighborhood_intel: NeighborhoodIntelOut | None = None
    flood_zone: FloodZoneOut | None = None
    extensive: dict[str, Any] | None = None
    dossier: DossierOut
    worker_runs: list[WorkerRunOut]


class AgenticJobCreateResponse(BaseModel):
    job_id: int
    property_id: int
    trace_id: str
    status: str


class AgenticJobStatusResponse(BaseModel):
    id: int
    property_id: int
    trace_id: str
    status: str
    progress: int
    current_step: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class PropertyEnvelope(BaseModel):
    property_id: int
    latest_job_id: int | None = None
    output: FullResearchOutput | None = None


class DossierEnvelope(BaseModel):
    property_id: int
    latest_job_id: int
    markdown: str


class EnrichmentStatusEnvelope(BaseModel):
    property_id: int
    enrichment_status: EnrichmentStatus
