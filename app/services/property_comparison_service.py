"""Property Comparison service — side-by-side comparison of 2-5 properties.

Pulls property data, Zillow enrichment, deal calculations, and produces
a ranked comparison with a winner recommendation.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.zillow_enrichment import ZillowEnrichment
from app.schemas.deal_calculator import DealCalculatorInput, DealCalculatorResponse
from app.services.deal_calculator_service import calculate_deal

logger = logging.getLogger(__name__)


def compare_properties(db: Session, property_ids: list[int]) -> dict:
    """Compare 2-5 properties side by side with deal metrics and a recommendation."""

    if len(property_ids) < 2:
        raise ValueError("Need at least 2 properties to compare.")
    if len(property_ids) > 5:
        raise ValueError("Maximum 5 properties per comparison.")
    if len(property_ids) != len(set(property_ids)):
        raise ValueError("Duplicate property IDs are not allowed.")

    properties = db.query(Property).filter(Property.id.in_(property_ids)).all()
    found_ids = {p.id for p in properties}
    missing = [pid for pid in property_ids if pid not in found_ids]
    if missing:
        raise ValueError(f"Properties not found: {missing}")

    comparisons = []
    for prop in properties:
        enrichment = (
            db.query(ZillowEnrichment)
            .filter(ZillowEnrichment.property_id == prop.id)
            .first()
        )

        # Run deal calculator (best-effort — skip on error)
        deal: DealCalculatorResponse | None = None
        try:
            deal = calculate_deal(db, DealCalculatorInput(property_id=prop.id))
        except Exception as e:
            logger.warning("Deal calc failed for property %d: %s", prop.id, e)

        zestimate = None
        rent_estimate = None
        photos = []
        if enrichment:
            zestimate = enrichment.zestimate
            rent_estimate = enrichment.rent_zestimate
            photos = (enrichment.photos or [])[:1]  # first photo only

        best_grade = None
        best_strategy = None
        best_roi = None
        best_profit = None
        if deal:
            best_strategy = deal.recommended_strategy
            for strat_name in ["wholesale", "flip", "rental", "brrrr"]:
                strat = getattr(deal, strat_name, None)
                if not strat:
                    continue
                if strat.deal_score:
                    if best_grade is None or strat.deal_score.score > (best_grade or 0):
                        best_grade = strat.deal_score.grade
                if strat.roi_percent is not None:
                    if best_roi is None or strat.roi_percent > best_roi:
                        best_roi = strat.roi_percent
                if strat.net_profit is not None:
                    if best_profit is None or strat.net_profit > best_profit:
                        best_profit = strat.net_profit

        comparisons.append({
            "property_id": prop.id,
            "address": prop.address,
            "city": prop.city,
            "state": prop.state,
            "zip_code": prop.zip_code,
            "price": prop.price,
            "bedrooms": prop.bedrooms,
            "bathrooms": prop.bathrooms,
            "square_feet": prop.square_feet,
            "lot_size": prop.lot_size,
            "year_built": prop.year_built,
            "property_type": prop.property_type.value if prop.property_type else None,
            "status": prop.status.value if prop.status else None,
            "deal_score": prop.deal_score,
            "score_grade": prop.score_grade,
            "zestimate": zestimate,
            "rent_estimate": rent_estimate,
            "photo": photos[0] if photos else None,
            "price_per_sqft": round(prop.price / prop.square_feet, 2) if prop.price and prop.square_feet else None,
            "deal": {
                "arv": deal.arv if deal else None,
                "recommended_strategy": best_strategy,
                "best_grade": best_grade,
                "best_roi": best_roi,
                "best_profit": best_profit,
                "wholesale_offer": deal.wholesale.offer_price if deal else None,
                "flip_profit": deal.flip.net_profit if deal else None,
                "rental_cash_flow": deal.rental.monthly_cash_flow if deal else None,
                "rental_cap_rate": deal.rental.cap_rate if deal else None,
            } if deal else None,
        })

    # Rank properties
    winner = _pick_winner(comparisons)

    # Build voice summary
    voice_summary = _build_voice_summary(comparisons, winner)

    return {
        "properties": comparisons,
        "winner": winner,
        "voice_summary": voice_summary,
        "compared_at": datetime.now(timezone.utc).isoformat(),
    }


def _pick_winner(comparisons: list[dict]) -> dict:
    """Score each property across multiple dimensions and pick the best."""
    scores: dict[int, float] = {}

    for comp in comparisons:
        pid = comp["property_id"]
        s = 0.0

        # Price per sqft (lower is better) — 25 pts
        ppsf_values = [c["price_per_sqft"] for c in comparisons if c["price_per_sqft"]]
        if comp["price_per_sqft"] and ppsf_values:
            best_ppsf = min(ppsf_values)
            if best_ppsf > 0:
                s += 25 * (best_ppsf / comp["price_per_sqft"])

        # Deal grade — 30 pts
        deal = comp.get("deal")
        if deal and deal.get("best_grade"):
            grade_pts = {"A": 30, "B": 24, "C": 18, "D": 10, "F": 0}
            s += grade_pts.get(deal["best_grade"], 0)

        # ROI — 20 pts
        roi_values = [
            c["deal"]["best_roi"]
            for c in comparisons
            if c.get("deal") and c["deal"].get("best_roi")
        ]
        if deal and deal.get("best_roi") and roi_values:
            max_roi = max(roi_values)
            if max_roi > 0:
                s += 20 * (deal["best_roi"] / max_roi)

        # Cash flow — 15 pts
        cf_values = [
            c["deal"]["rental_cash_flow"]
            for c in comparisons
            if c.get("deal") and c["deal"].get("rental_cash_flow")
        ]
        if deal and deal.get("rental_cash_flow") and cf_values:
            max_cf = max(cf_values)
            if max_cf > 0:
                s += 15 * (deal["rental_cash_flow"] / max_cf)

        # Zestimate vs price (higher ratio = more upside) — 10 pts
        if comp.get("zestimate") and comp["price"] and comp["price"] > 0:
            ratio = comp["zestimate"] / comp["price"]
            s += min(10, 10 * ratio)  # cap at 10

        scores[pid] = round(s, 1)

    best_pid = max(scores, key=scores.get)
    best_comp = next(c for c in comparisons if c["property_id"] == best_pid)

    reasons = []
    deal = best_comp.get("deal")
    if deal and deal.get("best_grade"):
        reasons.append(f"best deal grade ({deal['best_grade']})")
    if best_comp.get("price_per_sqft"):
        reasons.append(f"${best_comp['price_per_sqft']:,.0f}/sqft")
    if deal and deal.get("best_roi"):
        reasons.append(f"{deal['best_roi']:.1f}% ROI")

    return {
        "property_id": best_pid,
        "address": best_comp["address"],
        "score": scores[best_pid],
        "scores": scores,
        "reason": ", ".join(reasons) if reasons else "highest composite score",
    }


def _build_voice_summary(comparisons: list[dict], winner: dict) -> str:
    """Human-readable comparison summary for voice or MCP."""
    n = len(comparisons)
    lines = [f"Comparing {n} properties:\n"]

    for i, comp in enumerate(comparisons, 1):
        addr = f"{comp['address']}, {comp['city']}"
        price = f"${comp['price']:,.0f}" if comp['price'] else "N/A"
        beds = comp.get("bedrooms") or "?"
        baths = comp.get("bathrooms") or "?"
        sqft = f"{comp['square_feet']:,}" if comp.get("square_feet") else "?"

        line = f"{i}. {addr} — {price}, {beds}bd/{baths}ba, {sqft} sqft"
        if comp.get("price_per_sqft"):
            line += f", ${comp['price_per_sqft']:,.0f}/sqft"

        deal = comp.get("deal")
        if deal:
            parts = []
            if deal.get("best_grade"):
                parts.append(f"Grade {deal['best_grade']}")
            if deal.get("best_roi"):
                parts.append(f"ROI {deal['best_roi']:.1f}%")
            if deal.get("rental_cash_flow"):
                parts.append(f"cash flow ${deal['rental_cash_flow']:,.0f}/mo")
            if parts:
                line += f" [{', '.join(parts)}]"

        lines.append(line)

    lines.append(
        f"\nWinner: Property {winner['property_id']} ({winner['address']}) — {winner['reason']}."
    )
    return "\n".join(lines)
