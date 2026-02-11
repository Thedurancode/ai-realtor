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

    text = f"AGENTIC RESEARCH COMPLETE\n\n"
    text += f"Research Property ID: {prop_id}\n"
    text += f"Job ID: {job_id}\n"
    text += f"Strategy: {payload['strategy']}\n\n"

    # Property profile
    profile = output_data.get("property_profile", {})
    if profile:
        text += f"ADDRESS: {profile.get('normalized_address', arguments['address'])}\n"
        geo = profile.get("geo", {})
        if geo.get("lat"):
            text += f"Location: {geo['lat']}, {geo['lng']}\n"
        facts = profile.get("parcel_facts", {})
        parts = []
        if facts.get("beds"):
            parts.append(f"{facts['beds']} bed")
        if facts.get("baths"):
            parts.append(f"{facts['baths']} bath")
        if facts.get("sqft"):
            parts.append(f"{facts['sqft']:,} sqft")
        if facts.get("year"):
            parts.append(f"built {facts['year']}")
        if parts:
            text += f"Details: {' / '.join(parts)}\n"
        if profile.get("owner_names"):
            text += f"Owner: {', '.join(profile['owner_names'])}\n"

    # Comparable sales
    comps_sales = output_data.get("comps_sales", [])
    if comps_sales:
        text += f"\nCOMPARABLE SALES ({len(comps_sales)} found):\n"
        for c in comps_sales[:5]:
            price = f"${c['sale_price']:,.0f}" if c.get("sale_price") else "N/A"
            text += f"  - {c.get('address', 'Unknown')}: {price}"
            if c.get("distance_mi") is not None:
                text += f" ({c['distance_mi']:.1f} mi)"
            if c.get("similarity_score"):
                text += f" [score: {c['similarity_score']:.2f}]"
            text += "\n"

    # Comparable rentals
    comps_rentals = output_data.get("comps_rentals", [])
    if comps_rentals:
        text += f"\nCOMPARABLE RENTALS ({len(comps_rentals)} found):\n"
        for c in comps_rentals[:5]:
            rent = f"${c['rent']:,.0f}/mo" if c.get("rent") else "N/A"
            text += f"  - {c.get('address', 'Unknown')}: {rent}"
            if c.get("similarity_score"):
                text += f" [score: {c['similarity_score']:.2f}]"
            text += "\n"

    # Underwriting
    uw = output_data.get("underwrite", {})
    if uw:
        text += f"\nUNDERWRITING ANALYSIS:\n"
        arv = uw.get("arv_estimate", {})
        if arv.get("base"):
            text += f"  ARV (After Repair Value): ${arv['base']:,.0f}"
            if arv.get("low") and arv.get("high"):
                text += f" (range: ${arv['low']:,.0f} - ${arv['high']:,.0f})"
            text += "\n"
        rent_est = uw.get("rent_estimate", {})
        if rent_est.get("base"):
            text += f"  Rent Estimate: ${rent_est['base']:,.0f}/mo"
            if rent_est.get("low") and rent_est.get("high"):
                text += f" (range: ${rent_est['low']:,.0f} - ${rent_est['high']:,.0f})"
            text += "\n"
        text += f"  Rehab Tier: {uw.get('rehab_tier', 'N/A')}\n"
        rehab = uw.get("rehab_estimated_range", {})
        if rehab.get("low") and rehab.get("high"):
            text += f"  Rehab Cost: ${rehab['low']:,.0f} - ${rehab['high']:,.0f}\n"
        offer = uw.get("offer_price_recommendation", {})
        if offer.get("base"):
            text += f"  RECOMMENDED OFFER: ${offer['base']:,.0f}"
            if offer.get("low") and offer.get("high"):
                text += f" (range: ${offer['low']:,.0f} - ${offer['high']:,.0f})"
            text += "\n"

    # Risk score
    risk = output_data.get("risk_score", {})
    if risk:
        text += f"\nRISK ASSESSMENT:\n"
        if risk.get("title_risk") is not None:
            text += f"  Title Risk: {risk['title_risk']:.0%}\n"
        if risk.get("data_confidence") is not None:
            text += f"  Data Confidence: {risk['data_confidence']:.0%}\n"
        flags = risk.get("compliance_flags", [])
        if flags:
            text += f"  Flags: {', '.join(flags)}\n"

    # Flood zone
    flood = output_data.get("flood_zone")
    if flood:
        text += f"\nFLOOD ZONE:\n"
        text += f"  Zone: {flood.get('flood_zone', 'Unknown')}\n"
        text += f"  Description: {flood.get('description', 'N/A')}\n"
        if flood.get("in_floodplain"):
            text += f"  WARNING: Property is in a floodplain\n"
        if flood.get("insurance_required"):
            text += f"  Flood insurance is REQUIRED\n"
        else:
            text += f"  Flood insurance: not required\n"

    # Neighborhood intelligence
    neighborhood = output_data.get("neighborhood_intel")
    if neighborhood:
        text += f"\nNEIGHBORHOOD INTELLIGENCE:\n"
        ai_summary = neighborhood.get("ai_summary")
        if ai_summary:
            text += f"  {ai_summary}\n"
        else:
            crime = neighborhood.get("crime", {})
            if crime.get("summary"):
                text += f"  Crime: {crime['summary']}\n"
            schools = neighborhood.get("schools", {})
            if schools.get("summary"):
                text += f"  Schools: {schools['summary']}\n"
            market = neighborhood.get("market_trends", {})
            if market.get("summary"):
                text += f"  Market: {market['summary']}\n"

    # Extensive research data
    extensive = output_data.get("extensive")
    if extensive:
        epa = extensive.get("epa_environmental")
        if epa and epa.get("risk_summary"):
            text += f"\nEPA ENVIRONMENTAL:\n  {epa['risk_summary']}\n"
            for cat in ["superfund_sites", "brownfields", "toxic_releases", "hazardous_waste"]:
                sites = epa.get(cat, [])
                if sites:
                    text += f"  {cat.replace('_', ' ').title()} ({len(sites)}):\n"
                    for s in sites[:3]:
                        text += f"    - {s.get('name', 'Unknown')}\n"

        wildfire = extensive.get("wildfire_hazard")
        if wildfire and wildfire.get("hazard_level"):
            text += f"\nWILDFIRE HAZARD: {wildfire['hazard_level']}\n"
            if wildfire.get("description"):
                text += f"  {wildfire['description']}\n"

        hud = extensive.get("hud_opportunity")
        if hud and any(v is not None for v in hud.values()):
            text += f"\nHUD OPPORTUNITY INDICES:\n"
            for k, v in hud.items():
                if v is not None:
                    text += f"  {k.replace('_', ' ').title()}: {v}/100\n"

        seismic = extensive.get("seismic_hazard")
        if seismic and seismic.get("seismic_risk_level"):
            text += f"\nSEISMIC: {seismic.get('description', '')}\n"
            faults = seismic.get("nearby_faults", [])
            if faults:
                text += f"  {len(faults)} fault(s) within 10 miles\n"

        wetland = extensive.get("wetlands")
        if wetland and wetland.get("wetlands_found"):
            text += f"\nWETLANDS: {len(wetland.get('wetlands', []))} wetland(s) found — development may be restricted\n"

        historic = extensive.get("historic_places")
        if historic and historic.get("nearby_places"):
            text += f"\nHISTORIC PLACES: {len(historic['nearby_places'])} within 1 mile\n"
            if historic.get("in_historic_district"):
                text += "  In historic district — renovation restrictions, 20% tax credit eligible\n"

        school = extensive.get("school_district")
        if school and school.get("school_district"):
            text += f"\nSCHOOL DISTRICT: {school['school_district']}\n"

        # RapidAPI Tier 1 data
        us_re = extensive.get("us_real_estate")
        if us_re:
            if us_re.get("noise_score") is not None:
                text += f"\nNOISE SCORE: {us_re['noise_score']}/100\n"
                cats = us_re.get("noise_categories", {})
                for k, v in cats.items():
                    if v is not None:
                        text += f"  {k}: {v}\n"
            if us_re.get("sold_homes"):
                text += f"\nRECENTLY SOLD ({len(us_re['sold_homes'])} homes):\n"
                for h in us_re["sold_homes"][:5]:
                    price = f"${h['price']:,.0f}" if isinstance(h.get("price"), (int, float)) else str(h.get("price", "?"))
                    text += f"  - {h.get('address', 'Unknown')}: {price}\n"
            if us_re.get("mortgage_rates"):
                text += f"\nMORTGAGE RATES:\n"
                for k, v in us_re["mortgage_rates"].items():
                    if k != "raw" and v is not None:
                        text += f"  {k.replace('_', ' ').title()}: {v}%\n"

        ws = extensive.get("walk_score")
        if ws and ws.get("walk_score") is not None:
            text += f"\nWALKABILITY:\n"
            text += f"  Walk: {ws['walk_score']}/100 ({ws.get('walk_description', '')})\n"
            if ws.get("transit_score") is not None:
                text += f"  Transit: {ws['transit_score']}/100 ({ws.get('transit_description', '')})\n"
            if ws.get("bike_score") is not None:
                text += f"  Bike: {ws['bike_score']}/100 ({ws.get('bike_description', '')})\n"

        redfin = extensive.get("redfin")
        if redfin and redfin.get("redfin_estimate"):
            est = redfin["redfin_estimate"]
            est_str = f"${est:,.0f}" if isinstance(est, (int, float)) else str(est)
            text += f"\nREDFIN ESTIMATE: {est_str}\n"
            if redfin.get("last_sold_price"):
                price_str = f"${redfin['last_sold_price']:,.0f}" if isinstance(redfin["last_sold_price"], (int, float)) else str(redfin["last_sold_price"])
                text += f"  Last sold: {price_str}\n"
            if redfin.get("hoa_fee"):
                text += f"  HOA: ${redfin['hoa_fee']}/mo\n"

        rc = extensive.get("rentcast")
        if rc and rc.get("rent_estimate"):
            text += f"\nRENTCAST RENT: ${rc['rent_estimate']:,.0f}/mo (range: ${rc.get('rent_range_low', '?')}-${rc.get('rent_range_high', '?')})\n"
            if rc.get("comparables"):
                text += f"  Based on {len(rc['comparables'])} rental comps\n"

    # Worker summary
    runs = output_data.get("worker_runs", [])
    if runs:
        total_time = sum(r.get("runtime_ms", 0) for r in runs)
        total_calls = sum(r.get("web_calls", 0) for r in runs)
        text += f"\nRESEARCH STATS: {len(runs)} workers, {total_time/1000:.1f}s total, {total_calls} web searches\n"

    return [TextContent(type="text", text=text)]


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

    text = f"RESEARCH JOB STARTED\n\n"
    text += f"Job ID: {result.get('job_id')}\n"
    text += f"Research Property ID: {result.get('property_id')}\n"
    text += f"Trace ID: {result.get('trace_id')}\n"
    text += f"Status: {result.get('status')}\n\n"
    text += f"The research is running in the background. Use get_research_status with job ID {result.get('job_id')} to check progress."
    return [TextContent(type="text", text=text)]


