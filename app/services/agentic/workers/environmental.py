"""Environmental, hazard, and government data workers (FEMA, EPA, ArcGIS, NPS, USGS)."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.models.agentic_job import AgenticJob
from app.services.agentic.pipeline import EvidenceDraft
from app.services.agentic.workers._context import ServiceContext


async def worker_flood_zone(
    db: Session, job: AgenticJob, context: dict[str, Any], svc: ServiceContext
) -> dict[str, Any]:
    """Check FEMA flood zone data using free FEMA API."""
    profile = context.get("normalize_geocode", {}).get("property_profile", {})
    geo = profile.get("geo", {})
    lat = geo.get("lat")
    lng = geo.get("lng")
    evidence: list[EvidenceDraft] = []

    flood_data: dict[str, Any] = {
        "flood_zone": None,
        "description": None,
        "panel_number": None,
        "in_floodplain": None,
        "insurance_required": None,
        "source": "FEMA National Flood Hazard Layer",
    }

    if not lat or not lng:
        return {
            "data": {"flood_zone": flood_data},
            "unknowns": [{"field": "flood_zone", "reason": "No geocode available for FEMA lookup"}],
            "errors": [],
            "evidence": [],
            "web_calls": 0,
            "cost_usd": 0.0,
        }

    web_calls = 0
    try:
        # FEMA National Flood Hazard Layer (NFHL) ArcGIS REST API
        # This is the official free FEMA endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query",
                params={
                    "geometry": f"{lng},{lat}",
                    "geometryType": "esriGeometryPoint",
                    "inSR": "4326",
                    "spatialRel": "esriSpatialRelIntersects",
                    "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF,STATIC_BFE,DFIRM_ID",
                    "returnGeometry": "false",
                    "f": "json",
                },
                timeout=15.0,
            )
            web_calls += 1
            response.raise_for_status()
            data = response.json()

            features = data.get("features", [])
            if features:
                attrs = features[0].get("attributes", {})
                zone = attrs.get("FLD_ZONE", "")
                zone_subtype = attrs.get("ZONE_SUBTY", "")
                sfha = attrs.get("SFHA_TF", "")

                # Decode flood zone
                zone_descriptions = {
                    "A": "High risk - 1% annual chance flood (100-year floodplain)",
                    "AE": "High risk - 1% annual chance flood with base flood elevations",
                    "AH": "High risk - 1% annual chance of shallow flooding (1-3 ft)",
                    "AO": "High risk - 1% annual chance of sheet flow flooding",
                    "V": "High risk - coastal flood with wave action",
                    "VE": "High risk - coastal flood with base flood elevations",
                    "X": "Moderate to low risk - 0.2% annual chance flood (500-year) or minimal",
                    "B": "Moderate risk - between 100-year and 500-year floodplain",
                    "C": "Minimal risk - outside 500-year floodplain",
                    "D": "Undetermined risk - possible but not analyzed",
                }

                is_high_risk = zone in ("A", "AE", "AH", "AO", "AR", "V", "VE")
                description = zone_descriptions.get(zone, f"Zone {zone}")
                if zone_subtype:
                    description += f" ({zone_subtype})"

                flood_data["flood_zone"] = zone
                flood_data["description"] = description
                flood_data["panel_number"] = attrs.get("DFIRM_ID")
                flood_data["in_floodplain"] = is_high_risk
                flood_data["insurance_required"] = is_high_risk

                evidence.append(EvidenceDraft(
                    category="flood_zone",
                    claim=f"FEMA flood zone: {zone} - {description}. Insurance {'required' if is_high_risk else 'not required'}.",
                    source_url=f"https://msc.fema.gov/portal/search?AddressQuery={lat},{lng}",
                    raw_excerpt=f"FLD_ZONE={zone}, SFHA_TF={sfha}, ZONE_SUBTY={zone_subtype}",
                    confidence=0.95,
                ))
            else:
                flood_data["flood_zone"] = "X"
                flood_data["description"] = "No FEMA data — likely minimal flood risk"
                flood_data["in_floodplain"] = False
                flood_data["insurance_required"] = False

                evidence.append(EvidenceDraft(
                    category="flood_zone",
                    claim="No FEMA flood zone data found for this location — likely minimal risk.",
                    source_url=f"https://msc.fema.gov/portal/search?AddressQuery={lat},{lng}",
                    raw_excerpt="No features returned from NFHL query",
                    confidence=0.80,
                ))

    except Exception as e:
        logging.warning(f"FEMA flood zone lookup failed: {e}")
        return {
            "data": {"flood_zone": flood_data},
            "unknowns": [{"field": "flood_zone", "reason": f"FEMA API error: {str(e)[:100]}"}],
            "errors": [str(e)],
            "evidence": [],
            "web_calls": web_calls,
            "cost_usd": 0.0,
        }

    return {
        "data": {"flood_zone": flood_data},
        "unknowns": [],
        "errors": [],
        "evidence": evidence,
        "web_calls": web_calls,
        "cost_usd": 0.0,
    }


async def worker_epa_environmental(
    db: Session, job: AgenticJob, context: dict[str, Any], svc: ServiceContext
) -> dict[str, Any]:
    """Check EPA environmental hazards: Superfund, brownfields, toxic releases, hazardous waste within 5 miles (8047m)."""
    profile = context.get("normalize_geocode", {}).get("property_profile", {})
    geo = profile.get("geo", {})
    lat, lng = geo.get("lat"), geo.get("lng")
    evidence: list[EvidenceDraft] = []
    web_calls = 0

    epa_data: dict[str, Any] = {
        "superfund_sites": [],
        "brownfields": [],
        "toxic_releases": [],
        "hazardous_waste": [],
        "nearest_hazard_miles": None,
        "risk_summary": None,
    }

    if not lat or not lng:
        return {"data": {"epa_environmental": epa_data}, "unknowns": [{"field": "epa", "reason": "No geocode"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

    base_url = "https://geopub.epa.gov/arcgis/rest/services/EMEF/efpoints/MapServer"
    base_params = {
        "geometry": f"{lng},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "distance": "8047",
        "units": "esriSRUnit_Meter",
        "outFields": "primary_name,location_address,city_name,state_code,registry_id",
        "returnGeometry": "false",
        "f": "json",
    }

    layers = [
        (0, "superfund_sites", "Superfund (NPL) site"),
        (5, "brownfields", "Brownfield site"),
        (1, "toxic_releases", "Toxic Release Inventory facility"),
        (4, "hazardous_waste", "Hazardous waste handler"),
    ]

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            for layer_id, key, label in layers:
                resp = await client.get(f"{base_url}/{layer_id}/query", params=base_params)
                web_calls += 1
                resp.raise_for_status()
                features = resp.json().get("features", [])
                for feat in features[:10]:
                    attrs = feat.get("attributes", {})
                    site = {
                        "name": attrs.get("primary_name", "Unknown"),
                        "address": attrs.get("location_address", ""),
                        "city": attrs.get("city_name", ""),
                        "state": attrs.get("state_code", ""),
                    }
                    epa_data[key].append(site)
                    evidence.append(EvidenceDraft(
                        category="environmental",
                        claim=f"{label} within 5 miles: {site['name']}",
                        source_url=f"https://enviro.epa.gov/enviro/epa_home.aspx",
                        raw_excerpt=f"{site['name']} at {site['address']}, {site['city']}, {site['state']}",
                        confidence=0.95,
                    ))
    except Exception as e:
        logging.warning(f"EPA environmental lookup failed: {e}")
        return {"data": {"epa_environmental": epa_data}, "unknowns": [], "errors": [str(e)], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

    total_hazards = sum(len(epa_data[k]) for k in ["superfund_sites", "brownfields", "toxic_releases", "hazardous_waste"])
    if total_hazards == 0:
        epa_data["risk_summary"] = "No EPA environmental hazards found within 5 miles"
    else:
        parts = []
        if epa_data["superfund_sites"]:
            parts.append(f"{len(epa_data['superfund_sites'])} Superfund sites")
        if epa_data["brownfields"]:
            parts.append(f"{len(epa_data['brownfields'])} brownfields")
        if epa_data["toxic_releases"]:
            parts.append(f"{len(epa_data['toxic_releases'])} toxic release facilities")
        if epa_data["hazardous_waste"]:
            parts.append(f"{len(epa_data['hazardous_waste'])} hazardous waste handlers")
        epa_data["risk_summary"] = f"WARNING: {', '.join(parts)} within 5 miles"

    return {"data": {"epa_environmental": epa_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}


async def worker_wildfire_hazard(
    db: Session, job: AgenticJob, context: dict[str, Any], svc: ServiceContext
) -> dict[str, Any]:
    """Check USFS wildfire hazard potential (2023 dataset)."""
    profile = context.get("normalize_geocode", {}).get("property_profile", {})
    geo = profile.get("geo", {})
    lat, lng = geo.get("lat"), geo.get("lng")
    evidence: list[EvidenceDraft] = []

    wildfire_data: dict[str, Any] = {"hazard_level": None, "hazard_value": None, "description": None}

    if not lat or not lng:
        return {"data": {"wildfire_hazard": wildfire_data}, "unknowns": [{"field": "wildfire", "reason": "No geocode"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # USFS raster layer — use identify operation
            resp = await client.get(
                "https://apps.fs.usda.gov/arcx/rest/services/RDW_Wildfire/RMRS_WildfireHazardPotential_2023/MapServer/identify",
                params={
                    "geometry": f"{lng},{lat}",
                    "geometryType": "esriGeometryPoint",
                    "sr": "4326",
                    "tolerance": "1",
                    "mapExtent": f"{lng-1},{lat-1},{lng+1},{lat+1}",
                    "imageDisplay": "600,550,96",
                    "returnGeometry": "false",
                    "f": "json",
                },
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if results:
                attrs = results[0].get("attributes", {})
                class_desc = attrs.get("class_desc", attrs.get("Classname", ""))
                value = attrs.get("VALUE", attrs.get("Pixel Value", ""))

                level_map = {"1": "Very Low", "2": "Low", "3": "Moderate", "4": "High", "5": "Very High", "6": "Non-burnable"}
                level = level_map.get(str(value), class_desc.split(":")[-1].strip() if ":" in str(class_desc) else str(class_desc))

                wildfire_data["hazard_level"] = level
                wildfire_data["hazard_value"] = int(value) if str(value).isdigit() else None

                is_high = level in ("High", "Very High")
                wildfire_data["description"] = f"Wildfire hazard: {level}" + (" — may affect insurance availability" if is_high else "")

                evidence.append(EvidenceDraft(
                    category="wildfire",
                    claim=f"USFS wildfire hazard potential: {level}",
                    source_url="https://www.firelab.org/project/wildfire-hazard-potential",
                    raw_excerpt=f"class_desc={class_desc}, VALUE={value}",
                    confidence=0.90,
                ))
            else:
                wildfire_data["hazard_level"] = "Unknown"
                wildfire_data["description"] = "No USFS wildfire data available for this location"

    except Exception as e:
        logging.warning(f"Wildfire hazard lookup failed: {e}")
        return {"data": {"wildfire_hazard": wildfire_data}, "unknowns": [], "errors": [str(e)], "evidence": [], "web_calls": 1, "cost_usd": 0.0}

    return {"data": {"wildfire_hazard": wildfire_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": 1, "cost_usd": 0.0}


async def worker_hud_opportunity(
    db: Session, job: AgenticJob, context: dict[str, Any], svc: ServiceContext
) -> dict[str, Any]:
    """Get HUD Opportunity Indices: school proficiency, jobs, poverty, transit, labor, env health."""
    profile = context.get("normalize_geocode", {}).get("property_profile", {})
    geo = profile.get("geo", {})
    lat, lng = geo.get("lat"), geo.get("lng")
    evidence: list[EvidenceDraft] = []
    web_calls = 0

    hud_data: dict[str, Any] = {
        "school_proficiency_index": None,
        "jobs_proximity_index": None,
        "poverty_index": None,
        "transit_index": None,
        "labor_market_index": None,
        "environmental_health_index": None,
        "transportation_cost_index": None,
    }

    if not lat or not lng:
        return {"data": {"hud_opportunity": hud_data}, "unknowns": [{"field": "hud", "reason": "No geocode"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

    base_params = {
        "geometry": f"{lng},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "returnGeometry": "false",
        "f": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Layer 13: Block group level (school + jobs)
            resp1 = await client.get(
                "https://egis.hud.gov/arcgis/rest/services/affht/AffhtMapService/MapServer/13/query",
                params={**base_params, "outFields": "SCHL_IDX,JOBS_IDX"},
            )
            web_calls += 1
            resp1.raise_for_status()
            feats1 = resp1.json().get("features", [])
            if feats1:
                attrs = feats1[0].get("attributes", {})
                hud_data["school_proficiency_index"] = attrs.get("SCHL_IDX")
                hud_data["jobs_proximity_index"] = attrs.get("JOBS_IDX")

            # Layer 23: Tract level (poverty, transit, labor, env, transport cost)
            resp2 = await client.get(
                "https://egis.hud.gov/arcgis/rest/services/affht/AffhtMapService/MapServer/23/query",
                params={**base_params, "outFields": "POV_IDX,LBR_IDX,HAZ_IDX,TCOST_IDX,TRANS_IDX"},
            )
            web_calls += 1
            resp2.raise_for_status()
            feats2 = resp2.json().get("features", [])
            if feats2:
                attrs = feats2[0].get("attributes", {})
                hud_data["poverty_index"] = attrs.get("POV_IDX")
                hud_data["labor_market_index"] = attrs.get("LBR_IDX")
                hud_data["environmental_health_index"] = attrs.get("HAZ_IDX")
                hud_data["transportation_cost_index"] = attrs.get("TCOST_IDX")
                hud_data["transit_index"] = attrs.get("TRANS_IDX")

            # Build evidence
            scored = {k: v for k, v in hud_data.items() if v is not None}
            if scored:
                summary = ", ".join(f"{k.replace('_', ' ').title()}: {v}/100" for k, v in scored.items())
                evidence.append(EvidenceDraft(
                    category="opportunity_index",
                    claim=f"HUD Opportunity Indices: {summary}",
                    source_url="https://egis.hud.gov/affht/",
                    raw_excerpt=str(scored),
                    confidence=0.95,
                ))

    except Exception as e:
        logging.warning(f"HUD opportunity index lookup failed: {e}")
        return {"data": {"hud_opportunity": hud_data}, "unknowns": [], "errors": [str(e)], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

    return {"data": {"hud_opportunity": hud_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}


async def worker_wetlands(
    db: Session, job: AgenticJob, context: dict[str, Any], svc: ServiceContext
) -> dict[str, Any]:
    """Check USFWS National Wetlands Inventory."""
    profile = context.get("normalize_geocode", {}).get("property_profile", {})
    geo = profile.get("geo", {})
    lat, lng = geo.get("lat"), geo.get("lng")
    evidence: list[EvidenceDraft] = []

    wetlands_data: dict[str, Any] = {"wetlands_found": False, "wetlands": [], "development_restricted": False}

    if not lat or not lng:
        return {"data": {"wetlands": wetlands_data}, "unknowns": [{"field": "wetlands", "reason": "No geocode"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest/services/Wetlands/MapServer/identify",
                params={
                    "geometry": f"{lng},{lat}",
                    "geometryType": "esriGeometryPoint",
                    "sr": "4326",
                    "tolerance": "10",
                    "mapExtent": f"{lng-0.01},{lat-0.01},{lng+0.01},{lat+0.01}",
                    "imageDisplay": "600,550,96",
                    "returnGeometry": "false",
                    "f": "json",
                },
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            for r in results[:5]:
                attrs = r.get("attributes", {})
                wetland = {
                    "type": attrs.get("WETLAND_TYPE", "Unknown"),
                    "acres": attrs.get("ACRES"),
                    "classification": attrs.get("ATTRIBUTE", ""),
                    "system": attrs.get("SYSTEM_NAME", ""),
                    "water_regime": attrs.get("WATER_REGIME_NAME", ""),
                }
                wetlands_data["wetlands"].append(wetland)
                evidence.append(EvidenceDraft(
                    category="wetlands",
                    claim=f"Wetland present: {wetland['type']} ({wetland['acres']} acres, {wetland['system']})",
                    source_url="https://www.fws.gov/program/national-wetlands-inventory",
                    raw_excerpt=f"ATTRIBUTE={wetland['classification']}, WATER_REGIME={wetland['water_regime']}",
                    confidence=0.90,
                ))

            if wetlands_data["wetlands"]:
                wetlands_data["wetlands_found"] = True
                wetlands_data["development_restricted"] = True

    except Exception as e:
        logging.warning(f"Wetlands lookup failed: {e}")
        return {"data": {"wetlands": wetlands_data}, "unknowns": [], "errors": [str(e)], "evidence": [], "web_calls": 1, "cost_usd": 0.0}

    return {"data": {"wetlands": wetlands_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": 1, "cost_usd": 0.0}


async def worker_historic_places(
    db: Session, job: AgenticJob, context: dict[str, Any], svc: ServiceContext
) -> dict[str, Any]:
    """Check National Register of Historic Places within 1 mile."""
    profile = context.get("normalize_geocode", {}).get("property_profile", {})
    geo = profile.get("geo", {})
    lat, lng = geo.get("lat"), geo.get("lng")
    evidence: list[EvidenceDraft] = []

    historic_data: dict[str, Any] = {"in_historic_district": False, "nearby_places": [], "renovation_restricted": False, "tax_credit_eligible": False}

    if not lat or not lng:
        return {"data": {"historic_places": historic_data}, "unknowns": [{"field": "historic", "reason": "No geocode"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://mapservices.nps.gov/arcgis/rest/services/cultural_resources/nrhp_locations/MapServer/0/query",
                params={
                    "geometry": f"{lng},{lat}",
                    "geometryType": "esriGeometryPoint",
                    "inSR": "4326",
                    "spatialRel": "esriSpatialRelIntersects",
                    "distance": "1609",
                    "units": "esriSRUnit_Meter",
                    "outFields": "RESNAME,ResType,Address,City,State,County,Is_NHL",
                    "returnGeometry": "false",
                    "f": "json",
                },
            )
            resp.raise_for_status()
            features = resp.json().get("features", [])
            for feat in features[:10]:
                attrs = feat.get("attributes", {})
                place = {
                    "name": attrs.get("RESNAME", "Unknown"),
                    "type": attrs.get("ResType", ""),
                    "address": attrs.get("Address", ""),
                    "city": attrs.get("City", ""),
                    "state": attrs.get("State", ""),
                    "is_landmark": attrs.get("Is_NHL") == "Y",
                }
                historic_data["nearby_places"].append(place)

                if place["type"] == "district":
                    historic_data["in_historic_district"] = True
                    historic_data["renovation_restricted"] = True
                    historic_data["tax_credit_eligible"] = True

                evidence.append(EvidenceDraft(
                    category="historic",
                    claim=f"National Register: {place['name']} ({place['type']}) within 1 mile" + (" — National Historic Landmark" if place["is_landmark"] else ""),
                    source_url="https://www.nps.gov/subjects/nationalregister/database-research.htm",
                    raw_excerpt=f"{place['name']} at {place['address']}, {place['city']}, {place['state']}",
                    confidence=0.95,
                ))

    except Exception as e:
        logging.warning(f"Historic places lookup failed: {e}")
        return {"data": {"historic_places": historic_data}, "unknowns": [], "errors": [str(e)], "evidence": [], "web_calls": 1, "cost_usd": 0.0}

    return {"data": {"historic_places": historic_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": 1, "cost_usd": 0.0}


async def worker_seismic_hazard(
    db: Session, job: AgenticJob, context: dict[str, Any], svc: ServiceContext
) -> dict[str, Any]:
    """Check USGS seismic hazard (peak ground acceleration) and nearby quaternary faults."""
    profile = context.get("normalize_geocode", {}).get("property_profile", {})
    geo = profile.get("geo", {})
    lat, lng = geo.get("lat"), geo.get("lng")
    evidence: list[EvidenceDraft] = []
    web_calls = 0

    seismic_data: dict[str, Any] = {"peak_ground_acceleration": None, "seismic_risk_level": None, "nearby_faults": [], "description": None}

    if not lat or not lng:
        return {"data": {"seismic_hazard": seismic_data}, "unknowns": [{"field": "seismic", "reason": "No geocode"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # 1. Peak ground acceleration (raster identify)
            resp1 = await client.get(
                "https://earthquake.usgs.gov/arcgis/rest/services/haz/USpga250_2014/MapServer/identify",
                params={
                    "geometry": f"{lng},{lat}",
                    "geometryType": "esriGeometryPoint",
                    "sr": "4326",
                    "tolerance": "1",
                    "mapExtent": f"{lng-5},{lat-5},{lng+5},{lat+5}",
                    "imageDisplay": "600,550,96",
                    "returnGeometry": "false",
                    "f": "json",
                },
            )
            web_calls += 1
            resp1.raise_for_status()
            pga_results = resp1.json().get("results", [])
            if pga_results:
                attrs = pga_results[0].get("attributes", {})
                pga_val = attrs.get("ACC_VAL", attrs.get("Pixel Value"))
                if pga_val is not None:
                    pga = float(pga_val) if str(pga_val).replace(".", "").isdigit() else None
                    seismic_data["peak_ground_acceleration"] = pga
                    if pga is not None:
                        if pga >= 60:
                            seismic_data["seismic_risk_level"] = "High"
                        elif pga >= 20:
                            seismic_data["seismic_risk_level"] = "Moderate"
                        else:
                            seismic_data["seismic_risk_level"] = "Low"
                        seismic_data["description"] = f"Peak ground acceleration: {pga}%g ({seismic_data['seismic_risk_level']} risk)"

                        evidence.append(EvidenceDraft(
                            category="seismic",
                            claim=f"USGS seismic hazard: PGA={pga}%g — {seismic_data['seismic_risk_level']} risk",
                            source_url="https://earthquake.usgs.gov/hazards/hazmaps/",
                            raw_excerpt=f"ACC_VAL={pga_val}",
                            confidence=0.90,
                        ))

            # 2. Nearby quaternary faults (10km buffer)
            resp2 = await client.get(
                "https://earthquake.usgs.gov/arcgis/rest/services/haz/Qfaults/MapServer/21/query",
                params={
                    "geometry": f"{lng},{lat}",
                    "geometryType": "esriGeometryPoint",
                    "inSR": "4326",
                    "spatialRel": "esriSpatialRelIntersects",
                    "distance": "16093",
                    "units": "esriSRUnit_Meter",
                    "outFields": "fault_name,section_name,age,slip_rate,slip_sense",
                    "returnGeometry": "false",
                    "f": "json",
                },
            )
            web_calls += 1
            resp2.raise_for_status()
            faults = resp2.json().get("features", [])
            for feat in faults[:5]:
                attrs = feat.get("attributes", {})
                fault = {
                    "name": attrs.get("fault_name", "Unknown"),
                    "section": attrs.get("section_name", ""),
                    "age": attrs.get("age", ""),
                    "slip_rate": attrs.get("slip_rate", ""),
                }
                seismic_data["nearby_faults"].append(fault)
                evidence.append(EvidenceDraft(
                    category="seismic",
                    claim=f"Quaternary fault within 10 miles: {fault['name']}",
                    source_url="https://earthquake.usgs.gov/hazards/qfaults/",
                    raw_excerpt=f"fault={fault['name']}, age={fault['age']}, slip_rate={fault['slip_rate']}",
                    confidence=0.90,
                ))

    except Exception as e:
        logging.warning(f"Seismic hazard lookup failed: {e}")
        return {"data": {"seismic_hazard": seismic_data}, "unknowns": [], "errors": [str(e)], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

    return {"data": {"seismic_hazard": seismic_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}


async def worker_school_district(
    db: Session, job: AgenticJob, context: dict[str, Any], svc: ServiceContext
) -> dict[str, Any]:
    """Look up Census school district and tract GEOID."""
    profile = context.get("normalize_geocode", {}).get("property_profile", {})
    geo = profile.get("geo", {})
    lat, lng = geo.get("lat"), geo.get("lng")
    evidence: list[EvidenceDraft] = []
    web_calls = 0

    district_data: dict[str, Any] = {"school_district": None, "district_geoid": None, "census_tract_geoid": None}

    if not lat or not lng:
        return {"data": {"school_district": district_data}, "unknowns": [{"field": "school_district", "reason": "No geocode"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

    base_params = {
        "geometry": f"{lng},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "returnGeometry": "false",
        "f": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Unified school district
            resp1 = await client.get(
                "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/School/MapServer/0/query",
                params={**base_params, "outFields": "NAME,BASENAME,GEOID,LOGRADE,HIGRADE"},
            )
            web_calls += 1
            resp1.raise_for_status()
            feats1 = resp1.json().get("features", [])
            if feats1:
                attrs = feats1[0].get("attributes", {})
                district_data["school_district"] = attrs.get("NAME") or attrs.get("BASENAME")
                district_data["district_geoid"] = attrs.get("GEOID")

                evidence.append(EvidenceDraft(
                    category="school_district",
                    claim=f"School district: {district_data['school_district']} (GEOID: {district_data['district_geoid']})",
                    source_url="https://www.census.gov/programs-surveys/school-districts.html",
                    raw_excerpt=f"NAME={attrs.get('NAME')}, GEOID={attrs.get('GEOID')}, grades={attrs.get('LOGRADE')}-{attrs.get('HIGRADE')}",
                    confidence=0.95,
                ))

            # Census tract GEOID
            resp2 = await client.get(
                "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2021/MapServer/14/query",
                params={**base_params, "outFields": "GEOID,NAME,STATE,COUNTY,TRACT"},
            )
            web_calls += 1
            resp2.raise_for_status()
            feats2 = resp2.json().get("features", [])
            if feats2:
                attrs = feats2[0].get("attributes", {})
                district_data["census_tract_geoid"] = attrs.get("GEOID")

    except Exception as e:
        logging.warning(f"School district lookup failed: {e}")
        return {"data": {"school_district": district_data}, "unknowns": [], "errors": [str(e)], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

    return {"data": {"school_district": district_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}
