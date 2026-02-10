"""
=============================================================================
RESEARCH WORKER TEMPLATE
=============================================================================

Copy one of the three templates below to build a new research worker.
Each template matches a real pattern used in pipeline.py.

QUICK START:
  1. Copy the template that matches your data source
  2. Rename the method and data keys
  3. Wire it up (see REGISTRATION CHECKLIST at the bottom)
  4. Test it

=============================================================================
"""

# ── Imports you'll need (already available in pipeline.py) ─────────────────
#
# import logging
# import httpx
# from dataclasses import dataclass
# from typing import Any
# from sqlalchemy.orm import Session
#
# from app.config import settings
# from app.models.agentic_job import AgenticJob
# from app.models.agentic_property import ResearchProperty
# from app.services.agentic.providers import build_search_provider_from_settings
#
# @dataclass
# class EvidenceDraft:
#     category: str            # e.g. "flood_zone", "environmental", "walkability"
#     claim: str               # what was found (one sentence)
#     source_url: str          # provenance URL
#     raw_excerpt: str | None  # supporting raw text
#     confidence: float | None # 0.0 – 1.0 (see CONFIDENCE REFERENCE below)


# ═══════════════════════════════════════════════════════════════════════════
# TEMPLATE A: Government API Worker (free, high confidence)
# ═══════════════════════════════════════════════════════════════════════════
#
# Use this when your data comes from a public government REST API
# (ArcGIS, FEMA, EPA, USGS, HUD, Census, NPS, USFWS, etc.)
#
# Real examples in pipeline.py:
#   _worker_flood_zone     → FEMA NFHL ArcGIS
#   _worker_wetlands       → USFWS NWI ArcGIS
#   _worker_historic_places → NPS NRHP ArcGIS
#   _worker_epa_environmental → EPA EMEF ArcGIS (4 layers)
#   _worker_wildfire_hazard → USFS WHP ArcGIS
#   _worker_hud_opportunity → HUD AFFHT ArcGIS (2 layers)
#   _worker_seismic_hazard  → USGS Earthquake Hazards
#   _worker_school_district → Census TIGERweb ArcGIS
#
# ───────────────────────────────────────────────────────────────────────────

async def _worker_TEMPLATE_GOV_API(
    self, db: Session, job: AgenticJob, context: dict[str, Any]
) -> dict[str, Any]:
    """SHORT DESCRIPTION: what government data this checks."""

    # ── Step 1: Get property profile from the geocode worker ──────────
    profile = context.get("normalize_geocode", {}).get("property_profile", {})
    geo = profile.get("geo", {})
    lat, lng = geo.get("lat"), geo.get("lng")

    evidence: list[EvidenceDraft] = []
    web_calls = 0

    # Initialize your output data structure.
    # Convention: keys should be descriptive, values default to None or [].
    result_data: dict[str, Any] = {
        "finding_1": None,
        "finding_2": None,
        "items": [],
        "summary": None,
    }

    # ── Step 2: Guard clause — bail if no geocode ─────────────────────
    if not lat or not lng:
        return {
            "data": {"your_worker_name": result_data},
            "unknowns": [{"field": "your_worker_name", "reason": "No geocode available"}],
            "errors": [],
            "evidence": [],
            "web_calls": 0,
            "cost_usd": 0.0,
        }

    # ── Step 3: Call the government API ───────────────────────────────
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:

            # Most government GIS APIs use this ArcGIS REST pattern:
            resp = await client.get(
                # CHANGE THIS: your API endpoint
                "https://AGENCY.gov/arcgis/rest/services/YOUR_SERVICE/MapServer/LAYER_ID/query",
                params={
                    "geometry": f"{lng},{lat}",
                    "geometryType": "esriGeometryPoint",
                    "inSR": "4326",
                    "spatialRel": "esriSpatialRelIntersects",
                    # For proximity searches, add distance + units:
                    # "distance": "8047",              # meters (5 miles = 8047m)
                    # "units": "esriSRUnit_Meter",
                    # CHANGE THIS: fields you want back
                    "outFields": "FIELD_1,FIELD_2,FIELD_3",
                    "returnGeometry": "false",
                    "f": "json",
                },
            )
            web_calls += 1
            resp.raise_for_status()
            features = resp.json().get("features", [])

            # ── Step 4: Parse results ─────────────────────────────────
            for feat in features[:10]:  # Cap results to avoid noise
                attrs = feat.get("attributes", {})

                item = {
                    "name": attrs.get("FIELD_1", "Unknown"),
                    "value": attrs.get("FIELD_2"),
                    "detail": attrs.get("FIELD_3", ""),
                }
                result_data["items"].append(item)

                # Create evidence for each finding
                evidence.append(EvidenceDraft(
                    category="your_category",  # CHANGE THIS
                    claim=f"Found: {item['name']}",
                    source_url="https://AGENCY.gov",  # CHANGE THIS: human-readable page
                    raw_excerpt=f"FIELD_1={item['name']}, FIELD_2={item['value']}",
                    confidence=0.95,  # .gov sources = 0.95
                ))

            # ── Step 5: Build summary ─────────────────────────────────
            if result_data["items"]:
                result_data["summary"] = f"Found {len(result_data['items'])} results"
                result_data["finding_1"] = result_data["items"][0]["name"]
            else:
                result_data["summary"] = "No data found for this location"

    except Exception as e:
        logging.warning(f"Your worker failed: {e}")
        return {
            "data": {"your_worker_name": result_data},
            "unknowns": [],
            "errors": [str(e)],
            "evidence": [],
            "web_calls": web_calls,
            "cost_usd": 0.0,
        }

    # ── Step 6: Return standard shape ─────────────────────────────────
    return {
        "data": {"your_worker_name": result_data},
        "unknowns": [],
        "errors": [],
        "evidence": evidence,
        "web_calls": web_calls,
        "cost_usd": 0.0,  # Government APIs are free
    }


