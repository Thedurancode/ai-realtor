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
    text = voice

    # Inline key metrics
    pv = data.get("portfolio_value", {})
    if pv.get("total_properties"):
        text += f"\n\nPortfolio: {pv['total_properties']} properties, total ${pv.get('total_price', 0):,.0f}, avg ${pv.get('avg_price', 0):,.0f}."
        if pv.get("total_zestimate"):
            text += f" Total Zestimate: ${pv['total_zestimate']:,.0f}."

    pipeline = data.get("pipeline", {})
    if pipeline.get("by_status"):
        status_parts = [f"{s}: {c}" for s, c in pipeline["by_status"].items() if c > 0]
        if status_parts:
            text += f"\nPipeline: {', '.join(status_parts)}."

    ds = data.get("deal_scores", {})
    if ds.get("avg_score"):
        text += f"\nDeal scores: avg {ds['avg_score']}."

    ec = data.get("enrichment_coverage", {})
    if ec:
        text += f"\nEnrichment: {ec.get('zillow_pct', 0):.0f}% Zillow, {ec.get('skip_trace_pct', 0):.0f}% skip traced."

    return [TextContent(type="text", text=text.strip())]


async def handle_get_pipeline_summary(arguments: dict) -> list[TextContent]:
    """Pipeline status breakdown."""
    response = api_get("/analytics/pipeline")
    response.raise_for_status()
    data = response.json()

    voice = data.get("voice_summary", "No data.")
    text = voice

    pipeline = data.get("pipeline", {})
    if pipeline.get("by_status"):
        status_parts = [f"{s}: {c}" for s, c in pipeline["by_status"].items() if c > 0]
        if status_parts:
            text += f"\n\nBy status: {', '.join(status_parts)}."
    if pipeline.get("by_type"):
        type_parts = [f"{t}: {c}" for t, c in pipeline["by_type"].items() if c > 0]
        if type_parts:
            text += f" By type: {', '.join(type_parts)}."

    return [TextContent(type="text", text=text.strip())]


async def handle_get_contract_summary(arguments: dict) -> list[TextContent]:
    """Contract status across all properties."""
    response = api_get("/analytics/contracts")
    response.raise_for_status()
    data = response.json()

    voice = data.get("voice_summary", "No data.")
    text = voice

    contracts = data.get("contracts", {})
    if contracts.get("by_status"):
        status_parts = [f"{s}: {c}" for s, c in contracts["by_status"].items() if c > 0]
        if status_parts:
            text += f"\n\nBy status: {', '.join(status_parts)}."
    if contracts.get("unsigned_required"):
        text += f" {contracts['unsigned_required']} unsigned required contracts."

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
