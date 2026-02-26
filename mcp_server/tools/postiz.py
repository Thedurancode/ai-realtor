"""Postiz Social Media MCP Tools - Voice commands for social media management

Provides 6 tools:
1. upload_media_to_postiz - Upload images/videos to Postiz
2. publish_post - Publish custom post to social media
3. publish_property_post - Auto-generate and publish property post
4. batch_publish_properties - Publish multiple properties at once
5. get_connected_platforms - Get connected social platforms
6. schedule_social_media - Schedule post for later
"""

from mcp.types import Tool, TextContent
from ..server import register_tool
from ..utils.http_client import api_post

import logging
logger = logging.getLogger(__name__)


# ============================================================================
# Helper Functions
# ============================================================================

async def call_postiz_api(
    method: str,
    endpoint: str,
    data: dict = None
) -> dict:
    """Call local Postiz API endpoint"""
    try:
        if method.upper() == "GET":
            response = await api_post(endpoint, json=data or {})  # Using POST for simplicity
        else:
            response = await api_post(endpoint, json=data or {})

        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Postiz API error: {str(e)}")
        raise


# ============================================================================
# Tool Handlers
# ============================================================================

async def handle_upload_media_to_postiz(arguments: dict) -> list[TextContent]:
    """Upload media to Postiz"""
    agent_id = arguments.get("agent_id")
    image_url = arguments.get("image_url")

    if not agent_id:
        return [TextContent(type="text", text="Error: agent_id is required")]

    if not image_url:
        return [TextContent(type="text", text="Error: Either image_url or file_path must be provided")]

    try:
        data = {"agent_id": agent_id, "image_url": image_url}
        result = await call_postiz_api("POST", "/social/api/upload-media", data)

        voice = f"Media uploaded to Postiz. ID: {result.get('media_id')}"
        return [TextContent(type="text", text=voice)]
    except Exception as e:
        return [TextContent(type="text", text=f"Failed to upload media: {str(e)}")]


async def handle_publish_post(arguments: dict) -> list[TextContent]:
    """Publish post to social media via Postiz"""
    agent_id = arguments.get("agent_id")
    caption = arguments.get("caption")
    platforms = arguments.get("platforms", [])
    media_urls = arguments.get("media_urls")
    hashtags = arguments.get("hashtags")
    scheduled_at = arguments.get("scheduled_at")
    publish_immediately = arguments.get("publish_immediately", True)
    property_id = arguments.get("property_id")

    if not agent_id or not caption or not platforms:
        return [TextContent(type="text", text="Error: agent_id, caption, and platforms are required")]

    try:
        data = {
            "agent_id": agent_id,
            "caption": caption,
            "platforms": platforms,
            "publish_immediately": publish_immediately
        }

        if media_urls:
            data["media_urls"] = media_urls
        if hashtags:
            data["hashtags"] = hashtags
        if scheduled_at:
            data["scheduled_at"] = scheduled_at
        if property_id:
            data["property_id"] = property_id

        result = await call_postiz_api("POST", "/social/api/publish", data)

        platform_list = ", ".join(platforms)
        voice = f"Post published to {platform_list}. Postiz ID: {result.get('postiz_id')}"

        return [TextContent(type="text", text=voice)]
    except Exception as e:
        return [TextContent(type="text", text=f"Failed to publish post: {str(e)}")]


async def handle_publish_property_post(arguments: dict) -> list[TextContent]:
    """Auto-generate and publish property post"""
    agent_id = arguments.get("agent_id")
    property_id = arguments.get("property_id")
    platforms = arguments.get("platforms", ["facebook", "instagram"])
    scheduled_at = arguments.get("scheduled_at")
    publish_immediately = arguments.get("publish_immediately", True)

    if not agent_id or not property_id:
        return [TextContent(type="text", text="Error: agent_id and property_id are required")]

    try:
        data = {
            "agent_id": agent_id,
            "platforms": platforms,
            "publish_immediately": publish_immediately
        }

        if scheduled_at:
            data["scheduled_at"] = scheduled_at

        result = await call_postiz_api("POST", f"/social/api/property/{property_id}/publish", data)

        platform_list = ", ".join(platforms)
        media_count = result.get("media_count", 0)
        voice = f"Property {property_id} posted to {platform_list}. {media_count} photos included."

        return [TextContent(type="text", text=voice)]
    except Exception as e:
        return [TextContent(type="text", text=f"Failed to publish property post: {str(e)}")]