# ═══════════════════════════════════════════════════════════════════════════
# TEMPLATE B: Exa Web Search Worker (medium confidence)
# ═══════════════════════════════════════════════════════════════════════════
#
# Use this when there's no dedicated API and you need to search the web
# for information (articles, data portals, news, listings, etc.)
#
# Real examples in pipeline.py:
#   _worker_public_records       → "address assessor recorder parcel"
#   _worker_permits_violations   → "address permits violations open data"
#   _worker_neighborhood_intel   → 3 searches (crime, schools, trends)
#   _worker_subdivision_research → zoning/subdivision requirements
#
# ───────────────────────────────────────────────────────────────────────────

async def _worker_TEMPLATE_EXA_SEARCH(
    self, db: Session, job: AgenticJob, context: dict[str, Any]
) -> dict[str, Any]:
    """SHORT DESCRIPTION: what this searches the web for."""

    # ── Step 1: Get property context ──────────────────────────────────
    profile = context.get("normalize_geocode", {}).get("property_profile", {})
    address = profile.get("normalized_address", "")

    # Extract city/state for search queries
    parts = [p.strip() for p in address.split(",")]
    city = parts[1] if len(parts) > 1 else ""
    state = parts[2].split()[0] if len(parts) > 2 else ""
    location = f"{city}, {state}".strip(", ")

    evidence: list[EvidenceDraft] = []
    unknowns: list[dict[str, Any]] = []
    web_calls = 0

    result_data: dict[str, Any] = {
        "hits": [],
        "summary": None,
    }

    # ── Step 2: Guard clause ──────────────────────────────────────────
    if not address:
        return {
            "data": {"your_worker_name": result_data},
            "unknowns": [{"field": "your_worker_name", "reason": "No address available"}],
            "errors": [],
            "evidence": [],
            "web_calls": 0,
            "cost_usd": 0.0,
        }

    # ── Step 3: Search via Exa ────────────────────────────────────────
    #
    # Option A: Use self.search_provider (initialized in __init__)
    #   results = await self.search_provider.search(query=..., max_results=5)
    #
    # Option B: Build a fresh provider (useful if worker is standalone)
    search = build_search_provider_from_settings()

    # CHANGE THIS: craft a search query relevant to your domain
    query = f"{address} YOUR SEARCH TERMS HERE"

    results = await search.search(
        query=query,
        max_results=5,       # 5-10 is typical
        include_text=True,   # Set True if you need full page text
    )
    web_calls += 1

    # Sort by source quality (best sources first)
    results = sorted(
        results,
        key=lambda item: self._source_quality_score(
            item.get("url"), category="your_category"  # CHANGE THIS
        ),
        reverse=True,
    )

    # ── Step 4: Process results ───────────────────────────────────────
    if not results:
        unknowns.append({
            "field": "your_worker_name",
            "reason": "No results returned by search provider.",
        })
    else:
        for r in results:
            source_url = r.get("url", "internal://search/no-url")
            source_quality = self._source_quality_score(
                source_url, category="your_category"  # CHANGE THIS
            )

            result_data["hits"].append({
                "title": r.get("title", ""),
                "url": source_url,
                "snippet": r.get("snippet", "")[:300],
                "source_quality": source_quality,
            })

            evidence.append(EvidenceDraft(
                category="your_category",  # CHANGE THIS
                claim=f"Source found: {r.get('title', 'unknown')}",
                source_url=source_url,
                raw_excerpt=r.get("snippet", "")[:300],
                confidence=source_quality,  # Confidence = source quality for search
            ))

        result_data["summary"] = f"Found {len(results)} relevant sources"

    # ── Step 5: (Optional) AI synthesis with Claude ───────────────────
    #
    # If you have enough snippets, you can send them to Claude for
    # a synthesized analysis. Cost: ~$0.01 per call.
    #
    # ai_summary = None
    # cost_usd = 0.0
    # if settings.anthropic_api_key and result_data["hits"]:
    #     try:
    #         import anthropic
    #         client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    #         snippets_text = "\n".join(
    #             f"- {h['title']}: {h['snippet']}" for h in result_data["hits"][:5]
    #         )
    #         msg = client.messages.create(
    #             model="claude-sonnet-4-5-20250929",
    #             max_tokens=400,
    #             messages=[{
    #                 "role": "user",
    #                 "content": f"Based on these sources for {location}, write a "
    #                            f"concise 100-word analysis:\n\n{snippets_text}",
    #             }],
    #         )
    #         ai_summary = msg.content[0].text
    #         cost_usd = 0.01
    #     except Exception as e:
    #         logging.warning(f"Claude synthesis failed: {e}")
    # result_data["ai_summary"] = ai_summary

    # ── Step 6: Return standard shape ─────────────────────────────────
    return {
        "data": {"your_worker_name": result_data},
        "unknowns": unknowns,
        "errors": [],
        "evidence": evidence,
        "web_calls": web_calls,
        "cost_usd": 0.0,  # Or cost_usd if using Claude synthesis
    }


