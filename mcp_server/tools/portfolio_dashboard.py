"""Portfolio dashboard MCP tool — voice-friendly portfolio overview."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get


async def handle_portfolio_dashboard(arguments: dict) -> list[TextContent]:
    """Get a full portfolio snapshot."""
    params = {}
    if arguments.get("agent_id"):
        params["agent_id"] = arguments["agent_id"]

    response = api_get("/portfolio/dashboard", params=params)
    response.raise_for_status()
    data = response.json()

    return [TextContent(type="text", text=data.get("voice_summary", "No portfolio data available."))]


# ── Registration ──

register_tool(
    Tool(
        name="portfolio_dashboard",
        description=(
            "Get a bird's-eye view of your entire property portfolio. "
            "Shows total value, property counts by status, deal scores, "
            "enrichment coverage, contracts, offers, and top deals. "
            "Voice: 'How is my portfolio doing?' or 'Give me a portfolio summary' "
            "or 'What does my portfolio look like?'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "number",
                    "description": "Optional agent ID to filter by (omit for all)",
                },
            },
        },
    ),
    handle_portfolio_dashboard,
)
