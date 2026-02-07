from typing import Any

from pydantic import BaseModel, Field


class ExaResearchCreateRequest(BaseModel):
    instructions: str = Field(..., min_length=1)
    model: str = "exa-research-fast"


class ExaPropertyDossierRequest(BaseModel):
    address: str = Field(..., min_length=5)
    county: str | None = None
    strategy: str = "buy&hold"
    model: str = "exa-research-fast"


class ExaSubdivisionDossierRequest(BaseModel):
    address: str = Field(..., min_length=5)
    county: str | None = None
    target_strategy: str = "subdivide and build"
    target_lot_count: int | None = None
    model: str = "exa-research-fast"


class ExaResearchResponse(BaseModel):
    task_id: str | None = None
    status: str | None = None
    raw: dict[str, Any]
