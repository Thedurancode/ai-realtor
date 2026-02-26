"""Pydantic schemas for Remotion render jobs."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class RenderJobCreate(BaseModel):
    """Request to create a new render job."""
    template_id: str = Field(..., description="Template identifier (e.g., 'captioned-reel', 'slideshow')")
    composition_id: str = Field(..., description="Composition name within the template")
    input_props: Dict[str, Any] = Field(..., description="Input props for the Remotion composition")
    webhook_url: Optional[str] = Field(None, description="Optional webhook URL for completion notification")

    @validator('template_id')
    def validate_template_id(cls, v):
        """Ensure template_id is from allowed list."""
        allowed_templates = {'captioned-reel', 'slideshow'}
        if v not in allowed_templates:
            raise ValueError(f'template_id must be one of {allowed_templates}')
        return v

    @validator('webhook_url')
    def validate_webhook_url(cls, v):
        """Validate webhook URL if provided."""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('webhook_url must start with http:// or https://')
        return v


class RenderJobResponse(BaseModel):
    """Response with render job details."""
    id: str
    agent_id: int
    template_id: str
    composition_id: str
    input_props: Dict[str, Any]
    status: str
    progress: float
    output_url: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_sent: Optional[str] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    current_frame: Optional[int] = None
    total_frames: Optional[int] = None
    eta_seconds: Optional[int] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    updated_at: datetime


class RenderJobProgress(BaseModel):
    """Real-time progress update for a render job."""
    id: str
    status: str
    progress: float
    current_frame: Optional[int] = None
    total_frames: Optional[int] = None
    eta_seconds: Optional[int] = None


class RenderJobList(BaseModel):
    """List of render jobs for an agent."""
    jobs: list[RenderJobResponse]
    total: int
