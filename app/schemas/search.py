"""Search schemas for semantic vector search endpoints."""
from typing import Optional
from pydantic import BaseModel, Field


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Natural language search query")
    limit: int = Field(10, ge=1, le=50, description="Max results to return")
    status: Optional[str] = Field(None, description="Filter by property status")
    property_type: Optional[str] = Field(None, description="Filter by property type")
    min_price: Optional[float] = Field(None, description="Minimum price filter")
    max_price: Optional[float] = Field(None, description="Maximum price filter")


class ResearchSearchRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Natural language search query")
    dossier_limit: int = Field(5, ge=1, le=20)
    evidence_limit: int = Field(10, ge=1, le=50)


class PropertySearchResult(BaseModel):
    id: int
    title: Optional[str] = None
    address: str
    price: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    property_type: Optional[str] = None
    status: Optional[str] = None
    similarity: float


class DossierSearchResult(BaseModel):
    id: int
    research_property_id: int
    job_id: int
    snippet: str
    similarity: float


class EvidenceSearchResult(BaseModel):
    id: int
    research_property_id: int
    category: str
    claim: str
    source_url: Optional[str] = None
    confidence: Optional[float] = None
    snippet: Optional[str] = None
    similarity: float


class PropertySearchResponse(BaseModel):
    results: list[PropertySearchResult]
    query: str
    count: int
    voice_summary: str


class ResearchSearchResponse(BaseModel):
    dossiers: list[DossierSearchResult]
    evidence: list[EvidenceSearchResult]
    query: str
    total_count: int
    voice_summary: str


class BackfillRequest(BaseModel):
    table: str = Field(
        "all",
        pattern=r"^(properties|property_recaps|dossiers|evidence|all)$",
        description="Table to backfill or 'all'"
    )


class BackfillResponse(BaseModel):
    tables: dict
    duration_seconds: float
