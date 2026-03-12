"""Shotstack Enhanced Video Endpoints

7 feature enhancements:
  1. Social media clips (vertical 9:16, 15s/30s/60s)
  2. Batch rendering (multiple properties at once)
  3. Template marketplace (browse, render with merge fields)
  4. Video preview/thumbnail generation
  5. Webhook callback (Shotstack notifies us on completion)
  6. CMA/Market report videos
  7. Listing slideshow (photos + text + music, no TTS/HeyGen)
"""
import logging
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.shotstack_enhanced_service import (
    ShotstackEnhancedService,
    get_shotstack_enhanced_service,
    render_social_clip_task,
    process_batch_task,
    render_thumbnail_task,
    render_cma_video_task,
    render_listing_slideshow_task,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/shotstack", tags=["Shotstack Enhanced"])


# ======================================================================
# Request/Response Models
# ======================================================================

class SocialClipCreate(BaseModel):
    property_id: Optional[int] = None
    duration_target: int = Field(30, description="Target duration: 15, 30, or 60 seconds")
    aspect_ratio: str = Field("9:16", description="9:16 (vertical), 1:1 (square), 16:9 (landscape)")
    platform: str = Field("all", description="instagram_reels, tiktok, youtube_shorts, all")
    style: str = Field("professional", pattern=r'^(luxury|friendly|professional)$')
    caption_text: Optional[str] = Field(None, max_length=300)
    hashtags: Optional[List[str]] = None
    background_music_url: Optional[str] = None
    photo_urls: Optional[List[str]] = Field(None, description="Photo URLs; auto-pulled from Zillow if omitted")
    custom_text_overlays: Optional[List[str]] = Field(None, description="Custom text for each scene")


class BatchRenderCreate(BaseModel):
    property_ids: List[int] = Field(..., min_length=1, max_length=50)
    job_type: str = Field("property_video", description="property_video, social_clip, slideshow")
    style: str = Field("luxury", pattern=r'^(luxury|friendly|professional)$')
    name: Optional[str] = Field(None, max_length=200)


class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: str = Field("property_showcase", description="property_showcase, brand_intro, social_clip, market_report, slideshow")
    style: str = Field("professional")
    template_json: Dict[str, Any] = Field(..., description="Full Shotstack Edit JSON")
    merge_fields: Optional[List[Dict[str, str]]] = Field(None, description='[{"key":"HEADLINE","label":"Headline","default":"Dream Home"}]')
    aspect_ratio: str = Field("16:9")
    duration: Optional[float] = None
    tags: Optional[List[str]] = None
    preview_image_url: Optional[str] = None
    preview_video_url: Optional[str] = None
    is_premium: bool = False


class TemplateRenderRequest(BaseModel):
    merge_fields: Optional[Dict[str, str]] = Field(None, description='{"HEADLINE": "Beautiful Home", "PRICE": "$499,000"}')


class ThumbnailCreate(BaseModel):
    source_type: str = Field(..., description="property_video_job, social_clip, slideshow, cma_video")
    source_id: int = Field(...)
    frame_time: float = Field(2.0, description="Time in seconds to capture the frame")


class CmaVideoCreate(BaseModel):
    property_id: int
    style: str = Field("professional", pattern=r'^(luxury|friendly|professional)$')
    max_comps: int = Field(5, ge=1, le=10)
    include_rentals: bool = False
    background_music_url: Optional[str] = None


class SlideshowCreate(BaseModel):
    property_id: int
    style: str = Field("luxury", pattern=r'^(luxury|friendly|professional)$')
    photo_urls: Optional[List[str]] = Field(None, description="Photo URLs; auto-pulled from Zillow if omitted")
    title_text: Optional[str] = Field(None, max_length=300)
    subtitle_text: Optional[str] = Field(None, max_length=300)
    cta_text: Optional[str] = Field(None, max_length=300, description="Call-to-action text for the last slide")
    background_music_url: Optional[str] = None
    aspect_ratio: str = Field("16:9", description="16:9, 9:16, 1:1")
    seconds_per_photo: float = Field(4.0, ge=2.0, le=10.0)


# ======================================================================
# 1. SOCIAL MEDIA CLIPS — vertical short-form videos
# ======================================================================

@router.post("/social-clips", status_code=202)
async def create_social_clip(
    body: SocialClipCreate,
    background_tasks: BackgroundTasks,
    agent_id: int = 1,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """Generate a short-form vertical video for social media platforms."""
    clip, photo_urls = service.create_social_clip(
        agent_id=agent_id,
        property_id=body.property_id,
        duration_target=body.duration_target,
        aspect_ratio=body.aspect_ratio,
        platform=body.platform,
        style=body.style,
        caption_text=body.caption_text,
        hashtags=body.hashtags,
        background_music_url=body.background_music_url,
        photo_urls=body.photo_urls,
    )

    background_tasks.add_task(
        render_social_clip_task, clip.id, agent_id, photo_urls,
        body.custom_text_overlays, body.property_id,
    )

    return {
        "clip_id": clip.id,
        "status": "pending",
        "message": f"Social clip generation started ({body.duration_target}s {body.aspect_ratio} for {body.platform}).",
    }


@router.get("/social-clips")
def list_social_clips(
    agent_id: int = 1,
    limit: int = 20,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """List social clips for an agent."""
    return service.list_social_clips(agent_id, limit)


@router.get("/social-clips/{clip_id}")
def get_social_clip(
    clip_id: int,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """Get social clip status and details."""
    return service.get_social_clip(clip_id)


# ======================================================================
# 2. BATCH RENDERING — multiple properties at once
# ======================================================================

@router.post("/batch", status_code=202)
async def create_batch_render(
    body: BatchRenderCreate,
    background_tasks: BackgroundTasks,
    agent_id: int = 1,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """Batch render videos for multiple properties at once."""
    result = service.create_batch_render(
        agent_id=agent_id,
        property_ids=body.property_ids,
        job_type=body.job_type,
        style=body.style,
        name=body.name,
    )

    background_tasks.add_task(process_batch_task, result["batch_id"], agent_id, body.job_type, body.style)

    return result


@router.get("/batch")
def list_batch_jobs(
    agent_id: int = 1,
    limit: int = 20,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """List batch rendering jobs."""
    return service.list_batch_jobs(agent_id, limit)


@router.get("/batch/{batch_id}")
def get_batch_job(
    batch_id: int,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """Get batch job details with item statuses."""
    return service.get_batch_job(batch_id)


# ======================================================================
# 3. TEMPLATE MARKETPLACE — browse, create, render
# ======================================================================

@router.get("/marketplace")
def list_marketplace_templates(
    category: Optional[str] = None,
    style: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    featured_only: bool = False,
    limit: int = 20,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """Browse the template marketplace."""
    return service.list_marketplace_templates(category, style, aspect_ratio, featured_only, limit)


@router.get("/marketplace/{template_id}")
def get_marketplace_template(
    template_id: int,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """Get full template details including the Edit JSON."""
    return service.get_marketplace_template(template_id)


@router.post("/marketplace")
def create_marketplace_template(
    body: TemplateCreate,
    agent_id: Optional[int] = None,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """Add a template to the marketplace."""
    return service.create_marketplace_template(
        name=body.name,
        description=body.description,
        category=body.category,
        style=body.style,
        template_json=body.template_json,
        merge_fields=body.merge_fields,
        aspect_ratio=body.aspect_ratio,
        duration=body.duration,
        tags=body.tags,
        preview_image_url=body.preview_image_url,
        preview_video_url=body.preview_video_url,
        is_premium=body.is_premium,
        agent_id=agent_id,
    )


@router.post("/marketplace/{template_id}/render", status_code=202)
def render_marketplace_template(
    template_id: int,
    body: Optional[TemplateRenderRequest] = None,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """Render a marketplace template with optional merge field replacements."""
    merge_fields = body.merge_fields if body and body.merge_fields else None
    return service.render_marketplace_template(template_id, merge_fields)


@router.delete("/marketplace/{template_id}")
def delete_marketplace_template(
    template_id: int,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """Delete a template from the marketplace."""
    return service.delete_marketplace_template(template_id)


# ======================================================================
# 4. VIDEO PREVIEW/THUMBNAIL — still frame before full render
# ======================================================================

@router.post("/thumbnails", status_code=202)
async def create_thumbnail(
    body: ThumbnailCreate,
    background_tasks: BackgroundTasks,
    agent_id: int = 1,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """Generate a still-frame thumbnail from an existing video job's timeline."""
    thumb, timeline_json = service.create_thumbnail(
        agent_id=agent_id,
        source_type=body.source_type,
        source_id=body.source_id,
        frame_time=body.frame_time,
    )

    background_tasks.add_task(render_thumbnail_task, thumb.id, timeline_json, body.frame_time)

    return {
        "thumbnail_id": thumb.id,
        "status": "pending",
        "message": "Thumbnail generation started.",
    }


@router.get("/thumbnails/{thumbnail_id}")
def get_thumbnail(
    thumbnail_id: int,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """Get thumbnail status."""
    return service.get_thumbnail(thumbnail_id)


# ======================================================================
# 5. WEBHOOK CALLBACK — Shotstack notifies us on completion
# ======================================================================

@router.post("/webhook/callback")
async def shotstack_webhook_callback(
    request: Request,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """Receive Shotstack render completion webhooks.

    Configure in Shotstack dashboard:
      POST https://your-domain.com/shotstack/webhook/callback

    Payload from Shotstack:
    {
        "type": "render",
        "action": "render:completed" | "render:failed",
        "data": {
            "id": "render-id",
            "status": "done" | "failed",
            "url": "https://cdn.shotstack.io/..."
        }
    }
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    return service.handle_webhook_callback(payload)


@router.get("/webhook/log")
def list_webhook_logs(
    limit: int = 20,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """List recent Shotstack webhook deliveries."""
    return service.list_webhook_logs(limit)


# ======================================================================
# 6. CMA / MARKET REPORT VIDEOS
# ======================================================================

@router.post("/cma-videos", status_code=202)
async def create_cma_video(
    body: CmaVideoCreate,
    background_tasks: BackgroundTasks,
    agent_id: int = 1,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """Generate a Comparable Market Analysis video from comps data."""
    cma, prop = service.create_cma_video(
        agent_id=agent_id,
        property_id=body.property_id,
        style=body.style,
        max_comps=body.max_comps,
        include_rentals=body.include_rentals,
    )

    background_tasks.add_task(
        render_cma_video_task, cma.id, agent_id, body.property_id,
        body.max_comps, body.include_rentals, body.style,
        body.background_music_url,
    )

    return {
        "cma_video_id": cma.id,
        "status": "pending",
        "message": f"CMA video generation started for {prop.address}.",
    }


@router.get("/cma-videos")
def list_cma_videos(
    agent_id: int = 1,
    limit: int = 20,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """List CMA videos for an agent."""
    return service.list_cma_videos(agent_id, limit)


@router.get("/cma-videos/{cma_id}")
def get_cma_video(
    cma_id: int,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """Get CMA video status and details."""
    return service.get_cma_video(cma_id)


# ======================================================================
# 7. LISTING SLIDESHOW — photos + text + music, no TTS/HeyGen
# ======================================================================

@router.post("/slideshows", status_code=202)
async def create_listing_slideshow(
    body: SlideshowCreate,
    background_tasks: BackgroundTasks,
    agent_id: int = 1,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """Generate a listing slideshow video from property photos — fast, cheap, no AI needed."""
    slideshow, photo_urls = service.create_listing_slideshow(
        agent_id=agent_id,
        property_id=body.property_id,
        style=body.style,
        photo_urls=body.photo_urls,
        title_text=body.title_text,
        subtitle_text=body.subtitle_text,
        cta_text=body.cta_text,
        background_music_url=body.background_music_url,
        aspect_ratio=body.aspect_ratio,
        seconds_per_photo=body.seconds_per_photo,
    )

    background_tasks.add_task(render_listing_slideshow_task, slideshow.id, agent_id)

    return {
        "slideshow_id": slideshow.id,
        "status": "pending",
        "photo_count": len(photo_urls),
        "estimated_duration": len(photo_urls) * body.seconds_per_photo,
        "message": f"Listing slideshow started with {len(photo_urls)} photos.",
    }


@router.get("/slideshows")
def list_slideshows(
    agent_id: int = 1,
    limit: int = 20,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """List listing slideshows."""
    return service.list_slideshows(agent_id, limit)


@router.get("/slideshows/{slideshow_id}")
def get_slideshow(
    slideshow_id: int,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """Get slideshow status and details."""
    return service.get_slideshow(slideshow_id)


# ======================================================================
# 8. RENDERED MEDIA LIBRARY — browse all renders for a property/agent
# ======================================================================

@router.get("/media/property/{property_id}")
def get_property_rendered_media(
    property_id: int,
    agent_id: int = 1,
    status_filter: Optional[str] = None,
    media_type: Optional[str] = None,
    limit: int = 50,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """Get all rendered media for a property across all video types.

    Returns property videos, social clips, CMA videos, slideshows, and
    thumbnails — everything that has been rendered for this property.
    Use this when editing a template to see what existing media can be
    reused or selected instead of re-rendering.

    Filters:
      - status_filter: done, rendering, pending, failed
      - media_type: property_video, social_clip, cma_video, slideshow, thumbnail
    """
    return service.get_property_rendered_media(property_id, agent_id, status_filter, media_type, limit)


@router.get("/media/agent/{agent_id}")
def get_agent_rendered_media(
    agent_id: int,
    status_filter: Optional[str] = None,
    media_type: Optional[str] = None,
    limit: int = 50,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """Get all rendered media for an agent across all properties and types.

    Similar to the property endpoint but agent-wide — shows everything
    this agent has ever rendered. Useful for a media library view.
    """
    return service.get_agent_rendered_media(agent_id, status_filter, media_type, limit)


@router.get("/media/{media_type}/{media_id}/timeline")
def get_media_timeline(
    media_type: str,
    media_id: int,
    service: ShotstackEnhancedService = Depends(get_shotstack_enhanced_service),
):
    """Get the Shotstack Edit JSON (timeline) for a rendered media item.

    Use this to clone/modify an existing render — load the timeline into
    the editor, make changes, and re-render without starting from scratch.

    media_type: property_video, social_clip, cma_video, slideshow
    """
    return service.get_media_timeline(media_type, media_id)