async def handle_get_research_status(arguments: dict) -> list[TextContent]:
    job_id = int(arguments["job_id"])
    response = api_get(f"/agentic/jobs/{job_id}", timeout=10)
    response.raise_for_status()
    result = response.json()

    status = result.get("status", "unknown")
    progress = result.get("progress", 0)
    step = result.get("current_step")

    text = f"RESEARCH JOB STATUS\n\n"
    text += f"Job ID: {result.get('id')}\n"
    text += f"Property ID: {result.get('property_id')}\n"
    text += f"Status: {status.upper()}\n"
    text += f"Progress: {progress}%\n"
    if step:
        text += f"Current Step: {step}\n"
    if result.get("error_message"):
        text += f"Error: {result['error_message']}\n"
    if result.get("started_at"):
        text += f"Started: {result['started_at']}\n"
    if result.get("completed_at"):
        text += f"Completed: {result['completed_at']}\n"
    if status == "completed":
        text += f"\nResearch is complete! Use get_research_dossier with property ID {result.get('property_id')} to see the full report."
    return [TextContent(type="text", text=text)]


async def handle_get_research_dossier(arguments: dict) -> list[TextContent]:
    property_id = int(arguments["property_id"])
    response = api_get(f"/agentic/properties/{property_id}/dossier", timeout=10)
    response.raise_for_status()
    result = response.json()

    text = f"INVESTMENT DOSSIER (Property {property_id}, Job {result.get('latest_job_id')})\n\n"
    text += result.get("markdown", "No dossier content available.")
    return [TextContent(type="text", text=text)]


