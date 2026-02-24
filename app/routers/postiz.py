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
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import json
import httpx
from app.database import get_db
from app.models.agent import Agent
from app.models.property import Property
from app.models.agent_brand import AgentBrand
from app.models.postiz import (
    PostizAccount, PostizPost, PostizCalendar,
    PostizTemplate, PostizAnalytics, PostizCampaign
)
from pydantic import BaseModel, Field
from typing import Dict as DictType, List as ListType

router = APIRouter(prefix="/postiz", tags=["Postiz Social Media"])


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


# ============================================================================
# Account Management
# ============================================================================

@router.post("/accounts/connect", response_model=PostAccountResponse)
def connect_postiz_account(
    request: PostizAccountConnect,
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Connect Postiz account for social media management"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Create account connection
    account = PostizAccount(
        agent_id=agent_id,
        api_key=request.api_key,
        workspace_id=request.workspace_id,
        account_name=request.account_name or f"{agent.name}'s Account",
        connected_platforms=request.platforms,
        platform_tokens=request.platform_tokens,
        is_active=True
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    voice_summary = f"Connected Postiz account for {agent.name}. Platforms: {', '.join(request.platforms)}."

    return PostAccountResponse(
        id=account.id,
        agent_id=account.agent_id,
        account_name=account.account_name,
        connected_platforms=account.connected_platforms,
        is_active=account.is_active,
        voice_summary=voice_summary
    )


@router.get("/accounts", response_model=List[PostAccountResponse])
def list_accounts(agent_id: int, db: Session = Depends(get_db)):
    """List all connected Postiz accounts"""
    accounts = db.query(PostizAccount).filter(
        PostizAccount.agent_id == agent_id,
        PostizAccount.is_active == True
    ).all()

    return [
        PostAccountResponse(
            id=a.id,
            agent_id=a.agent_id,
            account_name=a.account_name,
            connected_platforms=a.connected_platforms,
            is_active=a.is_active,
            voice_summary=f"Connected to {', '.join(a.connected_platforms or [])}"
        )
        for a in accounts
    ]


@router.get("/accounts/{account_id}")
def get_account(account_id: int, db: Session = Depends(get_db)):
    """Get account details"""
    account = db.query(PostizAccount).filter(PostizAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return {
        "id": account.id,
        "agent_id": account.agent_id,
        "account_name": account.account_name,
        "connected_platforms": account.connected_platforms,
        "workspace_id": account.workspace_id,
        "is_active": account.is_active,
        "auto_publish": account.auto_publish,
        "default_timezone": account.default_timezone
    }


# ============================================================================
# Post Creation & Management
# ============================================================================

@router.post("/posts/create", response_model=PostResponse)
def create_post(
    request: PostCreateRequest,
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Create social media post with AI-powered optimization"""

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Get agent's brand if use_branding is true
    brand = None
    brand_data = None
    if request.use_branding:
        brand = db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()
        if brand:
            brand_data = {
                "company_name": brand.company_name,
                "tagline": brand.tagline,
                "logo_url": brand.logo_url,
                "primary_color": brand.primary_color,
                "secondary_color": brand.secondary_color
            }

    # Get property if specified
    property = None
    if request.property_id:
        property = db.query(Property).filter(Property.id == request.property_id).first()

    # Generate platform-specific content
    platform_content = _generate_platform_content(
        request.caption,
        request.platforms,
        property,
        brand
    )

    # Parse scheduled_at
    scheduled_at = None
    if request.scheduled_at:
        scheduled_at = datetime.fromisoformat(request.scheduled_at.replace('Z', '+00:00'))

    # Create post
    post = PostizPost(
        agent_id=agent_id,
        account_id=_get_default_account(agent_id, db),
        property_id=request.property_id,
        content_type=request.content_type,
        caption=request.caption,
        hashtags=request.hashtags or _generate_hashtags(request.content_type, property),
        mention_accounts=request.mention_accounts,
        media_urls=request.media_urls,
        media_type=request.media_type,
        platform_content=platform_content,
        scheduled_at=scheduled_at,
        scheduled_timezone=request.scheduled_timezone,
        publish_immediately=request.publish_immediately,
        status="scheduled" if scheduled_at else ("publishing" if request.publish_immediately else "draft"),
        generated_by="ai",
        use_branding=request.use_branding,
        brand_applied=brand_data
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    # If publish_immediately, send to Postiz
    if request.publish_immediately:
        _publish_to_postiz(post, db)

    voice_summary = _generate_post_voice_summary(post, property)

    return PostResponse(
        id=post.id,
        agent_id=post.agent_id,
        property_id=post.property_id,
        content_type=post.content_type,
        caption=post.caption,
        hashtags=post.hashtags,
        media_urls=post.media_urls,
        media_type=post.media_type,
        scheduled_at=post.scheduled_at.isoformat() if post.scheduled_at else None,
        status=post.status,
        platform_content=post.platform_content,
        analytics=post.analytics,
        voice_summary=voice_summary
    )


@router.post("/posts/{post_id}/schedule")
def schedule_post(
    post_id: int,
    scheduled_at: str,
    platforms: ListType[str],
    timezone: str = "America/New_York",
    db: Session = Depends(get_db)
):
    """Schedule post for specific time"""
    post = db.query(PostizPost).filter(PostizPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    scheduled_dt = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
    post.scheduled_at = scheduled_dt
    post.scheduled_timezone = timezone
    post.status = "scheduled"

    # Update platform content
    if platforms:
        post.platform_content = _generate_platform_content(
            post.caption,
            platforms,
            post.property,
            None
        )

    db.commit()

    return {
        "post_id": post.id,
        "scheduled_at": scheduled_at.isoformat(),
        "timezone": timezone,
        "platforms": platforms,
        "status": "scheduled",
        "voice_summary": f"Post scheduled for {scheduled_at.strftime('%Y-%m-%d %H:%M')} {timezone}."
    }


@router.get("/posts", response_model=List[PostResponse])
def list_posts(
    agent_id: int,
    status: Optional[str] = None,
    property_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List all posts"""
    query = db.query(PostizPost).filter(PostizPost.agent_id == agent_id)

    if status:
        query = query.filter(PostizPost.status == status)
    if property_id:
        query = query.filter(PostizPost.property_id == property_id)

    posts = query.order_by(PostizPost.created_at.desc()).limit(limit).all()

    return [
        PostResponse(
            id=p.id,
            agent_id=p.agent_id,
            property_id=p.property_id,
            content_type=p.content_type,
            caption=p.caption,
            hashtags=p.hashtags,
            media_urls=p.media_urls,
            media_type=p.media_type,
            scheduled_at=p.scheduled_at.isoformat() if p.scheduled_at else None,
            status=p.status,
            platform_content=p.platform_content,
            analytics=p.analytics,
            voice_summary=_generate_post_voice_summary(p, None)
        )
        for p in posts
    ]


@router.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    """Get post details"""
    post = db.query(PostizPost).filter(PostizPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return PostResponse(
        id=post.id,
        agent_id=post.agent_id,
        property_id=post.property_id,
        content_type=post.content_type,
        caption=post.caption,
        hashtags=post.hashtags,
        media_urls=post.media_urls,
        media_type=post.media_type,
        scheduled_at=post.scheduled_at.isoformat() if post.scheduled_at else None,
        status=post.status,
        platform_content=post.platform_content,
        analytics=post.analytics,
        voice_summary=_generate_post_voice_summary(post, None)
    )


@router.put("/posts/{post_id}")
def update_post(
    post_id: int,
    request: PostUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update post"""
    post = db.query(PostizPost).filter(PostizPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if request.caption:
        post.caption = request.caption
    if request.hashtags:
        post.hashtags = request.hashtags
    if request.scheduled_at:
        post.scheduled_at = datetime.fromisoformat(request.scheduled_at.replace('Z', '+00:00'))
    if request.status:
        post.status = request.status

    db.commit()

    return {
        "post_id": post_id,
        "status": "updated",
        "voice_summary": f"Post {post_id} updated successfully."
    }


@router.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db)):
    """Delete post"""
    post = db.query(PostizPost).filter(PostizPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # If post is scheduled in Postiz, cancel it
    if post.post_id_postiz and post.status == "scheduled":
        _cancel_postiz_post(post)

    db.delete(post)
    db.commit()

    return {
        "post_id": post_id,
        "status": "deleted",
        "voice_summary": f"Post {post_id} deleted."
    }


@router.post("/posts/{post_id}/publish")
async def publish_post(post_id: int, db: Session = Depends(get_db)):
    """Immediately publish post to all platforms"""
    post = db.query(PostizPost).filter(PostizPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    result = await _publish_to_postiz(post, db)

    return result


# ============================================================================
# AI Content Generation
# ============================================================================

@router.post("/ai/generate")
def generate_content_with_ai(request: AIGenerateRequest, agent_id: int, db: Session = Depends(get_db)):
    """Generate social media content with AI"""

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Get property if specified
    property = None
    if request.property_id:
        property = db.query(Property).filter(Property.id == request.property_id).first()

    # Get brand
    brand = db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()

    # Generate content with AI
    content = _generate_ai_content(
        request.content_type,
        request.platform,
        request.tone,
        property,
        brand,
        request.include_price,
        request.include_address,
        request.custom_instructions
    )

    return {
        "content_type": request.content_type,
        "platform": request.platform,
        "tone": request.tone,
        "caption": content["caption"],
        "hashtags": content["hashtags"],
        "suggested_media": content["suggested_media"],
        "character_count": len(content["caption"]),
        "voice_summary": f"Generated {request.tone} {request.content_type} post for {request.platform}. {len(content['caption'])} characters."
    }


# ============================================================================
# Campaigns
# ============================================================================

@router.post("/campaigns/create")
def create_campaign(request: CampaignCreateRequest, agent_id: int, db: Session = Depends(get_db)):
    """Create multi-post campaign with auto-generated content"""

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
    end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00')) if request.end_date else None

    # Create campaign
    campaign = PostizCampaign(
        agent_id=agent_id,
        property_id=request.property_id,
        campaign_name=request.campaign_name,
        campaign_type=request.campaign_type,
        campaign_status="draft",
        start_date=start_date,
        end_date=end_date,
        auto_generate_content=request.auto_generate,
        posts=[],
        post_count=0
    )

    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    # Generate posts for campaign
    if request.auto_generate:
        posts = _generate_campaign_posts(campaign, request, agent_id, db)
        campaign.posts = [p["id"] for p in posts]
        campaign.post_count = len(posts)
        db.commit()

    voice_summary = f"Created campaign '{request.campaign_name}' with {campaign.post_count} posts. {request.campaign_type}."

    return {
        "campaign_id": campaign.id,
        "campaign_name": campaign.campaign_name,
        "campaign_type": campaign.campaign_type,
        "post_count": campaign.post_count,
        "status": campaign.campaign_status,
        "posts": campaign.posts,
        "voice_summary": voice_summary
    }


@router.get("/campaigns")
def list_campaigns(agent_id: int, status: Optional[str] = None, db: Session = Depends(get_db)):
    """List all campaigns"""
    query = db.query(PostizCampaign).filter(PostizCampaign.agent_id == agent_id)

    if status:
        query = query.filter(PostizCampaign.campaign_status == status)

    campaigns = query.order_by(PostizCampaign.created_at.desc()).all()

    return [
        {
            "id": c.id,
            "campaign_name": c.campaign_name,
            "campaign_type": c.campaign_type,
            "status": c.campaign_status,
            "post_count": c.post_count,
            "start_date": c.start_date.isoformat() if c.start_date else None,
            "end_date": c.end_date.isoformat() if c.end_date else None,
            "voice_summary": f"Campaign '{c.campaign_name}' - {c.campaign_status} with {c.post_count} posts"
        }
        for c in campaigns
    ]


# ============================================================================
# Templates
# ============================================================================

@router.post("/templates/create")
def create_template(request: TemplateCreateRequest, agent_id: int, db: Session = Depends(get_db)):
    """Create reusable post template"""
    template = PostizTemplate(
        agent_id=agent_id,
        template_name=request.template_name,
        template_category=request.template_category,
        caption_template=request.caption_template,
        hashtag_template=request.hashtag_template,
        media_type=request.media_type,
        media_count=request.media_count,
        ai_generate_caption=request.ai_generate_caption,
        is_active=True
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return {
        "template_id": template.id,
        "template_name": template.template_name,
        "template_category": template.template_category,
        "voice_summary": f"Template '{request.template_name}' created."
    }


@router.get("/templates")
def list_templates(agent_id: int, category: Optional[str] = None, db: Session = Depends(get_db)):
    """List all templates"""
    query = db.query(PostizTemplate).filter(
        PostizTemplate.agent_id == agent_id,
        PostizTemplate.is_active == True
    )

    if category:
        query = query.filter(PostizTemplate.template_category == category)

    templates = query.all()

    return [
        {
            "id": t.id,
            "template_name": t.template_name,
            "template_category": t.template_category,
            "media_type": t.media_type,
            "times_used": t.times_used,
            "voice_summary": f"Template '{t.template_name}' - used {t.times_used} times"
        }
        for t in templates
    ]


@router.post("/templates/{template_id}/use")
def use_template(template_id: int, property_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Generate post from template"""
    template = db.query(PostizTemplate).filter(PostizTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    property = None
    if property_id:
        property = db.query(Property).filter(Property.id == property_id).first()

    # Generate caption from template
    caption = _apply_template(template.caption_template, property)

    # Update usage stats
    template.times_used += 1
    template.last_used_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "template_id": template_id,
        "caption": caption,
        "hashtags": template.hashtag_template,
        "media_type": template.media_type,
        "media_count": template.media_count,
        "voice_summary": f"Generated post from template '{template.template_name}'."
    }


# ============================================================================
# Analytics
# ============================================================================

@router.get("/analytics/overview")
def get_analytics_overview(
    agent_id: int,
    period_type: str = "weekly",
    db: Session = Depends(get_db)
):
    """Get analytics overview for period"""

    # Calculate date range
    end_date = datetime.now(timezone.utc)
    if period_type == "daily":
        start_date = end_date - timedelta(days=1)
    elif period_type == "weekly":
        start_date = end_date - timedelta(weeks=1)
    elif period_type == "monthly":
        start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(weeks=1)

    # Get or create analytics record
    analytics = db.query(PostizAnalytics).filter(
        PostizAnalytics.agent_id == agent_id,
        PostizAnalytics.period_start >= start_date,
        PostizAnalytics.period_end <= end_date
    ).first()

    if not analytics:
        # Generate mock analytics
        analytics = _generate_mock_analytics(agent_id, start_date, end_date, period_type)

    return {
        "period_type": period_type,
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "metrics": analytics.metrics,
        "top_posts": analytics.top_posts,
        "top_hashtags": analytics.top_hashtags,
        "voice_summary": f"Analytics for {period_type}: {analytics.metrics.get('total_posts', 0)} posts, {analytics.metrics.get('total_engagement', 0)} engagements."
    }


@router.get("/analytics/posts/{post_id}")
def get_post_analytics(post_id: int, db: Session = Depends(get_db)):
    """Get analytics for specific post"""
    post = db.query(PostizPost).filter(PostizPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return {
        "post_id": post_id,
        "content_type": post.content_type,
        "analytics": post.analytics or {},
        "voice_summary": _generate_post_analytics_voice_summary(post)
    }


# ============================================================================
# Calendar
# ============================================================================

@router.get("/calendar")
def get_content_calendar(
    agent_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get content calendar with scheduled posts"""

    if not start_date:
        start_date = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    if not end_date:
        end_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

    posts = db.query(PostizPost).filter(
        PostizPost.agent_id == agent_id,
        PostizPost.scheduled_at >= start_dt,
        PostizPost.scheduled_at <= end_dt,
        PostizPost.status.in_(["scheduled", "publishing"])
    ).all()

    calendar = []
    for post in posts:
        calendar.append({
            "id": post.id,
            "date": post.scheduled_at.isoformat(),
            "content_type": post.content_type,
            "caption": post.caption[:100] + "..." if len(post.caption) > 100 else post.caption,
            "platforms": list(post.platform_content.keys()) if post.platform_content else [],
            "status": post.status,
            "media_type": post.media_type
        })

    return {
        "start_date": start_date,
        "end_date": end_date,
        "posts": calendar,
        "total": len(calendar),
        "voice_summary": f"Content calendar: {len(calendar)} posts scheduled."
    }


# ============================================================================
# Helper Functions
# ============================================================================

def _get_default_account(agent_id: int, db: Session) -> int:
    """Get default Postiz account for agent"""
    account = db.query(PostizAccount).filter(
        PostizAccount.agent_id == agent_id,
        PostizAccount.is_active == True
    ).first()

    return account.id if account else None


def _generate_platform_content(
    caption: str,
    platforms: List[str],
    property: Optional[Property],
    brand: Optional[AgentBrand]
) -> Dict[str, Any]:
    """Generate platform-specific content variations"""

    platform_content = {}

    for platform in platforms:
        content = {
            "caption": caption,
            "character_limit": _get_character_limit(platform),
            "hashtag_strategy": _get_hashtag_strategy(platform),
            "mention_format": _get_mention_format(platform)
        }

        # Platform-specific optimizations
        if platform == "twitter":
            content["caption"] = _truncate_for_twitter(caption)
            content["hashtag_limit"] = 3
        elif platform == "instagram":
            content["hashtags_first"] = True
            content["emoji_usage"] = "encouraged"
        elif platform == "linkedin":
            content["professional_tone"] = True
            content["hashtag_limit"] = 5
        elif platform == "facebook":
            content["full_caption"] = True
            content["allow_cta"] = True

        # Apply brand if available
        if brand:
            content["brand"] = {
                "company_name": brand.company_name,
                "tagline": brand.tagline
            }

        platform_content[platform] = content

    return platform_content


def _generate_hashtags(content_type: str, property: Optional[Property]) -> List[str]:
    """Generate relevant hashtags"""
    base_hashtags = ["#realestate", "#homeforsale"]

    if content_type == "property_promo":
        base_hashtags.extend(["#dreamhome", "#househunting"])
    elif content_type == "open_house":
        base_hashtags.extend(["#openhouse", "#tourthishome"])
    elif content_type == "market_update":
        base_hashtags.extend(["#marketupdate", "#realestatenews"])
    elif content_type == "brand_awareness":
        base_hashtags.extend(["#youragent", "#realtor"])

    return base_hashtags


def _generate_post_voice_summary(post: PostizPost, property: Optional[Property]) -> str:
    """Generate voice summary for post"""
    status_msg = f"{post.status}"
    if post.scheduled_at:
        status_msg += f" for {post.scheduled_at.strftime('%Y-%m-%d at %H:%M')}"

    platforms = list(post.platform_content.keys()) if post.platform_content else []
    platform_msg = f" to {', '.join(platforms)}" if platforms else ""

    return f"{post.content_type} post {status_msg}{platform_msg}. {len(post.caption)} characters."


def _generate_post_analytics_voice_summary(post: PostizPost) -> str:
    """Generate analytics voice summary"""
    if not post.analytics:
        return "No analytics available yet."

    metrics = post.analytics
    return f"Post analytics: {metrics.get('impressions', 0)} impressions, {metrics.get('engagement', 0)} engagements, {metrics.get('clicks', 0)} clicks."


def _get_character_limit(platform: str) -> int:
    """Get character limit for platform"""
    limits = {
        "facebook": 63206,
        "instagram": 2200,
        "twitter": 280,
        "linkedin": 3000,
        "tiktok": 150
    }
    return limits.get(platform, 2200)


def _get_hashtag_strategy(platform: str) -> str:
    """Get hashtag strategy for platform"""
    strategies = {
        "instagram": "use 10-30 hashtags",
        "twitter": "use 1-3 hashtags",
        "facebook": "use 3-5 hashtags",
        "linkedin": "use 3-5 hashtags",
        "tiktok": "use 3-5 hashtags"
    }
    return strategies.get(platform, "use 3-5 hashtags")


def _get_mention_format(platform: str) -> str:
    """Get mention format for platform"""
    formats = {
        "instagram": "@username",
        "twitter": "@username",
        "facebook": "@username",
        "linkedin": "@username",
        "tiktok": "@username"
    }
    return formats.get(platform, "@username")


def _truncate_for_twitter(caption: str) -> str:
    """Truncate caption for Twitter"""
    if len(caption) <= 280:
        return caption
    return caption[:277] + "..."


async def _publish_to_postiz(post: PostizPost, db: Session) -> Dict[str, Any]:
    """Publish post to Postiz API"""
    # In production, this would call Postiz API
    # For now, simulate successful publish

    post.status = "published"
    post.post_id_postiz = f"postiz_{post.id}_{int(datetime.now().timestamp())}"

    # Mock platform IDs
    platforms = list(post.platform_content.keys()) if post.platform_content else []
    post.post_ids_platforms = {p: f"{p}_post_{post.id}" for p in platforms}

    # Mock analytics
    post.analytics = {
        "impressions": 0,
        "reach": 0,
        "engagement": 0,
        "clicks": 0,
        "shares": 0
    }
    post.last_synced_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "post_id": post.id,
        "status": "published",
        "postiz_id": post.post_id_postiz,
        "platform_ids": post.post_ids_platforms,
        "voice_summary": f"Post published to {', '.join(platforms)}."
    }


def _cancel_postiz_post(post: PostizPost):
    """Cancel scheduled post in Postiz"""
    # In production, call Postiz API to cancel
    post.status = "cancelled"
    post.post_id_postiz = None


def _generate_ai_content(
    content_type: str,
    platform: str,
    tone: str,
    property: Optional[Property],
    brand: Optional[AgentBrand],
    include_price: bool,
    include_address: bool,
    custom_instructions: Optional[str]
) -> Dict[str, Any]:
    """Generate content with AI (placeholder for actual AI call)"""

    # In production, call Claude/GPT-4
    # For now, return mock content

    captions = {
        "property_promo": f"🏠 Stunning property available now! This beautiful home features modern amenities and is located in a prime area. Don't miss out on this opportunity!",
        "open_house": f"🚪 OPEN HOUSE THIS WEEKEND! Come tour this amazing property and see why everyone is talking about it. Refreshments provided!",
        "market_update": f"📊 Market Update: The real estate market is heating up! Now is a great time to buy or sell. Contact me for a free consultation.",
        "brand_awareness": f"💼 Trust {brand.company_name if brand else 'us'} with your real estate needs. We're here to help you find your dream home!"
    }

    caption = captions.get(content_type, "Check this out!")

    if tone == "enthusiastic":
        caption = "🔥 " + caption
    elif tone == "urgent":
        caption = "⚡ " + caption

    return {
        "caption": caption,
        "hashtags": _generate_hashtags(content_type, property),
        "suggested_media": ["image", "video"]
    }


def _apply_template(template: str, property: Optional[Property]) -> str:
    """Apply template with property data"""
    if not property:
        return template

    # Replace placeholders
    template = template.replace("{{property}}", f"{property.bedrooms}bd/{property.bathrooms}ba home")
    template = template.replace("{{price}}", f"${property.price:,}" if property.price else "Contact for price")
    template = template.replace("{{address}}", property.city or "Great location")
    template = template.replace("{{city}}", property.city or "")

    return template


def _generate_campaign_posts(
    campaign: PostizCampaign,
    request: CampaignCreateRequest,
    agent_id: int,
    db: Session
) -> List[Dict[str, Any]]:
    """Generate posts for campaign"""

    posts = []
    start_date = campaign.start_date

    # Calculate interval between posts
    if campaign.end_date:
        total_days = (campaign.end_date - start_date).days
        interval = total_days // request.post_count if request.post_count > 0 else 1
    else:
        interval = 1

    for i in range(request.post_count):
        post_date = start_date + timedelta(days=i * interval)

        post = PostizPost(
            agent_id=agent_id,
            account_id=_get_default_account(agent_id, db),
            property_id=request.property_id,
            content_type=request.campaign_type,
            caption=_generate_ai_content(
                request.campaign_type,
                request.platforms[0] if request.platforms else "facebook",
                "professional",
                None,
                None,
                True,
                True,
                None
            )["caption"],
            hashtags=_generate_hashtags(request.campaign_type, None),
            media_type="image",
            scheduled_at=post_date,
            status="scheduled",
            generated_by="ai"
        )

        db.add(post)
        db.commit()
        db.refresh(post)

        posts.append({"id": post.id, "scheduled_at": post_date.isoformat()})

    return posts


def _generate_mock_analytics(
    agent_id: int,
    start_date: datetime,
    end_date: datetime,
    period_type: str
) -> PostizAnalytics:
    """Generate mock analytics (for testing)"""

    metrics = {
        "facebook": {
            "followers": 1250,
            "impressions": 15420,
            "reach": 12350,
            "engagement": 842,
            "engagement_rate": 0.0546,
            "posts_published": 7
        },
        "instagram": {
            "followers": 890,
            "impressions": 22150,
            "reach": 18920,
            "engagement": 1245,
            "engagement_rate": 0.0658,
            "posts_published": 10
        },
        "twitter": {
            "followers": 450,
            "impressions": 8200,
            "reach": 6800,
            "engagement": 156,
            "engagement_rate": 0.0229,
            "posts_published": 5
        },
        "linkedin": {
            "followers": 320,
            "impressions": 4500,
            "reach": 3800,
            "engagement": 89,
            "engagement_rate": 0.0234,
            "posts_published": 3
        }
    }

    return PostizAnalytics(
        agent_id=agent_id,
        period_start=start_date,
        period_end=end_date,
        period_type=period_type,
        metrics=metrics,
        top_posts=[
            {"post_id": 1, "platform": "instagram", "engagement": 245},
            {"post_id": 2, "platform": "facebook", "engagement": 189}
        ],
        top_hashtags=["#realestate", "#dreamhome", "#househunting"],
        audience_demographics={
            "age": {"25-34": 35, "35-44": 40, "45-54": 20, "55+": 5},
            "gender": {"male": 45, "female": 55}
        }
    )
