"""Deal calculator MCP tools."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post
from ..utils.property_resolver import find_property_by_address


# ── Handlers ──

async def handle_calculate_deal(arguments: dict) -> list[TextContent]:
    property_id = arguments.get("property_id")
    address = arguments.get("address")
    if not property_id and address:
        property_id = find_property_by_address(address)
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id or address.")]

    params = {"property_id": property_id, "rehab_tier": arguments.get("rehab_tier", "medium")}
    if arguments.get("arv_override"):
        params["arv"] = arguments["arv_override"]
    if arguments.get("monthly_rent_override"):
        params["monthly_rent"] = arguments["monthly_rent_override"]

    response = api_post("/deal-calculator/voice", params=params)
    response.raise_for_status()
    data = response.json()

    text = data.get("voice_summary", "")

    # Concise strategy comparison
    def _fmt(label, s):
        if not s:
            return ""
        ds = s.get("deal_score", {})
        grade = ds.get("grade", "?") if ds else "?"
        parts = [f"offer ${s.get('offer_price', 0):,.0f}", f"profit ${s.get('net_profit', 0) or 0:,.0f}"]
        if s.get("roi_percent"):
            parts.append(f"ROI {s['roi_percent']:.1f}%")
        if s.get("monthly_cash_flow"):
            parts.append(f"cash flow ${s['monthly_cash_flow']:,.0f}/mo")
        if s.get("cap_rate"):
            parts.append(f"cap rate {s['cap_rate']:.1f}%")
        brrrr = s.get("brrrr")
        if brrrr and brrrr.get("infinite_return"):
            parts.append("INFINITE RETURN")
        return f"\n{label} (Grade {grade}): {', '.join(parts)}."

    text += "\n"
    text += _fmt("Wholesale", data.get("wholesale", {}))
    text += _fmt("Fix & Flip", data.get("flip", {}))
    text += _fmt("Rental", data.get("rental", {}))
    if data.get("brrrr"):
        text += _fmt("BRRRR", data["brrrr"])

    rec = data.get('recommended_strategy', '').replace('_', ' ').title()
    text += f"\n\nRecommended: {rec}. {data.get('recommendation_reason', '')}"
    text += f"\nARV: ${data.get('arv', 0):,.0f} (source: {data.get('data_sources', {}).get('arv_source', 'unknown')})."
    return [TextContent(type="text", text=text.strip())]


async def handle_compare_strategies(arguments: dict) -> list[TextContent]:
    property_id = arguments.get("property_id")
    address = arguments.get("address")
    if not property_id and address:
        property_id = find_property_by_address(address)
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id or address.")]

    response = api_get(f"/deal-calculator/property/{property_id}")
    response.raise_for_status()
    data = response.json()

    addr = data.get('property_address', 'this property')
    text = f"Strategy comparison for {addr} (list ${data.get('list_price', 0) or 0:,.0f}, ARV ${data.get('arv', 0):,.0f}):\n"

    strategies = ["wholesale", "flip", "rental"]
    if data.get("brrrr"):
        strategies.append("brrrr")

    for s_name in strategies:
        s = data.get(s_name, {})
        if not s:
            continue
        ds = s.get("deal_score", {})
        grade = ds.get("grade", "?") if ds else "?"
        label = s_name.replace("_", " ").title()
        parts = [f"offer ${s.get('offer_price', 0):,.0f}", f"profit ${s.get('net_profit', 0) or 0:,.0f}"]
        if s.get("roi_percent"):
            parts.append(f"ROI {s['roi_percent']:.1f}%")
        if s.get("monthly_cash_flow"):
            parts.append(f"cash flow ${s['monthly_cash_flow']:,.0f}/mo")
        if s.get("cap_rate"):
            parts.append(f"cap rate {s['cap_rate']:.1f}%")
        brrrr = s.get("brrrr")
        if brrrr and brrrr.get("infinite_return"):
            parts.append("INFINITE RETURN")
        text += f"\n{label} (Grade {grade}): {', '.join(parts)}."

    rec = data.get('recommended_strategy', '').replace('_', ' ').title()
    text += f"\n\nRecommended: {rec}. {data.get('recommendation_reason', '')}"
    return [TextContent(type="text", text=text.strip())]


async def handle_what_if_deal(arguments: dict) -> list[TextContent]:
    property_id = arguments.get("property_id")
    address = arguments.get("address")
    if not property_id and address:
        property_id = find_property_by_address(address)
    if not property_id:
        return [TextContent(type="text", text="Please provide a property_id or address.")]

    payload = {"property_id": property_id}
    if arguments.get("arv_override"):
        payload["arv_override"] = arguments["arv_override"]
    if arguments.get("monthly_rent_override"):
        payload["monthly_rent_override"] = arguments["monthly_rent_override"]
    if arguments.get("rehab_tier"):
        payload["rehab"] = {"tier": arguments["rehab_tier"]}

    response = api_post("/deal-calculator/calculate", json=payload)
    response.raise_for_status()
    data = response.json()

    overrides = []
    if arguments.get("arv_override"):
        overrides.append(f"ARV ${arguments['arv_override']:,.0f}")
    if arguments.get("monthly_rent_override"):
        overrides.append(f"rent ${arguments['monthly_rent_override']:,.0f}/mo")
    if arguments.get("rehab_tier"):
        overrides.append(f"{arguments['rehab_tier']} rehab")

    text = f"What-if scenario with {', '.join(overrides)}:\n\n" if overrides else "What-if scenario:\n\n"
    text += data.get("voice_summary", "")
    return [TextContent(type="text", text=text.strip())]


# ── Tool Registration ──

register_tool(Tool(name="calculate_deal", description="Calculate deal metrics for a property across wholesale, flip, and rental strategies. Automatically pulls Zillow/underwriting data. Returns recommended strategy with offer price and profit. Voice: 'Calculate the deal for property 5' or 'Run deal numbers on the Brooklyn property with heavy rehab'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID"}, "address": {"type": "string", "description": "Property address (alternative to property_id)"}, "rehab_tier": {"type": "string", "enum": ["light", "medium", "heavy"], "default": "medium", "description": "Rehab tier: light ($15/sqft), medium ($35/sqft), heavy ($60/sqft)"}, "arv_override": {"type": "number", "description": "Override ARV for what-if analysis"}, "monthly_rent_override": {"type": "number", "description": "Override monthly rent for what-if analysis"}}}), handle_calculate_deal)

register_tool(Tool(name="compare_strategies", description="Compare wholesale, flip, and rental strategies side-by-side for a property. Shows offer price, profit, ROI, and cash flow for each. Voice: 'Compare strategies for property 5' or 'Compare wholesale vs flip for the Main Street property'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID"}, "address": {"type": "string", "description": "Property address (alternative to property_id)"}}}), handle_compare_strategies)

register_tool(Tool(name="what_if_deal", description="Run a what-if scenario on a deal with custom assumptions. Voice: 'What if the ARV is 500 thousand on property 5?' or 'Recalculate property 3 with heavy rehab and 2000 rent'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID"}, "address": {"type": "string", "description": "Property address (alternative to property_id)"}, "arv_override": {"type": "number", "description": "Custom ARV value"}, "monthly_rent_override": {"type": "number", "description": "Custom monthly rent"}, "rehab_tier": {"type": "string", "enum": ["light", "medium", "heavy"], "description": "Rehab tier"}}}), handle_what_if_deal)
