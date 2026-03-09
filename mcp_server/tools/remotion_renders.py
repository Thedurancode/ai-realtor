"""Remotion Video Render MCP tools — trigger and manage video renders via voice/chat."""
import json
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


async def handle_render_video(arguments: dict) -> list[TextContent]:
    template = arguments.get("template")
    if not template:
        return [TextContent(type="text", text="Please provide a template (property-showcase, cinematic-event-recap, captioned-reel, slideshow, timeline-editor).")]

    # Build payload
    payload = {
        "template_id": template,
        "composition_id": arguments.get("composition_id", ""),
        "input_props": arguments.get("input_props", {}),
    }
    if arguments.get("webhook_url"):
        payload["webhook_url"] = arguments["webhook_url"]

    response = api_post("/v1/renders", json=payload)
    response.raise_for_status()
    job = response.json()

    text = f"Render job created: {job['id']}\n"
    text += f"Template: {job['template_id']} | Status: {job['status']}\n"
    text += f"Track progress: check_render_status with render_id={job['id']}"
    return [TextContent(type="text", text=text)]


async def handle_render_property_video(arguments: dict) -> list[TextContent]:
    """Convenience tool — renders a PropertyShowcase video from property data."""
    props = {}
    for key in ("propertyAddress", "propertyPrice", "propertyPhotos", "logoUrl",
                "companyName", "tagline", "primaryColor", "secondaryColor",
                "agentName", "agentPhone", "agentEmail", "ctaText", "audioUrl"):
        if arguments.get(key) is not None:
            props[key] = arguments[key]

    # Map common snake_case to camelCase
    if arguments.get("property_address"):
        props["propertyAddress"] = arguments["property_address"]
    if arguments.get("property_price"):
        props["propertyPrice"] = arguments["property_price"]
    if arguments.get("property_photos"):
        props["propertyPhotos"] = arguments["property_photos"]
    if arguments.get("agent_name"):
        props["agentName"] = arguments["agent_name"]
    if arguments.get("agent_phone"):
        props["agentPhone"] = arguments["agent_phone"]

    # Property details
    details = {}
    if arguments.get("bedrooms"):
        details["bedrooms"] = arguments["bedrooms"]
    if arguments.get("bathrooms"):
        details["bathrooms"] = arguments["bathrooms"]
    if arguments.get("square_feet"):
        details["squareFeet"] = arguments["square_feet"]
    if details:
        props["propertyDetails"] = details

    payload = {
        "template_id": "property-showcase",
        "composition_id": "PropertyShowcase",
        "input_props": props,
    }
    if arguments.get("webhook_url"):
        payload["webhook_url"] = arguments["webhook_url"]

    response = api_post("/v1/renders", json=payload)
    response.raise_for_status()
    job = response.json()

    text = f"Property video render started: {job['id']}\n"
    text += f"Status: {job['status']}\n"
    if props.get("propertyAddress"):
        text += f"Property: {props['propertyAddress']}\n"
    photos = props.get("propertyPhotos", [])
    text += f"Photos: {len(photos)} | Estimated duration: ~{3 + len(photos) * 4 + 4}s"
    return [TextContent(type="text", text=text)]


async def handle_check_render_status(arguments: dict) -> list[TextContent]:
    render_id = arguments.get("render_id")
    if not render_id:
        return [TextContent(type="text", text="Please provide a render_id.")]

    response = api_get(f"/v1/renders/{render_id}/progress")
    response.raise_for_status()
    p = response.json()

    icon = {"queued": "...", "rendering": "...", "uploading": "...",
            "completed": "OK", "failed": "FAIL", "canceled": "X"}.get(p["status"], "?")

    text = f"[{icon}] Render {p['id']}: {p['status']}"
    if p.get("progress"):
        text += f" ({p['progress'] * 100:.0f}%)"
    if p.get("current_frame") and p.get("total_frames"):
        text += f" — frame {p['current_frame']}/{p['total_frames']}"
    if p.get("eta_seconds"):
        text += f" | ETA: {p['eta_seconds']}s"

    # If completed, get the full job for output_url
    if p["status"] == "completed":
        full = api_get(f"/v1/renders/{render_id}")
        if full.status_code == 200:
            job = full.json()
            if job.get("output_url"):
                text += f"\nVideo URL: {job['output_url']}"

    return [TextContent(type="text", text=text)]


