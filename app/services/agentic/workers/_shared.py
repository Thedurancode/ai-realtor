"""Shared utility functions used by multiple workers."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.skip_trace import SkipTrace
from app.models.zillow_enrichment import ZillowEnrichment
from app.models.agentic_property import ResearchProperty
from app.services.agentic.utils import utcnow
from app.services.agentic.workers._context import ServiceContext


def source_quality_score(
    svc: ServiceContext, source_url: str | None, category: str | None = None
) -> float:
    if not source_url:
        return 0.25
    if source_url.startswith("internal://"):
        return 0.95

    parsed = urlparse(source_url)
    host = (parsed.netloc or "").lower()
    host = host[4:] if host.startswith("www.") else host
    if not host:
        return 0.25

    if host.endswith(".gov") or any(
        host.endswith(domain) for domain in svc.high_trust_domains
    ):
        return 0.95
    if any(host.endswith(domain) for domain in svc.medium_trust_domains):
        return 0.70
    if category in {"public_records", "permits", "subdivision"}:
        return 0.45
    return 0.50


def default_comp_radius_mi(svc: ServiceContext, city: str | None) -> float:
    """
    Deterministic default:
    - urban markets: 1.0mi
    - suburban/other markets: 3.0mi
    """
    normalized_city = (city or "").strip().lower()
    if normalized_city in svc.urban_radius_cities:
        return 1.0
    return 3.0


def effective_comp_score(svc: ServiceContext, comp: dict[str, Any]) -> float:
    similarity = float(comp.get("similarity_score") or 0.0)
    details = comp.get("details") or {}
    sq = details.get("source_quality")
    if sq is None:
        sq = source_quality_score(svc, comp.get("source_url"), category="comps")
        details["source_quality"] = sq
        comp["details"] = details
    return round((0.85 * similarity) + (0.15 * float(sq)), 6)


def compute_enrichment_status(
    crm_property: Property | None,
    skip_trace: SkipTrace | None,
    zillow: ZillowEnrichment | None,
    max_age_hours: int | None = None,
) -> dict[str, Any]:
    has_crm_match = crm_property is not None
    has_skip_owner = bool(skip_trace and skip_trace.owner_name)
    has_zillow = zillow is not None

    missing: list[str] = []
    if not has_crm_match:
        missing.append("crm_property_match")
    if not has_skip_owner:
        missing.append("skip_trace_owner")
    if not has_zillow:
        missing.append("zillow_enrichment")

    timestamps = []
    if skip_trace and skip_trace.created_at:
        timestamps.append(skip_trace.created_at)
    if zillow and zillow.updated_at:
        timestamps.append(zillow.updated_at)

    latest = max(timestamps) if timestamps else None
    age_hours = None
    is_fresh = None
    if max_age_hours is not None:
        if latest is None:
            is_fresh = False
        else:
            age_hours = round((utcnow() - latest).total_seconds() / 3600.0, 3)
            is_fresh = age_hours <= float(max_age_hours)

    return {
        "has_crm_property_match": has_crm_match,
        "has_skip_trace_owner": has_skip_owner,
        "has_zillow_enrichment": has_zillow,
        "is_enriched": has_crm_match and has_skip_owner and has_zillow,
        "is_fresh": is_fresh,
        "age_hours": age_hours,
        "max_age_hours": max_age_hours,
        "matched_property_id": crm_property.id if crm_property else None,
        "skip_trace_id": skip_trace.id if skip_trace else None,
        "zillow_enrichment_id": zillow.id if zillow else None,
        "missing": missing,
        "last_enriched_at": latest.isoformat() if latest else None,
    }


def resolve_enrichment_max_age_hours(
    assumptions: dict[str, Any] | None, *, strict_required: bool
) -> int | None:
    assumptions = assumptions or {}
    raw = assumptions.get("enriched_max_age_hours")
    if raw is None:
        return 168 if strict_required else None

    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "assumptions.enriched_max_age_hours must be a positive integer"
        ) from exc

    if value <= 0:
        raise ValueError(
            "assumptions.enriched_max_age_hours must be a positive integer"
        )
    return value


def find_matching_crm_property(
    db: Session, rp: ResearchProperty
) -> Property | None:
    query = db.query(Property)

    if rp.state:
        query = query.filter(Property.state.ilike(rp.state))
    if rp.city:
        query = query.filter(Property.city.ilike(rp.city))

    exact = query.filter(Property.address.ilike(rp.raw_address)).first()
    if exact:
        return exact

    return query.filter(Property.address.ilike(f"%{rp.raw_address}%")).first()
