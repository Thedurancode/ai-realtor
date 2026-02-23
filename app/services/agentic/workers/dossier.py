"""Dossier writer worker — generates the final investment memo with AI narrative."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.models.agentic_job import AgenticJob
from app.models.dossier import Dossier
from app.models.evidence_item import EvidenceItem
from app.services.agentic.pipeline import EvidenceDraft
from app.services.agentic.utils import utcnow
from app.services.agentic.workers._context import ServiceContext


# ---------------------------------------------------------------------------
# Helper: raw-data appendix (tables + evidence trail)
# ---------------------------------------------------------------------------

def build_data_appendix(
    profile: dict,
    sales: list[dict],
    rentals: list[dict],
    underwrite: dict,
    risk_score: dict,
    flood: dict,
    evidences: list[EvidenceItem],
) -> str:
    """Build a raw data appendix for the AI dossier."""
    lines: list[str] = []

    # Comps table
    if sales:
        lines.append("### Comparable Sales")
        lines.append("| Address | Price | Distance | Score |")
        lines.append("|---------|-------|----------|-------|")
        for c in sales[:8]:
            price = f"${c['sale_price']:,.0f}" if c.get("sale_price") else "N/A"
            lines.append(
                f"| {c['address']} | {price} | {c.get('distance_mi', '?')} mi | {c['similarity_score']:.2f} |"
            )
        lines.append("")

    if rentals:
        lines.append("### Comparable Rentals")
        lines.append("| Address | Rent | Score |")
        lines.append("|---------|------|-------|")
        for c in rentals[:8]:
            rent = f"${c['rent']:,.0f}/mo" if c.get("rent") else "N/A"
            lines.append(f"| {c['address']} | {rent} | {c['similarity_score']:.2f} |")
        lines.append("")

    # Evidence trail
    if evidences:
        lines.append("### Evidence Trail")
        for ev in evidences:
            lines.append(f"- [{ev.category}] {ev.claim} — {ev.source_url}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helper: structured (no-AI) fallback dossier
# ---------------------------------------------------------------------------

def build_structured_dossier(
    profile: dict,
    sales: list[dict],
    rentals: list[dict],
    underwrite: dict,
    risk_score: dict,
    flood: dict,
    neighborhood: dict,
    evidences: list[EvidenceItem],
    context: dict[str, Any] | None = None,
) -> str:
    """Fallback structured dossier when Claude is unavailable."""
    context = context or {}
    citation_refs = " ".join([f"[^e{ev.id}]" for ev in evidences[:6]])
    markdown: list[str] = []
    markdown.append(f"# Property Dossier: {profile.get('normalized_address', 'unknown')}")
    markdown.append("")

    # Property profile
    markdown.append("## Property Profile")
    markdown.append(f"- Address: {profile.get('normalized_address', 'unknown')} {citation_refs}".strip())
    markdown.append(f"- APN: {profile.get('apn') or 'unknown'}")
    geo = profile.get("geo") or {}
    markdown.append(f"- Geo: {geo.get('lat', 'unknown')}, {geo.get('lng', 'unknown')}")
    facts = profile.get("parcel_facts") or {}
    markdown.append(f"- Beds/Baths/Sqft: {facts.get('beds') or '?'} / {facts.get('baths') or '?'} / {facts.get('sqft') or '?'}")
    if profile.get("owner_names"):
        markdown.append(f"- Owner: {', '.join(profile['owner_names'])}")
    markdown.append("")

    # Flood zone
    if flood and flood.get("flood_zone"):
        markdown.append("## Flood Zone")
        markdown.append(f"- Zone: {flood['flood_zone']} — {flood.get('description', '')}")
        markdown.append(f"- In floodplain: {'Yes' if flood.get('in_floodplain') else 'No'}")
        markdown.append(f"- Insurance required: {'Yes' if flood.get('insurance_required') else 'No'}")
        markdown.append("")

    # Neighborhood
    if neighborhood:
        ai_summary = neighborhood.get("ai_summary")
        if ai_summary:
            markdown.append("## Neighborhood Analysis")
            markdown.append(ai_summary)
            markdown.append("")

    # Extensive research data
    epa = context.get("epa_environmental", {}).get("epa_environmental", {})
    if epa and epa.get("risk_summary"):
        markdown.append("## EPA Environmental")
        markdown.append(f"- {epa['risk_summary']}")
        markdown.append("")

    wildfire = context.get("wildfire_hazard", {}).get("wildfire_hazard", {})
    if wildfire and wildfire.get("hazard_level"):
        markdown.append("## Wildfire Hazard")
        markdown.append(f"- Level: {wildfire['hazard_level']}")
        if wildfire.get("description"):
            markdown.append(f"- {wildfire['description']}")
        markdown.append("")

    hud = context.get("hud_opportunity", {}).get("hud_opportunity", {})
    if hud and any(v is not None for v in hud.values()):
        markdown.append("## HUD Opportunity Indices")
        for k, v in hud.items():
            if v is not None:
                markdown.append(f"- {k.replace('_', ' ').title()}: {v}/100")
        markdown.append("")

    wetland = context.get("wetlands", {}).get("wetlands", {})
    if wetland and wetland.get("wetlands_found"):
        markdown.append("## Wetlands")
        markdown.append(f"- {len(wetland.get('wetlands', []))} wetland(s) found — development restricted")
        markdown.append("")

    historic = context.get("historic_places", {}).get("historic_places", {})
    if historic and historic.get("nearby_places"):
        markdown.append("## Historic Places")
        if historic.get("in_historic_district"):
            markdown.append("- WARNING: In historic district — renovation restrictions, 20% federal tax credit eligible")
        for p in historic["nearby_places"][:5]:
            markdown.append(f"- {p.get('name', 'Unknown')} ({p.get('type', '')})")
        markdown.append("")

    seismic = context.get("seismic_hazard", {}).get("seismic_hazard", {})
    if seismic and seismic.get("seismic_risk_level"):
        markdown.append("## Seismic Hazard")
        markdown.append(f"- {seismic.get('description', '')}")
        faults = seismic.get("nearby_faults", [])
        if faults:
            markdown.append(f"- {len(faults)} fault(s) within 10 miles")
        markdown.append("")

    school = context.get("school_district", {}).get("school_district", {})
    if school and school.get("school_district"):
        markdown.append("## School District")
        markdown.append(f"- District: {school['school_district']}")
        markdown.append("")

    # RapidAPI Tier 1 data
    us_re = context.get("us_real_estate", {}).get("us_real_estate", {})
    if us_re and us_re.get("noise_score") is not None:
        markdown.append("## Noise Score")
        markdown.append(f"- Score: {us_re['noise_score']}/100")
        cats = us_re.get("noise_categories", {})
        for k, v in cats.items():
            if v is not None:
                markdown.append(f"- {k}: {v}")
        markdown.append("")

    if us_re and us_re.get("sold_homes"):
        markdown.append(f"## Recently Sold Homes ({len(us_re['sold_homes'])} in area)")
        for h in us_re["sold_homes"][:5]:
            price = f"${h['price']:,.0f}" if isinstance(h.get("price"), (int, float)) else str(h.get("price", "?"))
            markdown.append(f"- {h.get('address', 'Unknown')}: {price} ({h.get('date', '?')})")
        markdown.append("")

    ws = context.get("walk_score", {}).get("walk_score", {})
    if ws and ws.get("walk_score") is not None:
        markdown.append("## Walkability")
        markdown.append(f"- Walk Score: {ws['walk_score']}/100 ({ws.get('walk_description', '')})")
        if ws.get("transit_score") is not None:
            markdown.append(f"- Transit Score: {ws['transit_score']}/100 ({ws.get('transit_description', '')})")
        if ws.get("bike_score") is not None:
            markdown.append(f"- Bike Score: {ws['bike_score']}/100 ({ws.get('bike_description', '')})")
        markdown.append("")

    redfin = context.get("redfin", {}).get("redfin", {})
    if redfin and redfin.get("redfin_estimate"):
        est = redfin["redfin_estimate"]
        est_str = f"${est:,.0f}" if isinstance(est, (int, float)) else str(est)
        markdown.append("## Redfin Data")
        markdown.append(f"- Redfin Estimate: {est_str}")
        if redfin.get("last_sold_price"):
            price_str = f"${redfin['last_sold_price']:,.0f}" if isinstance(redfin["last_sold_price"], (int, float)) else str(redfin["last_sold_price"])
            markdown.append(f"- Last Sold: {price_str}")
        if redfin.get("hoa_fee"):
            markdown.append(f"- HOA Fee: ${redfin['hoa_fee']}/mo")
        markdown.append("")

    rc = context.get("rentcast", {}).get("rentcast", {})
    if rc and rc.get("rent_estimate"):
        markdown.append("## RentCast Rent Estimate")
        markdown.append(f"- Rent: ${rc['rent_estimate']:,.0f}/mo")
        markdown.append(f"- Range: ${rc.get('rent_range_low', '?')}-${rc.get('rent_range_high', '?')}")
        if rc.get("comparables"):
            markdown.append(f"- Based on {len(rc['comparables'])} comparable rentals")
        markdown.append("")

    # Comps
    markdown.append("## Comparable Sales (Top 8)")
    if sales:
        for comp in sales[:8]:
            markdown.append(f"- {comp['address']} | ${comp.get('sale_price') or '?'} | score={comp['similarity_score']:.3f}")
    else:
        markdown.append("- No qualified comps found")
    markdown.append("")

    markdown.append("## Comparable Rentals (Top 8)")
    if rentals:
        for comp in rentals[:8]:
            markdown.append(f"- {comp['address']} | rent=${comp.get('rent') or '?'} | score={comp['similarity_score']:.3f}")
    else:
        markdown.append("- No qualified rental comps found")
    markdown.append("")

    # Underwriting
    markdown.append("## Underwriting")
    offer = underwrite.get("offer_price_recommendation") or {}
    markdown.append(f"- Offer (low/base/high): {offer.get('low') or '?'} / {offer.get('base') or '?'} / {offer.get('high') or '?'}")
    markdown.append(f"- Rehab tier: {underwrite.get('rehab_tier') or '?'}")
    markdown.append("")

    # Risk
    markdown.append("## Risk")
    markdown.append(f"- Title risk: {risk_score.get('title_risk', '?')}")
    markdown.append(f"- Data confidence: {risk_score.get('data_confidence', '?')}")
    markdown.append(f"- Flags: {', '.join(risk_score.get('compliance_flags', [])) or 'none'}")
    markdown.append("")

    # Evidence
    markdown.append("## Evidence")
    if evidences:
        for ev in evidences:
            markdown.append(f"[^e{ev.id}]: {ev.source_url} (captured_at={ev.captured_at.isoformat()})")
    else:
        markdown.append("- No evidence records found.")

    return "\n".join(markdown)


# ---------------------------------------------------------------------------
# Main worker entry-point
# ---------------------------------------------------------------------------

async def worker_dossier_writer(
    db: Session,
    job: AgenticJob,
    context: dict[str, Any],
    svc: ServiceContext,
) -> dict[str, Any]:
    """Generate the final investment-memo dossier for a research job.

    Attempts an AI-powered narrative via Claude; falls back to a structured
    markdown document when the LLM is unavailable.
    """
    profile = context.get("normalize_geocode", {}).get("property_profile", {})
    underwrite = context.get("underwriting", {}).get("underwrite", {})
    risk_score = context.get("underwriting", {}).get("risk_score", {})
    sales = context.get("comps_sales", {}).get("comps_sales", [])
    rentals = context.get("comps_rentals", {}).get("comps_rentals", [])
    neighborhood = context.get("neighborhood_intel", {}).get("neighborhood_intel", {})
    flood = context.get("flood_zone", {}).get("flood_zone", {})
    public_records = context.get("public_records", {}).get("public_records_hits", [])
    permits = context.get("permits_violations", {}).get("permit_violation_hits", [])

    evidences = (
        db.query(EvidenceItem)
        .filter(EvidenceItem.job_id == job.id)
        .order_by(EvidenceItem.id.asc())
        .all()
    )

    strategy = (job.assumptions or {}).get("strategy", job.strategy or "wholesale")
    cost_usd = 0.0

    # ── Build structured data summary for Claude ──────────────────────────
    data_summary: list[str] = []

    # Property profile
    facts = profile.get("parcel_facts", {})
    geo = profile.get("geo", {})
    data_summary.append(f"PROPERTY: {profile.get('normalized_address', 'unknown')}")
    parts: list[str] = []
    if facts.get("beds"):
        parts.append(f"{facts['beds']} bed")
    if facts.get("baths"):
        parts.append(f"{facts['baths']} bath")
    if facts.get("sqft"):
        parts.append(f"{facts['sqft']:,} sqft")
    if facts.get("year"):
        parts.append(f"built {facts['year']}")
    if parts:
        data_summary.append(f"Details: {' / '.join(parts)}")
    if profile.get("owner_names"):
        data_summary.append(f"Owner: {', '.join(profile['owner_names'])}")
    assessed = profile.get("assessed_values", {})
    if assessed.get("zestimate"):
        data_summary.append(f"Zestimate: ${assessed['zestimate']:,.0f}")
    if assessed.get("rent_zestimate"):
        data_summary.append(f"Rent Zestimate: ${assessed['rent_zestimate']:,.0f}/mo")

    # Comps
    if sales:
        data_summary.append(f"\nCOMPARABLE SALES ({len(sales)} found):")
        for c in sales[:8]:
            price = f"${c['sale_price']:,.0f}" if c.get("sale_price") else "N/A"
            data_summary.append(f"  - {c['address']}: {price} (score: {c['similarity_score']:.2f}, dist: {c.get('distance_mi', '?')} mi)")
    else:
        data_summary.append("\nCOMPARABLE SALES: None found")

    if rentals:
        data_summary.append(f"\nCOMPARABLE RENTALS ({len(rentals)} found):")
        for c in rentals[:8]:
            rent = f"${c['rent']:,.0f}/mo" if c.get("rent") else "N/A"
            data_summary.append(f"  - {c['address']}: {rent} (score: {c['similarity_score']:.2f})")
    else:
        data_summary.append("\nCOMPARABLE RENTALS: None found")

    # Underwriting
    if underwrite:
        data_summary.append(f"\nUNDERWRITING (strategy: {strategy}):")
        arv = underwrite.get("arv_estimate", {})
        if arv.get("base"):
            data_summary.append(f"  ARV: ${arv['base']:,.0f} (low: ${arv.get('low', 0):,.0f}, high: ${arv.get('high', 0):,.0f})")
        rent_est = underwrite.get("rent_estimate", {})
        if rent_est.get("base"):
            data_summary.append(f"  Rent estimate: ${rent_est['base']:,.0f}/mo")
        data_summary.append(f"  Rehab tier: {underwrite.get('rehab_tier', 'unknown')}")
        rehab = underwrite.get("rehab_estimated_range", {})
        if rehab.get("low"):
            data_summary.append(f"  Rehab cost: ${rehab['low']:,.0f} - ${rehab.get('high', 0):,.0f}")
        offer = underwrite.get("offer_price_recommendation", {})
        if offer.get("base"):
            data_summary.append(f"  OFFER RECOMMENDATION: ${offer['base']:,.0f} (low: ${offer.get('low', 0):,.0f}, high: ${offer.get('high', 0):,.0f})")

    # Risk
    if risk_score:
        data_summary.append("\nRISK ASSESSMENT:")
        if risk_score.get("title_risk") is not None:
            data_summary.append(f"  Title risk: {risk_score['title_risk']:.0%}")
        if risk_score.get("data_confidence") is not None:
            data_summary.append(f"  Data confidence: {risk_score['data_confidence']:.0%}")
        flags = risk_score.get("compliance_flags", [])
        if flags:
            data_summary.append(f"  Compliance flags: {', '.join(flags)}")

    # Flood zone
    if flood:
        data_summary.append("\nFLOOD ZONE:")
        data_summary.append(f"  Zone: {flood.get('flood_zone', 'unknown')}")
        data_summary.append(f"  Description: {flood.get('flood_zone_description', 'unknown')}")
        data_summary.append(f"  In floodplain: {flood.get('in_floodplain', 'unknown')}")
        data_summary.append(f"  Insurance required: {flood.get('insurance_required', 'unknown')}")

    # Neighborhood
    if neighborhood:
        ai_neighborhood = neighborhood.get("ai_summary")
        if ai_neighborhood:
            data_summary.append(f"\nNEIGHBORHOOD ANALYSIS:\n{ai_neighborhood}")
        else:
            for cat in ["crime", "schools", "market_trends"]:
                items = neighborhood.get(cat, [])
                if items:
                    data_summary.append(f"\n{cat.upper()} DATA:")
                    for item in items[:3]:
                        data_summary.append(f"  - {item.get('title', '')}: {item.get('snippet', '')[:150]}")

    # Public records & permits
    if public_records:
        data_summary.append(f"\nPUBLIC RECORDS ({len(public_records)} sources found):")
        for r in public_records[:5]:
            data_summary.append(f"  - {r.get('title', '')}: {r.get('snippet', '')[:100]}")
    if permits:
        data_summary.append(f"\nPERMITS/VIOLATIONS ({len(permits)} sources found):")
        for r in permits[:5]:
            data_summary.append(f"  - {r.get('title', '')}: {r.get('snippet', '')[:100]}")

    # Extensive research data (opt-in)
    epa = context.get("epa_environmental", {}).get("epa_environmental", {})
    if epa and epa.get("risk_summary"):
        data_summary.append("\nEPA ENVIRONMENTAL:")
        data_summary.append(f"  {epa['risk_summary']}")
        for cat in ["superfund_sites", "brownfields", "toxic_releases", "hazardous_waste"]:
            sites = epa.get(cat, [])
            if sites:
                data_summary.append(f"  {cat.replace('_', ' ').title()} ({len(sites)}):")
                for s in sites[:3]:
                    data_summary.append(f"    - {s.get('name', 'Unknown')} at {s.get('address', '')}")

    wildfire = context.get("wildfire_hazard", {}).get("wildfire_hazard", {})
    if wildfire and wildfire.get("hazard_level"):
        data_summary.append(f"\nWILDFIRE HAZARD: {wildfire['hazard_level']}")
        if wildfire.get("description"):
            data_summary.append(f"  {wildfire['description']}")

    hud = context.get("hud_opportunity", {}).get("hud_opportunity", {})
    if hud and any(v is not None for v in hud.values()):
        data_summary.append("\nHUD OPPORTUNITY INDICES (0-100 scale, higher=better):")
        for k, v in hud.items():
            if v is not None:
                data_summary.append(f"  {k.replace('_', ' ').title()}: {v}/100")

    wetland = context.get("wetlands", {}).get("wetlands", {})
    if wetland and wetland.get("wetlands_found"):
        data_summary.append(f"\nWETLANDS: {len(wetland.get('wetlands', []))} wetland(s) found — development may be restricted")
        for w in wetland.get("wetlands", [])[:3]:
            data_summary.append(f"  - {w.get('type', 'Unknown')}, {w.get('acres', '?')} acres, {w.get('system', '')}")

    historic = context.get("historic_places", {}).get("historic_places", {})
    if historic and historic.get("nearby_places"):
        data_summary.append(f"\nHISTORIC PLACES ({len(historic['nearby_places'])} within 1 mile):")
        if historic.get("in_historic_district"):
            data_summary.append("  WARNING: Property in historic district — renovation restrictions apply, 20% federal tax credit available")
        for p in historic["nearby_places"][:5]:
            data_summary.append(f"  - {p.get('name', 'Unknown')} ({p.get('type', '')})" + (" — National Historic Landmark" if p.get("is_landmark") else ""))

    seismic = context.get("seismic_hazard", {}).get("seismic_hazard", {})
    if seismic and seismic.get("peak_ground_acceleration") is not None:
        data_summary.append(f"\nSEISMIC HAZARD: {seismic.get('description', '')}")
        faults = seismic.get("nearby_faults", [])
        if faults:
            data_summary.append(f"  Nearby faults ({len(faults)}):")
            for f in faults[:3]:
                data_summary.append(f"    - {f.get('name', 'Unknown')} (age: {f.get('age', '?')})")

    school = context.get("school_district", {}).get("school_district", {})
    if school and school.get("school_district"):
        data_summary.append(f"\nSCHOOL DISTRICT: {school['school_district']}")
        if school.get("census_tract_geoid"):
            data_summary.append(f"  Census tract GEOID: {school['census_tract_geoid']}")

    # RapidAPI Tier 1 data
    us_re = context.get("us_real_estate", {}).get("us_real_estate", {})
    if us_re:
        if us_re.get("noise_score") is not None:
            data_summary.append(f"\nNOISE SCORE: {us_re['noise_score']}/100")
            cats = us_re.get("noise_categories", {})
            if cats:
                for k, v in cats.items():
                    if v is not None:
                        data_summary.append(f"  {k}: {v}")
        if us_re.get("sold_homes"):
            data_summary.append(f"\nRECENTLY SOLD HOMES ({len(us_re['sold_homes'])} in area):")
            for h in us_re["sold_homes"][:5]:
                price = f"${h['price']:,.0f}" if isinstance(h.get("price"), (int, float)) else str(h.get("price", "?"))
                data_summary.append(f"  - {h.get('address', 'Unknown')}: {price} ({h.get('date', '?')})")
        if us_re.get("mortgage_rates"):
            data_summary.append("\nCURRENT MORTGAGE RATES:")
            for k, v in us_re["mortgage_rates"].items():
                if k != "raw" and v is not None:
                    data_summary.append(f"  {k.replace('_', ' ').title()}: {v}%")

    ws = context.get("walk_score", {}).get("walk_score", {})
    if ws and ws.get("walk_score") is not None:
        data_summary.append("\nWALKABILITY:")
        data_summary.append(f"  Walk Score: {ws['walk_score']}/100 ({ws.get('walk_description', '')})")
        if ws.get("transit_score") is not None:
            data_summary.append(f"  Transit Score: {ws['transit_score']}/100 ({ws.get('transit_description', '')})")
        if ws.get("bike_score") is not None:
            data_summary.append(f"  Bike Score: {ws['bike_score']}/100 ({ws.get('bike_description', '')})")

    redfin = context.get("redfin", {}).get("redfin", {})
    if redfin and redfin.get("redfin_estimate"):
        est = redfin["redfin_estimate"]
        est_str = f"${est:,.0f}" if isinstance(est, (int, float)) else str(est)
        data_summary.append("\nREDFIN DATA:")
        data_summary.append(f"  Redfin Estimate: {est_str}")
        if redfin.get("last_sold_price"):
            data_summary.append(f"  Last sold: ${redfin['last_sold_price']:,.0f}" if isinstance(redfin["last_sold_price"], (int, float)) else f"  Last sold: {redfin['last_sold_price']}")
        if redfin.get("hoa_fee"):
            data_summary.append(f"  HOA fee: ${redfin['hoa_fee']}/mo")

    rc = context.get("rentcast", {}).get("rentcast", {})
    if rc and rc.get("rent_estimate"):
        data_summary.append("\nRENTCAST RENT ESTIMATE:")
        data_summary.append(f"  Rent: ${rc['rent_estimate']:,.0f}/mo (range: ${rc.get('rent_range_low', '?')}-${rc.get('rent_range_high', '?')})")
        if rc.get("comparables"):
            data_summary.append(f"  Based on {len(rc['comparables'])} comparable rentals")

    structured_data = "\n".join(data_summary)

    # ── Try Claude AI narrative ───────────────────────────────────────────
    ai_narrative = None
    if settings.anthropic_api_key:
        try:
            from app.services.llm_service import llm_service as _llm

            ai_narrative = await _llm.agenerate(
                f"""You are a senior real estate investment analyst writing an investment memo. Based on the data below, write a comprehensive property dossier in markdown format.

