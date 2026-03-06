"""VideoGen MCP Tools - AI Avatar Video Generation

Generate AI avatar videos and post to social media via voice commands.
"""
import json

from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


async def handle_generate_avatar_video(arguments: dict) -> list[TextContent]:
    property_id = arguments.get("property_id")
    if not property_id:
        return [TextContent(type="text", text="Error: property_id is required")]

    resp = api_post("/videogen/post", json={
        "property_id": property_id,
        "avatar_id": arguments.get("avatar_id", "Anna-public-1_20230714"),
        "script_type": arguments.get("script_type", "promotion"),
        "platforms": arguments.get("platforms", ["instagram", "tiktok"]),
    })
    return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]


async def handle_check_video_status(arguments: dict) -> list[TextContent]:
    video_id = arguments.get("video_id")
    if not video_id:
        return [TextContent(type="text", text="Error: video_id is required")]
    resp = api_get(f"/videogen/status/{video_id}")
    return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]


async def handle_list_avatars(arguments: dict) -> list[TextContent]:
    resp = api_get("/videogen/avatars/cached")
    return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]


async def handle_create_video_and_post(arguments: dict) -> list[TextContent]:
    property_id = arguments.get("property_id")
    if not property_id:
        return [TextContent(type="text", text="Error: property_id is required")]
    resp = api_post("/videogen/post", json={
        "property_id": property_id,
        "caption": arguments.get("caption"),
        "platforms": arguments.get("platforms", ["instagram", "tiktok", "youtube"]),
        "avatar_id": arguments.get("avatar_id", "Anna-public-1_20230714"),
    })
    return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]


async def handle_generate_test_video(arguments: dict) -> list[TextContent]:
    script = arguments.get("script", "This is a test of the AI avatar video system.")
    resp = api_post("/videogen/generate", json={"script": script, "test": True})
    return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]


# ── Register Tools ──

register_tool(
    Tool(
        name="generate_avatar_video",
        description="Generate AI avatar video from property data and post to social media.",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "integer", "description": "Property ID"},
                "avatar_id": {"type": "string", "description": "Avatar ID"},
                "script_type": {"type": "string", "enum": ["promotion", "market_update", "open_house"]},
                "platforms": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["property_id"],
        },
    ),
    handle_generate_avatar_video,
)

register_tool(
    Tool(
        name="check_video_status",
        description="Check the status of a VideoGen video generation.",
        inputSchema={
            "type": "object",
            "properties": {"video_id": {"type": "string", "description": "Video ID"}},
            "required": ["video_id"],
        },
    ),
    handle_check_video_status,
)

register_tool(
    Tool(
        name="list_video_avatars",
        description="List all available AI avatars for video generation.",
        inputSchema={"type": "object", "properties": {}},
    ),
    handle_list_avatars,
)

register_tool(
    Tool(
        name="create_video_and_post",
        description="Generate AI avatar video and post to social media. Complete workflow.",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "integer", "description": "Property ID"},
                "caption": {"type": "string", "description": "Custom caption"},
                "platforms": {"type": "array", "items": {"type": "string"}},
                "avatar_id": {"type": "string", "description": "Avatar ID"},
            },
            "required": ["property_id"],
        },
    ),
    handle_create_video_and_post,
)

register_tool(
    Tool(
        name="generate_test_video",
        description="Generate a test video without actual processing.",
        inputSchema={
            "type": "object",
            "properties": {"script": {"type": "string", "description": "Test script"}},
        },
    ),
    handle_generate_test_video,
)
