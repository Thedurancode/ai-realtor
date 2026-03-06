"""Shotstack Video Pipeline MCP Tools

Generate property showcase videos and brand videos via the Shotstack rendering pipeline.
Full pipeline: script generation -> ElevenLabs TTS -> HeyGen talking heads -> Pexels stock -> Shotstack render.
Also includes Shotstack template management (list, inspect, render with merge fields).
"""
import json

from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


def _get_shotstack():
    """Lazy-import ShotstackService to avoid import-time side effects."""
    from app.services.shotstack_service import ShotstackService
    return ShotstackService()


def _fetch_template_raw(template_id: str) -> tuple:
    """Fetch a Shotstack template via raw HTTP (preserves full asset JSON).
    Returns (template_dict, name) or (None, None) on failure.
    """
    import requests
    from app.config import settings
    host = (
        "https://api.shotstack.io/stage"
        if settings.shotstack_stage
        else "https://api.shotstack.io/v1"
    )
    resp = requests.get(
        f"{host}/templates/{template_id}",
        headers={"x-api-key": settings.shotstack_api_key},
    )
    if resp.status_code != 200:
        return None, None
    data = resp.json().get("response", {})
    return data.get("template", {}), data.get("name", "Untitled")


# ── Helpers ──────────────────────────────────────────────────────────

def _fmt_status(data: dict) -> str:
    """Format a video job status response for voice/text output."""
    status = data.get("status", "unknown")
    job_id = data.get("job_id")
    prop_id = data.get("property_id")
    video_url = data.get("video_url")
    error = data.get("error")
    style = data.get("style", "")
    duration = data.get("duration")

    STATUS_LABELS = {
        "pending": "Queued",
        "loading_data": "Loading property & brand data",
        "generating_script": "Writing AI script",
        "enhancing_script": "Enhancing script for voiceover",
        "generating_tts": "Generating voiceover audio (ElevenLabs)",
        "uploading_audio": "Uploading audio to cloud",
        "generating_talking_heads": "Generating talking head videos (HeyGen)",
        "generating_talking_head": "Generating talking head video (HeyGen)",
        "fetching_stock_footage": "Fetching stock footage (Pexels)",
        "building_timeline": "Building Shotstack timeline",
        "rendering": "Rendering video (Shotstack)",
        "done": "Complete",
        "failed": "Failed",
    }

    label = STATUS_LABELS.get(status, status)
    parts = [f"Job #{job_id}: {label}"]

    if prop_id and prop_id != 0:
        parts[0] += f" (property #{prop_id})"
    if style:
        parts.append(f"Style: {style}")
    if duration:
        parts.append(f"Duration: {duration}s")
    if video_url:
        parts.append(f"Video URL: {video_url}")
    if error:
        parts.append(f"Error: {error}")

    return "\n".join(parts)


def _get_agent_id() -> int:
    """Get agent_id from the API (uses the API key to resolve)."""
    # The middleware resolves the agent from the API key, so we call a
    # lightweight endpoint and extract agent_id from the response.
    resp = api_get("/properties/", params={"limit": 1})
    data = resp.json()
    if isinstance(data, list) and data:
        return data[0].get("agent_id", 1)
    return 1


# ── Handlers ─────────────────────────────────────────────────────────

async def handle_render_property_video(arguments: dict) -> list[TextContent]:
    """Start the full property video pipeline."""
    property_id = arguments.get("property_id")
    if not property_id:
        return [TextContent(type="text", text="Error: property_id is required")]

    agent_id = _get_agent_id()
    style = arguments.get("style", "luxury")

    body = {"style": style}
    queries = arguments.get("video_search_queries")
    if queries:
        body["video_search_queries"] = queries

    resp = api_post(
        f"/agent-brand/{agent_id}/property-video/{property_id}",
        json=body,
    )

    if resp.status_code >= 400:
        return [TextContent(type="text", text=f"Error ({resp.status_code}): {resp.text}")]

    data = resp.json()
    job_id = data.get("job_id")
    return [TextContent(
        type="text",
        text=(
            f"Property video started! Job #{job_id}.\n"
            f"Style: {style}\n"
            f"Pipeline: script -> TTS -> talking heads -> stock footage -> Shotstack render\n"
            f"This takes 10-15 minutes. Check status with check_video_render_status."
        ),
    )]


