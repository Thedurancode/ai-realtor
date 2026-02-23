"""RapidAPI-powered property data workers (US Real Estate, Walk Score, Redfin, RentCast)."""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.agentic_job import AgenticJob
from app.models.agentic_property import ResearchProperty
from app.services.agentic.pipeline import EvidenceDraft
from app.services.agentic.workers._context import ServiceContext
from app.services.agentic.workers._shared import source_quality_score


async def worker_us_real_estate(
    db: Session, job: AgenticJob, context: dict[str, Any], svc: ServiceContext
) -> dict[str, Any]:
    """US Real Estate API: noise score, recently sold homes, and mortgage rates."""
    profile = context.get("normalize_geocode", {}).get("property_profile", {})
    geo = profile.get("geo", {})
    lat, lng = geo.get("lat"), geo.get("lng")
    address = profile.get("normalized_address", "")
    evidence: list[EvidenceDraft] = []
    web_calls = 0

    us_re_data: dict[str, Any] = {
        "noise_score": None,
        "noise_categories": {},
        "sold_homes": [],
        "mortgage_rates": {},
    }

    if not settings.rapidapi_key:
        return {"data": {"us_real_estate": us_re_data}, "unknowns": [{"field": "us_real_estate", "reason": "No RapidAPI key"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

    headers = {
        "x-rapidapi-key": settings.rapidapi_key,
        "x-rapidapi-host": "us-real-estate.p.rapidapi.com",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # 1) Noise score (lat/lng based)
            if lat and lng:
                try:
                    resp = await client.get(
                        "https://us-real-estate.p.rapidapi.com/location/noise-score",
                        params={"lat": str(lat), "lng": str(lng)},
                        headers=headers,
                    )
                    web_calls += 1
                    if resp.status_code == 200:
                        noise_data = resp.json()
                        data_node = noise_data.get("data", noise_data)
                        us_re_data["noise_score"] = data_node.get("noise_score") or data_node.get("score")
                        categories = data_node.get("noise_categories") or data_node.get("categories") or {}
                        if isinstance(categories, dict):
                            us_re_data["noise_categories"] = categories
                        elif isinstance(categories, list):
                            for cat in categories:
                                if isinstance(cat, dict):
                                    us_re_data["noise_categories"][cat.get("name", "unknown")] = cat.get("score")
                        if us_re_data["noise_score"] is not None:
                            evidence.append(EvidenceDraft(
                                category="noise",
                                claim=f"Noise score: {us_re_data['noise_score']}/100",
                                source_url="https://www.realtor.com/",
                                raw_excerpt=f"Noise categories: {us_re_data['noise_categories']}",
                                confidence=0.85,
                            ))
                except Exception as e:
                    logging.warning(f"US Real Estate noise score failed: {e}")

            # 2) Recently sold homes (by zip or city/state)
            zip_code = profile.get("parcel_facts", {}).get("zip") or ""
            # Try to extract zip from address
            if not zip_code and address:
                zip_match = re.search(r"\b(\d{5})\b", address)
                if zip_match:
                    zip_code = zip_match.group(1)

            if zip_code:
                try:
                    resp = await client.get(
                        "https://us-real-estate.p.rapidapi.com/sold-homes",
                        params={"postal_code": zip_code, "offset": "0", "limit": "10", "sort": "sold_date"},
                        headers=headers,
                    )
                    web_calls += 1
                    if resp.status_code == 200:
                        sold_data = resp.json()
                        results = sold_data.get("data", {}).get("results", sold_data.get("results", []))
                        if isinstance(results, list):
                            for item in results[:10]:
                                loc = item.get("location", {})
                                addr = loc.get("address", {}) if isinstance(loc, dict) else {}
                                desc = item.get("description", {})
                                sold_home = {
                                    "address": addr.get("line", item.get("address", "Unknown")),
                                    "city": addr.get("city", ""),
                                    "price": item.get("last_sold_price") or item.get("price") or desc.get("sold_price"),
                                    "date": item.get("last_sold_date") or item.get("sold_date"),
                                    "beds": desc.get("beds") or item.get("beds"),
                                    "baths": desc.get("baths") or item.get("baths"),
                                    "sqft": desc.get("sqft") or item.get("sqft"),
                                }
                                us_re_data["sold_homes"].append(sold_home)
                        if us_re_data["sold_homes"]:
                            evidence.append(EvidenceDraft(
                                category="sold_homes",
                                claim=f"{len(us_re_data['sold_homes'])} recently sold homes in ZIP {zip_code}",
                                source_url="https://www.realtor.com/",
                                raw_excerpt=f"Top sold: {us_re_data['sold_homes'][0].get('address', '')} at ${us_re_data['sold_homes'][0].get('price', '?')}",
                                confidence=0.85,
                            ))
                except Exception as e:
                    logging.warning(f"US Real Estate sold homes failed: {e}")

            # 3) Mortgage rates
            try:
                resp = await client.get(
                    "https://us-real-estate.p.rapidapi.com/finance/average-rate",
                    headers=headers,
                )
                web_calls += 1
                if resp.status_code == 200:
                    rate_data = resp.json()
                    data_node = rate_data.get("data", rate_data)
                    # Extract common rate fields
                    if isinstance(data_node, dict):
                        for key in ["thirty_year_fixed", "fifteen_year_fixed", "five_one_arm",
                                    "rate_30", "rate_15", "rate_51_arm",
                                    "30_year_fixed", "15_year_fixed"]:
                            if key in data_node:
                                us_re_data["mortgage_rates"][key] = data_node[key]
                        # Try nested rates
                        rates = data_node.get("rates") or data_node.get("mortgage_rates")
                        if isinstance(rates, (dict, list)):
                            us_re_data["mortgage_rates"]["raw"] = rates
                    if us_re_data["mortgage_rates"]:
                        evidence.append(EvidenceDraft(
                            category="finance",
                            claim="Current mortgage rates retrieved",
                            source_url="https://www.realtor.com/mortgage/rates/",
                            raw_excerpt=str(us_re_data["mortgage_rates"])[:200],
                            confidence=0.90,
                        ))
            except Exception as e:
                logging.warning(f"US Real Estate mortgage rates failed: {e}")

    except Exception as e:
        logging.warning(f"US Real Estate worker failed: {e}")
        return {"data": {"us_real_estate": us_re_data}, "unknowns": [], "errors": [str(e)], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

    return {"data": {"us_real_estate": us_re_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}


async def worker_walk_score(
    db: Session, job: AgenticJob, context: dict[str, Any], svc: ServiceContext
) -> dict[str, Any]:
    """Walk Score API: walk, transit, and bike scores."""
    profile = context.get("normalize_geocode", {}).get("property_profile", {})
    geo = profile.get("geo", {})
    lat, lng = geo.get("lat"), geo.get("lng")
    address = profile.get("normalized_address", "")
    evidence: list[EvidenceDraft] = []

    walk_data: dict[str, Any] = {
        "walk_score": None,
        "walk_description": None,
        "transit_score": None,
        "transit_description": None,
        "bike_score": None,
        "bike_description": None,
    }

    if not settings.rapidapi_key:
        return {"data": {"walk_score": walk_data}, "unknowns": [{"field": "walk_score", "reason": "No RapidAPI key"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}
    if not lat or not lng:
        return {"data": {"walk_score": walk_data}, "unknowns": [{"field": "walk_score", "reason": "No geocode"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

    headers = {
        "x-rapidapi-key": settings.rapidapi_key,
        "x-rapidapi-host": "walk-score.p.rapidapi.com",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://walk-score.p.rapidapi.com/score",
                params={
                    "lat": str(lat),
                    "lon": str(lng),
                    "address": address,
                    "transit": "1",
                    "bike": "1",
                },
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

            walk_data["walk_score"] = data.get("walkscore")
            walk_data["walk_description"] = data.get("description")

            transit = data.get("transit", {})
            if isinstance(transit, dict):
                walk_data["transit_score"] = transit.get("score")
                walk_data["transit_description"] = transit.get("description")

            bike = data.get("bike", {})
            if isinstance(bike, dict):
                walk_data["bike_score"] = bike.get("score")
                walk_data["bike_description"] = bike.get("description")

            parts = []
            if walk_data["walk_score"] is not None:
                parts.append(f"Walk: {walk_data['walk_score']}/100 ({walk_data['walk_description'] or ''})")
            if walk_data["transit_score"] is not None:
                parts.append(f"Transit: {walk_data['transit_score']}/100 ({walk_data['transit_description'] or ''})")
            if walk_data["bike_score"] is not None:
                parts.append(f"Bike: {walk_data['bike_score']}/100 ({walk_data['bike_description'] or ''})")

            if parts:
                evidence.append(EvidenceDraft(
                    category="walkability",
                    claim=f"Walkability scores — {'; '.join(parts)}",
                    source_url=data.get("ws_link", "https://www.walkscore.com/"),
                    raw_excerpt=f"Walk={walk_data['walk_score']}, Transit={walk_data['transit_score']}, Bike={walk_data['bike_score']}",
                    confidence=0.95,
                ))

    except Exception as e:
        logging.warning(f"Walk Score lookup failed: {e}")
        return {"data": {"walk_score": walk_data}, "unknowns": [], "errors": [str(e)], "evidence": evidence, "web_calls": 1, "cost_usd": 0.0}

    return {"data": {"walk_score": walk_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": 1, "cost_usd": 0.0}


async def worker_redfin(
    db: Session, job: AgenticJob, context: dict[str, Any], svc: ServiceContext
) -> dict[str, Any]:
    """Redfin API: property estimate, market data, and walk score from Redfin."""
    profile = context.get("normalize_geocode", {}).get("property_profile", {})
    address = profile.get("normalized_address", "")
    evidence: list[EvidenceDraft] = []
    web_calls = 0

    redfin_data: dict[str, Any] = {
        "redfin_estimate": None,
        "property_url": None,
        "property_type": None,
        "year_built": None,
        "lot_size": None,
        "hoa_fee": None,
        "listing_status": None,
        "last_sold_price": None,
        "last_sold_date": None,
        "walk_score": None,
        "transit_score": None,
        "bike_score": None,
    }

    if not settings.rapidapi_key:
        return {"data": {"redfin": redfin_data}, "unknowns": [{"field": "redfin", "reason": "No RapidAPI key"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}
    if not address:
        return {"data": {"redfin": redfin_data}, "unknowns": [{"field": "redfin", "reason": "No address"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

    headers = {
        "x-rapidapi-key": settings.rapidapi_key,
        "x-rapidapi-host": "redfin-com-data.p.rapidapi.com",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Step 1: Auto-complete to find property URL
            resp = await client.get(
                "https://redfin-com-data.p.rapidapi.com/auto-complete",
                params={"query": address},
                headers=headers,
            )
            web_calls += 1
            if resp.status_code != 200:
                return {"data": {"redfin": redfin_data}, "unknowns": [{"field": "redfin", "reason": f"Auto-complete returned {resp.status_code}"}], "errors": [], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

            ac_data = resp.json()
            # Find best match from auto-complete results
            property_url = None
            results = ac_data.get("data", ac_data.get("results", []))
            if isinstance(results, list):
                for item in results:
                    if isinstance(item, dict):
                        url = item.get("url") or item.get("link")
                        if url:
                            property_url = url
                            break
            elif isinstance(results, dict):
                # Sometimes nested: data.sections[].rows[]
                sections = results.get("sections", [])
                for section in sections:
                    rows = section.get("rows", [])
                    for row in rows:
                        url = row.get("url") or row.get("link")
                        if url:
                            property_url = url
                            break
                    if property_url:
                        break

            if not property_url:
                return {"data": {"redfin": redfin_data}, "unknowns": [{"field": "redfin", "reason": "No property match found"}], "errors": [], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

            redfin_data["property_url"] = property_url

            # Step 2: Get property info
            resp2 = await client.get(
                "https://redfin-com-data.p.rapidapi.com/properties/get-info",
                params={"url": property_url},
                headers=headers,
            )
            web_calls += 1
            if resp2.status_code == 200:
                info = resp2.json()
                data_node = info.get("data", info)
                if isinstance(data_node, dict):
                    # Basic info
                    basic = data_node.get("basicInfo", data_node)
                    redfin_data["redfin_estimate"] = basic.get("price") or data_node.get("predictedValue") or data_node.get("avm", {}).get("predictedValue")
                    redfin_data["property_type"] = basic.get("propertyType") or data_node.get("propertyType")
                    redfin_data["year_built"] = basic.get("yearBuilt") or data_node.get("yearBuilt")
                    redfin_data["lot_size"] = basic.get("lotSize") or data_node.get("lotSize")
                    redfin_data["listing_status"] = basic.get("listingStatus") or data_node.get("status")

                    # Financial
                    redfin_data["hoa_fee"] = data_node.get("hoaFee") or data_node.get("hoa", {}).get("fee") if isinstance(data_node.get("hoa"), dict) else None
                    redfin_data["last_sold_price"] = data_node.get("lastSoldPrice") or data_node.get("salePrice")
                    redfin_data["last_sold_date"] = data_node.get("lastSoldDate") or data_node.get("saleDate")

                    if redfin_data["redfin_estimate"]:
                        evidence.append(EvidenceDraft(
                            category="valuation",
                            claim=f"Redfin estimate: ${redfin_data['redfin_estimate']:,.0f}" if isinstance(redfin_data["redfin_estimate"], (int, float)) else f"Redfin estimate: {redfin_data['redfin_estimate']}",
                            source_url=f"https://www.redfin.com{property_url}" if property_url.startswith("/") else property_url,
                            raw_excerpt=f"Type: {redfin_data['property_type']}, Year: {redfin_data['year_built']}, Last sold: {redfin_data['last_sold_price']}",
                            confidence=0.85,
                        ))

            # Step 3: Walk score from Redfin
            try:
                resp3 = await client.get(
                    "https://redfin-com-data.p.rapidapi.com/properties/get-walk-score",
                    params={"url": property_url},
                    headers=headers,
                )
                web_calls += 1
                if resp3.status_code == 200:
                    ws_data = resp3.json()
                    data_node = ws_data.get("data", ws_data)
                    if isinstance(data_node, dict):
                        for ws_item in data_node.get("walkScoreData", data_node.get("scores", [data_node])):
                            if isinstance(ws_item, dict):
                                if ws_item.get("walkScore") is not None or ws_item.get("walk_score") is not None:
                                    redfin_data["walk_score"] = ws_item.get("walkScore") or ws_item.get("walk_score")
                                if ws_item.get("transitScore") is not None or ws_item.get("transit_score") is not None:
                                    redfin_data["transit_score"] = ws_item.get("transitScore") or ws_item.get("transit_score")
                                if ws_item.get("bikeScore") is not None or ws_item.get("bike_score") is not None:
                                    redfin_data["bike_score"] = ws_item.get("bikeScore") or ws_item.get("bike_score")
                                break
            except Exception as e:
                logging.warning(f"Redfin walk score failed: {e}")

    except Exception as e:
        logging.warning(f"Redfin worker failed: {e}")
        return {"data": {"redfin": redfin_data}, "unknowns": [], "errors": [str(e)], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

    return {"data": {"redfin": redfin_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}


async def worker_rentcast(
    db: Session, job: AgenticJob, context: dict[str, Any], svc: ServiceContext
) -> dict[str, Any]:
    """RentCast API: independent rent estimate with comparable rentals."""
    profile = context.get("normalize_geocode", {}).get("property_profile", {})
    address = profile.get("normalized_address", "")
    facts = profile.get("parcel_facts", {})
    evidence: list[EvidenceDraft] = []

    rentcast_data: dict[str, Any] = {
        "rent_estimate": None,
        "rent_range_low": None,
        "rent_range_high": None,
        "comparables": [],
    }

    if not settings.rentcast_api_key:
        return {"data": {"rentcast": rentcast_data}, "unknowns": [{"field": "rentcast", "reason": "No RentCast API key"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}
    if not address:
        return {"data": {"rentcast": rentcast_data}, "unknowns": [{"field": "rentcast", "reason": "No address"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

    headers = {"X-Api-Key": settings.rentcast_api_key}
    params: dict[str, Any] = {"address": address}
    if facts.get("beds"):
        params["bedrooms"] = facts["beds"]
    if facts.get("baths"):
        params["bathrooms"] = facts["baths"]
    if facts.get("sqft"):
        params["squareFootage"] = facts["sqft"]

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://api.rentcast.io/v1/avm/rent/long-term",
                params=params,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

            rentcast_data["rent_estimate"] = data.get("rent")
            rentcast_data["rent_range_low"] = data.get("rentRangeLow")
            rentcast_data["rent_range_high"] = data.get("rentRangeHigh")

            comps = data.get("comparables", [])
            for comp in comps[:10]:
                rentcast_data["comparables"].append({
                    "address": comp.get("formattedAddress", "Unknown"),
                    "rent": comp.get("price"),
                    "distance_mi": comp.get("distance"),
                    "correlation": comp.get("correlation"),
                    "beds": comp.get("bedrooms"),
                    "baths": comp.get("bathrooms"),
                    "sqft": comp.get("squareFootage"),
                })

            if rentcast_data["rent_estimate"]:
                evidence.append(EvidenceDraft(
                    category="rent_estimate",
                    claim=f"RentCast rent estimate: ${rentcast_data['rent_estimate']:,.0f}/mo (range: ${rentcast_data['rent_range_low'] or '?'}-${rentcast_data['rent_range_high'] or '?'})",
                    source_url="https://www.rentcast.io/",
                    raw_excerpt=f"{len(rentcast_data['comparables'])} comparable rentals used",
                    confidence=0.90,
                ))

    except Exception as e:
        logging.warning(f"RentCast lookup failed: {e}")
        return {"data": {"rentcast": rentcast_data}, "unknowns": [], "errors": [str(e)], "evidence": evidence, "web_calls": 1, "cost_usd": 0.0}

    return {"data": {"rentcast": rentcast_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": 1, "cost_usd": 0.0}