async def handle_batch_publish_properties(arguments: dict) -> list[TextContent]:
    """Publish posts for multiple properties at once"""
    agent_id = arguments.get("agent_id")
    property_ids = arguments.get("property_ids", [])
    platforms = arguments.get("platforms", ["facebook", "instagram"])

    if not agent_id or not property_ids:
        return [TextContent(type="text", text="Error: agent_id and property_ids are required")]

    try:
        data = {
            "agent_id": agent_id,
            "property_ids": property_ids,
            "platforms": platforms
        }

        result = await call_postiz_api("POST", "/social/api/batch-publish", data)

        successful = result.get("successful", 0)
        total = result.get("total", 0)
        platform_list = ", ".join(platforms)

        voice = f"Batch publish complete: {successful}/{total} property posts published to {platform_list}."

        return [TextContent(type="text", text=voice)]
    except Exception as e:
        return [TextContent(type="text", text=f"Failed to batch publish: {str(e)}")]


async def handle_get_connected_platforms(arguments: dict) -> list[TextContent]:
    """Get connected social media platforms from Postiz"""
    agent_id = arguments.get("agent_id")

    if not agent_id:
        return [TextContent(type="text", text="Error: agent_id is required")]

    try:
        result = await call_postiz_api("GET", "/social/api/integrations", {"agent_id": agent_id})

        platforms = result.get("platforms", [])
        platform_names = [p.get("provider", "unknown") for p in platforms]

        voice = f"Connected to {len(platforms)} platforms: {', '.join(platform_names)}"

        return [TextContent(type="text", text=voice)]
    except Exception as e:
        return [TextContent(type="text", text=f"Failed to get connected platforms: {str(e)}")]


async def handle_schedule_social_media(arguments: dict) -> list[TextContent]:
    """Schedule social media post for specific time"""
    agent_id = arguments.get("agent_id")
    property_id = arguments.get("property_id")
    caption = arguments.get("caption")
    platforms = arguments.get("platforms", [])
    schedule_time = arguments.get("schedule_time")
    media_urls = arguments.get("media_urls")

    if not agent_id or not platforms or not schedule_time:
        return [TextContent(type="text", text="Error: agent_id, platforms, and schedule_time are required")]

    if not property_id and not caption:
        return [TextContent(type="text", text="Error: Either property_id or caption must be provided")]

    try:
        data = {
            "agent_id": agent_id,
            "platforms": platforms,
            "publish_immediately": False
        }

        if property_id:
            # Use property post endpoint
            if schedule_time:
                data["scheduled_at"] = schedule_time
            result = await call_postiz_api("POST", f"/social/api/property/{property_id}/publish", data)
        else:
            # Use direct publish endpoint
            data["caption"] = caption
            data["scheduled_at"] = schedule_time
            if media_urls:
                data["media_urls"] = media_urls
            result = await call_postiz_api("POST", "/social/api/publish", data)

        from datetime import datetime
        scheduled_dt = datetime.fromisoformat(schedule_time.replace('Z', '+00:00'))
        time_str = scheduled_dt.strftime("%Y-%m-%d at %I:%M %p")
        platform_list = ", ".join(platforms)

        voice = f"Post scheduled for {time_str} to {platform_list}."

        return [TextContent(type="text", text=voice)]
    except Exception as e:
        return [TextContent(type="text", text=f"Failed to schedule post: {str(e)}")]


async def handle_preview_post(arguments: dict) -> list[TextContent]:
    """Preview post without publishing"""
    agent_id = arguments.get("agent_id")
    caption = arguments.get("caption")
    platforms = arguments.get("platforms", [])
    media_urls = arguments.get("media_urls")
    hashtags = arguments.get("hashtags")
    property_id = arguments.get("property_id")

    if not agent_id or not caption or not platforms:
        return [TextContent(type="text", text="Error: agent_id, caption, and platforms are required")]

    try:
        data = {
            "agent_id": agent_id,
            "caption": caption,
            "platforms": platforms
        }

        if media_urls:
            data["media_urls"] = media_urls
        if hashtags:
            data["hashtags"] = hashtags
        if property_id:
            data["property_id"] = property_id

        result = await call_postiz_api("POST", "/social/api/preview", data)

        previews = result.get("previews", [])
        total_warnings = result.get("total_warnings", 0)
        ready = result.get("ready_to_post", False)

        voice_parts = [f"Post preview for {len(platforms)} platforms:"]
        for preview in previews:
            platform = preview.get("platform_display", preview["platform"])
            chars = preview["character_count"]
            limit = preview["character_limit"]
            remaining = preview["character_remaining"]
            warnings = preview.get("warnings", [])

            voice_parts.append(f"\n{platform}: {chars}/{limit} chars ({remaining} remaining)")
            if warnings:
                voice_parts.append(f"  Warnings: {len(warnings)}")

        if ready:
            voice_parts.append(f"\n✅ Ready to post!")
        else:
            voice_parts.append(f"\n⚠️  Fix issues before posting")

        return [TextContent(type="text", text="\n".join(voice_parts))]
    except Exception as e:
        return [TextContent(type="text", text=f"Failed to generate preview: {str(e)}")]


