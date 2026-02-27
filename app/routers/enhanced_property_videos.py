"""Enhanced Property Videos Router

API endpoints for enhanced property video generation with avatar + footage.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.models.agent import Agent
from app.models.property import Property
from app.models.agent_video_profile import AgentVideoProfile
from app.models.property_video import PropertyVideo, VideoGenerationStatus
from app.schemas.property_video import (
    PropertyVideoCreate,
    PropertyVideoResponse,
    AgentVideoProfileCreate,
    AgentVideoProfileUpdate,
    AgentVideoProfileResponse,
    PropertyVideoSummary,
    VideoGenerationStatusResponse
)
from app.services.enhanced_property_video_service import EnhancedPropertyVideoService
from app.services.heygen_enhanced_service import create_agent_avatar

router = APIRouter(prefix="/enhanced-videos", tags=["Enhanced Property Videos"])


# ============================================================================
# Video Generation Endpoints
# ============================================================================

@router.post("/generate/{property_id}", response_model=dict)
async def generate_property_video(
    property_id: int,
    agent_id: int = Query(..., description="Agent ID"),
    style: str = Query("luxury", description="Video style: luxury, friendly, professional"),
    duration: int = Query(60, description="Target duration in seconds"),
    video_type: str = Query("property_tour", description="Video type"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Generate property video with agent avatar.

    Creates a complete property video featuring:
    - Agent intro with talking head avatar
    - AI-generated property footage
    - Professional voiceover
    - Call-to-action outro

    Process takes 5-10 minutes. Returns video_id for tracking.
    """
    # Verify property exists
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check agent profile
    profile = db.query(AgentVideoProfile).filter(
        AgentVideoProfile.agent_id == agent_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=400,
            detail=f"Agent video profile not found. Please create a profile first."
        )

    if not profile.heygen_avatar_id:
        raise HTTPException(
            status_code=400,
            detail=f"Agent profile missing custom avatar. Please create an avatar first."
        )

    # Create service and generate video (in background or sync)
    if background_tasks:
        # Run in background task
        background_tasks.add_task(
            _generate_video_background,
            property_id,
            agent_id,
            video_type,
            style,
            duration,
            db
        )

        return {
            "message": "Video generation started",
            "property_id": property_id,
            "estimated_time": "5-10 minutes",
            "status": "processing"
        }
    else:
        # Run synchronously (for testing)
        service = EnhancedPropertyVideoService(db)
        try:
            video = await service.generate_property_video(
                property_id=property_id,
                agent_id=agent_id,
                video_type=video_type,
                style=style,
                duration_target=duration
            )

            return {
                "message": "Video generated successfully",
                "video_id": video.id,
                "final_video_url": video.final_video_url,
                "duration": video.duration,
                "cost": video.generation_cost
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            await service.close()


async def _generate_video_background(
    property_id: int,
    agent_id: int,
    video_type: str,
    style: str,
    duration: int,
    db: Session
):
    """Background task for video generation."""
    service = EnhancedPropertyVideoService(db)
    try:
        await service.generate_property_video(
            property_id=property_id,
            agent_id=agent_id,
            video_type=video_type,
            style=style,
            duration_target=duration
        )
    finally:
        await service.close()


@router.get("/", response_model=List[PropertyVideoSummary])
async def list_videos(
    agent_id: Optional[int] = Query(None, description="Filter by agent"),
    property_id: Optional[int] = Query(None, description="Filter by property"),
    status: Optional[str] = Query(None, description="Filter by status"),
    video_type: Optional[str] = Query(None, description="Filter by video type"),
    limit: int = Query(50, description="Max results"),
    db: Session = Depends(get_db)
):
    """List all generated property videos."""
    query = db.query(PropertyVideo)

    if agent_id:
        query = query.filter(PropertyVideo.agent_id == agent_id)
    if property_id:
        query = query.filter(PropertyVideo.property_id == property_id)
    if status:
        query = query.filter(PropertyVideo.status == status)
    if video_type:
        query = query.filter(PropertyVideo.video_type == video_type)

    videos = query.order_by(PropertyVideo.created_at.desc()).limit(limit).all()

    return videos


@router.get("/{video_id}", response_model=PropertyVideoResponse)
async def get_video(
    video_id: int,
    db: Session = Depends(get_db)
):
    """Get specific video details."""
    video = db.query(PropertyVideo).filter(PropertyVideo.id == video_id).first()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    return video


@router.get("/{video_id}/status", response_model=VideoGenerationStatusResponse)
async def get_video_status(
    video_id: int,
    db: Session = Depends(get_db)
):
    """Check video generation status."""
    video = db.query(PropertyVideo).filter(PropertyVideo.id == video_id).first()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Get current step from generation_steps
    current_step = None
    if video.generation_steps:
        current_step = video.generation_steps[-1].get("step")

    # Calculate progress
    progress_map = {
        "draft": "0%",
        "generating_script": "10%",
        "script_completed": "20%",
        "generating_voiceover": "30%",
        "voiceover_completed": "40%",
        "generating_intro": "50%",
        "intro_completed": "60%",
        "generating_footage": "70%",
        "footage_completed": "80%",
        "assembling_video": "90%",
        "completed": "100%",
        "failed": "Failed"
    }

    progress = progress_map.get(video.status, "Unknown")

    return VideoGenerationStatusResponse(
        video_id=video.id,
        status=video.status,
        current_step=current_step,
        progress=progress,
        final_video_url=video.final_video_url,
        error_message=video.error_message,
        estimated_completion=video.completed_at
    )


@router.delete("/{video_id}")
async def delete_video(
    video_id: int,
    db: Session = Depends(get_db)
):
    """Delete a video record (does not delete S3 file)."""
    video = db.query(PropertyVideo).filter(PropertyVideo.id == video_id).first()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    db.delete(video)
    db.commit()

    return {"message": "Video deleted successfully"}


# ============================================================================
# Agent Video Profile Endpoints
# ============================================================================

@router.post("/agent/profile", response_model=AgentVideoProfileResponse)
async def create_agent_profile(
    profile: AgentVideoProfileCreate,
    db: Session = Depends(get_db)
):
    """Create or update agent video profile."""
    # Check if profile exists
    existing = db.query(AgentVideoProfile).filter(
        AgentVideoProfile.agent_id == profile.agent_id
    ).first()

    if existing:
        # Update existing
        existing.headshot_url = profile.headshot_url
        existing.voice_id = profile.voice_id
        existing.voice_style = profile.voice_style
        existing.background_color = profile.background_color
        existing.use_agent_branding = profile.use_agent_branding
        existing.default_intro_script = profile.default_intro_script
        existing.default_outro_script = profile.default_outro_script

        db.commit()
        db.refresh(existing)

        return existing
    else:
        # Create new
        new_profile = AgentVideoProfile(
            agent_id=profile.agent_id,
            headshot_url=profile.headshot_url,
            voice_id=profile.voice_id,
            voice_style=profile.voice_style,
            background_color=profile.background_color,
            use_agent_branding=profile.use_agent_branding,
            default_intro_script=profile.default_intro_script,
            default_outro_script=profile.default_outro_script
        )

        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)

        return new_profile


