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
# HeyGen service no longer used - using D-ID instead
# from app.services.heygen_enhanced_service import create_agent_avatar as create_agent_avatar_service

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

    if not profile.headshot_url:
        raise HTTPException(
            status_code=400,
            detail=f"Agent profile missing headshot. Please upload a photo first."
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
    db: Session  # This parameter is ignored, we create our own session
):
    """Background task for video generation."""
    from app.database import SessionLocal

    # Create a new database session for this background task
    bg_db = SessionLocal()
    try:
        service = EnhancedPropertyVideoService(bg_db)
        await service.generate_property_video(
            property_id=property_id,
            agent_id=agent_id,
            video_type=video_type,
            style=style,
            duration_target=duration
        )
    finally:
        await service.close()
        bg_db.close()


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
    Upload agent headshot for video generation.

    This stores the agent's photo which will be used as the intro frame
    in property videos. The system will use D-ID for talking head videos
    (if configured) or fall back to photo slideshows.
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

    # Update profile with headshot (HeyGen avatar creation removed - we use D-ID or photo slideshow)
    try:
        profile.headshot_url = photo_url
        # Note: heygen_avatar_id field is kept for backward compatibility but no longer used
        db.commit()

        return {
            "message": "Headshot updated successfully",
            "agent_id": agent_id,
            "headshot_url": photo_url,
            "status": "ready"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")


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
    - D-ID Talking Heads: $2.00 (if configured, otherwise $0)
    - PixVerse AI Footage: ~${:.2f} ({} clips × $0.02/clip)
    - ElevenLabs Voiceover: ~$0.03 (1 minute)
    - Assembly: ~$0.02 (processing + storage)
    """.format(num_clips * 0.02, num_clips)

    # D-ID cost (only if configured, otherwise 0)
    did_cost = 0.0
    # Check if D-ID is configured
    import os
    if os.getenv("DID_API_KEY"):
        did_cost = 2.00

    pixverse_cost = num_clips * 0.02
    elevenlabs_cost = 0.03
    assembly_cost = 0.02

    total = did_cost + pixverse_cost + elevenlabs_cost + assembly_cost

    breakdown = {
        "elevenlabs_voiceover": elevenlabs_cost,
        "pixverse_footage": pixverse_cost,
        "assembly": assembly_cost
    }

    # Only include D-ID if configured
    if did_cost > 0:
        breakdown["d_id_talking_heads"] = did_cost

    return {
        "estimated_cost": total,
        "breakdown": breakdown,
        "currency": "USD",
        "note": "Costs are estimates and may vary. D-ID talking heads require proper AWS SigV4 credentials."
    }
