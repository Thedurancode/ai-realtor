"""Agent Management - List, view, and update real estate agent profiles."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_patch


async def handle_list_agents(arguments: dict) -> list[TextContent]:
    """List all registered agents."""
    response = api_get("/agents")
    response.raise_for_status()
    data = response.json()

    agents = data if isinstance(data, list) else data.get("agents", [])

    if not agents:
        return [TextContent(type="text", text="No agents found.")]

    text = f"**Agents ({len(agents)})**\n\n"
    for agent in agents:
        agent_id = agent.get("id", "?")
        name = agent.get("name", "Unknown")
        email = agent.get("email", "")
        brokerage = agent.get("brokerage", "")
        phone = agent.get("phone", "")

        text += f"**{name}** (ID: {agent_id})\n"
        if email:
            text += f"  Email: {email}\n"
        if phone:
            text += f"  Phone: {phone}\n"
        if brokerage:
            text += f"  Brokerage: {brokerage}\n"
        text += "\n"

    return [TextContent(type="text", text=text)]


async def handle_get_agent(arguments: dict) -> list[TextContent]:
    """Get detailed information about a specific agent."""
    agent_id = arguments.get("agent_id")
    if not agent_id:
        return [TextContent(type="text", text="Error: agent_id is required.")]

    response = api_get(f"/agents/{agent_id}")
    response.raise_for_status()
    agent = response.json()

    text = f"**Agent Details**\n\n"
    text += f"**Name:** {agent.get('name', 'Unknown')}\n"
    text += f"**ID:** {agent.get('id', agent_id)}\n"
    text += f"**Email:** {agent.get('email', 'N/A')}\n"
    text += f"**Phone:** {agent.get('phone', 'N/A')}\n"
    text += f"**Brokerage:** {agent.get('brokerage', 'N/A')}\n"
    text += f"**License #:** {agent.get('license_number', 'N/A')}\n"
    text += f"**Status:** {agent.get('status', 'N/A')}\n"

    if agent.get("markets"):
        text += f"**Markets:** {', '.join(agent['markets'])}\n"
    if agent.get("specialties"):
        text += f"**Specialties:** {', '.join(agent['specialties'])}\n"
    if agent.get("created_at"):
        text += f"**Joined:** {agent['created_at']}\n"

    return [TextContent(type="text", text=text)]


async def handle_update_agent(arguments: dict) -> list[TextContent]:
    """Update an agent's profile information."""
    agent_id = arguments.get("agent_id")
    if not agent_id:
        return [TextContent(type="text", text="Error: agent_id is required.")]

    # Build update payload from provided fields
    update_fields = {}
    for field in ["name", "email", "phone", "brokerage", "license_number",
                   "markets", "specialties", "bio", "status"]:
        if field in arguments:
            update_fields[field] = arguments[field]

    if not update_fields:
        return [TextContent(type="text", text="Error: No fields to update. Provide at least one of: name, email, phone, brokerage, license_number, markets, specialties, bio, status.")]

    response = api_patch(f"/agents/{agent_id}", json=update_fields)
    response.raise_for_status()
    updated = response.json()

    text = f"**Agent Updated Successfully**\n\n"
    text += f"Agent ID: {agent_id}\n"
    text += f"Updated fields: {', '.join(update_fields.keys())}\n\n"

    for field, value in update_fields.items():
        text += f"  {field}: {value}\n"

    return [TextContent(type="text", text=text)]


# ── Registration ──

register_tool(
    Tool(
        name="list_agents",
        description=(
            "List all registered real estate agents. Returns name, email, phone, "
            "and brokerage for each agent. "
            "Voice: 'Show me all agents', 'List the agents in our system', "
            "'Who are our registered agents?', 'Get all agent profiles'"
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    handle_list_agents,
)

register_tool(
    Tool(
        name="get_agent",
        description=(
            "Get detailed information about a specific agent by ID. Returns full profile "
            "including name, email, phone, brokerage, license, markets, and specialties. "
            "Voice: 'Get agent 1 details', 'Show me agent profile for ID 3', "
            "'What's the info on agent 5?', 'Pull up agent details'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "number",
                    "description": "The agent's unique ID",
                },
            },
            "required": ["agent_id"],
        },
    ),
    handle_get_agent,
)

register_tool(
    Tool(
        name="update_agent",
        description=(
            "Update a real estate agent's profile. Can update name, email, phone, "
            "brokerage, license number, markets, specialties, bio, or status. "
            "Voice: 'Update agent 1 phone to 555-1234', 'Change agent 3 brokerage to Keller Williams', "
            "'Set agent email to new@email.com', 'Update my agent profile'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "number",
                    "description": "The agent's unique ID",
                },
                "name": {
                    "type": "string",
                    "description": "Agent's full name",
                },
                "email": {
                    "type": "string",
                    "description": "Agent's email address",
                },
                "phone": {
                    "type": "string",
                    "description": "Agent's phone number",
                },
                "brokerage": {
                    "type": "string",
                    "description": "Agent's brokerage name",
                },
                "license_number": {
                    "type": "string",
                    "description": "Real estate license number",
                },
                "markets": {
                    "type": "array",
                    "description": "Markets the agent operates in",
                    "items": {"type": "string"},
                },
                "specialties": {
                    "type": "array",
                    "description": "Agent's specialties (e.g., residential, commercial, luxury)",
                    "items": {"type": "string"},
                },
                "bio": {
                    "type": "string",
                    "description": "Agent bio or description",
                },
                "status": {
                    "type": "string",
                    "description": "Agent status (active, inactive, etc.)",
                },
            },
            "required": ["agent_id"],
        },
    ),
    handle_update_agent,
)
