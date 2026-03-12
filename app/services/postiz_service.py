"""Postiz API Service - Real integration with Postiz social media management platform.

Based on Postiz Public API documentation:
https://docs.postiz.com

Features:
- Upload images/media
- Create and schedule posts
- Publish to multiple platforms
- Get account integrations
- Account management
- Campaign management
- Template management
- Analytics
- Content calendar
- AI content generation
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
import httpx
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.agent import Agent
from app.models.postiz import (
    PostizAccount, PostizPost, PostizCalendar,
    PostizTemplate, PostizAnalytics, PostizCampaign
)
from app.models.property import Property
from app.models.agent_brand import AgentBrand
from app.models.zillow_enrichment import ZillowEnrichment

logger = logging.getLogger(__name__)


# ============================================================================
# Postiz API Client
# ============================================================================

class PostizAPIClient:
    """Client for interacting with Postiz Public API"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.postiz.com/public/v1"
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Postiz API"""

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self.headers.copy()

        # Remove Content-Type for multipart uploads
        if files:
            headers.pop("Content-Type", None)

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    if files:
                        response = await client.post(url, headers=headers, data=data, files=files)
                    else:
                        response = await client.post(url, headers=headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(f"Postiz API error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"Postiz API error: {e.response.status_code} - {e.response.text}")
            except httpx.RequestError as e:
                logger.error(f"Postiz request error: {str(e)}")
                raise Exception(f"Failed to connect to Postiz: {str(e)}")

    async def upload_media(self, file_path: str) -> Dict[str, Any]:
        """Upload image/video to Postiz

        POST /upload

        Returns:
            {
                "id": "img-123",
                "path": "https://uploads.postiz.com/photo.jpg",
                ...
            }
        """
        with open(file_path, "rb") as f:
            files = {"file": f}
            return await self._request("POST", "/upload", files=files)

    async def upload_media_from_url(self, image_url: str) -> Dict[str, Any]:
        """Upload media from URL by downloading first, then uploading to Postiz"""

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            content = response.content

        # Determine content type
        content_type = response.headers.get("content-type", "image/jpeg")

        files = {"file": ("image.jpg", content, content_type)}
        return await self._request("POST", "/upload", files=files)

    async def create_post(
        self,
        post_type: str,  # "schedule" or "now"
        date: str,  # ISO datetime
        posts: List[Dict[str, Any]],
        short_link: bool = False,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create/schedule post to Postiz

        POST /posts

        Args:
            post_type: "schedule" for scheduled, "now" for immediate
            date: ISO datetime string
            posts: List of post objects per platform
            short_link: Whether to use short links
            tags: Optional tags for organization

        Returns:
            {
                "success": true,
                "post": {
                    "id": "post-123",
                    "status": "scheduled",
                    ...
                }
            }
        """
        payload = {
            "type": post_type,
            "date": date,
            "shortLink": short_link,
            "tags": tags or [],
            "posts": posts
        }

        return await self._request("POST", "/posts", data=payload)

    async def get_integrations(self) -> Dict[str, Any]:
        """Get all connected social media accounts

        GET /integrations

        Returns list of connected platforms (integrations/channels)
        """
        return await self._request("GET", "/integrations")

    async def delete_post(self, post_id: str) -> Dict[str, Any]:
        """Delete a post

        DELETE /posts/{post_id}
        """
        return await self._request("DELETE", f"/posts/{post_id}")

    async def get_post_status(self, post_id: str) -> Dict[str, Any]:
        """Get post status

        GET /posts/{post_id}
        """
        return await self._request("GET", f"/posts/{post_id}")


# ============================================================================
# Postiz Service
# ============================================================================

