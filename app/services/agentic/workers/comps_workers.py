"""Comparable sales and rental workers with parsing/ranking helpers."""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any

from dateutil import parser as date_parser
from sqlalchemy.orm import Session

from app.models.agentic_job import AgenticJob
from app.models.agentic_property import ResearchProperty
from app.models.comp_rental import CompRental
from app.models.comp_sale import CompSale
from app.models.property import Property, PropertyStatus
from app.models.zillow_enrichment import ZillowEnrichment
from app.services.agentic.comps import (
    distance_proxy_mi,
    passes_hard_filters,
    similarity_score,
)
from app.services.agentic.pipeline import EvidenceDraft
from app.services.agentic.workers._context import ServiceContext
from app.services.agentic.workers._shared import (
    default_comp_radius_mi,
    effective_comp_score,
    source_quality_score,
)


# ---------------------------------------------------------------------------
# Worker: comps_sales
# ---------------------------------------------------------------------------


async def worker_comps_sales(
    db: Session, job: AgenticJob, context: dict[str, Any], svc: ServiceContext
) -> dict[str, Any]:
    profile = context.get("normalize_geocode", {}).get("property_profile")
    if not profile:
        return {
            "data": {"comps_sales": []},
            "unknowns": [{"field": "comps_sales", "reason": "Missing property profile from prior worker."}],
            "errors": [],
            "evidence": [],
            "web_calls": 0,
            "cost_usd": 0.0,
        }

    rp = db.query(ResearchProperty).filter(ResearchProperty.id == job.research_property_id).first()
    if rp is None:
        raise ValueError("Research property not found")

    radius = float(
        (job.assumptions or {}).get(
            "sales_radius_mi",
            default_comp_radius_mi(svc, rp.city),
        )
    )
    target_sqft = profile.get("parcel_facts", {}).get("sqft")
    target_beds = profile.get("parcel_facts", {}).get("beds")
    target_baths = profile.get("parcel_facts", {}).get("baths")

    errors: list[str] = []
    web_calls = 0

    # 1) Internal deterministic candidates (existing properties table).
    query = db.query(Property)
    if rp.state:
        query = query.filter(Property.state.ilike(rp.state))
    if rp.city:
        query = query.filter(Property.city.ilike(rp.city))

    candidates = query.limit(250).all()

    internal_selected: list[dict[str, Any]] = []
    for candidate in candidates:
        if candidate.address.strip().lower() == (rp.raw_address or "").strip().lower():
            continue

        candidate_date = (candidate.updated_at or candidate.created_at)
        candidate_sale_date = candidate_date.date() if candidate_date else None
        distance = distance_proxy_mi(
            target_zip=rp.zip_code,
            candidate_zip=candidate.zip_code,
            target_city=rp.city,
            candidate_city=candidate.city,
            target_state=rp.state,
            candidate_state=candidate.state,
        )

        if not passes_hard_filters(
            distance_mi=distance,
            radius_mi=radius,
            sale_or_list_date=candidate_sale_date,
            max_recency_months=12,
            target_sqft=target_sqft,
            candidate_sqft=candidate.square_feet,
            target_beds=target_beds,
            candidate_beds=candidate.bedrooms,
            target_baths=target_baths,
            candidate_baths=candidate.bathrooms,
        ):
            continue

        score = similarity_score(
            distance_mi=distance,
            radius_mi=radius,
            target_sqft=target_sqft,
            candidate_sqft=candidate.square_feet,
            target_beds=target_beds,
            candidate_beds=candidate.bedrooms,
            target_baths=target_baths,
            candidate_baths=candidate.bathrooms,
            sale_or_list_date=candidate_sale_date,
        )

        internal_selected.append(
            {
                "address": f"{candidate.address}, {candidate.city}, {candidate.state} {candidate.zip_code}",
                "distance_mi": distance,
                "sale_date": candidate_sale_date,
                "sale_price": candidate.price,
                "sqft": candidate.square_feet,
                "beds": candidate.bedrooms,
                "baths": candidate.bathrooms,
                "year_built": candidate.year_built,
                "similarity_score": score,
                "source_url": f"internal://properties/{candidate.id}",
                "details": {
                    "property_id": candidate.id,
                    "origin": "internal_crm",
                    "source_quality": 0.95,
                },
            }
        )

    # 2) External deterministic candidates from Exa text extraction.
    external_selected: list[dict[str, Any]] = []
    if len(internal_selected) < 8:
        external_selected, external_web_calls, external_errors = await build_external_comp_candidates(
            svc=svc,
            rp=rp,
            comp_type="sale",
            radius=radius,
            target_sqft=target_sqft,
            target_beds=target_beds,
            target_baths=target_baths,
            max_results=10,
            query_hint=f"{rp.city or ''} {rp.state or ''} {rp.zip_code or ''} recently sold homes",
        )
        web_calls += external_web_calls
        errors.extend(external_errors)

    selected = dedupe_and_rank_comps(
        svc=svc,
        comps=internal_selected + external_selected,
        top_n=8,
        date_field="sale_date",
    )

    min_sales_comps = int((job.assumptions or {}).get("min_sales_comps", 5))
    if len(selected) < min_sales_comps:
        fallback_radius = float(
            (job.assumptions or {}).get("sales_fallback_radius_mi", max(radius, 5.0))
        )
        if fallback_radius > radius:
            relaxed_external, relaxed_web_calls, relaxed_errors = await build_external_comp_candidates(
                svc=svc,
                rp=rp,
                comp_type="sale",
                radius=fallback_radius,
                target_sqft=target_sqft,
                target_beds=target_beds,
                target_baths=target_baths,
                max_results=15,
                query_hint=f"{rp.city or ''} {rp.state or ''} {rp.zip_code or ''} sold comps nearby",
            )
            web_calls += relaxed_web_calls
            errors.extend(relaxed_errors)
            selected = dedupe_and_rank_comps(
                svc=svc,
                comps=internal_selected + external_selected + relaxed_external,
                top_n=8,
                date_field="sale_date",
            )

    db.query(CompSale).filter(CompSale.job_id == job.id).delete()
    for comp in selected:
        db.add(
            CompSale(
                research_property_id=job.research_property_id,
                job_id=job.id,
                address=comp["address"],
                distance_mi=comp["distance_mi"],
                sale_date=comp["sale_date"],
                sale_price=comp["sale_price"],
                sqft=comp["sqft"],
                beds=comp["beds"],
                baths=comp["baths"],
                year_built=comp["year_built"],
                similarity_score=comp["similarity_score"],
                source_url=comp["source_url"],
                details=comp["details"],
            )
        )
    db.commit()

    evidence = [
        EvidenceDraft(
            category="comps_sales",
            claim=f"Selected sales comp: {comp['address']} with score {comp['similarity_score']:.3f}.",
            source_url=comp["source_url"],
            raw_excerpt=f"sale_price={comp.get('sale_price')}",
            confidence=max(0.5, min(0.98, float((comp.get("details") or {}).get("effective_score", comp.get("similarity_score", 0.5))))),
        )
        for comp in selected
    ]

    unknowns = []
    if not selected:
        unknowns.append(
            {
                "field": "comps_sales",
                "reason": "No sales comps matched hard filters (distance/recency/sqft/beds/baths).",
            }
        )
    elif len(selected) < min_sales_comps:
        unknowns.append(
            {
                "field": "comps_sales",
                "reason": f"Only {len(selected)} sales comps matched deterministic filters (target minimum {min_sales_comps}).",
            }
        )

    return {
        "data": {"comps_sales": selected},
        "unknowns": unknowns,
        "errors": errors,
        "evidence": evidence,
        "web_calls": web_calls,
        "cost_usd": 0.0,
    }


