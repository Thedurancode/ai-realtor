"""Agentic research MCP tools."""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


# ── Handlers ──

async def handle_research_property(arguments: dict) -> list[TextContent]:
    payload = {"address": arguments["address"]}
    if arguments.get("city"):
        payload["city"] = arguments["city"]
    if arguments.get("state"):
        payload["state"] = arguments["state"]
    if arguments.get("zip"):
        payload["zip"] = arguments["zip"]
    payload["strategy"] = arguments.get("strategy", "wholesale")
    assumptions = {}
    if arguments.get("rehab_tier"):
        assumptions["rehab_tier"] = arguments["rehab_tier"]
    if arguments.get("extensive"):
        assumptions["extra_agents"] = ["extensive"]
        payload["mode"] = "orchestrated"
        payload["limits"] = {"max_steps": 20, "max_web_calls": 50, "max_parallel_agents": 4, "timeout_seconds_per_step": 20}
    if assumptions:
        payload["assumptions"] = assumptions

    timeout = 180 if arguments.get("extensive") else 120
    response = api_post("/agentic/research", json=payload, timeout=timeout)
    response.raise_for_status()
    result = response.json()

    prop_id = result.get("property_id")
    job_id = result.get("latest_job_id")
    output_data = result.get("output", {})

    # Build a voice-friendly research summary
    profile = output_data.get("property_profile", {})
    addr = profile.get('normalized_address', arguments['address']) if profile else arguments['address']
    facts = profile.get("parcel_facts", {}) if profile else {}
    fact_parts = []
    if facts.get("beds"):
        fact_parts.append(f"{facts['beds']}-bed")
    if facts.get("baths"):
        fact_parts.append(f"{facts['baths']}-bath")
    if facts.get("sqft"):
        fact_parts.append(f"{facts['sqft']:,} sqft")
    if facts.get("year"):
        fact_parts.append(f"built {facts['year']}")
    fact_str = f" ({', '.join(fact_parts)})" if fact_parts else ""

    text = f"Research complete for {addr}{fact_str}."
    if profile and profile.get("owner_names"):
        text += f" Owner: {', '.join(profile['owner_names'])}."

    # Underwriting — the most important data
    uw = output_data.get("underwrite", {})
    if uw:
        uw_parts = []
        arv = uw.get("arv_estimate", {})
        if arv.get("base"):
            uw_parts.append(f"ARV ${arv['base']:,.0f}")
        rent_est = uw.get("rent_estimate", {})
        if rent_est.get("base"):
            uw_parts.append(f"rent ${rent_est['base']:,.0f}/mo")
        rehab = uw.get("rehab_estimated_range", {})
        if rehab.get("low") and rehab.get("high"):
            uw_parts.append(f"rehab ${rehab['low']:,.0f}-${rehab['high']:,.0f}")
        offer = uw.get("offer_price_recommendation", {})
        if offer.get("base"):
            uw_parts.append(f"recommended offer ${offer['base']:,.0f}")
        if uw_parts:
            text += f"\n\nUnderwriting: {', '.join(uw_parts)}."

    # Comps summary (counts only for voice)
    comps_sales = output_data.get("comps_sales", [])
    comps_rentals = output_data.get("comps_rentals", [])
    if comps_sales or comps_rentals:
        comp_parts = []
        if comps_sales:
            avg_price = sum(c.get('sale_price', 0) for c in comps_sales if c.get('sale_price')) / max(len([c for c in comps_sales if c.get('sale_price')]), 1)
            comp_parts.append(f"{len(comps_sales)} sale comps (avg ${avg_price:,.0f})")
        if comps_rentals:
            avg_rent = sum(c.get('rent', 0) for c in comps_rentals if c.get('rent')) / max(len([c for c in comps_rentals if c.get('rent')]), 1)
            comp_parts.append(f"{len(comps_rentals)} rental comps (avg ${avg_rent:,.0f}/mo)")
        text += f"\nComparables: {', '.join(comp_parts)}."

    # Risk
    risk = output_data.get("risk_score", {})
    if risk:
        risk_parts = []
        if risk.get("data_confidence") is not None:
            text += f"\nData confidence: {risk['data_confidence']:.0%}."
        flags = risk.get("compliance_flags", [])
        if flags:
            text += f" Flags: {', '.join(flags)}."

    # Flood
    flood = output_data.get("flood_zone")
    if flood:
        zone = flood.get('flood_zone', 'Unknown')
        text += f"\nFlood zone: {zone}."
        if flood.get("in_floodplain"):
            text += " WARNING: in floodplain."
        if flood.get("insurance_required"):
            text += " Insurance required."

    # Neighborhood
    neighborhood = output_data.get("neighborhood_intel")
    if neighborhood:
        ai_summary = neighborhood.get("ai_summary")
        if ai_summary:
            text += f"\nNeighborhood: {ai_summary}"

    # Extensive data — one-line summaries only
    extensive = output_data.get("extensive")
    if extensive:
        ext_parts = []
        epa = extensive.get("epa_environmental")
        if epa and epa.get("risk_summary"):
            ext_parts.append(f"EPA: {epa['risk_summary']}")
        wildfire = extensive.get("wildfire_hazard")
        if wildfire and wildfire.get("hazard_level"):
            ext_parts.append(f"wildfire: {wildfire['hazard_level']}")
        ws = extensive.get("walk_score")
        if ws and ws.get("walk_score") is not None:
            ext_parts.append(f"walkability {ws['walk_score']}/100")
        redfin = extensive.get("redfin")
        if redfin and redfin.get("redfin_estimate"):
            est = redfin["redfin_estimate"]
            est_str = f"${est:,.0f}" if isinstance(est, (int, float)) else str(est)
            ext_parts.append(f"Redfin estimate {est_str}")
        rc = extensive.get("rentcast")
        if rc and rc.get("rent_estimate"):
            ext_parts.append(f"RentCast ${rc['rent_estimate']:,.0f}/mo")
        if ext_parts:
            text += f"\n\nExtended research: {'; '.join(ext_parts)}."

    # Stats
    runs = output_data.get("worker_runs", [])
    if runs:
        total_time = sum(r.get("runtime_ms", 0) for r in runs)
        text += f"\n\nResearch used {len(runs)} workers in {total_time/1000:.1f}s."

    return [TextContent(type="text", text=text.strip())]