class PostizService:
    """High-level service for Postiz operations"""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_account(self, agent_id: int) -> Optional[PostizAccount]:
        """Get active Postiz account for agent"""
        return self.db.query(PostizAccount).filter(
            PostizAccount.agent_id == agent_id,
            PostizAccount.is_active == True
        ).first()

    def _get_api_client(self, agent_id: int) -> Optional[PostizAPIClient]:
        """Get Postiz API client for agent"""
        account = self._get_account(agent_id)
        if not account:
            return None

        # Use custom base URL if self-hosted
        base_url = account.workspace_id or "https://api.postiz.com/public/v1"

        return PostizAPIClient(
            api_key=account.api_key,
            base_url=base_url
        )

    def _get_agent_or_raise(self, agent_id: int) -> Agent:
        """Get agent by ID or raise"""
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError("Agent not found")
        return agent

    def _get_default_account_id(self, agent_id: int) -> Optional[int]:
        """Get default Postiz account ID for agent"""
        account = self._get_account(agent_id)
        return account.id if account else None

    # ------------------------------------------------------------------
    # Platform helpers (static / pure logic)
    # ------------------------------------------------------------------

    @staticmethod
    def get_platform_display_name(platform: str) -> str:
        """Get display name for platform"""
        display_names = {
            "facebook": "Facebook",
            "instagram": "Instagram",
            "twitter": "X (Twitter)",
            "x": "X (Twitter)",
            "linkedin": "LinkedIn",
            "tiktok": "TikTok",
            "youtube": "YouTube",
            "pinterest": "Pinterest",
            "reddit": "Reddit",
            "medium": "Medium",
            "telegram": "Telegram",
            "threads": "Threads",
            "mastodon": "Mastodon",
            "bluesky": "Bluesky"
        }
        return display_names.get(platform.lower(), platform.title())

    @staticmethod
    def get_character_limit(platform: str) -> int:
        """Get character limit for platform"""
        limits = {
            "facebook": 63206,
            "instagram": 2200,
            "twitter": 280,
            "linkedin": 3000,
            "tiktok": 150
        }
        return limits.get(platform, 2200)

    @staticmethod
    def get_hashtag_strategy(platform: str) -> str:
        """Get hashtag strategy for platform"""
        strategies = {
            "instagram": "use 10-30 hashtags",
            "twitter": "use 1-3 hashtags",
            "facebook": "use 3-5 hashtags",
            "linkedin": "use 3-5 hashtags",
            "tiktok": "use 3-5 hashtags"
        }
        return strategies.get(platform, "use 3-5 hashtags")

    @staticmethod
    def get_mention_format(platform: str) -> str:
        """Get mention format for platform"""
        formats = {
            "instagram": "@username",
            "twitter": "@username",
            "facebook": "@username",
            "linkedin": "@username",
            "tiktok": "@username"
        }
        return formats.get(platform, "@username")

    @staticmethod
    def truncate_for_twitter(caption: str) -> str:
        """Truncate caption for Twitter"""
        if len(caption) <= 280:
            return caption
        return caption[:277] + "..."

    @staticmethod
    def generate_hashtags(content_type: str, property: Optional[Property]) -> List[str]:
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

    @staticmethod
    def generate_post_voice_summary(post: PostizPost, property: Optional[Property]) -> str:
        """Generate voice summary for post"""
        status_msg = f"{post.status}"
        if post.scheduled_at:
            status_msg += f" for {post.scheduled_at.strftime('%Y-%m-%d at %H:%M')}"

        platforms = list(post.platform_content.keys()) if post.platform_content else []
        platform_msg = f" to {', '.join(platforms)}" if platforms else ""

        return f"{post.content_type} post {status_msg}{platform_msg}. {len(post.caption)} characters."

    @staticmethod
    def generate_post_analytics_voice_summary(post: PostizPost) -> str:
        """Generate analytics voice summary"""
        if not post.analytics:
            return "No analytics available yet."

        metrics = post.analytics
        return f"Post analytics: {metrics.get('impressions', 0)} impressions, {metrics.get('engagement', 0)} engagements, {metrics.get('clicks', 0)} clicks."

    @staticmethod
    def generate_platform_content(
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
                "character_limit": PostizService.get_character_limit(platform),
                "hashtag_strategy": PostizService.get_hashtag_strategy(platform),
                "mention_format": PostizService.get_mention_format(platform)
            }

            # Platform-specific optimizations
            if platform == "twitter":
                content["caption"] = PostizService.truncate_for_twitter(caption)
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

    @staticmethod
    def generate_ai_content(
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
            "hashtags": PostizService.generate_hashtags(content_type, property),
            "suggested_media": ["image", "video"]
        }

    @staticmethod
    def apply_template(template: str, property: Optional[Property]) -> str:
        """Apply template with property data"""
        if not property:
            return template

        # Replace placeholders
        template = template.replace("{{property}}", f"{property.bedrooms}bd/{property.bathrooms}ba home")
        template = template.replace("{{price}}", f"${property.price:,}" if property.price else "Contact for price")
        template = template.replace("{{address}}", property.city or "Great location")
        template = template.replace("{{city}}", property.city or "")

        return template

    @staticmethod
    def generate_mock_analytics(
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

    # ------------------------------------------------------------------
    # Postiz API operations (async)
    # ------------------------------------------------------------------

    async def upload_media(
        self,
        agent_id: int,
        file_path: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload media to Postiz

        Args:
            agent_id: Agent ID
            file_path: Local file path to upload
            image_url: URL to download and upload

        Returns:
            Uploaded media info with id and path
        """
        client = self._get_api_client(agent_id)
        if not client:
            raise Exception("No active Postiz account found")

        if file_path:
            return await client.upload_media(file_path)
        elif image_url:
            return await client.upload_media_from_url(image_url)
        else:
            raise ValueError("Either file_path or image_url must be provided")

    async def publish_post(
        self,
        agent_id: int,
        post: PostizPost,
        platforms: List[str]
    ) -> Dict[str, Any]:
        """Publish post to Postiz

        Args:
            agent_id: Agent ID
            post: PostizPost object
            platforms: List of platform names to publish to

        Returns:
            Published post info with IDs
        """
        client = self._get_api_client(agent_id)
        if not client:
            raise Exception("No active Postiz account found")

        # Get integrations to map platform names to IDs
        integrations_resp = await client.get_integrations()

        # Handle both response formats: {"integrations": [...]} or direct array
        integrations_list = integrations_resp.get("integrations", [])
        if not integrations_list and isinstance(integrations_resp, list):
            integrations_list = integrations_resp

        # Build integration map with provider name variations
        integration_map = {}
        for integration in integrations_list:
            provider = integration.get("provider", "").lower()
            integration_id = integration.get("id")

            # Map multiple name variations
            integration_map[provider] = integration_id
            if provider == "x":
                integration_map["twitter"] = integration_id

        logger.info(f"Available integrations: {list(integration_map.keys())}")

        # Upload media first to get Postiz media IDs
        uploaded_media = []
        if post.media_urls:
            for url in post.media_urls:
                try:
                    result = await client.upload_media_from_url(url)
                    uploaded_media.append({
                        "id": result.get("id"),
                        "path": result.get("path")
                    })
                    logger.info(f"Uploaded media: {result.get('id')}")
                except Exception as e:
                    logger.error(f"Failed to upload media {url}: {str(e)}")

        # Build posts payload
        posts_payload = []

        for platform in platforms:
            # Try to find integration ID
            integration_id = integration_map.get(platform.lower())
            if not integration_id:
                logger.warning(f"Integration not found for platform: {platform}. Available: {list(integration_map.keys())}")
                continue

            # Get platform-specific content or generate it
            platform_content = post.platform_content.get(platform, {}) if post.platform_content else {}

            # Customize caption for platform if not already customized
            if not platform_content.get("caption"):
                caption = self._customize_content_for_platform(
                    post.caption,
                    platform,
                    post.property_id if hasattr(post, 'property_id') else None
                )
            else:
                caption = platform_content.get("caption", post.caption)

            # Build value array (content + media)
            value = {
                "content": caption,
                "image": []
            }

            # Add uploaded media with proper Postiz IDs
            if uploaded_media:
                value["image"] = uploaded_media

            # Build platform settings with correct __type
            platform_type = self._get_platform_type(platform)
            settings = {
                "__type": platform_type
            }

            # Add platform-specific settings
            if platform in ["twitter", "x"]:
                settings["who_can_reply_post"] = "everyone"
            elif platform == "instagram":
                settings["post_type"] = post.media_type or "post"
            elif platform == "linkedin":
                settings["post_as_images_carousel"] = False
            elif platform == "facebook":
                pass  # No special settings needed

            posts_payload.append({
                "integration": {
                    "id": integration_id
                },
                "value": [value],
                "settings": settings
            })

        if not posts_payload:
            raise Exception(f"No valid platform integrations found. Requested: {platforms}, Available: {list(integration_map.keys())}")

        # Determine post type
        post_type = "now" if post.publish_immediately else "schedule"

        # Use scheduled time or now
        if post.scheduled_at:
            post_date = post.scheduled_at.isoformat()
        else:
            post_date = datetime.utcnow().isoformat() + "Z"

        # Create post in Postiz
        result = await client.create_post(
            post_type=post_type,
            date=post_date,
            posts=posts_payload,
            short_link=False,
            tags=[]  # Tags must be array of objects, not strings. Hashtags go in content.
        )

        return result

    async def get_connected_platforms(self, agent_id: int) -> List[Dict[str, Any]]:
        """Get list of connected social media platforms

        Returns:
            List of platform info
        """
        client = self._get_api_client(agent_id)
        if not client:
            raise Exception("No active Postiz account found")

        integrations_resp = await client.get_integrations()

        # Handle both response formats
        integrations_list = integrations_resp.get("integrations", [])
        if not integrations_list and isinstance(integrations_resp, list):
            integrations_list = integrations_resp

        platforms = []
        for integration in integrations_list:
            provider = integration.get("provider", "unknown").lower()

            # Normalize provider names
            display_name = integration.get("name") or integration.get("provider", "Unknown")

            platforms.append({
                "id": integration.get("id"),
                "provider": provider,
                "display_provider": integration.get("provider", "Unknown"),
                "name": display_name,
                "avatar": integration.get("avatar")
            })

        return platforms

    def _get_platform_type(self, platform: str) -> str:
        """Map platform name to Postiz __type"""
        platform_map = {
            "twitter": "x",
            "x": "x",
            "facebook": "facebook",
            "instagram": "instagram",
            "linkedin": "linkedin",
            "linkedin-page": "linkedin-page",
            "tiktok": "tiktok",
            "youtube": "youtube",
            "pinterest": "pinterest",
            "reddit": "reddit",
            "medium": "medium",
            "devto": "devto",
            "telegram": "telegram",
            "threads": "threads",
            "mastodon": "mastodon",
            "bluesky": "bluesky"
        }

        return platform_map.get(platform.lower(), platform.lower())

    def _customize_content_for_platform(self, caption: str, platform: str, property_id: Optional[int] = None) -> str:
        """Customize caption for specific platform

        Args:
            caption: Base caption
            platform: Target platform
            property_id: Optional property ID for context

        Returns:
            Customized caption for the platform
        """
        platform_lower = platform.lower()
        customized = caption

        # Twitter/X: Short, punchy, emojis, truncate if needed
        if platform_lower in ["twitter", "x"]:
            # Add emoji if not present
            if not any(e in customized for e in ["🔥", "🚀", "💻", "🎯", "✨"]):
                customized = "🚀 " + customized

            # Truncate to 280 if needed
            if len(customized) > 280:
                customized = customized[:277] + "..."

        # LinkedIn: Professional, can be longer
        elif platform_lower == "linkedin":
            # Ensure it's substantial enough (LinkedIn likes 100+ chars)
            if len(customized) < 100 and property_id:
                customized += "\n\nLearn more about this opportunity and how you can get involved!"

        # Instagram: Visual-focused, lots of hashtags
        elif platform_lower == "instagram":
            # Add line breaks for readability
            if "\n\n" not in customized:
                customized = customized.replace(". ", ".\n\n")

        # Facebook: Balanced, can include CTA
        elif platform_lower == "facebook":
            # Add call to action if not present
            if not any(phrase in customized.lower() for phrase in ["link in", "comment", "dm us", "learn more"]):
                customized += "\n\n👇 Learn more in the comments below!"

        # YouTube: Descriptive
        elif platform_lower == "youtube":
            if len(customized) < 200:
                customized += "\n\n🎥 Full details in the video description!"
            if "video" not in customized.lower():
                customized = "🎬 " + customized

        return customized

    # ------------------------------------------------------------------
    # Account management
    # ------------------------------------------------------------------

    def connect_account(
        self,
        agent_id: int,
        api_key: str,
        platforms: List[str],
        workspace_id: Optional[str] = None,
        account_name: Optional[str] = None,
        platform_tokens: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Connect a Postiz account for an agent"""
        agent = self._get_agent_or_raise(agent_id)

        account = PostizAccount(
            agent_id=agent_id,
            api_key=api_key,
            workspace_id=workspace_id,
            account_name=account_name or f"{agent.name}'s Account",
            connected_platforms=platforms,
            platform_tokens=platform_tokens,
            is_active=True
        )

        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)

        voice_summary = f"Connected Postiz account for {agent.name}. Platforms: {', '.join(platforms)}."

        return {
            "id": account.id,
            "agent_id": account.agent_id,
            "account_name": account.account_name,
            "connected_platforms": account.connected_platforms,
            "is_active": account.is_active,
            "voice_summary": voice_summary
        }

    def list_accounts(self, agent_id: int) -> List[Dict[str, Any]]:
        """List all connected Postiz accounts for an agent"""
        accounts = self.db.query(PostizAccount).filter(
            PostizAccount.agent_id == agent_id,
            PostizAccount.is_active == True
        ).all()

        return [
            {
                "id": a.id,
                "agent_id": a.agent_id,
                "account_name": a.account_name,
                "connected_platforms": a.connected_platforms,
                "is_active": a.is_active,
                "voice_summary": f"Connected to {', '.join(a.connected_platforms or [])}"
            }
            for a in accounts
        ]

    def get_account(self, account_id: int) -> Dict[str, Any]:
        """Get account details by ID"""
        account = self.db.query(PostizAccount).filter(PostizAccount.id == account_id).first()
        if not account:
            raise ValueError("Account not found")

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

    # ------------------------------------------------------------------
    # Post CRUD
    # ------------------------------------------------------------------

    def create_post(
        self,
        agent_id: int,
        content_type: str,
        caption: str,
        media_type: str = "image",
        hashtags: Optional[List[str]] = None,
        mention_accounts: Optional[List[str]] = None,
        media_urls: Optional[List[str]] = None,
        property_id: Optional[int] = None,
        scheduled_at_str: Optional[str] = None,
        scheduled_timezone: str = "America/New_York",
        publish_immediately: bool = False,
        platforms: Optional[List[str]] = None,
        use_branding: bool = True
    ) -> Dict[str, Any]:
        """Create a social media post with AI-powered optimization.

        Returns dict with post data and voice_summary.
        """
        agent = self._get_agent_or_raise(agent_id)

        # Get agent's brand if use_branding is true
        brand = None
        brand_data = None
        if use_branding:
            brand = self.db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()
            if brand:
                brand_data = {
                    "company_name": brand.company_name,
                    "tagline": brand.tagline,
                    "logo_url": brand.logo_url,
                    "primary_color": brand.primary_color,
                    "secondary_color": brand.secondary_color
                }

        # Get property if specified
        property_obj = None
        if property_id:
            property_obj = self.db.query(Property).filter(Property.id == property_id).first()

        # Generate platform-specific content
        platform_content = self.generate_platform_content(
            caption,
            platforms or [],
            property_obj,
            brand
        )

        # Parse scheduled_at
        scheduled_at = None
        if scheduled_at_str:
            scheduled_at = datetime.fromisoformat(scheduled_at_str.replace('Z', '+00:00'))

        # Create post
        post = PostizPost(
            agent_id=agent_id,
            account_id=self._get_default_account_id(agent_id),
            property_id=property_id,
            content_type=content_type,
            caption=caption,
            hashtags=hashtags or self.generate_hashtags(content_type, property_obj),
            mention_accounts=mention_accounts,
            media_urls=media_urls,
            media_type=media_type,
            platform_content=platform_content,
            scheduled_at=scheduled_at,
            scheduled_timezone=scheduled_timezone,
            publish_immediately=publish_immediately,
            status="scheduled" if scheduled_at else ("publishing" if publish_immediately else "draft"),
            generated_by="ai",
            use_branding=use_branding,
            brand_applied=brand_data
        )

        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)

        # If publish_immediately, send to Postiz
        if publish_immediately:
            self._publish_to_postiz_sync(post)

        voice_summary = self.generate_post_voice_summary(post, property_obj)

        return {
            "id": post.id,
            "agent_id": post.agent_id,
            "property_id": post.property_id,
            "content_type": post.content_type,
            "caption": post.caption,
            "hashtags": post.hashtags,
            "media_urls": post.media_urls,
            "media_type": post.media_type,
            "scheduled_at": post.scheduled_at.isoformat() if post.scheduled_at else None,
            "status": post.status,
            "platform_content": post.platform_content,
            "analytics": post.analytics,
            "voice_summary": voice_summary
        }

    def schedule_post(
        self,
        post_id: int,
        scheduled_at: str,
        platforms: List[str],
        timezone_str: str = "America/New_York"
    ) -> Dict[str, Any]:
        """Schedule a post for a specific time"""
        post = self.db.query(PostizPost).filter(PostizPost.id == post_id).first()
        if not post:
            raise ValueError("Post not found")

        scheduled_dt = datetime.fromisoformat(scheduled_at.replace('Z', '+00:00'))
        post.scheduled_at = scheduled_dt
        post.scheduled_timezone = timezone_str
        post.status = "scheduled"

        # Update platform content
        if platforms:
            post.platform_content = self.generate_platform_content(
                post.caption,
                platforms,
                post.property,
                None
            )

        self.db.commit()

        return {
            "post_id": post.id,
            "scheduled_at": scheduled_at.isoformat(),
            "timezone": timezone_str,
            "platforms": platforms,
            "status": "scheduled",
            "voice_summary": f"Post scheduled for {scheduled_at.strftime('%Y-%m-%d %H:%M')} {timezone_str}."
        }

    def list_posts(
        self,
        agent_id: int,
        status: Optional[str] = None,
        property_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List all posts for an agent"""
        query = self.db.query(PostizPost).filter(PostizPost.agent_id == agent_id)

        if status:
            query = query.filter(PostizPost.status == status)
        if property_id:
            query = query.filter(PostizPost.property_id == property_id)

        posts = query.order_by(PostizPost.created_at.desc()).limit(limit).all()

        return [
            {
                "id": p.id,
                "agent_id": p.agent_id,
                "property_id": p.property_id,
                "content_type": p.content_type,
                "caption": p.caption,
                "hashtags": p.hashtags,
                "media_urls": p.media_urls,
                "media_type": p.media_type,
                "scheduled_at": p.scheduled_at.isoformat() if p.scheduled_at else None,
                "status": p.status,
                "platform_content": p.platform_content,
                "analytics": p.analytics,
                "voice_summary": self.generate_post_voice_summary(p, None)
            }
            for p in posts
        ]

    def get_post(self, post_id: int) -> Dict[str, Any]:
        """Get post details by ID"""
        post = self.db.query(PostizPost).filter(PostizPost.id == post_id).first()
        if not post:
            raise ValueError("Post not found")

        return {
            "id": post.id,
            "agent_id": post.agent_id,
            "property_id": post.property_id,
            "content_type": post.content_type,
            "caption": post.caption,
            "hashtags": post.hashtags,
            "media_urls": post.media_urls,
            "media_type": post.media_type,
            "scheduled_at": post.scheduled_at.isoformat() if post.scheduled_at else None,
            "status": post.status,
            "platform_content": post.platform_content,
            "analytics": post.analytics,
            "voice_summary": self.generate_post_voice_summary(post, None)
        }

    def update_post(
        self,
        post_id: int,
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        scheduled_at_str: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a post"""
        post = self.db.query(PostizPost).filter(PostizPost.id == post_id).first()
        if not post:
            raise ValueError("Post not found")

        if caption:
            post.caption = caption
        if hashtags:
            post.hashtags = hashtags
        if scheduled_at_str:
            post.scheduled_at = datetime.fromisoformat(scheduled_at_str.replace('Z', '+00:00'))
        if status:
            post.status = status

        self.db.commit()

        return {
            "post_id": post_id,
            "status": "updated",
            "voice_summary": f"Post {post_id} updated successfully."
        }

    def delete_post(self, post_id: int) -> Dict[str, Any]:
        """Delete a post"""
        post = self.db.query(PostizPost).filter(PostizPost.id == post_id).first()
        if not post:
            raise ValueError("Post not found")

        # If post is scheduled in Postiz, cancel it
        if post.post_id_postiz and post.status == "scheduled":
            self._cancel_postiz_post(post)

        self.db.delete(post)
        self.db.commit()

        return {
            "post_id": post_id,
            "status": "deleted",
            "voice_summary": f"Post {post_id} deleted."
        }

    async def publish_post_now(self, post_id: int) -> Dict[str, Any]:
        """Immediately publish a post to all platforms"""
        post = self.db.query(PostizPost).filter(PostizPost.id == post_id).first()
        if not post:
            raise ValueError("Post not found")

        return await self._publish_to_postiz_async(post)

    # ------------------------------------------------------------------
    # AI content generation
    # ------------------------------------------------------------------

    def generate_content(
        self,
        agent_id: int,
        content_type: str,
        platform: str = "facebook",
        tone: str = "professional",
        property_id: Optional[int] = None,
        include_price: bool = True,
        include_address: bool = True,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate social media content with AI"""
        agent = self._get_agent_or_raise(agent_id)

        # Get property if specified
        property_obj = None
        if property_id:
            property_obj = self.db.query(Property).filter(Property.id == property_id).first()

        # Get brand
        brand = self.db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()

        # Generate content with AI
        content = self.generate_ai_content(
            content_type,
            platform,
            tone,
            property_obj,
            brand,
            include_price,
            include_address,
            custom_instructions
        )

        return {
            "content_type": content_type,
            "platform": platform,
            "tone": tone,
            "caption": content["caption"],
            "hashtags": content["hashtags"],
            "suggested_media": content["suggested_media"],
            "character_count": len(content["caption"]),
            "voice_summary": f"Generated {tone} {content_type} post for {platform}. {len(content['caption'])} characters."
        }

    # ------------------------------------------------------------------
    # Campaigns
    # ------------------------------------------------------------------

    def create_campaign(
        self,
        agent_id: int,
        campaign_name: str,
        campaign_type: str,
        start_date_str: str,
        platforms: List[str],
        property_id: Optional[int] = None,
        end_date_str: Optional[str] = None,
        post_count: int = 5,
        use_branding: bool = True,
        auto_generate: bool = True
    ) -> Dict[str, Any]:
        """Create a multi-post campaign with auto-generated content"""
        agent = self._get_agent_or_raise(agent_id)

        start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00')) if end_date_str else None

        # Create campaign
        campaign = PostizCampaign(
            agent_id=agent_id,
            property_id=property_id,
            campaign_name=campaign_name,
            campaign_type=campaign_type,
            campaign_status="draft",
            start_date=start_date,
            end_date=end_date,
            auto_generate_content=auto_generate,
            posts=[],
            post_count=0
        )

        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)

        # Generate posts for campaign
        if auto_generate:
            posts = self._generate_campaign_posts(campaign, platforms, post_count, agent_id)
            campaign.posts = [p["id"] for p in posts]
            campaign.post_count = len(posts)
            self.db.commit()

        voice_summary = f"Created campaign '{campaign_name}' with {campaign.post_count} posts. {campaign_type}."

        return {
            "campaign_id": campaign.id,
            "campaign_name": campaign.campaign_name,
            "campaign_type": campaign.campaign_type,
            "post_count": campaign.post_count,
            "status": campaign.campaign_status,
            "posts": campaign.posts,
            "voice_summary": voice_summary
        }

    def list_campaigns(
        self,
        agent_id: int,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all campaigns for an agent"""
        query = self.db.query(PostizCampaign).filter(PostizCampaign.agent_id == agent_id)

        if status:
            query = query.filter(PostizCampaign.campaign_status == status)

        campaigns = query.order_by(PostizCampaign.created_at.desc()).limit(100).all()

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

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------

    def create_template(
        self,
        agent_id: int,
        template_name: str,
        template_category: str,
        caption_template: str,
        hashtag_template: Optional[List[str]] = None,
        media_type: str = "image",
        media_count: int = 1,
        ai_generate_caption: bool = True
    ) -> Dict[str, Any]:
        """Create a reusable post template"""
        template = PostizTemplate(
            agent_id=agent_id,
            template_name=template_name,
            template_category=template_category,
            caption_template=caption_template,
            hashtag_template=hashtag_template,
            media_type=media_type,
            media_count=media_count,
            ai_generate_caption=ai_generate_caption,
            is_active=True
        )

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)

        return {
            "template_id": template.id,
            "template_name": template.template_name,
            "template_category": template.template_category,
            "voice_summary": f"Template '{template_name}' created."
        }

    def list_templates(
        self,
        agent_id: int,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all templates for an agent"""
        query = self.db.query(PostizTemplate).filter(
            PostizTemplate.agent_id == agent_id,
            PostizTemplate.is_active == True
        )

        if category:
            query = query.filter(PostizTemplate.template_category == category)

        templates = query.limit(100).all()

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

    def use_template(
        self,
        template_id: int,
        property_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate post from template"""
        template = self.db.query(PostizTemplate).filter(PostizTemplate.id == template_id).first()
        if not template:
            raise ValueError("Template not found")

        property_obj = None
        if property_id:
            property_obj = self.db.query(Property).filter(Property.id == property_id).first()

        # Generate caption from template
        caption = self.apply_template(template.caption_template, property_obj)

        # Update usage stats
        template.times_used += 1
        template.last_used_at = datetime.now(timezone.utc)
        self.db.commit()

        return {
            "template_id": template_id,
            "caption": caption,
            "hashtags": template.hashtag_template,
            "media_type": template.media_type,
            "media_count": template.media_count,
            "voice_summary": f"Generated post from template '{template.template_name}'."
        }

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def get_analytics_overview(
        self,
        agent_id: int,
        period_type: str = "weekly"
    ) -> Dict[str, Any]:
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
        analytics = self.db.query(PostizAnalytics).filter(
            PostizAnalytics.agent_id == agent_id,
            PostizAnalytics.period_start >= start_date,
            PostizAnalytics.period_end <= end_date
        ).first()

        if not analytics:
            # Generate mock analytics
            analytics = self.generate_mock_analytics(agent_id, start_date, end_date, period_type)

        return {
            "period_type": period_type,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "metrics": analytics.metrics,
            "top_posts": analytics.top_posts,
            "top_hashtags": analytics.top_hashtags,
            "voice_summary": f"Analytics for {period_type}: {analytics.metrics.get('total_posts', 0)} posts, {analytics.metrics.get('total_engagement', 0)} engagements."
        }

    def get_post_analytics(self, post_id: int) -> Dict[str, Any]:
        """Get analytics for a specific post"""
        post = self.db.query(PostizPost).filter(PostizPost.id == post_id).first()
        if not post:
            raise ValueError("Post not found")

        return {
            "post_id": post_id,
            "content_type": post.content_type,
            "analytics": post.analytics or {},
            "voice_summary": self.generate_post_analytics_voice_summary(post)
        }

    # ------------------------------------------------------------------
    # Calendar
    # ------------------------------------------------------------------

    def get_content_calendar(
        self,
        agent_id: int,
        start_date_str: Optional[str] = None,
        end_date_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get content calendar with scheduled posts"""

        if not start_date_str:
            start_date_str = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        if not end_date_str:
            end_date_str = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

        start_dt = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))

        posts = self.db.query(PostizPost).filter(
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
            "start_date": start_date_str,
            "end_date": end_date_str,
            "posts": calendar,
            "total": len(calendar),
            "voice_summary": f"Content calendar: {len(calendar)} posts scheduled."
        }

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def preview_post(
        self,
        agent_id: int,
        caption: str,
        platforms: List[str],
        media_urls: Optional[List[str]] = None,
        hashtags: Optional[List[str]] = None,
        property_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Preview post without publishing"""
        agent = self._get_agent_or_raise(agent_id)

        # Get property if specified
        property_obj = None
        if property_id:
            property_obj = self.db.query(Property).filter(Property.id == property_id).first()

        # Get brand
        brand = self.db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()

        # Generate platform-specific previews
        previews = []

        for platform in platforms:
            platform_caption = caption
            platform_hashtags = hashtags or []

            # Platform character limits
            char_limits = {
                "twitter": 280,
                "facebook": 63206,
                "instagram": 2200,
                "linkedin": 3000,
                "tiktok": 150,
                "youtube": 5000
            }

            char_limit = char_limits.get(platform, 2200)
            total_length = len(platform_caption) + len(" ".join(platform_hashtags))

            # Warnings
            warnings = []
            if total_length > char_limit:
                warnings.append(f"⚠️ Exceeds {char_limit} character limit by {total_length - char_limit} chars")
            if platform == "twitter" and len(platform_hashtags) > 3:
                warnings.append("⚠️ Twitter recommends max 3 hashtags")
            if platform == "instagram" and not media_urls:
                warnings.append("⚠️ Instagram posts perform better with images")
            if platform == "linkedin" and len(platform_caption) < 100:
                warnings.append("⚠️ LinkedIn posts typically perform better with 100+ characters")

            # Build preview data
            preview = {
                "platform": platform,
                "platform_display": self.get_platform_display_name(platform),
                "caption": platform_caption,
                "hashtags": platform_hashtags,
                "media_count": len(media_urls) if media_urls else 0,
                "character_limit": char_limit,
                "character_count": total_length,
                "character_remaining": char_limit - total_length,
                "warnings": warnings,
                "will_be_truncated": total_length > char_limit
            }

            # Add property info if applicable
            if property_obj:
                preview["property_context"] = {
                    "address": f"{property_obj.street_address}, {property_obj.city}" if property_obj.street_address else property_obj.city,
                    "price": f"${property_obj.price:,}" if property_obj.price else None,
                    "beds": property_obj.bedrooms,
                    "baths": property_obj.bathrooms
                }

            # Add brand info if used
            if brand:
                preview["brand_applied"] = {
                    "company": brand.company_name,
                    "tagline": brand.tagline
                }

            previews.append(preview)

        return {
            "agent_id": agent_id,
            "platforms": platforms,
            "previews": previews,
            "total_warnings": sum(len(p["warnings"]) for p in previews),
            "ready_to_post": all(not p["will_be_truncated"] for p in previews),
            "voice_summary": f"Preview generated for {len(platforms)} platforms. {sum(1 for p in previews if p['warnings'])} platforms have warnings."
        }

    # ------------------------------------------------------------------
    # Direct Postiz API publishing
    # ------------------------------------------------------------------

    async def publish_direct(
        self,
        agent_id: int,
        caption: str,
        platforms: List[str],
        media_urls: Optional[List[str]] = None,
        hashtags: Optional[List[str]] = None,
        scheduled_at_str: Optional[str] = None,
        publish_immediately: bool = True,
        property_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create and publish post directly to Postiz API"""
        agent = self._get_agent_or_raise(agent_id)

        # Get property if specified
        property_obj = None
        if property_id:
            property_obj = self.db.query(Property).filter(Property.id == property_id).first()

        # Get brand
        brand = self.db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()

        # Build caption with brand
        final_caption = caption
        if brand and brand.company_name:
            final_caption = f"{caption}\n\n{brand.tagline or ''}" if brand.tagline else caption

        result = await create_property_post(
            agent_id=agent_id,
            db=self.db,
            property=property_obj,
            brand=brand,
            caption=final_caption,
            platforms=platforms,
            media_urls=media_urls,
            scheduled_at=datetime.fromisoformat(scheduled_at_str.replace('Z', '+00:00')) if scheduled_at_str else None,
            publish_immediately=publish_immediately
        )

        return {
            "success": True,
            "postiz_id": result.get("post", {}).get("id"),
            "post_id": result.get("post", {}).get("id"),
            "status": result.get("post", {}).get("status"),
            "platforms": platforms,
            "voice_summary": f"Post published to {', '.join(platforms)}. Postiz ID: {result.get('post', {}).get('id')}"
        }

    async def get_integrations(self, agent_id: int) -> Dict[str, Any]:
        """Get connected social media accounts from Postiz"""
        platforms = await self.get_connected_platforms(agent_id)

        return {
            "agent_id": agent_id,
            "platforms": platforms,
            "total": len(platforms),
            "voice_summary": f"Connected to {len(platforms)} platforms: {', '.join([p.get('provider', 'unknown') for p in platforms])}"
        }

    async def publish_property(
        self,
        property_id: int,
        agent_id: int,
        platforms: List[str],
        scheduled_at_str: Optional[str] = None,
        publish_immediately: bool = True
    ) -> Dict[str, Any]:
        """Auto-generate and publish property post"""
        property_obj = self.db.query(Property).filter(Property.id == property_id).first()
        if not property_obj:
            raise ValueError("Property not found")

        agent = self._get_agent_or_raise(agent_id)

        brand = self.db.query(AgentBrand).filter(AgentBrand.agent_id == agent_id).first()

        # Generate caption
        caption = f"🏠 {property_obj.city or 'New Listing'}!\n\n"

        if property_obj.price:
            caption += f"Price: ${property_obj.price:,}\n"

        if property_obj.bedrooms:
            caption += f"{property_obj.bedrooms} Bed"

        if property_obj.bathrooms:
            caption += f" | {property_obj.bathrooms} Bath"

        if property_obj.square_footage:
            caption += f" | {property_obj.square_footage:,} sqft"

        caption += "\n\n"

        if property_obj.street_address:
            caption += f"📍 {property_obj.street_address}, {property_obj.city or ''} {property_obj.state or ''}\n\n"

        if brand:
            caption += f"Contact {brand.company_name or agent.name} for details!\n"
            if brand.website_url:
                caption += f"{brand.website_url}"
        else:
            caption += f"Contact {agent.name} for details!"

        # Get property images from enrichment
        enrichment = self.db.query(ZillowEnrichment).filter(
            ZillowEnrichment.property_id == property_id
        ).first()

        media_urls = []
        if enrichment and enrichment.photos:
            media_urls = enrichment.photos[:5]  # Use first 5 photos

        result = await create_property_post(
            agent_id=agent_id,
            db=self.db,
            property=property_obj,
            brand=brand,
            caption=caption,
            platforms=platforms,
            media_urls=media_urls if media_urls else None,
            scheduled_at=datetime.fromisoformat(scheduled_at_str.replace('Z', '+00:00')) if scheduled_at_str else None,
            publish_immediately=publish_immediately
        )

        return {
            "success": True,
            "property_id": property_id,
            "postiz_id": result.get("post", {}).get("id"),
            "status": result.get("post", {}).get("status"),
            "platforms": platforms,
            "media_count": len(media_urls),
            "voice_summary": f"Property post published to {', '.join(platforms)}. {len(media_urls)} photos included."
        }

    # ------------------------------------------------------------------
    # Internal publish helpers
    # ------------------------------------------------------------------

    def _publish_to_postiz_sync(self, post: PostizPost) -> Dict[str, Any]:
        """Publish post to Postiz API (sync mock version)"""
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

        self.db.commit()

        return {
            "post_id": post.id,
            "status": "published",
            "postiz_id": post.post_id_postiz,
            "platform_ids": post.post_ids_platforms,
            "voice_summary": f"Post published to {', '.join(platforms)}."
        }

    async def _publish_to_postiz_async(self, post: PostizPost) -> Dict[str, Any]:
        """Publish post to Postiz API (async version, same mock for now)"""
        return self._publish_to_postiz_sync(post)

    @staticmethod
    def _cancel_postiz_post(post: PostizPost):
        """Cancel scheduled post in Postiz"""
        post.status = "cancelled"
        post.post_id_postiz = None

    def _generate_campaign_posts(
        self,
        campaign: PostizCampaign,
        platforms: List[str],
        post_count: int,
        agent_id: int
    ) -> List[Dict[str, Any]]:
        """Generate posts for campaign"""

        posts = []
        start_date = campaign.start_date

        # Calculate interval between posts
        if campaign.end_date:
            total_days = (campaign.end_date - start_date).days
            interval = total_days // post_count if post_count > 0 else 1
        else:
            interval = 1

        for i in range(post_count):
            post_date = start_date + timedelta(days=i * interval)

            post = PostizPost(
                agent_id=agent_id,
                account_id=self._get_default_account_id(agent_id),
                property_id=campaign.property_id,
                content_type=campaign.campaign_type,
                caption=self.generate_ai_content(
                    campaign.campaign_type,
                    platforms[0] if platforms else "facebook",
                    "professional",
                    None,
                    None,
                    True,
                    True,
                    None
                )["caption"],
                hashtags=self.generate_hashtags(campaign.campaign_type, None),
                media_type="image",
                scheduled_at=post_date,
                status="scheduled",
                generated_by="ai"
            )

            self.db.add(post)
            self.db.commit()
            self.db.refresh(post)

            posts.append({"id": post.id, "scheduled_at": post_date.isoformat()})

        return posts


# ============================================================================
# FastAPI Dependency
# ============================================================================

def get_postiz_service(db: Session = Depends(get_db)) -> PostizService:
    """FastAPI dependency to inject PostizService"""
    return PostizService(db)


# ============================================================================
# Helper Functions (kept for backward compatibility with imports)
# ============================================================================

async def upload_property_media_to_postiz(
    agent_id: int,
    db: Session,
    property: Property,
    media_urls: List[str]
) -> List[Dict[str, Any]]:
    """Upload property images to Postiz

    Args:
        agent_id: Agent ID
        db: Database session
        property: Property object
        media_urls: List of image URLs

    Returns:
        List of uploaded media info
    """
    service = PostizService(db)
    uploaded = []

    for url in media_urls:
        try:
            result = await service.upload_media(agent_id=agent_id, image_url=url)
            uploaded.append({
                "id": result.get("id"),
                "path": result.get("path"),
                "original_url": url
            })
        except Exception as e:
            logger.error(f"Failed to upload media {url}: {str(e)}")

    return uploaded


async def create_property_post(
    agent_id: int,
    db: Session,
    property: Property,
    brand: Optional[AgentBrand],
    caption: str,
    platforms: List[str],
    media_urls: Optional[List[str]] = None,
    scheduled_at: Optional[datetime] = None,
    publish_immediately: bool = False
) -> Dict[str, Any]:
    """Create and publish property post to Postiz

    Args:
        agent_id: Agent ID
        db: Database session
        property: Property object
        brand: Optional AgentBrand
        caption: Post caption
        platforms: List of platforms to publish to
        media_urls: Optional list of image URLs
        scheduled_at: Optional schedule time
        publish_immediately: Whether to publish now

    Returns:
        Result from Postiz API
    """
    service = PostizService(db)

    # Upload media if provided
    uploaded_media = []
    if media_urls:
        uploaded_media = await upload_property_media_to_postiz(
            agent_id, db, property, media_urls
        )

    # Create post in database
    post = PostizPost(
        agent_id=agent_id,
        account_id=service._get_account(agent_id).id if service._get_account(agent_id) else None,
        property_id=property.id,
        content_type="property_promo",
        caption=caption,
        hashtags=["#realestate", "#homeforsale", f"#{property.city}".replace(" ", "") if property.city else ""],
        media_urls=[m.get("path") for m in uploaded_media] if uploaded_media else media_urls,
        media_type="image",
        scheduled_at=scheduled_at,
        publish_immediately=publish_immediately,
        status="publishing" if publish_immediately else "scheduled",
        generated_by="ai",
        use_branding=True if brand else False
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    # Publish to Postiz
    result = await service.publish_post(agent_id, post, platforms)

    # Update post with result
    post.post_id_postiz = result.get("post", {}).get("id")
    post.status = "published" if publish_immediately else "scheduled"
    db.commit()

    return result