# ---------------------------------------------------------------------------
# Worker: comps_rentals
# ---------------------------------------------------------------------------


async def worker_comps_rentals(
    db: Session, job: AgenticJob, context: dict[str, Any], svc: ServiceContext
) -> dict[str, Any]:
    profile = context.get("normalize_geocode", {}).get("property_profile")
    if not profile:
        return {
            "data": {"comps_rentals": []},
            "unknowns": [{"field": "comps_rentals", "reason": "Missing property profile from prior worker."}],
            "errors": [],
            "evidence": [],
            "web_calls": 0,
            "cost_usd": 0.0,
        }

    rp = db.query(ResearchProperty).filter(ResearchProperty.id == job.research_property_id).first()
    if rp is None:
        raise ValueError("Research property not found")

    radius = float(
        (job.assumptions or {}).get(
            "rental_radius_mi",
            default_comp_radius_mi(svc, rp.city),
        )
    )
    target_sqft = profile.get("parcel_facts", {}).get("sqft")
    target_beds = profile.get("parcel_facts", {}).get("beds")
    target_baths = profile.get("parcel_facts", {}).get("baths")

    errors: list[str] = []
    web_calls = 0

    # 1) Internal deterministic candidates.
    query = db.query(Property)
    if rp.state:
        query = query.filter(Property.state.ilike(rp.state))
    if rp.city:
        query = query.filter(Property.city.ilike(rp.city))

    candidates = query.limit(250).all()

    internal_selected: list[dict[str, Any]] = []
    for candidate in candidates:
        if candidate.address.strip().lower() == (rp.raw_address or "").strip().lower():
            continue

        rental_signal = None

        zillow = (
            db.query(ZillowEnrichment)
            .filter(ZillowEnrichment.property_id == candidate.id)
            .first()
        )
        if zillow and zillow.rent_zestimate:
            rental_signal = zillow.rent_zestimate

        if rental_signal is None:
            continue

        candidate_date = (candidate.updated_at or candidate.created_at)
        candidate_listed_date = candidate_date.date() if candidate_date else None
        distance = distance_proxy_mi(
            target_zip=rp.zip_code,
            candidate_zip=candidate.zip_code,
            target_city=rp.city,
            candidate_city=candidate.city,
            target_state=rp.state,
            candidate_state=candidate.state,
        )

        if not passes_hard_filters(
            distance_mi=distance,
            radius_mi=radius,
            sale_or_list_date=candidate_listed_date,
            max_recency_months=12,
            target_sqft=target_sqft,
            candidate_sqft=candidate.square_feet,
            target_beds=target_beds,
            candidate_beds=candidate.bedrooms,
            target_baths=target_baths,
            candidate_baths=candidate.bathrooms,
        ):
            continue

        score = similarity_score(
            distance_mi=distance,
            radius_mi=radius,
            target_sqft=target_sqft,
            candidate_sqft=candidate.square_feet,
            target_beds=target_beds,
            candidate_beds=candidate.bedrooms,
            target_baths=target_baths,
            candidate_baths=candidate.bathrooms,
            sale_or_list_date=candidate_listed_date,
        )

        internal_selected.append(
            {
                "address": f"{candidate.address}, {candidate.city}, {candidate.state} {candidate.zip_code}",
                "distance_mi": distance,
                "rent": rental_signal,
                "date_listed": candidate_listed_date,
                "sqft": candidate.square_feet,
                "beds": candidate.bedrooms,
                "baths": candidate.bathrooms,
                "similarity_score": score,
                "source_url": f"internal://properties/{candidate.id}",
                "details": {
                    "property_id": candidate.id,
                    "origin": "internal_crm",
                    "source_quality": 0.95,
                },
            }
        )

    # 2) External deterministic candidates from Exa text extraction.
    external_selected: list[dict[str, Any]] = []
    if len(internal_selected) < 8:
        external_selected, external_web_calls, external_errors = await build_external_comp_candidates(
            svc=svc,
            rp=rp,
            comp_type="rental",
            radius=radius,
            target_sqft=target_sqft,
            target_beds=target_beds,
            target_baths=target_baths,
            max_results=10,
            query_hint=f"{rp.city or ''} {rp.state or ''} {rp.zip_code or ''} homes for rent",
        )
        web_calls += external_web_calls
        errors.extend(external_errors)

    selected = dedupe_and_rank_comps(
        svc=svc,
        comps=internal_selected + external_selected,
        top_n=8,
        date_field="date_listed",
    )

    min_rental_comps = int((job.assumptions or {}).get("min_rental_comps", 5))
    if len(selected) < min_rental_comps:
        fallback_radius = float(
            (job.assumptions or {}).get("rental_fallback_radius_mi", max(radius, 5.0))
        )
        if fallback_radius > radius:
            relaxed_external, relaxed_web_calls, relaxed_errors = await build_external_comp_candidates(
                svc=svc,
                rp=rp,
                comp_type="rental",
                radius=fallback_radius,
                target_sqft=target_sqft,
                target_beds=target_beds,
                target_baths=target_baths,
                max_results=15,
                query_hint=f"{rp.city or ''} {rp.state or ''} {rp.zip_code or ''} homes for rent nearby",
            )
            web_calls += relaxed_web_calls
            errors.extend(relaxed_errors)
            selected = dedupe_and_rank_comps(
                svc=svc,
                comps=internal_selected + external_selected + relaxed_external,
                top_n=8,
                date_field="date_listed",
            )

    db.query(CompRental).filter(CompRental.job_id == job.id).delete()
    for comp in selected:
        db.add(
            CompRental(
                research_property_id=job.research_property_id,
                job_id=job.id,
                address=comp["address"],
                distance_mi=comp["distance_mi"],
                rent=comp["rent"],
                date_listed=comp["date_listed"],
                sqft=comp["sqft"],
                beds=comp["beds"],
                baths=comp["baths"],
                similarity_score=comp["similarity_score"],
                source_url=comp["source_url"],
                details=comp["details"],
            )
        )
    db.commit()

    evidence = [
        EvidenceDraft(
            category="comps_rentals",
            claim=f"Selected rental comp: {comp['address']} with score {comp['similarity_score']:.3f}.",
            source_url=comp["source_url"],
            raw_excerpt=f"rent={comp.get('rent')}",
            confidence=max(0.5, min(0.98, float((comp.get("details") or {}).get("effective_score", comp.get("similarity_score", 0.5))))),
        )
        for comp in selected
    ]

    unknowns = []
    if not selected:
        unknowns.append(
            {
                "field": "comps_rentals",
                "reason": "No rental comps matched hard filters or had rental signal.",
            }
        )
    elif len(selected) < min_rental_comps:
        unknowns.append(
            {
                "field": "comps_rentals",
                "reason": f"Only {len(selected)} rental comps matched deterministic filters (target minimum {min_rental_comps}).",
            }
        )

    return {
        "data": {"comps_rentals": selected},
        "unknowns": unknowns,
        "errors": errors,
        "evidence": evidence,
        "web_calls": web_calls,
        "cost_usd": 0.0,
    }


