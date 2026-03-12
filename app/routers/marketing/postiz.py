"""Postiz Social Media Marketing Router

Complete social media management integration with Postiz:
- Account connection
- Post creation and scheduling
- AI-powered content generation
- Multi-platform publishing
- Analytics and insights
- Campaign management
- Content calendar
- Templates
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional, List, Dict, Any
from app.services.postiz_service import PostizService, get_postiz_service
from pydantic import BaseModel, Field
from typing import Dict as DictType, List as ListType

router = APIRouter(prefix="/social", tags=["Social Media Management"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class PostizAccountConnect(BaseModel):
    """Connect Postiz account"""
    api_key: str
    workspace_id: Optional[str] = None
    account_name: Optional[str] = None
    platforms: ListType[str]  # facebook, instagram, twitter, linkedin, tiktok
    platform_tokens: Optional[DictType[str, str]] = None


class PostAccountResponse(BaseModel):
    id: int
    agent_id: int
    account_name: Optional[str]
    connected_platforms: Optional[ListType[str]]
    is_active: bool
    voice_summary: str


class PostCreateRequest(BaseModel):
    """Create social media post"""
    content_type: str  # property_promo, market_update, brand_awareness, testimonial, open_house
    caption: str
    hashtags: Optional[ListType[str]] = None
    mention_accounts: Optional[ListType[str]] = None
    media_urls: Optional[ListType[str]] = None
    media_type: str = "image"  # image, video, carousel, story
    property_id: Optional[int] = None

    # Scheduling
    scheduled_at: Optional[str] = None  # ISO datetime
    scheduled_timezone: str = "America/New_York"
    publish_immediately: bool = False

    # Platforms
    platforms: ListType[str] = ["facebook", "instagram"]  # platforms to publish to

    # Branding
    use_branding: bool = True


class PostUpdateRequest(BaseModel):
    """Update post"""
    caption: Optional[str] = None
    hashtags: Optional[ListType[str]] = None
    scheduled_at: Optional[str] = None
    status: Optional[str] = None


class PostResponse(BaseModel):
    id: int
    agent_id: int
    property_id: Optional[int]
    content_type: str
    caption: str
    hashtags: Optional[ListType[str]]
    media_urls: Optional[ListType[str]]
    media_type: str
    scheduled_at: Optional[str]
    status: str
    platform_content: Optional[DictType[str, Any]]
    analytics: Optional[DictType[str, Any]]
    voice_summary: str


class SchedulePostRequest(BaseModel):
    """Schedule post for specific time"""
    post_id: int
    scheduled_at: str  # ISO datetime
    platforms: ListType[str]
    timezone: str = "America/New_York"


class BulkScheduleRequest(BaseModel):
    """Bulk schedule posts from campaign"""
    campaign_id: int
    start_date: str  # ISO datetime
    platforms: ListType[str]
    frequency: str = "daily"  # daily, weekly, custom


class CampaignCreateRequest(BaseModel):
    """Create multi-post campaign"""
    campaign_name: str
    campaign_type: str  # property_launch, open_house, brand_awareness
    property_id: Optional[int] = None
    start_date: str
    end_date: Optional[str] = None
    platforms: ListType[str]
    post_count: int = 5
    use_branding: bool = True
    auto_generate: bool = True


class TemplateCreateRequest(BaseModel):
    """Create post template"""
    template_name: str
    template_category: str
    caption_template: str
    hashtag_template: Optional[ListType[str]] = None
    media_type: str = "image"
    media_count: int = 1
    ai_generate_caption: bool = True


class AIGenerateRequest(BaseModel):
    """Generate post content with AI"""
    content_type: str
    property_id: Optional[int] = None
    platform: str = "facebook"
    tone: str = "professional"  # professional, casual, enthusiastic, urgent
    include_price: bool = True
    include_address: bool = True
    custom_instructions: Optional[str] = None


class AnalyticsRequest(BaseModel):
    """Get analytics for period"""
    period_type: str = "weekly"  # daily, weekly, monthly
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    platforms: Optional[ListType[str]] = None


class MediaUploadRequest(BaseModel):
    """Upload media to Postiz"""
    image_url: Optional[str] = None
    # file upload handled separately


class PreviewPostRequest(BaseModel):
    """Preview post without publishing"""
    caption: str
    platforms: ListType[str]
    media_urls: Optional[ListType[str]] = None
    hashtags: Optional[ListType[str]] = None
    property_id: Optional[int] = None


class DirectPostRequest(BaseModel):
    """Create and publish post directly to Postiz API"""
    caption: str
    platforms: ListType[str]  # facebook, instagram, twitter, linkedin, tiktok, etc.
    media_urls: Optional[ListType[str]] = None
    hashtags: Optional[ListType[str]] = None
    scheduled_at: Optional[str] = None  # ISO datetime
    publish_immediately: bool = True
    property_id: Optional[int] = None


# ============================================================================
# Account Management
# ============================================================================

@router.post("/accounts/connect", response_model=PostAccountResponse)
def connect_postiz_account(
    request: PostizAccountConnect,
    agent_id: int,
    service: PostizService = Depends(get_postiz_service)
):
    """Connect Postiz account for social media management"""
    try:
        result = service.connect_account(
            agent_id=agent_id,
            api_key=request.api_key,
            platforms=request.platforms,
            workspace_id=request.workspace_id,
            account_name=request.account_name,
            platform_tokens=request.platform_tokens
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return PostAccountResponse(**result)


@router.get("/accounts", response_model=List[PostAccountResponse])
def list_accounts(
    agent_id: int,
    service: PostizService = Depends(get_postiz_service)
):
    """List all connected Postiz accounts"""
    results = service.list_accounts(agent_id)
    return [PostAccountResponse(**r) for r in results]


@router.get("/accounts/{account_id}")
def get_account(
    account_id: int,
    service: PostizService = Depends(get_postiz_service)
):
    """Get account details"""
    try:
        return service.get_account(account_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Post Creation & Management
# ============================================================================

@router.post("/posts/create", response_model=PostResponse)
def create_post(
    request: PostCreateRequest,
    agent_id: int,
    service: PostizService = Depends(get_postiz_service)
):
    """Create social media post with AI-powered optimization"""
    try:
        result = service.create_post(
            agent_id=agent_id,
            content_type=request.content_type,
            caption=request.caption,
            media_type=request.media_type,
            hashtags=request.hashtags,
            mention_accounts=request.mention_accounts,
            media_urls=request.media_urls,
            property_id=request.property_id,
            scheduled_at_str=request.scheduled_at,
            scheduled_timezone=request.scheduled_timezone,
            publish_immediately=request.publish_immediately,
            platforms=request.platforms,
            use_branding=request.use_branding
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return PostResponse(**result)


@router.post("/posts/{post_id}/schedule")
def schedule_post(
    post_id: int,
    scheduled_at: str,
    platforms: ListType[str],
    timezone: str = "America/New_York",
    service: PostizService = Depends(get_postiz_service)
):
    """Schedule post for specific time"""
    try:
        return service.schedule_post(
            post_id=post_id,
            scheduled_at=scheduled_at,
            platforms=platforms,
            timezone_str=timezone
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/posts", response_model=List[PostResponse])
def list_posts(
    agent_id: int,
    status: Optional[str] = None,
    property_id: Optional[int] = None,
    limit: int = 50,
    service: PostizService = Depends(get_postiz_service)
):
    """List all posts"""
    results = service.list_posts(
        agent_id=agent_id,
        status=status,
        property_id=property_id,
        limit=limit
    )
    return [PostResponse(**r) for r in results]


@router.get("/posts/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    service: PostizService = Depends(get_postiz_service)
):
    """Get post details"""
    try:
        result = service.get_post(post_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return PostResponse(**result)


@router.put("/posts/{post_id}")
def update_post(
    post_id: int,
    request: PostUpdateRequest,
    service: PostizService = Depends(get_postiz_service)
):
    """Update post"""
    try:
        return service.update_post(
            post_id=post_id,
            caption=request.caption,
            hashtags=request.hashtags,
            scheduled_at_str=request.scheduled_at,
            status=request.status
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    service: PostizService = Depends(get_postiz_service)
):
    """Delete post"""
    try:
        return service.delete_post(post_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/posts/{post_id}/publish")
async def publish_post(
    post_id: int,
    service: PostizService = Depends(get_postiz_service)
):
    """Immediately publish post to all platforms"""
    try:
        return await service.publish_post_now(post_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# AI Content Generation
# ============================================================================

@router.post("/ai/generate")
def generate_content_with_ai(
    request: AIGenerateRequest,
    agent_id: int,
    service: PostizService = Depends(get_postiz_service)
):
    """Generate social media content with AI"""
    try:
        return service.generate_content(
            agent_id=agent_id,
            content_type=request.content_type,
            platform=request.platform,
            tone=request.tone,
            property_id=request.property_id,
            include_price=request.include_price,
            include_address=request.include_address,
            custom_instructions=request.custom_instructions
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Campaigns
# ============================================================================

@router.post("/campaigns/create")
def create_social_campaign(
    request: CampaignCreateRequest,
    agent_id: int,
    service: PostizService = Depends(get_postiz_service)
):
    """Create multi-post campaign with auto-generated content"""
    try:
        return service.create_campaign(
            agent_id=agent_id,
            campaign_name=request.campaign_name,
            campaign_type=request.campaign_type,
            start_date_str=request.start_date,
            platforms=request.platforms,
            property_id=request.property_id,
            end_date_str=request.end_date,
            post_count=request.post_count,
            use_branding=request.use_branding,
            auto_generate=request.auto_generate
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/campaigns")
def list_social_campaigns(
    agent_id: int,
    status: Optional[str] = None,
    service: PostizService = Depends(get_postiz_service)
):
    """List all campaigns"""
    return service.list_campaigns(agent_id=agent_id, status=status)


# ============================================================================
# Templates
# ============================================================================

@router.post("/templates/create")
def create_social_template(
    request: TemplateCreateRequest,
    agent_id: int,
    service: PostizService = Depends(get_postiz_service)
):
    """Create reusable post template"""
    return service.create_template(
        agent_id=agent_id,
        template_name=request.template_name,
        template_category=request.template_category,
        caption_template=request.caption_template,
        hashtag_template=request.hashtag_template,
        media_type=request.media_type,
        media_count=request.media_count,
        ai_generate_caption=request.ai_generate_caption
    )


@router.get("/templates")
def list_social_templates(
    agent_id: int,
    category: Optional[str] = None,
    service: PostizService = Depends(get_postiz_service)
):
    """List all templates"""
    return service.list_templates(agent_id=agent_id, category=category)


@router.post("/templates/{template_id}/use")
def use_template(
    template_id: int,
    property_id: Optional[int] = None,
    service: PostizService = Depends(get_postiz_service)
):
    """Generate post from template"""
    try:
        return service.use_template(template_id=template_id, property_id=property_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Analytics
# ============================================================================

@router.get("/analytics/overview")
def get_social_analytics_overview(
    agent_id: int,
    period_type: str = "weekly",
    service: PostizService = Depends(get_postiz_service)
):
    """Get analytics overview for period"""
    return service.get_analytics_overview(agent_id=agent_id, period_type=period_type)


@router.get("/analytics/posts/{post_id}")
def get_post_analytics(
    post_id: int,
    service: PostizService = Depends(get_postiz_service)
):
    """Get analytics for specific post"""
    try:
        return service.get_post_analytics(post_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Calendar
# ============================================================================

@router.get("/calendar")
def get_content_calendar(
    agent_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    service: PostizService = Depends(get_postiz_service)
):
    """Get content calendar with scheduled posts"""
    return service.get_content_calendar(
        agent_id=agent_id,
        start_date_str=start_date,
        end_date_str=end_date
    )


# ============================================================================
# Real Postiz API Integration
# ============================================================================

@router.post("/api/preview")
async def preview_post(
    request: PreviewPostRequest,
    agent_id: int,
    service: PostizService = Depends(get_postiz_service)
):
    """Preview post without publishing

    Returns a preview of how the post will look on each platform
    with character counts, warnings, and platform-specific optimizations.
    """
    try:
        return service.preview_post(
            agent_id=agent_id,
            caption=request.caption,
            platforms=request.platforms,
            media_urls=request.media_urls,
            hashtags=request.hashtags,
            property_id=request.property_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/api/upload-media")
async def upload_media_to_postiz(
    agent_id: int,
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = None,
    service: PostizService = Depends(get_postiz_service)
):
    """Upload media to Postiz

    Uploads image or video to Postiz for use in posts.
    Supports either file upload or URL.

    Returns:
        {
            "id": "img-123",
            "path": "https://uploads.postiz.com/photo.jpg"
        }
    """
    try:
        if file:
            # Save uploaded file temporarily
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name

            result = await service.upload_media(agent_id=agent_id, file_path=tmp_path)

            # Cleanup
            os.unlink(tmp_path)

            return {
                "media_id": result.get("id"),
                "media_url": result.get("path"),
                "voice_summary": f"Media uploaded successfully to Postiz."
            }

        elif image_url:
            result = await service.upload_media(agent_id=agent_id, image_url=image_url)

            return {
                "media_id": result.get("id"),
                "media_url": result.get("path"),
                "original_url": image_url,
                "voice_summary": f"Media uploaded from URL to Postiz."
            }
        else:
            raise HTTPException(status_code=400, detail="Either file or image_url must be provided")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/publish")
async def publish_post_to_postiz(
    request: DirectPostRequest,
    agent_id: int,
    service: PostizService = Depends(get_postiz_service)
):
    """Create and publish post directly to Postiz API

    This endpoint integrates with the real Postiz API to:
    1. Upload media (if provided)
    2. Create post with platform-specific content
    3. Publish immediately or schedule

    Args:
        caption: Post caption text
        platforms: List of platforms (facebook, instagram, twitter, linkedin, tiktok)
        media_urls: Optional list of image URLs
        hashtags: Optional hashtags
        scheduled_at: Optional ISO datetime for scheduling
        publish_immediately: True to publish now, False to schedule
        property_id: Optional property ID for context

    Returns:
        Published post info with Postiz post ID and platform IDs
    """
    try:
        return await service.publish_direct(
            agent_id=agent_id,
            caption=request.caption,
            platforms=request.platforms,
            media_urls=request.media_urls,
            hashtags=request.hashtags,
            scheduled_at_str=request.scheduled_at,
            publish_immediately=request.publish_immediately,
            property_id=request.property_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish post: {str(e)}")


@router.get("/api/integrations")
async def get_postiz_integrations(
    agent_id: int,
    service: PostizService = Depends(get_postiz_service)
):
    """Get connected social media accounts from Postiz

    Returns list of all connected platforms (integrations/channels)
    with their IDs and details.
    """
    try:
        return await service.get_integrations(agent_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get integrations: {str(e)}")


@router.post("/api/property/{property_id}/publish")
async def publish_property_post(
    property_id: int,
    agent_id: int,
    platforms: ListType[str] = ["facebook", "instagram"],
    scheduled_at: Optional[str] = None,
    publish_immediately: bool = True,
    service: PostizService = Depends(get_postiz_service)
):
    """Auto-generate and publish property post

    Creates a property promotion post using:
    - Property details (address, price, features)
    - Agent branding
    - Property photos from enrichment

    Args:
        property_id: Property ID
        agent_id: Agent ID
        platforms: Platforms to publish to
        scheduled_at: Optional schedule time
        publish_immediately: Publish now if True

    Returns:
        Published post info
    """
    try:
        return await service.publish_property(
            property_id=property_id,
            agent_id=agent_id,
            platforms=platforms,
            scheduled_at_str=scheduled_at,
            publish_immediately=publish_immediately
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish property post: {str(e)}")


@router.post("/api/batch-publish")
async def batch_publish_posts(
    agent_id: int,
    property_ids: ListType[int],
    platforms: ListType[str] = ["facebook", "instagram"],
    service: PostizService = Depends(get_postiz_service)
):
    """Publish posts for multiple properties at once

    Args:
        agent_id: Agent ID
        property_ids: List of property IDs
        platforms: Platforms to publish to

    Returns:
        List of publish results
    """
    results = []

    for property_id in property_ids:
        try:
            result = await service.publish_property(
                property_id=property_id,
                agent_id=agent_id,
                platforms=platforms,
                publish_immediately=True
            )
            results.append({
                "property_id": property_id,
                "success": True,
                "result": result
            })
        except Exception as e:
            results.append({
                "property_id": property_id,
                "success": False,
                "error": str(e)
            })

    successful = sum(1 for r in results if r["success"])

    return {
        "agent_id": agent_id,
        "total": len(property_ids),
        "successful": successful,
        "failed": len(property_ids) - successful,
        "results": results,
        "voice_summary": f"Batch publish complete: {successful}/{len(property_ids)} posts published successfully."
    }
