from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime as dt

from app.models.research import ResearchStatus, ResearchType


class ResearchCreateRequest(BaseModel):
    """Request to create a research job"""
    research_type: ResearchType
    property_id: Optional[int] = None
    agent_id: Optional[int] = None
    parameters: Optional[dict] = None
    endpoints_to_call: Optional[List[dict]] = None


class ResearchResponse(BaseModel):
    """Research job response"""
    id: int
    research_type: ResearchType
    property_id: Optional[int]
    agent_id: Optional[int]
    status: ResearchStatus
    progress: int
    current_step: Optional[str]
    results: Optional[dict]
    error_message: Optional[str]
    started_at: Optional[dt]
    completed_at: Optional[dt]
    created_at: dt

    class Config:
        from_attributes = True


class AIResearchRequest(BaseModel):
    """Request for AI-powered custom research"""
    property_id: Optional[int] = None
    prompt: str
    model: Optional[str] = "claude-sonnet-4-20250514"
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 1.0
    system_prompt: Optional[str] = None
    property_context: Optional[bool] = True


class APIEndpointConfig(BaseModel):
    """Configuration for a single API endpoint call"""
    name: Optional[str] = None
    url: str
    method: Optional[str] = "GET"
    headers: Optional[dict] = None
    params: Optional[dict] = None
    json: Optional[dict] = None
    timeout: Optional[int] = 30


class APIResearchRequest(BaseModel):
    """Request for custom API research"""
    property_id: Optional[int] = None
    endpoints: List[APIEndpointConfig]