# ── Tool Registration ──

register_tool(Tool(name="research_property", description="Run a full agentic research analysis on a property address. Finds comparable sales, comparable rentals, calculates ARV, underwriting, risk score, and generates an investment dossier. Supports strategies: flip, rental, wholesale. Set extensive=true for deep research with EPA environmental, wildfire, seismic, wetlands, historic places, HUD indices, school districts, plus Redfin estimates, Walk/Transit/Bike scores, noise scores, recently sold homes, mortgage rates, and RentCast rent estimates. Voice: 'Do extensive research on 123 Main St New York'.", inputSchema={"type": "object", "properties": {"address": {"type": "string", "description": "Full property address to research (e.g., '123 Main St, New York, NY 10001')"}, "city": {"type": "string", "description": "City name (optional if included in address)"}, "state": {"type": "string", "description": "State abbreviation (optional if included in address)"}, "zip": {"type": "string", "description": "ZIP code (optional)"}, "strategy": {"type": "string", "description": "Investment strategy: flip (buy/renovate/sell), rental (buy for income), wholesale (buy below market/assign). Default: wholesale", "enum": ["flip", "rental", "wholesale"]}, "rehab_tier": {"type": "string", "description": "Renovation scope: light ($15/sqft), medium ($35/sqft), heavy ($60/sqft). Default: medium", "enum": ["light", "medium", "heavy"]}, "extensive": {"type": "boolean", "description": "Set true for extensive/deep research: adds EPA environmental, wildfire, seismic, wetlands, historic places, HUD indices, school districts, Redfin estimates, Walk/Transit/Bike scores, noise scores, sold homes, mortgage rates, and RentCast rent estimates. Default: false"}}, "required": ["address"]}), handle_research_property)

