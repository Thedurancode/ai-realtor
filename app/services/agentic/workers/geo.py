"""Geocode & normalize — enriches the research property with coordinates, CRM data, skip trace, and Zillow."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.models.agentic_job import AgenticJob
from app.models.agentic_property import ResearchProperty
from app.models.skip_trace import SkipTrace
from app.models.zillow_enrichment import ZillowEnrichment
from app.services.agentic.pipeline import EvidenceDraft
from app.services.agentic.utils import normalize_us_state_code
from app.services.agentic.workers._context import ServiceContext
from app.services.agentic.workers._shared import (
    compute_enrichment_status,
    find_matching_crm_property,
    resolve_enrichment_max_age_hours,
)
from app.services.google_places import google_places_service


async def worker_normalize_geocode(
    db: Session,
    job: AgenticJob,
    context: dict[str, Any],
    svc: ServiceContext,
) -> dict[str, Any]:
    """Geocode & normalize — enriches the research property with coordinates, CRM data, skip trace, and Zillow."""

    rp = db.query(ResearchProperty).filter(ResearchProperty.id == job.research_property_id).first()
    if rp is None:
        raise ValueError("Research property not found")

    unknowns: list[dict[str, Any]] = []
    errors: list[str] = []
    evidence: list[EvidenceDraft] = []
    web_calls = 0

    profile = {
        "normalized_address": rp.normalized_address,
        "geo": {"lat": rp.geo_lat, "lng": rp.geo_lng},
        "apn": rp.apn,
        "parcel_facts": {
            "sqft": None,
            "lot": None,
            "beds": None,
            "baths": None,
            "year": None,
        },
        "zoning": None,
        "owner_names": [],
        "mailing_address": None,
        "assessed_values": {},
        "tax_status": None,
        "transaction_history": [],
        "enrichment_status": {
            "has_crm_property_match": False,
            "has_skip_trace_owner": False,
            "has_zillow_enrichment": False,
            "is_enriched": False,
            "is_fresh": None,
            "age_hours": None,
            "max_age_hours": None,
            "matched_property_id": None,
            "skip_trace_id": None,
            "zillow_enrichment_id": None,
            "missing": ["crm_property_match", "skip_trace_owner", "zillow_enrichment"],
            "last_enriched_at": None,
        },
    }

    evidence.append(
        EvidenceDraft(
            category="input",
            claim=f"Input address normalized to '{rp.normalized_address}'.",
            source_url="internal://input",
            raw_excerpt=rp.raw_address,
            confidence=1.0,
        )
    )

    if settings.google_places_api_key:
        try:
            suggestions = await google_places_service.autocomplete(input_text=rp.raw_address, country="us")
            web_calls += 1
            if suggestions:
                details = await google_places_service.get_place_details(place_id=suggestions[0]["place_id"])
                web_calls += 1
                if details:
                    details_state = normalize_us_state_code(details.get("state"))
                    rp.city = rp.city or details.get("city")
                    rp.state = rp.state or details_state
                    rp.zip_code = rp.zip_code or details.get("zip_code")
                    rp.geo_lat = details.get("lat")
                    rp.geo_lng = details.get("lng")
                    profile["geo"] = {"lat": rp.geo_lat, "lng": rp.geo_lng}
                    evidence.append(
                        EvidenceDraft(
                            category="geocode",
                            claim="Address geocoded from Google Places details.",
                            source_url="internal://google_places/details",
                            raw_excerpt=details.get("formatted_address"),
                            confidence=0.95,
                        )
                    )
                else:
                    unknowns.append({"field": "geo", "reason": "Place details lookup returned no result."})
            else:
                unknowns.append({"field": "geo", "reason": "No geocoding candidates returned."})
        except Exception as exc:
            errors.append(f"Geocode lookup failed: {exc}")
    else:
        unknowns.append({"field": "geo", "reason": "GOOGLE_PLACES_API_KEY is not configured."})

    crm_property = find_matching_crm_property(db=db, rp=rp)
    latest_skip_trace = None
    latest_zillow = None
    if crm_property:
        profile["parcel_facts"] = {
            "sqft": crm_property.square_feet,
            "lot": crm_property.lot_size,
            "beds": crm_property.bedrooms,
            "baths": crm_property.bathrooms,
            "year": crm_property.year_built,
        }

        evidence.append(
            EvidenceDraft(
                category="property",
                claim=f"Matched CRM property record #{crm_property.id} for parcel facts.",
                source_url=f"internal://properties/{crm_property.id}",
                raw_excerpt=f"{crm_property.address}, {crm_property.city}, {crm_property.state}",
                confidence=0.85,
            )
        )

        skip_trace = (
            db.query(SkipTrace)
            .filter(SkipTrace.property_id == crm_property.id)
            .order_by(SkipTrace.created_at.desc())
            .first()
        )
        latest_skip_trace = skip_trace
        if skip_trace and skip_trace.owner_name:
            profile["owner_names"] = [skip_trace.owner_name]
            mailing_parts = [
                skip_trace.mailing_address,
                skip_trace.mailing_city,
                skip_trace.mailing_state,
                skip_trace.mailing_zip,
            ]
            profile["mailing_address"] = ", ".join([part for part in mailing_parts if part]) or None

            evidence.append(
                EvidenceDraft(
                    category="owner",
                    claim="Owner name and mailing address sourced from skip trace data.",
                    source_url=f"internal://skip_traces/property/{crm_property.id}",
                    raw_excerpt=skip_trace.owner_name,
                    confidence=0.75,
                )
            )
        else:
            unknowns.append({"field": "owner_names", "reason": "No skip trace owner data found."})

        zillow = (
            db.query(ZillowEnrichment)
            .filter(ZillowEnrichment.property_id == crm_property.id)
            .first()
        )
        latest_zillow = zillow
        if zillow:
            profile["assessed_values"] = {
                "annual_tax_amount": zillow.annual_tax_amount,
                "zestimate": zillow.zestimate,
                "rent_zestimate": zillow.rent_zestimate,
            }
            profile["tax_status"] = "unknown"

            if isinstance(zillow.price_history, list):
                for item in zillow.price_history[:8]:
                    profile["transaction_history"].append(
                        {
                            "date": item.get("date"),
                            "event": item.get("event"),
                            "amount": item.get("price"),
                            "source_url": zillow.zillow_url,
                        }
                    )

            evidence.append(
                EvidenceDraft(
                    category="tax",
                    claim="Tax and transaction history pulled from Zillow enrichment record.",
                    source_url=zillow.zillow_url or f"internal://zillow_enrichments/{zillow.id}",
                    raw_excerpt=str(zillow.annual_tax_amount),
                    confidence=0.7,
                )
            )
        else:
            unknowns.append({"field": "assessed_values", "reason": "No Zillow enrichment data found."})
    else:
        unknowns.append(
            {
                "field": "parcel_facts",
                "reason": "No matching property record in internal CRM dataset.",
            }
        )

    enrichment_max_age_hours = resolve_enrichment_max_age_hours(
        assumptions=job.assumptions or {},
        strict_required=bool((job.assumptions or {}).get("require_enriched_data")),
    )

    profile["enrichment_status"] = compute_enrichment_status(
        crm_property=crm_property,
        skip_trace=latest_skip_trace,
        zillow=latest_zillow,
        max_age_hours=enrichment_max_age_hours,
    )

    rp.latest_profile = profile
    db.commit()

    return {
        "data": {"property_profile": profile},
        "unknowns": unknowns,
        "errors": errors,
        "evidence": evidence,
        "web_calls": web_calls,
        "cost_usd": 0.0,
    }
