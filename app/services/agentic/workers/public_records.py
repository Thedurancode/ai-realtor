"""Exa-based search workers for public records, permits, and subdivision research."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.agentic_job import AgenticJob
from app.models.agentic_property import ResearchProperty
from app.services.agentic.pipeline import EvidenceDraft
from app.services.agentic.workers._context import ServiceContext
from app.services.agentic.workers._shared import source_quality_score


async def worker_public_records(
    db: Session, job: AgenticJob, context: dict[str, Any], svc: ServiceContext
) -> dict[str, Any]:
    """Search for public assessor / recorder / parcel records."""

    rp = db.query(ResearchProperty).filter(ResearchProperty.id == job.research_property_id).first()
    if rp is None:
        raise ValueError("Research property not found")

    query = f"{rp.normalized_address} assessor recorder parcel"
    results = await svc.search_provider.search(query=query, max_results=5)
    results = sorted(
        results,
        key=lambda item: source_quality_score(svc, item.get("url"), category="public_records"),
        reverse=True,
    )

    evidence: list[EvidenceDraft] = []
    unknowns: list[dict[str, Any]] = []

    if not results:
        unknowns.append(
            {
                "field": "public_records",
                "reason": "No public records hits returned by configured search provider.",
            }
        )

    for result in results:
        source_url = result.get("url", "internal://search/no-url")
        sq = source_quality_score(svc, source_url, category="public_records")
        evidence.append(
            EvidenceDraft(
                category="public_records",
                claim=f"Public records candidate found: {result.get('title', 'unknown')}.",
                source_url=source_url,
                raw_excerpt=result.get("snippet"),
                confidence=sq,
            )
        )
        result["source_quality"] = sq

    return {
        "data": {"public_records_hits": results},
        "unknowns": unknowns,
        "errors": [],
        "evidence": evidence,
        "web_calls": 1,
        "cost_usd": 0.0,
    }


async def worker_permits_violations(
    db: Session, job: AgenticJob, context: dict[str, Any], svc: ServiceContext
) -> dict[str, Any]:
    """Search for building permits and code violations via open-data portals."""

    rp = db.query(ResearchProperty).filter(ResearchProperty.id == job.research_property_id).first()
    if rp is None:
        raise ValueError("Research property not found")

    query = f"{rp.normalized_address} permits violations open data"
    results = await svc.search_provider.search(query=query, max_results=5)
    results = sorted(
        results,
        key=lambda item: source_quality_score(svc, item.get("url"), category="permits"),
        reverse=True,
    )

    evidence: list[EvidenceDraft] = []
    unknowns: list[dict[str, Any]] = []

    if not results:
        unknowns.append(
            {
                "field": "permits_violations",
                "reason": "No permit or violation records returned by configured search provider.",
            }
        )

    for result in results:
        source_url = result.get("url", "internal://search/no-url")
        sq = source_quality_score(svc, source_url, category="permits")
        evidence.append(
            EvidenceDraft(
                category="permits",
                claim=f"Permit/violation source candidate found: {result.get('title', 'unknown')}.",
                source_url=source_url,
                raw_excerpt=result.get("snippet"),
                confidence=sq,
            )
        )
        result["source_quality"] = sq

    return {
        "data": {"permit_violation_hits": results},
        "unknowns": unknowns,
        "errors": [],
        "evidence": evidence,
        "web_calls": 1,
        "cost_usd": 0.0,
    }


async def worker_subdivision_research(
    db: Session, job: AgenticJob, context: dict[str, Any], svc: ServiceContext
) -> dict[str, Any]:
    """Search for zoning, lot-size, frontage, and subdivision requirements."""

    rp = db.query(ResearchProperty).filter(ResearchProperty.id == job.research_property_id).first()
    if rp is None:
        raise ValueError("Research property not found")

    subdivision_goal = (job.assumptions or {}).get("subdivision_goal", "subdivide and build")
    query = (
        f"{rp.raw_address}, {rp.city or ''} {rp.state or ''} {rp.zip_code or ''} "
        f"zoning minimum lot size frontage subdivision requirements {subdivision_goal}"
    ).strip()

    results = await svc.search_provider.search(query=query, max_results=8, include_text=True)
    results = sorted(
        results,
        key=lambda item: source_quality_score(svc, item.get("url"), category="subdivision"),
        reverse=True,
    )
    evidence: list[EvidenceDraft] = []
    unknowns: list[dict[str, Any]] = []

    if not results:
        unknowns.append(
            {
                "field": "subdivision_research",
                "reason": "No subdivision sources returned by configured search provider.",
            }
        )

    for result in results[:8]:
        source_url = result.get("url", "internal://search/no-url")
        sq = source_quality_score(svc, source_url, category="subdivision")
        evidence.append(
            EvidenceDraft(
                category="subdivision",
                claim=f"Subdivision source candidate found: {result.get('title', 'unknown')}.",
                source_url=source_url,
                raw_excerpt=(result.get("snippet") or "")[:500],
                confidence=sq,
            )
        )

    summary_hits = [
        {
            "title": result.get("title"),
            "url": result.get("url"),
            "snippet": (result.get("snippet") or "")[:500],
            "source_quality": source_quality_score(svc, result.get("url"), category="subdivision"),
        }
        for result in results[:8]
    ]

    return {
        "data": {
            "subdivision_research": {
                "goal": subdivision_goal,
                "query": query,
                "hits": summary_hits,
            }
        },
        "unknowns": unknowns,
        "errors": [],
        "evidence": evidence,
        "web_calls": 1,
        "cost_usd": 0.0,
    }
