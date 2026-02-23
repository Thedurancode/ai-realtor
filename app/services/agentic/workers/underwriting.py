"""Underwriting worker — computes ARV, rehab estimate, cash flow, and risk score."""

from __future__ import annotations

from statistics import mean
from typing import Any

from sqlalchemy.orm import Session

from app.models.agentic_job import AgenticJob
from app.models.evidence_item import EvidenceItem
from app.models.risk_score import RiskScore
from app.models.underwriting import Underwriting
from app.services.agentic.pipeline import EvidenceDraft
from app.services.agentic.workers._context import ServiceContext


async def worker_underwriting(
    db: Session,
    job: AgenticJob,
    context: dict[str, Any],
    svc: ServiceContext,
) -> dict[str, Any]:
    """Underwriting worker — computes ARV, rehab estimate, cash flow, and risk score."""

    assumptions = job.assumptions or {}

    profile = context.get("normalize_geocode", {}).get("property_profile", {})
    sales = context.get("comps_sales", {}).get("comps_sales", [])
    rentals = context.get("comps_rentals", {}).get("comps_rentals", [])

    sale_prices = [float(item["sale_price"]) for item in sales if item.get("sale_price") is not None]
    rents = [float(item["rent"]) for item in rentals if item.get("rent") is not None]

    arv_base = mean(sale_prices) if sale_prices else None
    arv_low = (arv_base * 0.9) if arv_base is not None else None
    arv_high = (arv_base * 1.1) if arv_base is not None else None

    rent_base = mean(rents) if rents else None
    rent_low = (rent_base * 0.9) if rent_base is not None else None
    rent_high = (rent_base * 1.1) if rent_base is not None else None

    rehab_tier = assumptions.get("rehab_tier", "medium")
    if rehab_tier not in {"light", "medium", "heavy"}:
        rehab_tier = "medium"

    sqft = profile.get("parcel_facts", {}).get("sqft")
    rehab_per_sqft = {"light": 15.0, "medium": 35.0, "heavy": 60.0}[rehab_tier]
    rehab_base = float(sqft * rehab_per_sqft) if sqft else None
    rehab_low = (rehab_base * 0.8) if rehab_base is not None else None
    rehab_high = (rehab_base * 1.2) if rehab_base is not None else None

    fees = {
        "closing": float(assumptions.get("closing_cost", 5000.0)),
        "holding": float(assumptions.get("holding_cost", 3000.0)),
        "assignment": float(assumptions.get("assignment_fee", 10000.0 if job.strategy == "wholesale" else 0.0)),
        "misc": float(assumptions.get("misc_fee", 1500.0)),
    }
    total_fees = sum(fees.values())

    offer_base: float | None = None
    if arv_base is not None:
        if job.strategy == "wholesale":
            offer_base = (arv_base * 0.70) - (rehab_high or 0.0) - total_fees
        elif job.strategy == "flip":
            target_margin = float(assumptions.get("target_margin", 0.20))
            offer_base = (arv_base * (1.0 - target_margin)) - (rehab_base or 0.0) - total_fees
        else:
            rent_cap = (rent_base * 100.0) if rent_base is not None else arv_base * 0.75
            offer_base = min(arv_base * 0.80, rent_cap) - (rehab_base or 0.0) - total_fees

    offer_low = (offer_base * 0.9) if offer_base is not None else None
    offer_high = (offer_base * 1.1) if offer_base is not None else None

    underwrite = {
        "arv_estimate": {"low": arv_low, "base": arv_base, "high": arv_high},
        "rent_estimate": {"low": rent_low, "base": rent_base, "high": rent_high},
        "rehab_tier": rehab_tier,
        "rehab_estimated_range": {"low": rehab_low, "base": rehab_base, "high": rehab_high},
        "offer_price_recommendation": {"low": offer_low, "base": offer_base, "high": offer_high},
        "fees": fees,
        "sensitivity_table": [
            {
                "scenario": "conservative",
                "arv_multiplier": 0.95,
                "rent_multiplier": 0.95,
                "offer_adjustment": -0.08,
            },
            {
                "scenario": "base",
                "arv_multiplier": 1.0,
                "rent_multiplier": 1.0,
                "offer_adjustment": 0.0,
            },
            {
                "scenario": "optimistic",
                "arv_multiplier": 1.05,
                "rent_multiplier": 1.05,
                "offer_adjustment": 0.08,
            },
        ],
    }

    evidence = [
        EvidenceDraft(
            category="underwriting",
            claim="Underwriting calculations generated deterministically from comps and configured assumptions.",
            source_url=f"internal://agentic_jobs/{job.id}/underwriting",
            raw_excerpt=f"strategy={job.strategy}",
            confidence=1.0,
        )
    ]

    unknowns = []
    if arv_base is None:
        unknowns.append({"field": "arv_estimate", "reason": "No qualified sales comps available."})
    if rent_base is None:
        unknowns.append({"field": "rent_estimate", "reason": "No qualified rental comps available."})

    db.query(Underwriting).filter(Underwriting.job_id == job.id).delete()
    db.add(
        Underwriting(
            research_property_id=job.research_property_id,
            job_id=job.id,
            strategy=job.strategy,
            assumptions=assumptions,
            arv_low=arv_low,
            arv_base=arv_base,
            arv_high=arv_high,
            rent_low=rent_low,
            rent_base=rent_base,
            rent_high=rent_high,
            rehab_tier=rehab_tier,
            rehab_low=rehab_low,
            rehab_high=rehab_high,
            offer_low=offer_low,
            offer_base=offer_base,
            offer_high=offer_high,
            fees=fees,
            sensitivity=underwrite["sensitivity_table"],
        )
    )

    # Expert-style risk score derived from coverage, source quality and contradiction checks.
    evidence_rows = db.query(EvidenceItem).filter(EvidenceItem.job_id == job.id).all()
    evidence_count = len(evidence_rows)
    coverage = min(1.0, evidence_count / 12.0)
    evidence_confidences = [float(item.confidence) for item in evidence_rows if item.confidence is not None]
    mean_evidence_confidence = mean(evidence_confidences) if evidence_confidences else 0.5
    quality_adjustment = (mean_evidence_confidence - 0.5) * 0.4

    unknown_penalty = min(0.6, len(unknowns) * 0.1)
    contradiction_penalty = 0.0
    title_risk = 0.75 if not profile.get("owner_names") else 0.35

    compliance_flags = []
    if not profile.get("owner_names"):
        compliance_flags.append("owner_not_verified")
    if not sales:
        compliance_flags.append("insufficient_sales_comps")
    if not rentals:
        compliance_flags.append("insufficient_rental_comps")

    valuation_conflict_threshold = float(assumptions.get("valuation_conflict_threshold", 0.30))
    zestimate = (profile.get("assessed_values") or {}).get("zestimate")
    if arv_base is not None and zestimate is not None:
        denom = max(abs(float(zestimate)), 1.0)
        diff_ratio = abs(float(arv_base) - float(zestimate)) / denom
        if diff_ratio > valuation_conflict_threshold:
            compliance_flags.append("valuation_conflict_zestimate_vs_comps")
            contradiction_penalty += 0.12

    rent_zestimate = (profile.get("assessed_values") or {}).get("rent_zestimate")
    if rent_base is not None and rent_zestimate is not None:
        denom = max(abs(float(rent_zestimate)), 1.0)
        diff_ratio = abs(float(rent_base) - float(rent_zestimate)) / denom
        if diff_ratio > valuation_conflict_threshold:
            compliance_flags.append("rent_conflict_zestimate_vs_comps")
            contradiction_penalty += 0.10

    data_confidence = max(
        0.0,
        min(1.0, coverage - unknown_penalty + 0.25 + quality_adjustment - contradiction_penalty),
    )

    risk_score = {
        "title_risk": round(title_risk, 3),
        "data_confidence": round(data_confidence, 3),
        "compliance_flags": compliance_flags,
        "notes": (
            "Risk score combines deterministic coverage, evidence quality, and cross-source "
            "contradiction checks."
        ),
    }

    db.query(RiskScore).filter(RiskScore.job_id == job.id).delete()
    db.add(
        RiskScore(
            research_property_id=job.research_property_id,
            job_id=job.id,
            title_risk=risk_score["title_risk"],
            data_confidence=risk_score["data_confidence"],
            compliance_flags=risk_score["compliance_flags"],
            notes=risk_score["notes"],
        )
    )
    db.commit()

    return {
        "data": {"underwrite": underwrite, "risk_score": risk_score},
        "unknowns": unknowns,
        "errors": [],
        "evidence": evidence,
        "web_calls": 0,
        "cost_usd": 0.0,
    }