# ---------------------------------------------------------------------------
# Dedupe & ranking
# ---------------------------------------------------------------------------


def dedupe_and_rank_comps(
    svc: ServiceContext,
    comps: list[dict[str, Any]],
    top_n: int,
    date_field: str,
) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for item in comps:
        key = (
            (item.get("address") or "").strip().lower(),
            (item.get("source_url") or "").strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        details = item.get("details") or {}
        details["effective_score"] = effective_comp_score(svc, item)
        item["details"] = details
        deduped.append(item)

    return sorted(
        deduped,
        key=lambda item: (
            (item.get("details") or {}).get("effective_score", item.get("similarity_score", 0.0)),
            item.get("similarity_score", 0.0),
            item.get(date_field) or date.min,
        ),
        reverse=True,
    )[:top_n]


# ---------------------------------------------------------------------------
# External comp candidate builder
# ---------------------------------------------------------------------------


async def build_external_comp_candidates(
    svc: ServiceContext,
    rp: ResearchProperty,
    comp_type: str,
    radius: float,
    target_sqft: int | None,
    target_beds: int | None,
    target_baths: float | None,
    max_results: int,
    query_hint: str,
) -> tuple[list[dict[str, Any]], int, list[str]]:
    web_calls = 0
    errors: list[str] = []

    try:
        hits = await svc.search_provider.search(
            query=query_hint,
            max_results=max_results,
            include_text=True,
        )
        web_calls += 1
    except Exception as exc:
        return [], web_calls, [f"External comp search failed: {exc}"]

    extracted: list[dict[str, Any]] = []
    for hit in hits:
        text_blob = " ".join(
            part
            for part in [
                hit.get("title") or "",
                hit.get("snippet") or "",
                hit.get("text") or "",
            ]
            if part
        )

        for row in extract_comp_entries_from_text(
            text=text_blob,
            comp_type=comp_type,
            source_url=hit.get("url") or "internal://search/no-url",
            published_date=hit.get("published_date"),
        ):
            sq = source_quality_score(svc, row.get("source_url"), category="comps")
            distance = distance_proxy_mi(
                target_zip=rp.zip_code,
                candidate_zip=row.get("zip_code"),
                target_city=rp.city,
                candidate_city=row.get("city"),
                target_state=rp.state,
                candidate_state=row.get("state"),
            )

            candidate_date = row.get("date")
            if not passes_hard_filters(
                distance_mi=distance,
                radius_mi=radius,
                sale_or_list_date=candidate_date,
                max_recency_months=12,
                target_sqft=target_sqft,
                candidate_sqft=row.get("sqft"),
                target_beds=target_beds,
                candidate_beds=row.get("beds"),
                target_baths=target_baths,
                candidate_baths=row.get("baths"),
            ):
                continue

            score = similarity_score(
                distance_mi=distance,
                radius_mi=radius,
                target_sqft=target_sqft,
                candidate_sqft=row.get("sqft"),
                target_beds=target_beds,
                candidate_beds=row.get("beds"),
                target_baths=target_baths,
                candidate_baths=row.get("baths"),
                sale_or_list_date=candidate_date,
            )

            if comp_type == "sale":
                extracted.append(
                    {
                        "address": row.get("address"),
                        "distance_mi": distance,
                        "sale_date": candidate_date,
                        "sale_price": row.get("price"),
                        "sqft": row.get("sqft"),
                        "beds": row.get("beds"),
                        "baths": row.get("baths"),
                        "year_built": None,
                        "similarity_score": score,
                        "source_url": row.get("source_url"),
                        "details": {
                            "origin": "external_exa",
                            "source_quality": sq,
                        },
                    }
                )
            else:
                extracted.append(
                    {
                        "address": row.get("address"),
                        "distance_mi": distance,
                        "rent": row.get("price"),
                        "date_listed": candidate_date,
                        "sqft": row.get("sqft"),
                        "beds": row.get("beds"),
                        "baths": row.get("baths"),
                        "similarity_score": score,
                        "source_url": row.get("source_url"),
                        "details": {
                            "origin": "external_exa",
                            "source_quality": sq,
                        },
                    }
                )

    return extracted, web_calls, errors


# ---------------------------------------------------------------------------
# Text extraction / parsing helpers (no svc needed)
# ---------------------------------------------------------------------------


def extract_comp_entries_from_text(
    text: str,
    comp_type: str,
    source_url: str,
    published_date: str | None,
) -> list[dict[str, Any]]:
    if not text:
        return []

    published = parse_date_safe(published_date)
    address_pattern = re.compile(
        r"(?P<address>\d{1,6}\s+[A-Za-z0-9 .#-]+,\s*[A-Za-z .-]+,\s*[A-Z]{2}\s*\d{5})"
    )
    matches = list(address_pattern.finditer(text))
    if not matches:
        return []

    rows: list[dict[str, Any]] = []
    for match in matches[:40]:
        address = match.group("address").strip()
        address = re.sub(r"^(?:19|20)\d{2}\s+(\d{1,6}\s+.+)$", r"\1", address)
        parsed = parse_address_components(address)
        if not parsed:
            continue

        window_after = text[match.end(): min(len(text), match.end() + 260)]
        window = text[max(0, match.start() - 120): min(len(text), match.end() + 260)]
        price = extract_price(window_after, comp_type=comp_type) or extract_price(window, comp_type=comp_type)
        beds = extract_int(window_after, r"(\d{1,2})\s*(?:bds?|beds?)") or extract_int(window, r"(\d{1,2})\s*(?:bds?|beds?)")
        baths = extract_float(window_after, r"(\d{1,2}(?:\.\d+)?)\s*(?:ba|baths?)") or extract_float(window, r"(\d{1,2}(?:\.\d+)?)\s*(?:ba|baths?)")
        sqft = extract_int(window_after, r"([0-9][0-9,]{2,})\s*(?:sq\s*ft|sqft)") or extract_int(window, r"([0-9][0-9,]{2,})\s*(?:sq\s*ft|sqft)")

        candidate_date = extract_relative_zillow_days(window_after) or extract_date_from_text(window_after) or extract_relative_zillow_days(window) or extract_date_from_text(window) or published
        if candidate_date is None:
            continue
        if price is None:
            continue

        rows.append(
            {
                "address": address,
                "city": parsed["city"],
                "state": parsed["state"],
                "zip_code": parsed["zip_code"],
                "price": price,
                "beds": beds,
                "baths": baths,
                "sqft": sqft,
                "date": candidate_date,
                "source_url": source_url,
            }
        )

    return rows


def parse_address_components(full_address: str) -> dict[str, str] | None:
    m = re.match(r"^(.+?),\s*([^,]+),\s*([A-Z]{2})\s*(\d{5})$", full_address.strip())
    if not m:
        return None
    return {
        "street": m.group(1).strip(),
        "city": m.group(2).strip(),
        "state": m.group(3).strip(),
        "zip_code": m.group(4).strip(),
    }


def extract_int(text: str, pattern: str) -> int | None:
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", ""))
    except Exception:
        return None


def extract_float(text: str, pattern: str) -> float | None:
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


def extract_price(text: str, comp_type: str) -> float | None:
    if comp_type == "rental":
        rent_match = re.search(r"\$\s*([0-9][0-9,]{2,})\s*(?:/\s*mo|/mo|per\s*month)", text, flags=re.IGNORECASE)
        if rent_match:
            return float(rent_match.group(1).replace(",", ""))

    price_values = [
        float(value.replace(",", ""))
        for value in re.findall(r"\$\s*([0-9][0-9,]{2,})", text)
    ]
    if not price_values:
        return None

    if comp_type == "rental":
        # Rental signals are typically in lower ranges.
        rental_prices = [value for value in price_values if value <= 15000]
        return rental_prices[0] if rental_prices else None

    sale_prices = [value for value in price_values if value >= 50000]
    return sale_prices[0] if sale_prices else None


def extract_relative_zillow_days(text: str) -> date | None:
    m = re.search(r"(\d{1,3})\s+days\s+on\s+zillow", text, flags=re.IGNORECASE)
    if not m:
        return None
    try:
        days = int(m.group(1))
        return date.today() - timedelta(days=days)
    except Exception:
        return None


def extract_date_from_text(text: str) -> date | None:
    m = re.search(
        r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{4})",
        text,
        flags=re.IGNORECASE,
    )
    if not m:
        return None
    return parse_date_safe(m.group(1))


def parse_date_safe(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date_parser.parse(value).date()
    except Exception:
        return None
