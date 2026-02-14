"""Comparable Sales Dashboard MCP tools."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get


def _format_comp_sale(i: int, s: dict) -> str:
    price = f"${s['sale_price']:,.0f}" if s.get("sale_price") else "N/A"
    sqft = f"{s['sqft']:,} sqft" if s.get("sqft") else ""
    beds = f"{s['beds']}bd" if s.get("beds") else ""
    baths = f"/{s['baths']}ba" if s.get("baths") else ""
    dist = f"{s['distance_mi']:.1f}mi" if s.get("distance_mi") is not None else ""
    match = f"{s['similarity_score']*100:.0f}% match" if s.get("similarity_score") else ""
    date = s.get("sale_date", "")
    parts = [p for p in [sqft, f"{beds}{baths}", dist, match, date] if p]
    detail = ", ".join(parts)
    return f"  {i}. {s.get('address', 'Unknown')} — {price} ({detail})"


def _format_comp_rental(i: int, r: dict) -> str:
    rent = f"${r['rent']:,.0f}/mo" if r.get("rent") else "N/A"
    sqft = f"{r['sqft']:,} sqft" if r.get("sqft") else ""
    beds = f"{r['beds']}bd" if r.get("beds") else ""
    baths = f"/{r['baths']}ba" if r.get("baths") else ""
    dist = f"{r['distance_mi']:.1f}mi" if r.get("distance_mi") is not None else ""
    match = f"{r['similarity_score']*100:.0f}% match" if r.get("similarity_score") else ""
    parts = [p for p in [sqft, f"{beds}{baths}", dist, match] if p]
    detail = ", ".join(parts)
    return f"  {i}. {r.get('address', 'Unknown')} — {rent} ({detail})"


async def handle_get_comps_dashboard(arguments: dict) -> list[TextContent]:
    """Get full comp dashboard."""
    property_id = arguments.get("property_id")
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id.")]

    response = api_get(f"/comps/{property_id}")
    if response.status_code == 404:
        return [TextContent(type="text", text=f"Property {property_id} not found.")]
    response.raise_for_status()
    data = response.json()

    voice = data.get("voice_summary", "No comp data.")
    text = f"{voice}\n\n"

    # Subject
    subject = data.get("subject", {})
    text += f"Subject: {subject.get('address', 'N/A')}\n"
    text += f"  List Price: ${subject.get('price', 0):,.0f}"
    if subject.get("zestimate"):
        text += f" | Zestimate: ${subject['zestimate']:,.0f}"
    text += f"\n  {subject.get('beds', '?')}bd/{subject.get('baths', '?')}ba, {subject.get('sqft', '?')} sqft\n\n"

    # Sales comps
    sales = data.get("comp_sales", [])
    if sales:
        text += f"COMPARABLE SALES ({len(sales)}):\n"
        for i, s in enumerate(sales[:10], 1):
            text += _format_comp_sale(i, s) + "\n"
        text += "\n"

    # Market metrics
    metrics = data.get("market_metrics", {})
    if metrics.get("comp_count"):
        text += "MARKET METRICS:\n"
        text += f"  Median Price: ${metrics.get('median_sale_price', 0):,.0f}\n"
        text += f"  Avg Price/sqft: ${metrics.get('avg_price_per_sqft', 0):,.0f}\n"
        if metrics.get("price_range"):
            text += f"  Range: ${metrics['price_range']['min']:,.0f} - ${metrics['price_range']['max']:,.0f}\n"
        if metrics.get("price_trend") and metrics["price_trend"] != "insufficient_data":
            text += f"  Trend: {metrics['price_trend']} ({metrics.get('trend_pct', 0):+.1f}%)\n"
        if metrics.get("subject_vs_market"):
            text += f"  vs Market: {metrics['subject_vs_market'].replace('_', ' ')} ({metrics.get('subject_difference_pct', 0):+.1f}%)\n"
        text += "\n"

    # Rentals
    rentals = data.get("comp_rentals", [])
    if rentals:
        text += f"COMPARABLE RENTALS ({len(rentals)}):\n"
        for i, r in enumerate(rentals[:5], 1):
            text += _format_comp_rental(i, r) + "\n"
        text += "\n"

    # Internal portfolio
    internal = data.get("internal_portfolio_comps", [])
    if internal:
        text += f"PORTFOLIO COMPS ({len(internal)}):\n"
        for c in internal[:5]:
            price = f"${c['price']:,.0f}" if c.get("price") else "N/A"
            text += f"  Property #{c['property_id']} {c['address']} — {price} ({c.get('status', 'N/A')})\n"
        text += "\n"

    # Recommendation
    rec = data.get("pricing_recommendation", "")
    if rec:
        text += f"RECOMMENDATION: {rec}\n"

    return [TextContent(type="text", text=text.strip())]


async def handle_get_comp_sales(arguments: dict) -> list[TextContent]:
    """Get sales comps only."""
    property_id = arguments.get("property_id")
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id.")]

    response = api_get(f"/comps/{property_id}/sales")
    if response.status_code == 404:
        return [TextContent(type="text", text=f"Property {property_id} not found.")]
    response.raise_for_status()
    data = response.json()

    voice = data.get("voice_summary", "No sales comp data.")
    sales = data.get("comp_sales", [])

    if not sales:
        return [TextContent(type="text", text=voice)]

    text = f"{voice}\n\n"
    for i, s in enumerate(sales[:10], 1):
        text += _format_comp_sale(i, s) + "\n"

    rec = data.get("pricing_recommendation", "")
    if rec:
        text += f"\n{rec}"

    return [TextContent(type="text", text=text.strip())]


async def handle_get_comp_rentals(arguments: dict) -> list[TextContent]:
    """Get rental comps only."""
    property_id = arguments.get("property_id")
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id.")]

    response = api_get(f"/comps/{property_id}/rentals")
    if response.status_code == 404:
        return [TextContent(type="text", text=f"Property {property_id} not found.")]
    response.raise_for_status()
    data = response.json()

    voice = data.get("voice_summary", "No rental comp data.")
    rentals = data.get("comp_rentals", [])

    if not rentals:
        return [TextContent(type="text", text=voice)]

    text = f"{voice}\n\n"
    for i, r in enumerate(rentals[:10], 1):
        text += _format_comp_rental(i, r) + "\n"

    return [TextContent(type="text", text=text.strip())]


# ── Registration ──

register_tool(
    Tool(
        name="get_comps_dashboard",
        description=(
            "Get full comparable sales dashboard — comp sales, comp rentals, market metrics, "
            "internal portfolio matches, and AI pricing recommendation. "
            "Voice: 'Show me comps for property 5', 'What are the comparables?', "
            "'Compare property 5 to nearby sales', 'Market analysis for property 5'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "The property ID to analyze",
                },
            },
            "required": ["property_id"],
        },
    ),
    handle_get_comps_dashboard,
)

register_tool(
    Tool(
        name="get_comp_sales",
        description=(
            "Get comparable sales for a property with market metrics and pricing recommendation. "
            "Voice: 'What have similar properties sold for?', 'Nearby sales for property 5', "
            "'Sales comps'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "The property ID to analyze",
                },
            },
            "required": ["property_id"],
        },
    ),
    handle_get_comp_sales,
)

register_tool(
    Tool(
        name="get_comp_rentals",
        description=(
            "Get comparable rentals for a property. "
            "Voice: 'What are similar properties renting for?', 'Rental comps for property 5', "
            "'What's the rental market like?'"
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "The property ID to analyze",
                },
            },
            "required": ["property_id"],
        },
    ),
    handle_get_comp_rentals,
)
