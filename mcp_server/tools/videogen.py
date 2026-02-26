"""VideoGen MCP Tools - AI Avatar Video Generation

Generate AI avatar videos and post to social media via voice commands.
"""
import asyncio
import httpx
from datetime import datetime, timezone

from mcp_server.server import mcp
from mcp_server.tools.registry import register_tool, Tool
from mcp_server.utils.api import api_call
from mcp_server.utils.properties import resolve_property


# ============================================================================
# VideoGen Tools
# ============================================================================

async def handle_generate_avatar_video(params: dict) -> dict:
    """Generate AI avatar video from property data

    Args:
        property_id: Property ID
        avatar_id: Avatar ID (default: Anna)
        script_type: promotion, market_update, open_house
        platforms: List of platforms to post to

    Returns:
        Generated video info
    """
    property_id = params.get("property_id")
    avatar_id = params.get("avatar_id", "Anna-public-1_20230714")
    script_type = params.get("script_type", "promotion")
    platforms = params.get("platforms", ["instagram", "tiktok"])

    if not property_id:
        return {"error": "property_id is required"}

    # Generate video and post
    result = await api_call(
        "POST",
        "/videogen/post",
        json={
            "property_id": property_id,
            "avatar_id": avatar_id,
            "script_type": script_type,
            "platforms": platforms
        }
    )

    return result


async def handle_check_video_status(params: dict) -> dict:
    """Check video generation status

    Args:
        video_id: Video ID from generation

    Returns:
        Current status and video URL if complete
    """
    video_id = params.get("video_id")

    if not video_id:
        return {"error": "video_id is required"}

    result = await api_call(
        "GET",
        f"/videogen/status/{video_id}"
    )

    return result


async def handle_list_avatars(params: dict) -> dict:
    """List available AI avatars

    Returns:
        List of avatars with preview images
    """
    result = await api_call("GET", "/videogen/avatars/cached")

    return {
        "avatars": result.get("avatars", [])[:10],  # Return first 10
        "total": result.get("total", 0),
        "summary": f"Found {result.get('total', 0)} AI avatars. Choose one for your video."
    }


async def handle_create_video_and_post(params: dict) -> dict:
    """Generate video and post to social media (complete workflow)

    Args:
        property_id: Property ID
        caption: Optional custom caption
        platforms: List of platforms (default: instagram, tiktok, youtube)
        avatar_id: Avatar ID (default: Anna)

    Returns:
        Posted video info with platform IDs
    """
    property_id = params.get("property_id")
    caption = params.get("caption")
    platforms = params.get("platforms", ["instagram", "tiktok", "youtube"])
    avatar_id = params.get("avatar_id", "Anna-public-1_20230714")

    if not property_id:
        return {"error": "property_id is required"}

    result = await api_call(
        "POST",
        "/videogen/post",
        json={
            "property_id": property_id,
            "caption": caption,
            "platforms": platforms,
            "avatar_id": avatar_id
        }
    )

    return result


async def handle_generate_test_video(params: dict) -> dict:
    """Generate test video (quick, no actual processing)

    Args:
        script: Test script

    Returns:
        Test video info
    """
    script = params.get("script", "This is a test of the AI avatar video system.")

    result = await api_call(
        "POST",
        "/videogen/generate",
        json={
            "script": script,
            "test": True
        }
    )

    return {
        "test_mode": True,
        "video_id": result.get("video_id"),
        "script_used": script,
        "summary": "Test video generated successfully (no actual processing)."
    }


# ============================================================================
# Register Tools
# ============================================================================

register_tool(
    Tool(
        name="generate_avatar_video",
        description="Generate AI avatar video from property data and post to social media. Creates professional video with AI spokesperson. Takes 2-5 minutes to process.",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "integer",
                    "description": "Property ID to generate video for"
                },
                "avatar_id": {
                    "type": "string",
                    "description": "Avatar ID (default: Anna-public-1_20230714)"
                },
                "script_type": {
                    "type": "string",
                    "enum": ["promotion", "market_update", "open_house"],
                    "description": "Type of script to generate"
                },
                "platforms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Platforms to post to (instagram, tiktok, youtube, facebook)"
                }
            },
            "required": ["property_id"]
        }
    ),
    handle_generate_avatar_video
)

register_tool(
    Tool(
        name="check_video_status",
        description="Check the status of a VideoGen video generation. Returns current status (processing, completed, failed) and video URL when ready.",
        inputSchema={
            "type": "object",
            "properties": {
                "video_id": {
                    "type": "string",
                    "description": "Video ID from generation"
                }
            },
            "required": ["video_id"]
        }
    ),
    handle_check_video_status
)

register_tool(
    Tool(
        name="list_video_avatars",
        description="List all available AI avatars for video generation. Shows avatar names, preview images, genders, and categories.",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    handle_list_avatars
)

register_tool(
    Tool(
        name="create_video_and_post",
        description="Generate AI avatar video and automatically post to social media. Complete workflow: generate video, wait for processing, upload to Postiz, post to all platforms. Takes 3-5 minutes.",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "integer",
                    "description": "Property ID"
                },
                "caption": {
                    "type": "string",
                    "description": "Optional custom caption for social post"
                },
                "platforms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Platforms to post to"
                },
                "avatar_id": {
                    "type": "string",
                    "description": "Avatar ID (default: Anna)"
                }
            },
            "required": ["property_id"]
        }
    ),
    handle_create_video_and_post
)

register_tool(
    Tool(
        name="generate_test_video",
        description="Generate a test video without actual processing. Useful for testing the workflow quickly.",
        inputSchema={
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "Test script for avatar to speak"
                }
            }
        }
    ),
    handle_generate_test_video
)
