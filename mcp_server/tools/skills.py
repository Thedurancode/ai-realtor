"""
Skills System MCP Tools - Voice Commands for Agent Skill Management
"""
import httpx
from mcp.types import Tool, TextContent
from mcp_server.server import register_tool
from mcp_server.tools.base import API_BASE_URL
from typing import Dict, Any, List


async def handle_list_skills(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    List all available skills

    Voice: "Show me all available skills"
    Voice: "What skills can I enable?"
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/skills",
            timeout=30.0
        )
        response.raise_for_status()
        result = response.json()

    if not result:
        return [TextContent(
            type="text",
            text="No skills available."
        )]

    total = len(result)
    enabled = len([s for s in result if s.get("is_enabled")])

    voice_lines = [f"You have {total} skill{'s' if total != 1 else ''} ({enabled} enabled)"]

    for skill in result[:10]:
        status = "✅" if skill.get("is_enabled") else "❌"
        voice_lines.append(f"{status} {skill.get('name', 'Unknown')}: {skill.get('description', '')[:60]}")

    if len(result) > 10:
        voice_lines.append(f"... and {len(result) - 10} more")

    return [TextContent(type="text", text="\n".join(voice_lines))]


async def handle_enable_skill(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Enable a skill for the agent

    Voice: "Enable the voice commands skill"
    Voice: "Turn on property scoring"
    """
    skill_id_or_name = arguments.get("skill_id_or_name")

    if not skill_id_or_name:
        return [TextContent(type="text", text="Please provide a skill ID or name")]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/skills/{skill_id_or_name}/enable",
            timeout=30.0
        )
        if response.status_code == 404:
            return [TextContent(type="text", text=f"Skill '{skill_id_or_name}' not found")]
        response.raise_for_status()
        result = response.json()

    return [TextContent(
        type="text",
        text=f"Skill '{result.get('name', skill_id_or_name)}' enabled successfully."
    )]


async def handle_disable_skill(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Disable a skill for the agent

    Voice: "Disable the voice commands skill"
    Voice: "Turn off property scoring"
    """
    skill_id_or_name = arguments.get("skill_id_or_name")

    if not skill_id_or_name:
        return [TextContent(type="text", text="Please provide a skill ID or name")]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/skills/{skill_id_or_name}/disable",
            timeout=30.0
        )
        if response.status_code == 404:
            return [TextContent(type="text", text=f"Skill '{skill_id_or_name}' not found")]
        response.raise_for_status()
        result = response.json()

    return [TextContent(
        type="text",
        text=f"Skill '{result.get('name', skill_id_or_name)}' disabled."
    )]


async def handle_get_skill(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Get skill details

    Voice: "Show me details for the voice commands skill"
    Voice: "What does the property scoring skill do?"
    """
    skill_id_or_name = arguments.get("skill_id_or_name")

    if not skill_id_or_name:
        return [TextContent(type="text", text="Please provide a skill ID or name")]

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/skills/{skill_id_or_name}",
            timeout=30.0
        )
        if response.status_code == 404:
            return [TextContent(type="text", text=f"Skill '{skill_id_or_name}' not found")]
        response.raise_for_status()
        result = response.json()

    voice_lines = [
        f"Skill: {result.get('name', 'Unknown')}",
        f"Description: {result.get('description', 'No description')}",
        f"Status: {'Enabled' if result.get('is_enabled') else 'Disabled'}",
        f"Version: {result.get('version', 'Unknown')}"
    ]

    if result.get("capabilities"):
        voice_lines.append(f"\nCapabilities: {', '.join(result['capabilities'][:5])}")

    if result.get("settings"):
        voice_lines.append(f"\nSettings: {len(result['settings'])} configurable")

    return [TextContent(type="text", text="\n".join(voice_lines))]


async def handle_configure_skill(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Configure skill settings

    Voice: "Configure the voice commands skill"
    Voice: "Update settings for property scoring"
    """
    skill_id_or_name = arguments.get("skill_id_or_name")
    settings = arguments.get("settings", {})

    if not skill_id_or_name:
        return [TextContent(type="text", text="Please provide a skill ID or name")]

    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{API_BASE_URL}/skills/{skill_id_or_name}/configure",
            json=settings,
            timeout=30.0
        )
        if response.status_code == 404:
            return [TextContent(type="text", text=f"Skill '{skill_id_or_name}' not found")]
        response.raise_for_status()
        result = response.json()

    return [TextContent(
        type="text",
        text=f"Skill '{result.get('name', skill_id_or_name)}' configured successfully."
    )]


async def handle_check_skill_status(arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Check if a skill is enabled

    Voice: "Is the voice commands skill enabled?"
    Voice: "Check if property scoring is active"
    """
    skill_id_or_name = arguments.get("skill_id_or_name")

    if not skill_id_or_name:
        return [TextContent(type="text", text="Please provide a skill ID or name")]

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/skills/{skill_id_or_name}",
            timeout=30.0
        )
        if response.status_code == 404:
            return [TextContent(type="text", text=f"Skill '{skill_id_or_name}' not found")]
        response.raise_for_status()
        result = response.json()

    status = "enabled" if result.get("is_enabled") else "disabled"
    return [TextContent(
        type="text",
        text=f"Skill '{result.get('name', skill_id_or_name)}' is {status}."
    )]


# ==========================================================================
# REGISTER TOOLS
# ==========================================================================

register_tool(
    Tool(
        name="list_skills",
        description="List all available agent skills. Voice: 'Show me all available skills' or 'What skills can I enable?'.",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    handle_list_skills
)

register_tool(
    Tool(
        name="enable_skill",
        description="Enable a skill for the agent. Voice: 'Enable the voice commands skill' or 'Turn on property scoring'.",
        inputSchema={
            "type": "object",
            "properties": {
                "skill_id_or_name": {"type": "string", "description": "Skill ID or name"}
            },
            "required": ["skill_id_or_name"]
        }
    ),
    handle_enable_skill
)

register_tool(
    Tool(
        name="disable_skill",
        description="Disable a skill for the agent. Voice: 'Disable the voice commands skill' or 'Turn off property scoring'.",
        inputSchema={
            "type": "object",
            "properties": {
                "skill_id_or_name": {"type": "string", "description": "Skill ID or name"}
            },
            "required": ["skill_id_or_name"]
        }
    ),
    handle_disable_skill
)

register_tool(
    Tool(
        name="get_skill",
        description="Get skill details. Voice: 'Show me details for the voice commands skill' or 'What does the property scoring skill do?'.",
        inputSchema={
            "type": "object",
            "properties": {
                "skill_id_or_name": {"type": "string", "description": "Skill ID or name"}
            },
            "required": ["skill_id_or_name"]
        }
    ),
    handle_get_skill
)

register_tool(
    Tool(
        name="configure_skill",
        description="Configure skill settings. Voice: 'Configure the voice commands skill' or 'Update settings for property scoring'.",
        inputSchema={
            "type": "object",
            "properties": {
                "skill_id_or_name": {"type": "string", "description": "Skill ID or name"},
                "settings": {"type": "object", "description": "Settings to configure"}
            },
            "required": ["skill_id_or_name"]
        }
    ),
    handle_configure_skill
)

register_tool(
    Tool(
        name="check_skill_status",
        description="Check if a skill is enabled. Voice: 'Is the voice commands skill enabled?' or 'Check if property scoring is active'.",
        inputSchema={
            "type": "object",
            "properties": {
                "skill_id_or_name": {"type": "string", "description": "Skill ID or name"}
            },
            "required": ["skill_id_or_name"]
        }
    ),
    handle_check_skill_status
)