STRATEGY: {strategy}

{structured_data}

Write the dossier with these sections:
1. **Executive Summary** (2-3 sentences: is this a good deal? key numbers, go/no-go recommendation)
2. **Property Overview** (address, details, owner, condition indicators)
3. **Market Analysis** (comps analysis — are they strong? price trends, rental demand)
4. **Environmental & Natural Hazards** (flood zone, EPA sites, wildfire risk, seismic risk, wetlands — whatever data is available)
5. **Neighborhood Profile** (safety, schools, HUD opportunity indices, demographics, historic district impacts, market outlook)
6. **Financial Analysis** (ARV, rent estimate, rehab costs, offer recommendation with reasoning)
7. **Risk Factors** (title risk, data confidence, compliance flags, insurance implications, what's missing)
8. **Recommendation** (clear buy/pass/investigate-further with specific next steps)

Be specific with numbers. If data is missing, say so clearly and explain the impact. Write for an experienced investor who needs actionable intelligence, not fluff.""",
                model="claude-sonnet-4-5-20250929",
                max_tokens=1500,
            )
            cost_usd = 0.02  # Approximate Sonnet cost for 1500 tokens
        except Exception as e:
            logging.warning(f"Claude dossier generation failed: {e}")
            ai_narrative = None

    # ── Build final markdown ──────────────────────────────────────────────
    if ai_narrative:
        # AI-generated dossier with data appendix
        markdown_text = ai_narrative
        markdown_text += "\n\n---\n\n## Raw Data Appendix\n\n"
        markdown_text += build_data_appendix(profile, sales, rentals, underwrite, risk_score, flood, evidences)
    else:
        # Fallback: structured markdown (original approach, enhanced)
        markdown_text = build_structured_dossier(
            profile, sales, rentals, underwrite, risk_score, flood, neighborhood, evidences, context
        )

    # Persist
    db.query(Dossier).filter(Dossier.job_id == job.id).delete()
    new_dossier = Dossier(
        research_property_id=job.research_property_id,
        job_id=job.id,
        markdown=markdown_text,
        citations=[{"evidence_id": ev.id, "source_url": ev.source_url} for ev in evidences],
    )
    db.add(new_dossier)
    db.commit()

    # Auto-embed dossier for vector search
    try:
        from app.services.embedding_service import embedding_service
        db.refresh(new_dossier)
        embedding_service.embed_dossier(db, new_dossier.id)
    except Exception:
        pass  # best-effort, don't break pipeline

    return {
        "data": {"dossier": {"markdown": markdown_text}},
        "unknowns": [],
        "errors": [],
        "evidence": [
            EvidenceDraft(
                category="dossier",
                claim=f"Dossier generated {'with AI narrative' if ai_narrative else 'from structured data'}.",
                source_url=f"internal://agentic_jobs/{job.id}/dossier",
                raw_excerpt=None,
                confidence=1.0,
            )
        ],
        "web_calls": 0,
        "cost_usd": cost_usd,
    }