async def handle_list_renders(arguments: dict) -> list[TextContent]:
    response = api_get("/v1/renders")
    response.raise_for_status()
    data = response.json()

    jobs = data.get("jobs", [])
    if not jobs:
        return [TextContent(type="text", text="No render jobs found.")]

    text = f"Render Jobs ({data.get('total', len(jobs))}):\n\n"
    for j in jobs[:20]:
        status_icon = {"completed": "OK", "failed": "FAIL", "rendering": "...",
                       "queued": "Q", "canceled": "X"}.get(j["status"], "?")
        text += f"  [{status_icon}] {j['id'][:8]}... — {j['template_id']}"
        if j.get("progress"):
            text += f" ({j['progress'] * 100:.0f}%)"
        text += f" | {j['status']}\n"

    return [TextContent(type="text", text=text)]


async def handle_cancel_render(arguments: dict) -> list[TextContent]:
    render_id = arguments.get("render_id")
    if not render_id:
        return [TextContent(type="text", text="Please provide a render_id.")]

    response = api_post(f"/v1/renders/{render_id}/cancel")
    response.raise_for_status()
    job = response.json()
    return [TextContent(type="text", text=f"Render {job['id']} canceled. Status: {job['status']}")]


# ── Tool Registration ──

register_tool(Tool(
    name="render_video",
    description="Render a Remotion video using any template. Templates: property-showcase, cinematic-event-recap, captioned-reel, slideshow, timeline-editor. Voice: 'Render a property showcase video' or 'Create a slideshow from these photos'.",
    inputSchema={
        "type": "object",
        "properties": {
            "template": {"type": "string", "description": "Template: property-showcase, cinematic-event-recap, captioned-reel, slideshow, timeline-editor"},
            "composition_id": {"type": "string", "description": "Remotion composition ID (auto-detected from template if omitted)"},
            "input_props": {"type": "object", "description": "Props to pass to the composition (varies by template)"},
            "webhook_url": {"type": "string", "description": "URL to receive notification when render completes"},
        },
        "required": ["template"],
    },
), handle_render_video)

register_tool(Tool(
    name="render_property_video",
    description="Render a polished property showcase video with photos, price, details, and agent branding. Voice: 'Make a listing video for 123 Main St with these photos' or 'Render a property video for the Miami condo'.",
    inputSchema={
        "type": "object",
        "properties": {
            "property_address": {"type": "string", "description": "Property address"},
            "property_price": {"type": "string", "description": "Price like '$500,000'"},
            "property_photos": {"type": "array", "items": {"type": "string"}, "description": "Array of photo URLs"},
            "bedrooms": {"type": "number", "description": "Number of bedrooms"},
            "bathrooms": {"type": "number", "description": "Number of bathrooms"},
            "square_feet": {"type": "number", "description": "Square footage"},
            "agent_name": {"type": "string", "description": "Agent name for outro"},
            "agent_phone": {"type": "string", "description": "Agent phone for outro"},
            "logoUrl": {"type": "string", "description": "Logo image URL"},
            "audioUrl": {"type": "string", "description": "ElevenLabs voiceover audio URL"},
            "webhook_url": {"type": "string", "description": "Webhook URL for completion notification"},
        },
        "required": ["property_address"],
    },
), handle_render_property_video)

register_tool(Tool(
    name="check_render_status",
    description="Check the status and progress of a video render job. Voice: 'How is my video render doing?' or 'Check render status'.",
    inputSchema={
        "type": "object",
        "properties": {
            "render_id": {"type": "string", "description": "Render job ID"},
        },
        "required": ["render_id"],
    },
), handle_check_render_status)

register_tool(Tool(
    name="list_renders",
    description="List all video render jobs. Voice: 'Show my renders' or 'List all video jobs'.",
    inputSchema={"type": "object", "properties": {}},
), handle_list_renders)

register_tool(Tool(
    name="cancel_render",
    description="Cancel an in-progress video render. Voice: 'Cancel that render' or 'Stop the video render'.",
    inputSchema={
        "type": "object",
        "properties": {
            "render_id": {"type": "string", "description": "Render job ID to cancel"},
        },
        "required": ["render_id"],
    },
), handle_cancel_render)
