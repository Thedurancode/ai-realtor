"""Neighborhood intelligence worker — crime, schools, demographics, market trends."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.models.agentic_job import AgenticJob
from app.services.agentic.pipeline import EvidenceDraft
from app.services.agentic.providers import build_search_provider_from_settings
from app.services.agentic.workers._context import ServiceContext
from app.services.agentic.workers._shared import source_quality_score


async def worker_neighborhood_intel(
    db: Session,
    job: AgenticJob,
    context: dict[str, Any],
    svc: ServiceContext,
) -> dict[str, Any]:
    """Search for neighborhood data: crime, schools, demographics, walkability, trends."""
    profile = context.get("normalize_geocode", {}).get("property_profile", {})
    address = profile.get("normalized_address", "")
    geo = profile.get("geo", {})
    evidence: list[EvidenceDraft] = []
    web_calls = 0

    # Extract city/state for neighborhood queries
    parts = [p.strip() for p in address.split(",")]
    city = parts[1] if len(parts) > 1 else ""
    state = parts[2].split()[0] if len(parts) > 2 else ""
    location = f"{city}, {state}".strip(", ")

    neighborhood_data: dict[str, Any] = {
        "crime": [],
        "schools": [],
        "demographics": [],
        "market_trends": [],
        "walkability": [],
    }

    search = build_search_provider_from_settings()

    # Search 1: Crime & safety
    if location:
        crime_results = await search.search(
            query=f"{location} crime rate safety statistics neighborhood",
            max_results=5,
            include_text=True,
        )
        web_calls += 1
        for r in crime_results:
            neighborhood_data["crime"].append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("snippet", "")[:300],
            })
            evidence.append(EvidenceDraft(
                category="neighborhood",
                claim=f"Crime/safety data: {r.get('title', 'unknown')}",
                source_url=r.get("url", ""),
                raw_excerpt=r.get("snippet", "")[:300],
                confidence=source_quality_score(svc, r.get("url", "")),
            ))

    # Search 2: Schools & demographics
    if location:
        school_results = await search.search(
            query=f"{location} school ratings demographics population income median home value",
            max_results=5,
            include_text=True,
        )
        web_calls += 1
        for r in school_results:
            neighborhood_data["schools"].append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("snippet", "")[:300],
            })
            evidence.append(EvidenceDraft(
                category="neighborhood",
                claim=f"School/demographic data: {r.get('title', 'unknown')}",
                source_url=r.get("url", ""),
                raw_excerpt=r.get("snippet", "")[:300],
                confidence=source_quality_score(svc, r.get("url", "")),
            ))

    # Search 3: Market trends & gentrification
    if location:
        trend_results = await search.search(
            query=f"{location} real estate market trends 2025 2026 home prices appreciation inventory",
            max_results=5,
            include_text=True,
        )
        web_calls += 1
        for r in trend_results:
            neighborhood_data["market_trends"].append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("snippet", "")[:300],
            })
            evidence.append(EvidenceDraft(
                category="neighborhood",
                claim=f"Market trend data: {r.get('title', 'unknown')}",
                source_url=r.get("url", ""),
                raw_excerpt=r.get("snippet", "")[:300],
                confidence=source_quality_score(svc, r.get("url", "")),
            ))

    # Use Claude to synthesize if available
    ai_summary = None
    cost_usd = 0.0
    if settings.anthropic_api_key and any(
        neighborhood_data[k] for k in neighborhood_data
    ):
        try:
            from app.services.llm_service import llm_service as _llm

            snippets_text = ""
            for category, items in neighborhood_data.items():
                if items:
                    snippets_text += f"\n### {category.upper()}\n"
                    for item in items[:3]:
                        snippets_text += f"- {item['title']}: {item['snippet']}\n"

            ai_summary = await _llm.agenerate(
                f"""You are a real estate investment analyst. Based on these neighborhood data snippets for {location}, write a concise neighborhood analysis (150-250 words). Cover: safety, schools, demographics, market trends, and overall investment outlook. Be specific with any numbers or ratings found. If data is sparse, note what's missing.

{snippets_text}

Write the analysis as prose paragraphs, not bullet points. Focus on what matters for a real estate investor.""",
                model="claude-3-5-sonnet-20241022",
                max_tokens=600,
            )
            cost_usd = 0.01  # Approximate Sonnet cost
        except Exception as e:
            ai_summary = None
            logging.warning(f"Claude neighborhood synthesis failed: {e}")

    neighborhood_data["ai_summary"] = ai_summary

    return {
        "data": {"neighborhood_intel": neighborhood_data},
        "unknowns": [{"field": "neighborhood", "reason": "No location data"}] if not location else [],
        "errors": [],
        "evidence": evidence,
        "web_calls": web_calls,
        "cost_usd": cost_usd,
    }
