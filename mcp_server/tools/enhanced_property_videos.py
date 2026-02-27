"""Enhanced Property Video MCP Tools

Voice commands for enhanced property video generation with avatars and AI footage.
"""
import asyncio
from typing import Dict, Any, List
from mcp_server.types import TextContent

from mcp_server.utils.api import api_get, api_post
from mcp_server.utils.property import find_property_by_address
from mcp_server.models import get_db, Property, AgentVideoProfile
from sqlalchemy.orm import Session


async def handle_generate_enhanced_video(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Generate enhanced property video with agent avatar and AI footage.

    Voice: "Generate an enhanced video for property 5" or "Create a luxury video for the Miami condo"
    """
    property_id = arguments.get("property_id")
    address = arguments.get("address")
    agent_id = arguments.get("agent_id", 1)  # Default to agent 1
    style = arguments.get("style", "luxury")
    duration = arguments.get("duration", 60)

    # Resolve property
    db: Session = next(get_db())
    try:
        if address:
            property = find_property_by_address(db, address)
            property_id = property.id
        elif property_id:
            property = db.query(Property).filter(Property.id == property_id).first()
        else:
            return [TextContent(
                type="text",
                text="❌ Please provide either property_id or address"
            )]

        if not property:
            return [TextContent(
                type="text",
                text=f"❌ Property not found"
            )]

        # Check agent profile
        profile = db.query(AgentVideoProfile).filter(
            AgentVideoProfile.agent_id == agent_id
        ).first()

        if not profile:
            return [TextContent(
                type="text",
                text=f"❌ Agent video profile not found. Please set up your agent profile with avatar and voice first."
            )]

        if not profile.heygen_avatar_id:
            return [TextContent(
                type="text",
                text=f"❌ Agent avatar not created. Please create a custom avatar first."
            )]

        # Generate video (run in background)
        response = await api_post(
            f"/enhanced-videos/generate/{property_id}",
            params={
                "agent_id": agent_id,
                "style": style,
                "duration": duration,
                "background_tasks": True
            }
        )

        return [TextContent(
            type="text",
            text=f"🎬 Enhanced video generation started for property at {property.address}!\n\n"
                 f"Style: {style}\n"
                 f"Estimated time: 5-10 minutes\n\n"
                 f"You'll receive a notification when it's ready. The video will include:\n"
                 f"• Agent intro with your custom avatar\n"
                 f"• AI-generated property footage\n"
                 f"• Professional voiceover\n"
                 f"• Call-to-action outro"
        )]

    finally:
        db.close()


async def handle_list_enhanced_videos(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    List all generated enhanced property videos.

    Voice: "Show me my enhanced videos" or "List all property videos"
    """
    agent_id = arguments.get("agent_id")
    status_filter = arguments.get("status")

    params = {}
    if agent_id:
        params["agent_id"] = agent_id
    if status_filter:
        params["status"] = status_filter

    response = await api_get("/enhanced-videos/", params=params if params else None)

    videos = response
    if not videos or len(videos) == 0:
        return [TextContent(
            type="text",
            text="📹 No enhanced videos found. Generate your first video with 'Generate enhanced video for property X'"
        )]

    text = f"📹 Found {len(videos)} enhanced video(s):\n\n"

    for video in videos[:10]:  # Show first 10
        status_emoji = {
            "completed": "✅",
            "failed": "❌",
            "processing": "⏳",
            "assembling_video": "🎬"
        }.get(video.get("status"), "📹")

        text += f"{status_emoji} Video {video['id']}: {video['status']}\n"
        text += f"   Property: {video['property_id']}\n"
        text += f"   Style: {video['style']}\n"

        if video.get("duration"):
            text += f"   Duration: {video['duration']}s\n"
        if video.get("final_video_url"):
            text += f"   🎥 {video['final_video_url']}\n"

        text += "\n"

    if len(videos) > 10:
        text += f"... and {len(videos) - 10} more videos\n"

    return [TextContent(type="text", text=text)]


async def handle_get_enhanced_video_status(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Check generation status for a specific enhanced video.

    Voice: "What's the status of video 3?" or "Check video 5 status"
    """
    video_id = arguments.get("video_id")

    if not video_id:
        return [TextContent(
            type="text",
            text="❌ Please provide video_id"
        )]

    response = await api_get(f"/enhanced-videos/{video_id}/status")

    video = response
    status = video.get("status")
    current_step = video.get("current_step")
    progress = video.get("progress")

    # Status emoji
    status_emoji = {
        "completed": "✅",
        "failed": "❌",
        "draft": "📝",
        "generating_script": "✍️",
        "generating_voiceover": "🎙️",
        "generating_intro": "🎭",
        "generating_footage": "🎬",
        "assembling_video": "🔧"
    }.get(status, "📹")

    text = f"{status_emoji} Video {video_id}\n\n"
    text += f"Status: {status}\n"
    text += f"Progress: {progress}\n"

    if current_step:
        step_name = current_step.replace("_", " ").title()
        text += f"Current Step: {step_name}\n"

    if status == "completed":
        text += f"\n🎬 Video ready!\n"
        text += f"📺 Watch: {video.get('final_video_url', 'N/A')}\n"

        if video.get("duration"):
            text += f"⏱️ Duration: {video['duration']:.1f}s\n"
        if video.get("thumbnail_url"):
            text += f"🖼️ Thumbnail: {video['thumbnail_url']}\n"

    elif status == "failed":
        text += f"\n❌ Generation failed\n"
        text += f"Error: {video.get('error_message', 'Unknown error')}\n"

    return [TextContent(type="text", text=text)]


async def handle_create_agent_video_profile(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Create agent video profile for enhanced videos.

    Voice: "Set up my video profile" or "Create agent profile with voice xyz"
    """
    agent_id = arguments.get("agent_id", 1)
    headshot_url = arguments.get("headshot_url")
    voice_id = arguments.get("voice_id", "21m00Tcm4TlvDq8ikWAM")  # Default ElevenLabs voice
    voice_style = arguments.get("voice_style", "professional")

    if not headshot_url:
        return [TextContent(
            type="text",
            text="❌ Please provide headshot_url (URL to your photo)"
        )]

    # Create profile
    payload = {
        "agent_id": agent_id,
        "headshot_url": headshot_url,
        "voice_id": voice_id,
        "voice_style": voice_style
    }

    response = await api_post("/enhanced-videos/agent/profile", json=payload)

    return [TextContent(
        type="text",
        text=f"✅ Agent video profile created successfully!\n\n"
             f"Next step: Create your custom avatar with 'Create my avatar from photo {headshot_url}'\n\n"
             f"Profile details:\n"
             f"• Voice ID: {voice_id}\n"
             f"• Style: {voice_style}"
    )]


async def handle_create_agent_avatar(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Create custom HeyGen avatar from agent's photo.

    Voice: "Create my avatar from photo https://..." or "Make an avatar from my headshot"
    """
    agent_id = arguments.get("agent_id", 1)
    photo_url = arguments.get("photo_url")
    gender = arguments.get("gender", "female")

    if not photo_url:
        return [TextContent(
            type="text",
            text="❌ Please provide photo_url (link to your headshot photo)"
        )]

    try:
        response = await api_post(
            f"/enhanced-videos/agent/{agent_id}/avatar",
            params={
                "photo_url": photo_url,
                "gender": gender
            }
        )

        avatar_id = response.get("avatar_id")

        return [TextContent(
            type="text",
            text=f"🎭 Custom avatar creation started!\n\n"
                 f"Avatar ID: {avatar_id}\n"
                 f"This takes 1-3 minutes to process.\n\n"
                 f"You'll be notified when it's ready. After that, you can generate videos "
                 f"with your personalized talking head avatar!"
        )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Avatar creation failed: {str(e)}\n\n"
                 f"Make sure your photo URL is publicly accessible and shows a clear, "
                 f"front-facing photo of your face."
        )]


async def handle_estimate_video_cost(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Estimate cost for video generation.

    Voice: "How much does a video cost?" or "Estimate video generation cost"
    """
    num_clips = arguments.get("num_clips", 5)
    duration = arguments.get("duration", 60)

    response = await api_post(
        "/enhanced-videos/estimate-cost",
        params={
            "num_clips": num_clips,
            "duration": duration
        }
    )

    total = response.get("estimated_cost")
    breakdown = response.get("breakdown", {})

    text = f"💰 Estimated Video Generation Cost\n\n"
    text += f"Total: ${total:.2f} USD\n\n"
    text += f"Cost Breakdown:\n"
    text += f"• HeyGen Avatar (intro + outro): ${breakdown.get('heygen', 0):.2f}\n"
    text += f"• PixVerse Footage ({num_clips} clips): ${breakdown.get('pixverse', 0):.2f}\n"
    text += f"• ElevenLabs Voiceover: ${breakdown.get('elevenlabs', 0):.2f}\n"
    text += f"• Assembly & Storage: ${breakdown.get('assembly', 0):.2f}\n\n"
    text += f"Note: Actual costs may vary slightly based on video duration and API pricing."

    return [TextContent(type="text", text=text)]


# ============================================================================
# Tool Registry
# ============================================================================

async def register_enhanced_video_tools(tools_registry: dict):
    """Register enhanced video tools with MCP server."""

    tools_registry["generate_enhanced_video"] = {
        "name": "generate_enhanced_video",
        "description": "Generate enhanced property video with agent avatar, AI footage, and voiceover",
        "inputSchema": {
            "type": "object",
            "properties": {
                "property_id": {"type": "integer"},
                "address": {"type": "string"},
                "agent_id": {"type": "integer", "default": 1},
                "style": {"type": "string", "enum": ["luxury", "friendly", "professional"], "default": "luxury"},
                "duration": {"type": "integer", "default": 60}
            }
        },
        "handler": handle_generate_enhanced_video
    }

    tools_registry["list_enhanced_videos"] = {
        "name": "list_enhanced_videos",
        "description": "List all generated enhanced property videos",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "integer"},
                "status": {"type": "string"}
            }
        },
        "handler": handle_list_enhanced_videos
    }

    tools_registry["get_enhanced_video_status"] = {
        "name": "get_enhanced_video_status",
        "description": "Check generation status for a specific enhanced video",
        "inputSchema": {
            "type": "object",
            "properties": {
                "video_id": {"type": "integer"}
            },
            "required": ["video_id"]
        },
        "handler": handle_get_enhanced_video_status
    }

    tools_registry["create_agent_video_profile"] = {
        "name": "create_agent_video_profile",
        "description": "Create agent video profile for enhanced videos",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "integer", "default": 1},
                "headshot_url": {"type": "string"},
                "voice_id": {"type": "string"},
                "voice_style": {"type": "string", "enum": ["luxury", "friendly", "professional"], "default": "professional"}
            },
            "required": ["headshot_url"]
        },
        "handler": handle_create_agent_video_profile
    }

    tools_registry["create_agent_avatar"] = {
        "name": "create_agent_avatar",
        "description": "Create custom HeyGen avatar from agent's photo",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "integer", "default": 1},
                "photo_url": {"type": "string"},
                "gender": {"type": "string", "enum": ["male", "female"], "default": "female"}
            },
            "required": ["photo_url"]
        },
        "handler": handle_create_agent_avatar
    }

    tools_registry["estimate_video_cost"] = {
        "name": "estimate_video_cost",
        "description": "Estimate cost for enhanced video generation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "num_clips": {"type": "integer", "default": 5},
                "duration": {"type": "integer", "default": 60}
            }
        },
        "handler": handle_estimate_video_cost
    }

    return tools_registry
