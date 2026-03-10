"""Enhanced Property Video MCP Tools

Voice commands for enhanced property video generation with avatars and AI footage.
"""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


async def handle_generate_enhanced_video(arguments: dict) -> list[TextContent]:
    """Generate enhanced property video with agent avatar and AI footage."""
    property_id = arguments.get("property_id")
    address = arguments.get("address")
    agent_id = arguments.get("agent_id", 1)
    style = arguments.get("style", "luxury")
    duration = arguments.get("duration", 60)

    if not property_id and not address:
        return [TextContent(type="text", text="Please provide either property_id or address.")]

    # Resolve property by address if needed
    if address and not property_id:
        resp = api_get("/properties/", params={"search": address, "limit": 1})
        resp.raise_for_status()
        props = resp.json()
        if not props:
            return [TextContent(type="text", text=f"No property found matching '{address}'.")]
        property_id = props[0]["id"]

    response = api_post(
        f"/enhanced-videos/generate/{property_id}",
        params={
            "agent_id": agent_id,
            "style": style,
            "duration": duration,
            "background_tasks": True
        }
    )
    response.raise_for_status()
    data = response.json()

    return [TextContent(
        type="text",
        text=f"Enhanced video generation started for property {property_id}.\n\n"
             f"Style: {style}\n"
             f"Estimated time: 5-10 minutes\n\n"
             f"The video will include:\n"
             f"- Agent intro with your custom avatar\n"
             f"- AI-generated property footage\n"
             f"- Professional voiceover\n"
             f"- Call-to-action outro"
    )]


async def handle_list_enhanced_videos(arguments: dict) -> list[TextContent]:
    """List all generated enhanced property videos."""
    params = {}
    if arguments.get("agent_id"):
        params["agent_id"] = arguments["agent_id"]
    if arguments.get("status"):
        params["status"] = arguments["status"]

    response = api_get("/enhanced-videos/", params=params if params else None)
    response.raise_for_status()
    videos = response.json()

    if not videos:
        return [TextContent(type="text", text="No enhanced videos found. Generate your first with 'Generate enhanced video for property X'.")]

    text = f"Found {len(videos)} enhanced video(s):\n\n"
    for video in videos[:10]:
        status = video.get("status", "unknown")
        text += f"Video {video['id']}: {status}\n"
        text += f"   Property: {video['property_id']}\n"
        text += f"   Style: {video.get('style', 'N/A')}\n"
        if video.get("duration"):
            text += f"   Duration: {video['duration']}s\n"
        if video.get("final_video_url"):
            text += f"   URL: {video['final_video_url']}\n"
        text += "\n"

    if len(videos) > 10:
        text += f"... and {len(videos) - 10} more videos\n"

    return [TextContent(type="text", text=text)]


async def handle_get_enhanced_video_status(arguments: dict) -> list[TextContent]:
    """Check generation status for a specific enhanced video."""
    video_id = arguments.get("video_id")
    if not video_id:
        return [TextContent(type="text", text="Please provide video_id.")]

    response = api_get(f"/enhanced-videos/{video_id}/status")
    response.raise_for_status()
    video = response.json()

    status = video.get("status")
    current_step = video.get("current_step")
    progress = video.get("progress")

    text = f"Video {video_id}\n\n"
    text += f"Status: {status}\n"
    text += f"Progress: {progress}\n"

    if current_step:
        text += f"Current Step: {current_step.replace('_', ' ').title()}\n"

    if status == "completed":
        text += f"\nVideo ready!\n"
        text += f"Watch: {video.get('final_video_url', 'N/A')}\n"
        if video.get("duration"):
            text += f"Duration: {video['duration']:.1f}s\n"
        if video.get("thumbnail_url"):
            text += f"Thumbnail: {video['thumbnail_url']}\n"
    elif status == "failed":
        text += f"\nGeneration failed.\n"
        text += f"Error: {video.get('error_message', 'Unknown error')}\n"

    return [TextContent(type="text", text=text)]


async def handle_create_agent_video_profile(arguments: dict) -> list[TextContent]:
    """Create agent video profile for enhanced videos."""
    headshot_url = arguments.get("headshot_url")
    if not headshot_url:
        return [TextContent(type="text", text="Please provide headshot_url (URL to your photo).")]

    payload = {
        "agent_id": arguments.get("agent_id", 1),
        "headshot_url": headshot_url,
        "voice_id": arguments.get("voice_id", "21m00Tcm4TlvDq8ikWAM"),
        "voice_style": arguments.get("voice_style", "professional")
    }

    response = api_post("/enhanced-videos/agent/profile", json=payload)
    response.raise_for_status()

    return [TextContent(
        type="text",
        text=f"Agent video profile created successfully!\n\n"
             f"Next step: Create your custom avatar with 'Create my avatar from photo {headshot_url}'\n\n"
             f"Profile details:\n"
             f"- Voice ID: {payload['voice_id']}\n"
             f"- Style: {payload['voice_style']}"
    )]


