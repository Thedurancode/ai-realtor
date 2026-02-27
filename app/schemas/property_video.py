"""Property Video Schemas

Pydantic models for enhanced property video generation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


# ============================================================================
# Request Schemas
# ============================================================================

class PropertyVideoCreate(BaseModel):
    """Request to generate property video"""
    style: str = Field(default="luxury", description="Video style: luxury, friendly, professional")
    duration: int = Field(default=60, description="Target duration in seconds")
    video_type: str = Field(default="property_tour", description="Video type")


class AgentVideoProfileCreate(BaseModel):
    """Create agent video profile"""
    agent_id: int
    headshot_url: str = Field(..., description="URL to agent's headshot photo")
    voice_id: str = Field(..., description="ElevenLabs voice ID")
    voice_style: str = Field(default="professional", description="Voice style")
    background_color: str = Field(default="#f8fafc", description="Background hex color")
    use_agent_branding: bool = Field(default=True, description="Use agent branding")
    default_intro_script: Optional[str] = Field(None, description="Default intro script")
    default_outro_script: Optional[str] = Field(None, description="Default outro script")


class AgentVideoProfileUpdate(BaseModel):
    """Update agent video profile"""
    headshot_url: Optional[str] = None
    voice_id: Optional[str] = None
    voice_style: Optional[str] = None
    background_color: Optional[str] = None
    use_agent_branding: Optional[bool] = None
    default_intro_script: Optional[str] = None
    default_outro_script: Optional[str] = None


# ============================================================================
# Response Schemas
# ============================================================================

class PropertyVideoResponse(BaseModel):
    """Property video response"""
    id: int
    agent_id: int
    property_id: int
    video_type: str
    style: str
    duration_target: int
    status: str
    final_video_url: Optional[str]
    thumbnail_url: Optional[str]
    duration: Optional[float]
    resolution: Optional[str]
    file_size: Optional[int]
    generation_cost: Optional[float]
    cost_breakdown: Optional[Dict]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AgentVideoProfileResponse(BaseModel):
    """Agent video profile response"""
    id: int
    agent_id: int
    headshot_url: str
    heygen_avatar_id: Optional[str]
    voice_id: str
    voice_style: str
    background_color: str
    use_agent_branding: bool
    default_intro_script: Optional[str]
    default_outro_script: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class VideoGenerationStatusResponse(BaseModel):
    """Video generation status"""
    video_id: int
    status: str
    current_step: Optional[str]
    progress: Optional[str]
    final_video_url: Optional[str]
    error_message: Optional[str]
    estimated_completion: Optional[datetime]


# ============================================================================
# Summary Schemas
# ============================================================================

class PropertyVideoSummary(BaseModel):
    """Brief video summary for lists"""
    id: int
    property_id: int
    video_type: str
    status: str
    style: str
    duration: Optional[float]
    thumbnail_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CostEstimateResponse(BaseModel):
    """Cost estimate for video generation"""
    estimated_cost: float
    breakdown: Dict[str, float]
    currency: str = "USD"