# ═══════════════════════════════════════════════════════════════════════════
# TEMPLATE C: RapidAPI Worker (paid, requires API key)
# ═══════════════════════════════════════════════════════════════════════════
#
# Use this when your data comes from a paid API on RapidAPI or similar.
# Always check for the API key before making calls.
#
# Real examples in pipeline.py:
#   _worker_us_real_estate → RapidAPI US Real Estate (noise, sold homes, rates)
#   _worker_walk_score     → RapidAPI Walk Score (walk/transit/bike)
#   _worker_redfin         → RapidAPI Redfin (estimate, last sold, HOA)
#   _worker_rentcast       → RentCast API (rent estimate + comps)
#
# ───────────────────────────────────────────────────────────────────────────

async def _worker_TEMPLATE_RAPIDAPI(
    self, db: Session, job: AgenticJob, context: dict[str, Any]
) -> dict[str, Any]:
    """SHORT DESCRIPTION: what paid API data this fetches."""

    # ── Step 1: Get property context ──────────────────────────────────
    profile = context.get("normalize_geocode", {}).get("property_profile", {})
    geo = profile.get("geo", {})
    lat, lng = geo.get("lat"), geo.get("lng")
    address = profile.get("normalized_address", "")
    facts = profile.get("parcel_facts", {})

    evidence: list[EvidenceDraft] = []

    result_data: dict[str, Any] = {
        "score": None,
        "details": {},
        "items": [],
    }

    # ── Step 2: Guard clauses (key + geocode) ─────────────────────────
    #
    # CHANGE THIS: use your API key from settings or env.
    #   Option A: settings.rapidapi_key     (shared RapidAPI key)
    #   Option B: settings.your_api_key     (dedicated key — add to app/config.py)
    #   Option C: os.getenv("YOUR_API_KEY") (env var directly)
    #
    if not settings.rapidapi_key:
        return {
            "data": {"your_worker_name": result_data},
            "unknowns": [{"field": "your_worker_name", "reason": "No API key configured"}],
            "errors": [],
            "evidence": [],
            "web_calls": 0,
            "cost_usd": 0.0,
        }

    if not lat or not lng:
        return {
            "data": {"your_worker_name": result_data},
            "unknowns": [{"field": "your_worker_name", "reason": "No geocode available"}],
            "errors": [],
            "evidence": [],
            "web_calls": 0,
            "cost_usd": 0.0,
        }

    # ── Step 3: Call the API ──────────────────────────────────────────
    #
    # CHANGE THIS: RapidAPI headers use x-rapidapi-key + x-rapidapi-host.
    # Non-RapidAPI services use their own auth headers.
    #
    headers = {
        "x-rapidapi-key": settings.rapidapi_key,
        "x-rapidapi-host": "your-api.p.rapidapi.com",  # CHANGE THIS
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                # CHANGE THIS: your API endpoint
                "https://your-api.p.rapidapi.com/endpoint",
                params={
                    "lat": str(lat),
                    "lon": str(lng),
                    "address": address,
                    # Add any optional params from property facts:
                    # "bedrooms": facts.get("beds"),
                    # "bathrooms": facts.get("baths"),
                    # "sqft": facts.get("sqft"),
                },
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

            # ── Step 4: Parse response ────────────────────────────────
            #
            # CHANGE THIS: extract the fields you need from the response.
            #
            result_data["score"] = data.get("score")
            result_data["details"] = {
                "field_a": data.get("fieldA"),
                "field_b": data.get("fieldB"),
            }

            # Build a human-readable summary for evidence
            parts = []
            if result_data["score"] is not None:
                parts.append(f"Score: {result_data['score']}/100")
            if result_data["details"].get("field_a"):
                parts.append(f"Field A: {result_data['details']['field_a']}")

            if parts:
                evidence.append(EvidenceDraft(
                    category="your_category",  # CHANGE THIS
                    claim=f"API results — {'; '.join(parts)}",
                    source_url="https://provider-website.com/",  # CHANGE THIS
                    raw_excerpt=str(result_data["details"]),
                    confidence=0.85,  # Paid APIs: 0.70–0.90 depending on provider
                ))

    except Exception as e:
        logging.warning(f"Your API lookup failed: {e}")
        return {
            "data": {"your_worker_name": result_data},
            "unknowns": [],
            "errors": [str(e)],
            "evidence": evidence,
            "web_calls": 1,
            "cost_usd": 0.0,
        }

    # ── Step 5: Return standard shape ─────────────────────────────────
    return {
        "data": {"your_worker_name": result_data},
        "unknowns": [],
        "errors": [],
        "evidence": evidence,
        "web_calls": 1,
        "cost_usd": 0.0,  # Track if your API charges per call
    }


# ═══════════════════════════════════════════════════════════════════════════
#
#  REGISTRATION CHECKLIST
#
#  After writing your worker method, wire it up in 3 places in pipeline.py:
#
# ═══════════════════════════════════════════════════════════════════════════
#
#
# STEP 1 — Add the method to the AgenticResearchService class
# ─────────────────────────────────────────────────────────────
#
#   Paste your worker method into the class body in pipeline.py.
#   Location: after the last _worker_* method (before helper methods).
#
#
# STEP 2 — Register in worker_fns dict (~line 474)
# ─────────────────────────────────────────────────
#
#   Find this dict in the `orchestrated()` method and add your entry:
#
#   worker_fns: dict[str, Callable[[], Awaitable[dict[str, Any]]]] = {
#       # ... existing workers ...
#       "your_worker_name": lambda: self._worker_your_worker_name(db, job, context),
#   }
#
#   Also add to the sequential `workers` list (~line 426) if you want it
#   to run in sequential mode too.
#
#
# STEP 3 — Add AgentSpec to _build_agent_specs() (~line 547)
# ──────────────────────────────────────────────────────────
#
#   Pick ONE of these options:
#
#   # A) Always run (add to core_specs list, before dossier_writer):
#   AgentSpec(name="your_worker_name", dependencies={"normalize_geocode"}),
#
#   # B) Add to the "extensive" opt-in group (inside the existing block):
#   if isinstance(extra_agents, list) and "extensive" in extra_agents:
#       extensive_specs = [
#           # ... existing extensive workers ...
#           AgentSpec(name="your_worker_name", dependencies={"normalize_geocode"}),
#       ]
#
#   # C) Create a NEW opt-in group (add after the extensive block):
#   if isinstance(extra_agents, list) and "your_group" in extra_agents:
#       specs.insert(-1, AgentSpec(
#           name="your_worker_name",
#           dependencies={"normalize_geocode"},
#       ))
#       specs[-1].dependencies.add("your_worker_name")  # dossier depends on it
#
#   # D) Depends on other workers (e.g. needs comps data):
#   AgentSpec(
#       name="your_worker_name",
#       dependencies={"normalize_geocode", "comps_sales", "comps_rentals"},
#   ),
#
#   IMPORTANT: If you add to extensive or a new group, also add this line
#   so dossier_writer waits for your worker:
#       specs[-1].dependencies.add("your_worker_name")
#
#
# STEP 4 (Optional) — Show data in the dossier
# ─────────────────────────────────────────────
#
#   In _worker_dossier_writer() (~line 3293), add a section so the AI
#   narrative includes your data:
#
#   your_data = context.get("your_worker_name", {}).get("your_worker_name", {})
#   if your_data and your_data.get("score") is not None:
#       data_summary.append(f"\nYOUR SECTION TITLE:")
#       data_summary.append(f"  Score: {your_data['score']}/100")
#       for item in your_data.get("items", [])[:5]:
#           data_summary.append(f"  - {item.get('name', 'Unknown')}")
#
#
# ═══════════════════════════════════════════════════════════════════════════
#
#  RETURN SHAPE CONTRACT
#
#  Every worker MUST return a dict with exactly these 6 keys:
#
# ═══════════════════════════════════════════════════════════════════════════
#
#   {
#       "data": {                              # Your results
#           "your_worker_name": {              #   Nested under worker name
#               "field_1": value,              #   Your data fields
#               "field_2": value,
#           }
#       },
#       "unknowns": [                          # What couldn't be determined
#           {"field": "name", "reason": "why"}
#       ],
#       "errors": ["error message"],           # Errors encountered (strings)
#       "evidence": [EvidenceDraft(...)],       # Evidence items collected
#       "web_calls": 1,                        # Number of HTTP requests made
#       "cost_usd": 0.0,                       # API cost (0.0 for free APIs)
#   }
#
#   KEY RULE: Nest your data under data["your_worker_name"]. Downstream
#   workers access it as: context.get("your_worker_name", {}).get("your_worker_name", {})
#
#
# ═══════════════════════════════════════════════════════════════════════════
#
#  CONFIDENCE SCORE REFERENCE
#
# ═══════════════════════════════════════════════════════════════════════════
#
#   Source Type                          Score
#   ────────────────────────────────     ─────
#   Internal CRM (internal:// URL)      0.95
#   .gov / .mil direct API              0.95
#   Government GIS (ArcGIS hosted)      0.90 – 0.95
#   Paid API (Walk Score, RentCast)     0.85 – 0.90
#   Zillow / Realtor.com / Redfin       0.70
#   Exa search (use _source_quality_score())  varies
#   Public records / permits portals    0.45
#   Unknown domain                      0.50
#   No source URL                       0.25
#
#   Use self._source_quality_score(url, category="your_category") for
#   automatic scoring based on domain trust tiers.
#
#
# ═══════════════════════════════════════════════════════════════════════════
#
#  WORKER IDEAS — READY TO BUILD
#
# ═══════════════════════════════════════════════════════════════════════════
#
#   Worker Name              Template   API / Source                        Free?
#   ────────────────────     ────────   ────────────────────────────────   ─────
#   census_demographics      A (Gov)    Census ACS API                     Yes
#   air_quality              A (Gov)    EPA AirNow API                     Yes
#   internet_speed           A (Gov)    FCC Broadband Map API              Yes
#   solar_potential          C (Paid)   Google Solar API                   Paid
#   crime_stats              B (Exa)    FBI UCR / local PD open data      Yes
#   zoning_lookup            B (Exa)    Municipal open data portals        Yes
#   property_tax_trends      A (Gov)    County assessor GIS               Yes
#   noise_level              C (Paid)   HowLoud API (RapidAPI)            Paid
#   utility_costs            B (Exa)    EIA + local utility data          Yes
#   building_permits_detail  A (Gov)    Local open data (Socrata/CKAN)    Yes
#   climate_risk             A (Gov)    NOAA Climate API                   Yes
#   broadband_availability   A (Gov)    FCC BDC API                        Yes
#   transportation           A (Gov)    DOT National Transit Database     Yes
#   market_rent_trends       C (Paid)   Zillow ZORI API                   Paid
#   insurance_estimate       C (Paid)   Various insurance APIs             Paid
#
#
# ═══════════════════════════════════════════════════════════════════════════
#
#  RULES
#
# ═══════════════════════════════════════════════════════════════════════════
#
#   1. Always return ALL 6 keys (data, unknowns, errors, evidence,
#      web_calls, cost_usd) — even if empty.
#
#   2. Nest data under data["your_worker_name"] — the dossier writer
#      and other workers read it via context.get("worker_name", {}).
#
#   3. Guard against missing geocode — check lat/lng before API calls.
#      Guard against missing API keys — check before paid API calls.
#
#   4. Use httpx.AsyncClient with timeout=15.0 — all workers are async.
#
#   5. Log warnings, don't crash — wrap API calls in try/except, append
#      errors to the errors list, return partial results.
#
#   6. Set confidence honestly — .gov = 0.95, paid API = 0.85,
#      web search = use _source_quality_score().
#
#   7. Track web_calls — increment for every HTTP request made.
#
#   8. Cap results — use [:10] or [:5] when iterating API features
#      to avoid noise and keep dossier readable.
#
#   9. Evidence claims should be one sentence, human-readable, and
#      include the key data point found.
#
#  10. Method name must be _worker_{name} and the name must match
#      the key used in worker_fns and AgentSpec.
#