register_tool(Tool(name="research_property_async", description="Start an async agentic research job on a property. Returns immediately with a job_id you can poll. Use get_research_status to check progress. Good for long-running research while doing other tasks. Voice: 'Start researching 456 Oak St in the background'.", inputSchema={"type": "object", "properties": {"address": {"type": "string", "description": "Full property address to research"}, "city": {"type": "string", "description": "City name (optional)"}, "state": {"type": "string", "description": "State abbreviation (optional)"}, "zip": {"type": "string", "description": "ZIP code (optional)"}, "strategy": {"type": "string", "description": "Investment strategy: flip, rental, wholesale. Default: wholesale", "enum": ["flip", "rental", "wholesale"]}}, "required": ["address"]}), handle_research_property_async)

register_tool(Tool(name="get_research_status", description="Check the status and progress of an agentic research job. Returns progress percentage, current worker step, and completion status. Voice: 'What's the status of research job 5?'.", inputSchema={"type": "object", "properties": {"job_id": {"type": "number", "description": "The research job ID returned from research_property_async"}}, "required": ["job_id"]}), handle_get_research_status)

register_tool(Tool(name="get_research_dossier", description="Get the investment dossier for a researched property. Returns a comprehensive markdown report with property profile, comparable sales, comparable rentals, underwriting analysis, risk score, and recommendations. Voice: 'Get the research dossier for property 15'.", inputSchema={"type": "object", "properties": {"property_id": {"type": "number", "description": "The agentic research property ID (from research_property or research_property_async results)"}}, "required": ["property_id"]}), handle_get_research_dossier)