async def handle_render_brand_video(arguments: dict) -> list[TextContent]:
    """Start a brand video (logo intro + talking head + CTA outro)."""
    script = arguments.get("script")
    if not script:
        return [TextContent(type="text", text="Error: script is required (the text for the talking head to speak)")]

    agent_id = _get_agent_id()

    body = {
        "script": script,
        "enhance_script": arguments.get("enhance_script", True),
        "style": arguments.get("style", "professional"),
    }
    music_url = arguments.get("background_music_url")
    if music_url:
        body["background_music_url"] = music_url

    resp = api_post(f"/agent-brand/{agent_id}/brand-video", json=body)

    if resp.status_code >= 400:
        return [TextContent(type="text", text=f"Error ({resp.status_code}): {resp.text}")]

    data = resp.json()
    job_id = data.get("job_id")
    return [TextContent(
        type="text",
        text=(
            f"Brand video started! Job #{job_id}.\n"
            f"Structure: 4s logo intro -> talking head (~2 min) -> 6s CTA outro\n"
            f"This takes 10-15 minutes. Check status with check_video_render_status."
        ),
    )]


async def handle_check_video_render_status(arguments: dict) -> list[TextContent]:
    """Check the status of a video render job (polls Shotstack if rendering)."""
    job_id = arguments.get("job_id")
    if not job_id:
        return [TextContent(type="text", text="Error: job_id is required")]

    agent_id = _get_agent_id()
    resp = api_get(f"/agent-brand/{agent_id}/property-video/{job_id}/status")

    if resp.status_code >= 400:
        return [TextContent(type="text", text=f"Error ({resp.status_code}): {resp.text}")]

    return [TextContent(type="text", text=_fmt_status(resp.json()))]


async def handle_get_video_timeline(arguments: dict) -> list[TextContent]:
    """Get the Shotstack timeline JSON for a video job."""
    job_id = arguments.get("job_id")
    if not job_id:
        return [TextContent(type="text", text="Error: job_id is required")]

    agent_id = _get_agent_id()
    resp = api_get(f"/agent-brand/{agent_id}/property-video/{job_id}/timeline")

    if resp.status_code >= 400:
        return [TextContent(type="text", text=f"Error ({resp.status_code}): {resp.text}")]

    return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]


async def handle_list_video_jobs(arguments: dict) -> list[TextContent]:
    """List all property/brand video jobs for the agent."""
    agent_id = _get_agent_id()

    # The agent-brand router doesn't have a list endpoint for jobs,
    # so we query the properties and check for video jobs via a direct DB query.
    # For now, use the enhanced-videos list endpoint as fallback.
    resp = api_get("/enhanced-videos/", params={
        "limit": arguments.get("limit", 20),
    })

    if resp.status_code == 404:
        return [TextContent(type="text", text="No video jobs found. Generate one with render_property_video or render_brand_video.")]

    if resp.status_code >= 400:
        return [TextContent(type="text", text=f"Error ({resp.status_code}): {resp.text}")]

    videos = resp.json()
    if not videos:
        return [TextContent(type="text", text="No video jobs found. Generate one with render_property_video or render_brand_video.")]

    lines = [f"Found {len(videos)} video(s):"]
    for v in videos:
        vid = v.get("id") or v.get("video_id", "?")
        status = v.get("status", "unknown")
        prop_id = v.get("property_id", "—")
        url = v.get("final_video_url") or v.get("video_url") or ""
        line = f"  #{vid} — property #{prop_id} — {status}"
        if url:
            line += f" — {url}"
        lines.append(line)

    return [TextContent(type="text", text="\n".join(lines))]


async def handle_preview_video_script(arguments: dict) -> list[TextContent]:
    """Preview the AI-generated voiceover script for a property (no rendering)."""
    property_id = arguments.get("property_id")
    if not property_id:
        return [TextContent(type="text", text="Error: property_id is required")]

    resp = api_post(f"/v1/property-videos/script-preview?property_id={property_id}")

    if resp.status_code >= 400:
        return [TextContent(type="text", text=f"Error ({resp.status_code}): {resp.text}")]

    data = resp.json()
    script = data.get("script", "")
    word_count = data.get("word_count", 0)
    duration = data.get("estimated_duration_seconds", 0)
    prop = data.get("property", {})

    return [TextContent(
        type="text",
        text=(
            f"Script preview for {prop.get('address', 'property')} (${prop.get('price', 0):,.0f}):\n\n"
            f"{script}\n\n"
            f"Words: {word_count} | Est. duration: {duration}s"
        ),
    )]


# ── Register Tools ───────────────────────────────────────────────────

register_tool(
    Tool(
        name="render_property_video",
        description=(
            "Generate a full property showcase video with Shotstack. "
            "Pipeline: AI script -> ElevenLabs voiceover -> HeyGen talking head intro/outro -> "
            "Pexels stock footage -> Shotstack render. Takes 10-15 minutes. "
            "Voice: 'Make a video for property 3', 'Create a luxury video for the Brickell condo'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "integer", "description": "Property ID to generate video for"},
                "style": {
                    "type": "string",
                    "enum": ["luxury", "friendly", "professional"],
                    "description": "Video style preset (default: luxury)",
                },
                "video_search_queries": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Custom Pexels search queries for stock footage (optional, auto-generated if omitted)",
                },
            },
            "required": ["property_id"],
        },
    ),
    handle_render_property_video,
)

