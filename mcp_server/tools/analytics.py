"""Analytics MCP tools — cross-property portfolio intelligence."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get


def _format_dict_section(title: str, data: dict, indent: int = 2) -> str:
    """Format a dict section for display."""
    prefix = " " * indent
    text = f"{title}:\n"
    for k, v in data.items():
        if isinstance(v, dict):
            text += f"{prefix}{k}:\n"
            for k2, v2 in v.items():
                text += f"{prefix}  {k2}: {v2}\n"
        elif isinstance(v, list):
            text += f"{prefix}{k}: {len(v)} items\n"
            for item in v[:5]:
                if isinstance(item, dict):
                    summary = ", ".join(f"{ik}={iv}" for ik, iv in item.items())
                    text += f"{prefix}  - {summary}\n"
        else:
            text += f"{prefix}{k}: {v}\n"
    return text


async def handle_get_portfolio_summary(arguments: dict) -> list[TextContent]:
    """Full portfolio analytics."""
    response = api_get("/analytics/portfolio")
    response.raise_for_status()
    data = response.json()

    voice = data.get("voice_summary", "No data available.")
    text = f"{voice}\n\n"
    text += _format_dict_section("Pipeline", data.get("pipeline", {}))
    text += _format_dict_section("Portfolio Value", data.get("portfolio_value", {}))
    text += _format_dict_section("Contracts", data.get("contracts", {}))
    text += _format_dict_section("Activity", data.get("activity", {}))
    text += _format_dict_section("Deal Scores", data.get("deal_scores", {}))
    text += _format_dict_section("Enrichment Coverage", data.get("enrichment_coverage", {}))

    return [TextContent(type="text", text=text.strip())]


async def handle_get_pipeline_summary(arguments: dict) -> list[TextContent]:
    """Pipeline status breakdown."""
    response = api_get("/analytics/pipeline")
    response.raise_for_status()
    data = response.json()

    voice = data.get("voice_summary", "No data.")
    text = f"{voice}\n\n"
    text += _format_dict_section("Pipeline Details", data.get("pipeline", {}))

    return [TextContent(type="text", text=text.strip())]


async def handle_get_contract_summary(arguments: dict) -> list[TextContent]:
    """Contract status across all properties."""
    response = api_get("/analytics/contracts")
    response.raise_for_status()
    data = response.json()

    voice = data.get("voice_summary", "No data.")
    text = f"{voice}\n\n"
    text += _format_dict_section("Contract Details", data.get("contracts", {}))

    return [TextContent(type="text", text=text.strip())]


# ── Registration ──

register_tool(
    Tool(
        name="get_portfolio_summary",
        description=(
            "Get full portfolio analytics — pipeline status, total value, contract readiness, "
            "activity trends, deal scores, and enrichment coverage. "
            "Voice: 'How's my portfolio?', 'Give me the numbers', 'Portfolio overview'."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    handle_get_portfolio_summary,
)

register_tool(
    Tool(
        name="get_pipeline_summary",
        description=(
            "Get pipeline breakdown — how many properties by status and type. "
            "Voice: 'How many properties are pending?', 'Pipeline status', 'Show my funnel'."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    handle_get_pipeline_summary,
)

register_tool(
    Tool(
        name="get_contract_summary",
        description=(
            "Get contract status across all properties — total, by status, unsigned required. "
            "Voice: 'Contract status across all properties', 'How many contracts are pending?'."
        ),
        inputSchema={"type": "object", "properties": {}},
    ),
    handle_get_contract_summary,
)
