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
    text += "\n\n=== STRATEGY COMPARISON ===\n\n"

    def _fmt_strategy(label, s):
        ds = s.get("deal_score", {})
        grade = ds.get("grade", "?") if ds else "?"
        block = f"{label} (Grade {grade}):\n"
        block += f"  Offer: ${s.get('offer_price', 0):,.0f}\n"
        block += f"  Profit: ${s.get('net_profit', 0) or 0:,.0f}\n"
        if s.get("roi_percent"):
            block += f"  ROI: {s['roi_percent']:.1f}%\n"
        if s.get("monthly_cash_flow"):
            block += f"  Cash Flow: ${s['monthly_cash_flow']:,.0f}/mo\n"
        if s.get("cap_rate"):
            block += f"  Cap Rate: {s['cap_rate']:.1f}%\n"
        if s.get("cash_on_cash_return"):
            block += f"  Cash-on-Cash: {s['cash_on_cash_return']:.1f}%\n"
        if s.get("holding_costs"):
            block += f"  Holding Costs: ${s['holding_costs']:,.0f}\n"
        fin = s.get("financing")
        if fin:
            block += f"  Financing: ${fin['loan_amount']:,.0f} loan @ {fin['interest_rate']*100:.1f}% ({fin['loan_type']})\n"
            block += f"  Monthly P&I: ${fin['monthly_payment']:,.0f}\n"
        eb = s.get("expense_breakdown")
        if eb:
            block += f"  Monthly Expenses: ${eb['total_monthly']:,.0f} (mgmt ${eb['property_management']:,.0f} + vacancy ${eb['vacancy_reserve']:,.0f} + capex ${eb['capex_reserve']:,.0f} + repairs ${eb['repairs_reserve']:,.0f} + ins ${eb['insurance']:,.0f} + tax ${eb['property_tax']:,.0f} + debt ${eb['debt_service']:,.0f})\n"
        brrrr = s.get("brrrr")
        if brrrr:
            block += f"  Initial Cash In: ${brrrr['initial_cash_in']:,.0f}\n"
            block += f"  Refi Loan: ${brrrr['refi_loan_amount']:,.0f}\n"
            block += f"  Cash Back at Refi: ${brrrr['cash_back_at_refi']:,.0f}\n"
            block += f"  Cash Left in Deal: ${brrrr['cash_left_in_deal']:,.0f}\n"
            if brrrr.get("infinite_return"):
                block += f"  *** INFINITE RETURN — All cash recovered! ***\n"
            block += f"  Post-Refi Cash Flow: ${brrrr['monthly_cash_flow_post_refi']:,.0f}/mo\n"
        return block

    text += _fmt_strategy("WHOLESALE", data.get("wholesale", {}))
    text += "\n"
    text += _fmt_strategy("FIX & FLIP", data.get("flip", {}))
    text += "\n"
    text += _fmt_strategy("RENTAL", data.get("rental", {}))

    brrrr_data = data.get("brrrr")
    if brrrr_data:
        text += "\n"
        text += _fmt_strategy("BRRRR", brrrr_data)

    text += f"\nRECOMMENDED: {data.get('recommended_strategy', '').upper()}\n{data.get('recommendation_reason', '')}"
    text += f"\nARV: ${data.get('arv', 0):,.0f} (source: {data.get('data_sources', {}).get('arv_source', 'unknown')})"
    return [TextContent(type="text", text=text)]


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

    text = f"Strategy Comparison: {data.get('property_address', '')}\n"
    text += f"List Price: ${data.get('list_price', 0) or 0:,.0f} | ARV: ${data.get('arv', 0):,.0f}\n\n"

    strategies = ["wholesale", "flip", "rental"]
    if data.get("brrrr"):
        strategies.append("brrrr")

    for s_name in strategies:
        s = data.get(s_name, {})
        ds = s.get("deal_score", {})
        grade = ds.get("grade", "?") if ds else "?"
        text += f"{s_name.upper()} (Grade {grade}):\n"
        text += f"  Offer: ${s.get('offer_price', 0):,.0f}\n"
        text += f"  Profit: ${s.get('net_profit', 0) or 0:,.0f}\n"
        if s.get("roi_percent"):
            text += f"  ROI: {s['roi_percent']:.1f}%\n"
        if s.get("monthly_cash_flow"):
            text += f"  Cash Flow: ${s['monthly_cash_flow']:,.0f}/mo\n"
        if s.get("cap_rate"):
            text += f"  Cap Rate: {s['cap_rate']:.1f}%\n"
        brrrr = s.get("brrrr")
        if brrrr and brrrr.get("infinite_return"):
            text += f"  *** INFINITE RETURN ***\n"
        text += "\n"

    text += f"RECOMMENDED: {data.get('recommended_strategy', '').upper()}\n"
    text += data.get("recommendation_reason", "")
    return [TextContent(type="text", text=text)]


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

    text = "WHAT-IF SCENARIO\n"
    if arguments.get("arv_override"):
        text += f"Custom ARV: ${arguments['arv_override']:,.0f}\n"
    if arguments.get("monthly_rent_override"):
        text += f"Custom Rent: ${arguments['monthly_rent_override']:,.0f}/mo\n"
    if arguments.get("rehab_tier"):
        text += f"Rehab Tier: {arguments['rehab_tier']}\n"
    text += "\n"
    text += data.get("voice_summary", "")
    return [TextContent(type="text", text=text)]


# ── Tool Registration ──

register_tool(Tool(name="calculate_deal", description="Calculate deal metrics for a property across wholesale, flip, and rental strategies. Automatically pulls Zillow/underwriting data. Returns recommended strategy with offer price and profit. Voice: 'Calculate the deal for property 5' or 'Run deal numbers on the Brooklyn property with heavy rehab'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID"}, "address": {"type": "string", "description": "Property address (alternative to property_id)"}, "rehab_tier": {"type": "string", "enum": ["light", "medium", "heavy"], "default": "medium", "description": "Rehab tier: light ($15/sqft), medium ($35/sqft), heavy ($60/sqft)"}, "arv_override": {"type": "number", "description": "Override ARV for what-if analysis"}, "monthly_rent_override": {"type": "number", "description": "Override monthly rent for what-if analysis"}}}), handle_calculate_deal)

register_tool(Tool(name="compare_strategies", description="Compare wholesale, flip, and rental strategies side-by-side for a property. Shows offer price, profit, ROI, and cash flow for each. Voice: 'Compare strategies for property 5' or 'Compare wholesale vs flip for the Main Street property'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID"}, "address": {"type": "string", "description": "Property address (alternative to property_id)"}}}), handle_compare_strategies)

register_tool(Tool(name="what_if_deal", description="Run a what-if scenario on a deal with custom assumptions. Voice: 'What if the ARV is 500 thousand on property 5?' or 'Recalculate property 3 with heavy rehab and 2000 rent'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "Property ID"}, "address": {"type": "string", "description": "Property address (alternative to property_id)"}, "arv_override": {"type": "number", "description": "Custom ARV value"}, "monthly_rent_override": {"type": "number", "description": "Custom monthly rent"}, "rehab_tier": {"type": "string", "enum": ["light", "medium", "heavy"], "description": "Rehab tier"}}}), handle_what_if_deal)
