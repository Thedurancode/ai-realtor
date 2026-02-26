"""Pydantic schemas for timeline video projects."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TimelineClip(BaseModel):
    """A single clip on a timeline track."""
    id: str
    start: int  # frame number
    duration: int  # frames
    type: str  # "video" | "image" | "text"
    src: Optional[str] = None  # for video/image
    text: Optional[str] = None  # for text clips
    style: Optional[Dict[str, Any]] = None  # CSS styles
    transition: Optional[str] = "none"  # "none" | "fade" | "slide" | "zoom"


class TimelineTrack(BaseModel):
    """A track containing multiple clips."""
    id: str
    type: str  # "video" | "image" | "text" | "audio"
    clips: List[TimelineClip]


class TimelineData(BaseModel):
    """Complete timeline data structure."""
    tracks: List[TimelineTrack]
    duration: int  # total frames


class TimelineProjectCreate(BaseModel):
    """Request to create a timeline project."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    timeline_data: TimelineData
    fps: int = Field(30, ge=1, le=60)
    width: int = Field(1080, ge=480, le=3840)
    height: int = Field(1920, ge=480, le=3840)


class TimelineProjectUpdate(BaseModel):
    """Request to update a timeline project."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    timeline_data: Optional[TimelineData] = None
    fps: Optional[int] = Field(None, ge=1, le=60)
    width: Optional[int] = Field(None, ge=480, le=3840)
    height: Optional[int] = Field(None, ge=480, le=3840)
    status: Optional[str] = Field(None, pattern="^(draft|rendering|completed)$")


class TimelineProjectResponse(BaseModel):
    """Response with timeline project details."""
    id: str
    agent_id: int
    name: str
    description: Optional[str] = None
    timeline_data: TimelineData
    fps: int
    width: int
    height: int
    status: str
    render_job_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    rendered_at: Optional[datetime] = None


class TimelineProjectList(BaseModel):
    """List of timeline projects."""
    projects: List[TimelineProjectResponse]
    total: int


class RenderFromTimelineRequest(BaseModel):
    """Request to render a timeline project."""
    webhook_url: Optional[str] = None