@router.get("/agent/profile/{agent_id}", response_model=AgentVideoProfileResponse)
async def get_agent_profile(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Get agent video profile."""
    profile = db.query(AgentVideoProfile).filter(
        AgentVideoProfile.agent_id == agent_id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Agent profile not found")

    return profile


@router.put("/agent/profile/{agent_id}", response_model=AgentVideoProfileResponse)
async def update_agent_profile(
    agent_id: int,
    updates: AgentVideoProfileUpdate,
    db: Session = Depends(get_db)
):
    """Update agent video profile."""
    profile = db.query(AgentVideoProfile).filter(
        AgentVideoProfile.agent_id == agent_id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Agent profile not found")

    # Update fields
    if updates.headshot_url:
        profile.headshot_url = updates.headshot_url
    if updates.voice_id:
        profile.voice_id = updates.voice_id
    if updates.voice_style:
        profile.voice_style = updates.voice_style
    if updates.background_color:
        profile.background_color = updates.background_color
    if updates.use_agent_branding is not None:
        profile.use_agent_branding = updates.use_agent_branding
    if updates.default_intro_script:
        profile.default_intro_script = updates.default_intro_script
    if updates.default_outro_script:
        profile.default_outro_script = updates.default_outro_script

    db.commit()
    db.refresh(profile)

    return profile


@router.post("/agent/{agent_id}/avatar", response_model=dict)
async def create_agent_avatar(
    agent_id: int,
    photo_url: str = Query(..., description="URL to agent's headshot photo"),
    gender: str = Query("female", description="Gender for voice matching"),
    db: Session = Depends(get_db)
):
    """
    Create custom HeyGen avatar from agent's photo.

    This creates a personalized talking head avatar from the agent's photo.
    Takes 1-3 minutes to process.
    """
    # Get agent
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Get or create profile
    profile = db.query(AgentVideoProfile).filter(
        AgentVideoProfile.agent_id == agent_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=400,
            detail="Please create an agent video profile first"
        )

    # Create avatar
    try:
        avatar_id = await create_agent_avatar(
            agent_id=agent_id,
            photo_url=photo_url,
            agent_name=agent.name,
            gender=gender
        )

        # Update profile
        profile.heygen_avatar_id = avatar_id
        profile.headshot_url = photo_url
        db.commit()

        return {
            "message": "Custom avatar created successfully",
            "avatar_id": avatar_id,
            "agent_id": agent_id,
            "status": "processing"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Avatar creation failed: {str(e)}")


# ============================================================================
# Cost Estimation
# ============================================================================

@router.post("/estimate-cost")
async def estimate_cost(
    num_clips: int = Query(5, description="Number of property clips"),
    duration: int = Query(60, description="Video duration in seconds"),
):
    """
    Estimate cost for video generation.

    Returns breakdown by component:
    - HeyGen: $2.00 (intro + outro)
    - PixVerse: ~$0.10 (5 clips × $0.02)
    - ElevenLabs: ~$0.03 (1 minute voiceover)
    - Assembly: ~$0.02 (S3 storage)
    """
    heygen_cost = 2.00
    pixverse_cost = num_clips * 0.02
    elevenlabs_cost = 0.03
    assembly_cost = 0.02

    total = heygen_cost + pixverse_cost + elevenlabs_cost + assembly_cost

    return {
        "estimated_cost": total,
        "breakdown": {
            "heygen": heygen_cost,
            "pixverse": pixverse_cost,
            "elevenlabs": elevenlabs_cost,
            "assembly": assembly_cost
        },
        "currency": "USD",
        "note": "Costs are estimates and may vary"
    }