async def handle_create_agent_avatar(arguments: dict) -> list[TextContent]:
    """Create custom HeyGen avatar from agent's photo."""
    photo_url = arguments.get("photo_url")
    if not photo_url:
        return [TextContent(type="text", text="Please provide photo_url (link to your headshot photo).")]

    agent_id = arguments.get("agent_id", 1)
    gender = arguments.get("gender", "female")

    response = api_post(
        f"/enhanced-videos/agent/{agent_id}/avatar",
        params={"photo_url": photo_url, "gender": gender}
    )
    response.raise_for_status()
    data = response.json()

    return [TextContent(
        type="text",
        text=f"Custom avatar creation started!\n\n"
             f"Avatar ID: {data.get('avatar_id')}\n"
             f"This takes 1-3 minutes to process.\n\n"
             f"You'll be notified when it's ready. After that, you can generate videos "
             f"with your personalized talking head avatar!"
    )]


async def handle_estimate_video_cost(arguments: dict) -> list[TextContent]:
    """Estimate cost for video generation."""
    num_clips = arguments.get("num_clips", 5)
    duration = arguments.get("duration", 60)

    response = api_post(
        "/enhanced-videos/estimate-cost",
        params={"num_clips": num_clips, "duration": duration}
    )
    response.raise_for_status()
    data = response.json()

    total = data.get("estimated_cost", 0)
    breakdown = data.get("breakdown", {})

    text = f"Estimated Video Generation Cost\n\n"
    text += f"Total: ${total:.2f} USD\n\n"
    text += f"Cost Breakdown:\n"
    text += f"- HeyGen Avatar (intro + outro): ${breakdown.get('heygen', 0):.2f}\n"
    text += f"- PixVerse Footage ({num_clips} clips): ${breakdown.get('pixverse', 0):.2f}\n"
    text += f"- ElevenLabs Voiceover: ${breakdown.get('elevenlabs', 0):.2f}\n"
    text += f"- Assembly & Storage: ${breakdown.get('assembly', 0):.2f}\n\n"
    text += f"Note: Actual costs may vary slightly based on video duration and API pricing."

    return [TextContent(type="text", text=text)]


# ============================================================================
# Tool Registrations
# ============================================================================

register_tool(
    Tool(name="generate_enhanced_video", description="Generate enhanced property video with agent avatar, AI footage, and voiceover.", inputSchema={
        "type": "object",
        "properties": {
            "property_id": {"type": "integer", "description": "Property ID"},
            "address": {"type": "string", "description": "Property address to search for"},
            "agent_id": {"type": "integer", "description": "Agent ID", "default": 1},
            "style": {"type": "string", "enum": ["luxury", "friendly", "professional"], "default": "luxury"},
            "duration": {"type": "integer", "description": "Video duration in seconds", "default": 60}
        }
    }),
    handle_generate_enhanced_video
)

register_tool(
    Tool(name="list_enhanced_videos", description="List all generated enhanced property videos.", inputSchema={
        "type": "object",
        "properties": {
            "agent_id": {"type": "integer", "description": "Filter by agent ID"},
            "status": {"type": "string", "description": "Filter by status"}
        }
    }),
    handle_list_enhanced_videos
)

register_tool(
    Tool(name="get_enhanced_video_status", description="Check generation status for a specific enhanced video.", inputSchema={
        "type": "object",
        "properties": {
            "video_id": {"type": "integer", "description": "Video ID to check"}
        },
        "required": ["video_id"]
    }),
    handle_get_enhanced_video_status
)

register_tool(
    Tool(name="create_agent_video_profile", description="Create agent video profile for enhanced videos.", inputSchema={
        "type": "object",
        "properties": {
            "agent_id": {"type": "integer", "description": "Agent ID", "default": 1},
            "headshot_url": {"type": "string", "description": "URL to agent headshot photo"},
            "voice_id": {"type": "string", "description": "ElevenLabs voice ID"},
            "voice_style": {"type": "string", "enum": ["luxury", "friendly", "professional"], "default": "professional"}
        },
        "required": ["headshot_url"]
    }),
    handle_create_agent_video_profile
)

register_tool(
    Tool(name="create_agent_avatar", description="Create custom HeyGen avatar from agent's photo.", inputSchema={
        "type": "object",
        "properties": {
            "agent_id": {"type": "integer", "description": "Agent ID", "default": 1},
            "photo_url": {"type": "string", "description": "URL to headshot photo"},
            "gender": {"type": "string", "enum": ["male", "female"], "default": "female"}
        },
        "required": ["photo_url"]
    }),
    handle_create_agent_avatar
)

register_tool(
    Tool(name="estimate_video_cost", description="Estimate cost for enhanced video generation.", inputSchema={
        "type": "object",
        "properties": {
            "num_clips": {"type": "integer", "description": "Number of video clips", "default": 5},
            "duration": {"type": "integer", "description": "Video duration in seconds", "default": 60}
        }
    }),
    handle_estimate_video_cost
)
