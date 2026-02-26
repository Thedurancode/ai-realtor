"""VideoGen AI Video Generation Router

Generate AI avatar videos and post to social media via Postiz.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel

from app.database import get_db
from app.models.agent import Agent
from app.models.property import Property
from app.models.videogen import VideoGenVideo, VideoGenAvatar, VideoGenScriptTemplate
from app.services.videogen_service import VideoGenService, generate_video_and_upload
from app.services.postiz_service import PostizService, create_property_post
from app.models.agent_brand import AgentBrand

router = APIRouter(prefix="/videogen", tags=["VideoGen AI Videos"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class VideoGenerateRequest(BaseModel):
    """Generate AI avatar video"""
    avatar_id: str = "Anna-public-1_20230714"
    script: Optional[str] = None  # Auto-generate if not provided
    script_type: str = "promotion"  # promotion, market_update, open_house
    property_id: Optional[int] = None
    aspect_ratio: str = "16:9"  # 16:9 (landscape) or 9:16 (portrait/TikTok)
    voice_id: Optional[str] = None
    background: str = "#FFFFFF"
    test: bool = False  # If True, skip actual generation


class VideoPostRequest(BaseModel):
    """Generate video and post to social media"""
    avatar_id: str = "Anna-public-1_20230714"
    property_id: Optional[int] = None
    caption: Optional[str] = None
    platforms: List[str] = ["instagram", "tiktok", "youtube"]
    script_type: str = "promotion"
    aspect_ratio: Optional[str] = None  # Auto-detect based on platforms


class AvatarListResponse(BaseModel):
    """Available AI avatars"""
    avatars: List[dict]
    total: int
    voice_summary: str


class VideoStatusResponse(BaseModel):
    """Video generation status"""
    video_id: str
    status: str  # processing, completed, failed
    video_url: Optional[str]
    error: Optional[str]
    created_at: str


# ============================================================================
# Avatar Management
# ============================================================================

@router.get("/avatars", response_model=AvatarListResponse)
async def list_avatars(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """List available AI avatars

    Returns all avatars from VideoGen with preview images and details.
    """
    service = VideoGenService()

    try:
        avatars = await service.list_avatars()

        # Update local cache
        for avatar_data in avatars[:20]:  # Cache first 20
            existing = db.query(VideoGenAvatar).filter(
                VideoGenAvatar.avatar_id == avatar_data.get("avatar_id")
            ).first()

            if not existing:
                new_avatar = VideoGenAvatar(
                    avatar_id=avatar_data.get("avatar_id"),
                    avatar_name=avatar_data.get("avatar_name"),
                    preview_image_url=avatar_data.get("preview_image_url"),
                    gender=avatar_data.get("gender"),
                    category=avatar_data.get("category"),
                    default_voice_id=avatar_data.get("default_voice_id")
                )
                db.add(new_avatar)

        db.commit()

        return AvatarListResponse(
            avatars=avatars[:20],  # Return first 20
            total=len(avatars),
            voice_summary=f"Found {len(avatars)} AI avatars available."
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch avatars: {str(e)}")


@router.get("/avatars/cached")
async def list_cached_avatars(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """List cached avatars from database (faster, no API call)"""
    avatars = db.query(VideoGenAvatar).filter(
        VideoGenAvatar.is_active == True
    ).limit(50).all()

    return {
        "avatars": [
            {
                "avatar_id": a.avatar_id,
                "avatar_name": a.avatar_name,
                "preview_image_url": a.preview_image_url,
                "gender": a.gender,
                "category": a.category,
                "times_used": a.times_used
            }
            for a in avatars
        ],
        "total": len(avatars),
        "voice_summary": f"Showing {len(avatars)} cached avatars."
    }


# ============================================================================
# Video Generation
# ============================================================================

@router.post("/generate")
async def generate_video(
    request: VideoGenerateRequest,
    agent_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate AI avatar video

    Creates an AI avatar video speaking the provided script.
    Can auto-generate script from property data if not provided.

    Returns video_id for tracking status.
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Get property if specified
    property = None
    if request.property_id:
        property = db.query(Property).filter(Property.id == request.property_id).first()

    # Generate script if not provided
    if not request.script:
        service = VideoGenService()
        if property:
            property_data = {
                "city": property.city,
                "property_type": property.property_type,
                "bedrooms": property.bedrooms,
                "bathrooms": property.bathrooms,
                "square_footage": property.square_footage,
                "price": property.price
            }
            script = await service.generate_property_script(property_data, request.script_type)
        else:
            script = "Check out this amazing property opportunity!"
    else:
        script = request.script

    # Generate video
    service = VideoGenService()
    try:
        result = await service.generate_video(
            script=script,
            avatar_id=request.avatar_id,
            voice_id=request.voice_id,
            background=request.background,
            aspect_ratio=request.aspect_ratio,
            test=request.test
        )

        video_data = result.get("data", {})
        video_id = video_data.get("video_id")

        # Save to database
        video_record = VideoGenVideo(
            agent_id=agent_id,
            property_id=request.property_id,
            video_id=video_id,
            avatar_id=request.avatar_id,
            voice_id=request.voice_id,
            script=script,
            script_type=request.script_type,
            aspect_ratio=request.aspect_ratio,
            status="processing",
            generation_started_at=datetime.now(timezone.utc),
            metadata={
                "test": request.test,
                "background": request.background
            }
        )

        db.add(video_record)
        db.commit()
        db.refresh(video_record)

        # Update avatar usage
        avatar = db.query(VideoGenAvatar).filter(
            VideoGenAvatar.avatar_id == request.avatar_id
        ).first()
        if avatar:
            avatar.times_used += 1
            avatar.last_used_at = datetime.now(timezone.utc)
            db.commit()

        return {
            "video_id": video_id,
            "status": "processing",
            "script": script,
            "estimated_time": video_data.get("estimated_time", 120),
            "voice_summary": f"Generating AI avatar video. Will take approximately 2-5 minutes."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")


@router.get("/status/{video_id}")
async def get_video_status(
    video_id: str,
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Check video generation status

    Returns current status and video URL if complete.
    """
    # Check database first
    video_record = db.query(VideoGenVideo).filter(
        VideoGenVideo.video_id == video_id
    ).first()

    if not video_record:
        raise HTTPException(status_code=404, detail="Video not found")

    # Get fresh status from API
    service = VideoGenService()
    try:
        status_response = await service.get_video_status(video_id)
        status_data = status_response.get("data", {})
        status = status_data.get("status")

        # Update database
        video_record.status = status

        if status == "completed":
            video_record.video_url = status_data.get("video_url")
            video_record.generation_completed_at = datetime.now(timezone.utc)

        elif status == "failed":
            video_record.error_message = status_data.get("error", "Unknown error")

        db.commit()

        return VideoStatusResponse(
            video_id=video_id,
            status=status,
            video_url=status_data.get("video_url"),
            error=status_data.get("error"),
            created_at=video_record.created_at.isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check status: {str(e)}")


# ============================================================================
# Video + Social Media Posting
# ============================================================================

@router.post("/post")
async def generate_and_post(
    request: VideoPostRequest,
    agent_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate AI avatar video and post to social media

    Complete workflow:
    1. Generate script (AI or custom)
    2. Create video with VideoGen
    3. Wait for processing
    4. Upload to Postiz
    5. Post to all specified platforms

    This may take 3-5 minutes to complete.
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Get property
    property = None
    if request.property_id:
        property = db.query(Property).filter(Property.id == request.property_id).first()
        if not property:
            raise HTTPException(status_code=404, detail="Property not found")

    # Auto-detect aspect ratio for TikTok/Reels
    aspect_ratio = request.aspect_ratio
    if not aspect_ratio:
        if "tiktok" in request.platforms or "instagram" in request.platforms:
            aspect_ratio = "9:16"  # Portrait for Reels/TikTok
        else:
            aspect_ratio = "16:9"  # Landscape for YouTube/Facebook

    # Generate script
    service = VideoGenService()
    if property:
        property_data = {
            "city": property.city,
            "property_type": property.property_type,
            "bedrooms": property.bedrooms,
            "bathrooms": property.bathrooms,
            "square_footage": property.square_footage,
            "price": property.price
        }
        script = await service.generate_property_script(property_data, request.script_type)
    else:
        script = "Check out this amazing opportunity!"

    # Generate caption if not provided
    caption = request.caption
    if not caption and property:
        brand = db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()
        caption = f"🏠 {property.city} Property Tour!\n\n{property.bedrooms} bed | {property.bathrooms} bath | ${property.price:,}\n\n{brand.tagline if brand else 'DM for details!'}\n\n#realestate #propertytour #dreamhome"
    elif not caption:
        caption = "🎬 AI-generated video featuring our latest opportunity!\n\n#realestate #ai #innovation"

    try:
        # Generate video and upload to Postiz
        result = await generate_video_and_upload(
            script=script,
            avatar_id=request.avatar_id,
            agent_id=agent_id,
            db=db,
            aspect_ratio=aspect_ratio,
            platforms=request.platforms
        )

        # Post to social media
        post_result = await create_property_post(
            agent_id=agent_id,
            db=db,
            property=property,
            brand=db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first(),
            caption=caption,
            platforms=request.platforms,
            media_urls=[result["postiz_media_url"]],
            publish_immediately=True
        )

        # Update video record
        video_id = result["videogen_video_id"]
        video_record = db.query(VideoGenVideo).filter(
            VideoGenVideo.video_id == video_id
        ).first()

        if video_record:
            video_record.postiz_media_id = result["postiz_media_id"]
            video_record.postiz_media_url = result["postiz_media_url"]
            video_record.postiz_post_id = post_result.get("post", {}).get("id")
            video_record.platforms = request.platforms
            video_record.platforms_posted = request.platforms
            video_record.post_status = "posted"
            video_record.status = "posted"
            db.commit()

        return {
            "success": True,
            "video_id": video_id,
            "video_url": result["video_url"],
            "postiz_post_id": post_result.get("post", {}).get("id"),
            "platforms_posted": request.platforms,
            "script_used": script,
            "caption_used": caption,
            "voice_summary": f"Generated AI avatar video and posted to {', '.join(request.platforms)}. Check your social media accounts!"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate and post: {str(e)}")


# ============================================================================
# Script Templates
# ============================================================================

@router.post("/templates")
async def create_template(
    template_name: str,
    template_category: str,
    script_template: str,
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Create reusable script template"""
    template = VideoGenScriptTemplate(
        agent_id=agent_id,
        template_name=template_name,
        template_category=template_category,
        script_template=script_template
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return {
        "template_id": template.id,
        "template_name": template.template_name,
        "voice_summary": f"Template '{template_name}' created."
    }


@router.get("/templates")
async def list_templates(
    agent_id: int,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List script templates"""
    query = db.query(VideoGenScriptTemplate).filter(
        VideoGenScriptTemplate.agent_id == agent_id,
        VideoGenScriptTemplate.is_active == True
    )

    if category:
        query = query.filter(VideoGenScriptTemplate.template_category == category)

    templates = query.all()

    return {
        "templates": [
            {
                "id": t.id,
                "template_name": t.template_name,
                "template_category": t.template_category,
                "times_used": t.times_used
            }
            for t in templates
        ],
        "total": len(templates)
    }