# ============================================================================
# Tool Registrations
# ============================================================================

register_tool(
    Tool(
        name="upload_media_to_postiz",
        description="Upload media (images/videos) to Postiz for use in social media posts. Provide either image_url or file_path.",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "integer", "description": "Agent ID"},
                "image_url": {"type": "string", "description": "URL of image to upload"}
            },
            "required": ["agent_id"]
        }
    ),
    handle_upload_media_to_postiz
)

register_tool(
    Tool(
        name="preview_post",
        description="Preview a social media post before publishing. Shows character counts, platform-specific warnings, and how the post will look on each platform.",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "integer", "description": "Agent ID"},
                "caption": {"type": "string", "description": "Post caption text"},
                "platforms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Platforms to preview (facebook, instagram, twitter, linkedin, tiktok)"
                },
                "media_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of image URLs"
                },
                "hashtags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional hashtags"
                },
                "property_id": {"type": "integer", "description": "Optional property ID for context"}
            },
            "required": ["agent_id", "caption", "platforms"]
        }
    ),
    handle_preview_post
)

register_tool(
    Tool(
        name="publish_post",
        description="Publish a custom post to social media platforms via Postiz. Supports Facebook, Instagram, Twitter, LinkedIn, TikTok and more.",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "integer", "description": "Agent ID"},
                "caption": {"type": "string", "description": "Post caption text"},
                "platforms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Platforms to publish to (facebook, instagram, twitter, linkedin, tiktok)"
                },
                "media_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of image URLs"
                },
                "hashtags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional hashtags"
                },
                "scheduled_at": {"type": "string", "description": "Optional ISO datetime for scheduling (e.g., 2026-02-25T10:00:00Z)"},
                "publish_immediately": {"type": "boolean", "description": "Publish now if True (default: true)"},
                "property_id": {"type": "integer", "description": "Optional property ID for context"}
            },
            "required": ["agent_id", "caption", "platforms"]
        }
    ),
    handle_publish_post
)

register_tool(
    Tool(
        name="publish_property_post",
        description="Auto-generate and publish a property promotion post to social media. Uses property details, photos from Zillow enrichment, and agent branding.",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "integer", "description": "Agent ID"},
                "property_id": {"type": "integer", "description": "Property ID"},
                "platforms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Platforms to publish to (default: [facebook, instagram])"
                },
                "scheduled_at": {"type": "string", "description": "Optional schedule time (ISO datetime)"},
                "publish_immediately": {"type": "boolean", "description": "Publish now if True (default: true)"}
            },
            "required": ["agent_id", "property_id"]
        }
    ),
    handle_publish_property_post
)

register_tool(
    Tool(
        name="batch_publish_properties",
        description="Publish posts for multiple properties at once. Each property gets an auto-generated post with photos and details.",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "integer", "description": "Agent ID"},
                "property_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "List of property IDs to publish"
                },
                "platforms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Platforms to publish to (default: [facebook, instagram])"
                }
            },
            "required": ["agent_id", "property_ids"]
        }
    ),
    handle_batch_publish_properties
)

register_tool(
    Tool(
        name="get_connected_platforms",
        description="Get list of connected social media platforms from Postiz. Shows which platforms (Facebook, Instagram, Twitter, LinkedIn, TikTok, etc.) are configured.",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "integer", "description": "Agent ID"}
            },
            "required": ["agent_id"]
        }
    ),
    handle_get_connected_platforms
)

register_tool(
    Tool(
        name="schedule_social_media",
        description="Schedule a social media post for a specific time. Can auto-generate from property or use custom caption.",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "integer", "description": "Agent ID"},
                "property_id": {"type": "integer", "description": "Optional property ID for auto-generated post"},
                "caption": {"type": "string", "description": "Custom post caption (required if no property_id)"},
                "platforms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Platforms to publish to"
                },
                "schedule_time": {"type": "string", "description": "ISO datetime for scheduling (e.g., 2026-02-25T10:00:00Z)"},
                "media_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional media URLs"
                }
            },
            "required": ["agent_id", "platforms", "schedule_time"]
        }
    ),
    handle_schedule_social_media
)