async def handle_research_property_async(arguments: dict) -> list[TextContent]:
    payload = {"address": arguments["address"]}
    if arguments.get("city"):
        payload["city"] = arguments["city"]
    if arguments.get("state"):
        payload["state"] = arguments["state"]
    if arguments.get("zip"):
        payload["zip"] = arguments["zip"]
    payload["strategy"] = arguments.get("strategy", "wholesale")

    response = api_post("/agentic/jobs", json=payload, timeout=15)
    response.raise_for_status()
    result = response.json()

    text = f"Research job #{result.get('job_id')} started for {arguments['address']}. Running in the background — use get_research_status with job ID {result.get('job_id')} to check progress."
    return [TextContent(type="text", text=text)]


async def handle_get_research_status(arguments: dict) -> list[TextContent]:
    job_id = int(arguments["job_id"])
    response = api_get(f"/agentic/jobs/{job_id}", timeout=10)
    response.raise_for_status()
    result = response.json()

    status = result.get("status", "unknown")
    progress = result.get("progress", 0)
    step = result.get("current_step")

    text = f"Research job #{result.get('id')}: {status} ({progress}% complete)."
    if step:
        text += f" Current step: {step}."
    if result.get("error_message"):
        text += f" Error: {result['error_message']}."
    if status == "completed":
        text += f" Research is done — use get_research_dossier with property ID {result.get('property_id')} for the full report."
    return [TextContent(type="text", text=text)]


async def handle_get_research_dossier(arguments: dict) -> list[TextContent]:
    property_id = int(arguments["property_id"])
    response = api_get(f"/agentic/properties/{property_id}/dossier", timeout=10)
    response.raise_for_status()
    result = response.json()

    text = f"Investment dossier for property {property_id}:\n\n"
    text += result.get("markdown", "No dossier content available.")
    return [TextContent(type="text", text=text.strip())]


# ── Tool Registration ──

register_tool(Tool(name="research_property", description="Run a full agentic research analysis on a property address. Finds comparable sales, comparable rentals, calculates ARV, underwriting, risk score, and generates an investment dossier. Supports strategies: flip, rental, wholesale. Set extensive=true for deep research with EPA environmental, wildfire, seismic, wetlands, historic places, HUD indices, school districts, plus Redfin estimates, Walk/Transit/Bike scores, noise scores, recently sold homes, mortgage rates, and RentCast rent estimates. Voice: 'Do extensive research on 123 Main St New York'.", inputSchema={"type": "object", "properties": {"address": {"type": "string", "description": "Full property address to research (e.g., '123 Main St, New York, NY 10001')"}, "city": {"type": "string", "description": "City name (optional if included in address)"}, "state": {"type": "string", "description": "State abbreviation (optional if included in address)"}, "zip": {"type": "string", "description": "ZIP code (optional)"}, "strategy": {"type": "string", "description": "Investment strategy: flip (buy/renovate/sell), rental (buy for income), wholesale (buy below market/assign). Default: wholesale", "enum": ["flip", "rental", "wholesale"]}, "rehab_tier": {"type": "string", "description": "Renovation scope: light ($15/sqft), medium ($35/sqft), heavy ($60/sqft). Default: medium", "enum": ["light", "medium", "heavy"]}, "extensive": {"type": "boolean", "description": "Set true for extensive/deep research: adds EPA environmental, wildfire, seismic, wetlands, historic places, HUD indices, school districts, Redfin estimates, Walk/Transit/Bike scores, noise scores, sold homes, mortgage rates, and RentCast rent estimates. Default: false"}}, "required": ["address"]}), handle_research_property)

register_tool(Tool(name="research_property_async", description="Start an async agentic research job on a property. Returns immediately with a job_id you can poll. Use get_research_status to check progress. Good for long-running research while doing other tasks. Voice: 'Start researching 456 Oak St in the background'.", inputSchema={"type": "object", "properties": {"address": {"type": "string", "description": "Full property address to research"}, "city": {"type": "string", "description": "City name (optional)"}, "state": {"type": "string", "description": "State abbreviation (optional)"}, "zip": {"type": "string", "description": "ZIP code (optional)"}, "strategy": {"type": "string", "description": "Investment strategy: flip, rental, wholesale. Default: wholesale", "enum": ["flip", "rental", "wholesale"]}}, "required": ["address"]}), handle_research_property_async)

register_tool(Tool(name="get_research_status", description="Check the status and progress of an agentic research job. Returns progress percentage, current worker step, and completion status. Voice: 'What's the status of research job 5?'.", inputSchema={"type": "object", "properties": {"job_id": {"type": "number", "description": "The research job ID returned from research_property_async"}}, "required": ["job_id"]}), handle_get_research_status)

register_tool(Tool(name="get_research_dossier", description="Get the investment dossier for a researched property. Returns a comprehensive markdown report with property profile, comparable sales, comparable rentals, underwriting analysis, risk score, and recommendations. Voice: 'Get the research dossier for property 15'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "The agentic research property ID (from research_property or research_property_async results)"}}, "required": ["property_id"]}), handle_get_research_dossier)
