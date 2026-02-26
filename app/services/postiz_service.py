"""Postiz API Service - Real integration with Postiz social media management platform.

Based on Postiz Public API documentation:
https://docs.postiz.com

Features:
- Upload images/media
- Create and schedule posts
- Publish to multiple platforms
- Get account integrations
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx
from sqlalchemy.orm import Session

from app.models.postiz import PostizAccount, PostizPost
from app.models.property import Property
from app.models.agent_brand import AgentBrand

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


# ============================================================================
# Helper Functions
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