register_tool(
    Tool(
        name="render_brand_video",
        description=(
            "Generate a ~2 minute brand video: 4s logo intro -> HeyGen talking head with cloned voice -> "
            "6s branded CTA outro with contact info. Requires brand profile with voice clone, avatar, and logo. "
            "Voice: 'Make a brand video about our spring campaign', 'Create an intro video for my channel'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "The script for the talking head to speak (10-10000 chars)",
                },
                "style": {
                    "type": "string",
                    "enum": ["luxury", "friendly", "professional"],
                    "description": "Script enhancement style (default: professional)",
                },
                "enhance_script": {
                    "type": "boolean",
                    "description": "AI-enhance the script for better voiceover delivery (default: true)",
                },
                "background_music_url": {
                    "type": "string",
                    "description": "Optional URL to a background music MP3 file",
                },
            },
            "required": ["script"],
        },
    ),
    handle_render_brand_video,
)

register_tool(
    Tool(
        name="check_video_render_status",
        description=(
            "Check the status of a Shotstack video render job. Polls Shotstack live if currently rendering. "
            "Returns status, video URL (when done), and error details (if failed). "
            "Voice: 'What's the status of video job 5?', 'Is my video done yet?'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "job_id": {"type": "integer", "description": "Video job ID returned by render_property_video or render_brand_video"},
            },
            "required": ["job_id"],
        },
    ),
    handle_check_video_render_status,
)

register_tool(
    Tool(
        name="get_video_timeline",
        description=(
            "Get the raw Shotstack timeline JSON for a video job. Shows the full Edit payload: "
            "tracks, clips, transitions, effects, and output settings. "
            "Voice: 'Show me the timeline for video job 3'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "job_id": {"type": "integer", "description": "Video job ID"},
            },
            "required": ["job_id"],
        },
    ),
    handle_get_video_timeline,
)

register_tool(
    Tool(
        name="list_video_jobs",
        description=(
            "List all video generation jobs (property videos and brand videos). "
            "Shows job ID, status, property, and video URL. "
            "Voice: 'Show me all my videos', 'List video jobs'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max results (default: 20)"},
            },
        },
    ),
    handle_list_video_jobs,
)

register_tool(
    Tool(
        name="preview_video_script",
        description=(
            "Preview the AI-generated voiceover script for a property without rendering. "
            "Shows the script text, word count, and estimated duration. "
            "Voice: 'Preview the script for property 3', 'What would the voiceover say for the Miami condo?'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {"type": "integer", "description": "Property ID to generate script for"},
            },
            "required": ["property_id"],
        },
    ),
    handle_preview_video_script,
)


# ── Shotstack Template Handlers ──────────────────────────────────────

async def handle_list_shotstack_templates(arguments: dict) -> list[TextContent]:
    """List all saved Shotstack templates."""
    ss = _get_shotstack()
    try:
        templates = ss.list_templates()
    finally:
        ss.close()

    if not templates:
        return [TextContent(type="text", text="No Shotstack templates found. Save one with save_shotstack_template.")]

    lines = [f"Found {len(templates)} Shotstack template(s):"]
    for t in templates:
        lines.append(f"  - {t['name']} (ID: {t['id']})")
    return [TextContent(type="text", text="\n".join(lines))]


async def handle_get_shotstack_template(arguments: dict) -> list[TextContent]:
    """Inspect a Shotstack template — shows timeline structure and merge fields."""
    template_id = arguments.get("template_id")
    if not template_id:
        return [TextContent(type="text", text="Error: template_id is required")]

    # Use raw HTTP to get full JSON (the SDK strips asset types on deserialization)
    template, name = _fetch_template_raw(template_id)
    if not template:
        return [TextContent(type="text", text=f"Template {template_id} not found.")]

    # Extract merge fields from the template JSON
    template_str = json.dumps(template)
    import re
    merge_fields = sorted(set(re.findall(r'\{\{\s*(\w+)\s*\}\}', template_str)))

    # Summarize timeline structure
    timeline = template.get("timeline", {})
    tracks = timeline.get("tracks", [])
    track_summary = []
    for i, track in enumerate(tracks):
        clips = track.get("clips", [])
        clip_types = []
        for c in clips:
            asset = c.get("asset") or {}
            clip_types.append(asset.get("type", "unknown") if isinstance(asset, dict) else "unknown")
        track_summary.append(f"  Track {i}: {len(clips)} clip(s) [{', '.join(clip_types)}]")

    output = template.get("output", {})

    parts = [
        f"Template: {name}",
        f"ID: {template_id}",
        f"Output: {output.get('format', 'mp4')} {output.get('resolution', 'hd')} @ {output.get('fps', 30)}fps",
        "",
        "Timeline:",
        *track_summary,
    ]

    if merge_fields:
        parts.extend(["", f"Merge fields ({len(merge_fields)}): {', '.join(merge_fields)}",
                       "Use these with render_shotstack_template to customize the video."])
    else:
        parts.extend(["", "No merge fields found (this template has no customizable placeholders)."])

    # Include full JSON for reference
    parts.extend(["", "Full template JSON:", json.dumps(template, indent=2)])

    return [TextContent(type="text", text="\n".join(parts))]


async def handle_render_shotstack_template(arguments: dict) -> list[TextContent]:
    """Render a Shotstack template with optional merge field replacements."""
    template_id = arguments.get("template_id")
    if not template_id:
        return [TextContent(type="text", text="Error: template_id is required")]

    merge_fields = arguments.get("merge_fields")

    ss = _get_shotstack()
    try:
        result = ss.render_template(template_id, merge_fields)
    finally:
        ss.close()

    render_id = result.get("id", "unknown")
    status = result.get("status", "unknown")

    merge_info = ""
    if merge_fields:
        merge_info = f"\nMerge fields applied: {json.dumps(merge_fields)}"

    return [TextContent(
        type="text",
        text=(
            f"Template render started!\n"
            f"Render ID: {render_id}\n"
            f"Status: {status}{merge_info}\n"
            f"Check progress with check_shotstack_render (render_id: '{render_id}')."
        ),
    )]


async def handle_check_shotstack_render(arguments: dict) -> list[TextContent]:
    """Check status of a direct Shotstack render (template or custom)."""
    render_id = arguments.get("render_id")
    if not render_id:
        return [TextContent(type="text", text="Error: render_id is required")]

    ss = _get_shotstack()
    try:
        result = ss.get_render_status(render_id)
    finally:
        ss.close()

    status = result.get("status", "unknown")
    url = result.get("url")

    parts = [f"Render {render_id}: {status}"]
    if url:
        parts.append(f"Video URL: {url}")

    return [TextContent(type="text", text="\n".join(parts))]


async def handle_delete_shotstack_template(arguments: dict) -> list[TextContent]:
    """Delete a Shotstack template."""
    template_id = arguments.get("template_id")
    if not template_id:
        return [TextContent(type="text", text="Error: template_id is required")]

    ss = _get_shotstack()
    try:
        ss.delete_template(template_id)
    finally:
        ss.close()

    return [TextContent(type="text", text=f"Template {template_id} deleted.")]


# ── Register Template Tools ─────────────────────────────────────────

register_tool(
    Tool(
        name="list_shotstack_templates",
        description=(
            "List all saved Shotstack video templates. Shows template name and ID. "
            "Voice: 'Show me my video templates', 'What templates do I have?'."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    handle_list_shotstack_templates,
)

register_tool(
    Tool(
        name="get_shotstack_template",
        description=(
            "Inspect a Shotstack template. Shows timeline structure (tracks, clips), "
            "output settings, and available merge fields ({{ PLACEHOLDER }} values you can customize). "
            "Voice: 'Show me the Luxury Property Showcase template', 'What merge fields does template X have?'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "template_id": {"type": "string", "description": "Shotstack template ID"},
            },
            "required": ["template_id"],
        },
    ),
    handle_get_shotstack_template,
)

register_tool(
    Tool(
        name="render_shotstack_template",
        description=(
            "Render a Shotstack template with optional merge field replacements. "
            "Pass merge_fields to customize placeholders like {{ HEADLINE }}, {{ PRICE }}, {{ VIDEO_URL }}. "
            "Voice: 'Render the luxury template with the Brickell property', 'Use my brand intro template'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "template_id": {"type": "string", "description": "Shotstack template ID to render"},
                "merge_fields": {
                    "type": "object",
                    "description": "Key-value pairs to replace merge fields, e.g. {\"HEADLINE\": \"Dream Home\", \"PRICE\": \"$895,000\"}",
                    "additionalProperties": {"type": "string"},
                },
            },
            "required": ["template_id"],
        },
    ),
    handle_render_shotstack_template,
)

register_tool(
    Tool(
        name="check_shotstack_render",
        description=(
            "Check the status of a Shotstack render by render ID. Returns status and video URL when done. "
            "Use this for template renders (render_shotstack_template gives you the render_id). "
            "Voice: 'Is my template render done?', 'Check render abc123'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "render_id": {"type": "string", "description": "Shotstack render ID"},
            },
            "required": ["render_id"],
        },
    ),
    handle_check_shotstack_render,
)

register_tool(
    Tool(
        name="delete_shotstack_template",
        description=(
            "Delete a Shotstack template permanently. "
            "Voice: 'Delete the old template', 'Remove template X'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "template_id": {"type": "string", "description": "Shotstack template ID to delete"},
            },
            "required": ["template_id"],
        },
    ),
    handle_delete_shotstack_template,
)
