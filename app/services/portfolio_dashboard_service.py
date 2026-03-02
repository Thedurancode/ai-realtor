"""Portfolio Dashboard service — bird's-eye view of the entire portfolio.

Returns total value, property counts by status/type, pipeline health,
top and bottom performers, and a voice-friendly summary.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import func, case, desc
from sqlalchemy.orm import Session

from app.models.property import Property, PropertyStatus, PropertyType
from app.models.zillow_enrichment import ZillowEnrichment
from app.models.contract import Contract
from app.models.offer import Offer

logger = logging.getLogger(__name__)


def get_portfolio_dashboard(db: Session, agent_id: int | None = None) -> dict:
    """Build a full portfolio snapshot with key metrics."""

    base = db.query(Property)
    if agent_id:
        base = base.filter(Property.agent_id == agent_id)

    total = base.count()
    if total == 0:
        return {
            "total_properties": 0,
            "voice_summary": "Your portfolio is empty. Add a property to get started.",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── Aggregate metrics ──
    agg = base.with_entities(
        func.count(Property.id).label("count"),
        func.sum(Property.price).label("total_value"),
        func.avg(Property.price).label("avg_price"),
        func.min(Property.price).label("min_price"),
        func.max(Property.price).label("max_price"),
        func.avg(Property.deal_score).label("avg_deal_score"),
        func.avg(Property.square_feet).label("avg_sqft"),
    ).first()

    total_value = agg.total_value or 0
    avg_price = agg.avg_price or 0
    avg_deal_score = agg.avg_deal_score

    # ── By status ──
    status_counts = dict(
        base.with_entities(
            Property.status, func.count(Property.id)
        ).group_by(Property.status).all()
    )

    # ── By type ──
    type_counts = dict(
        base.with_entities(
            Property.property_type, func.count(Property.id)
        ).group_by(Property.property_type).all()
    )

    # ── Pipeline health ──
    pipeline_counts = dict(
        base.filter(Property.pipeline_status.isnot(None))
        .with_entities(Property.pipeline_status, func.count(Property.id))
        .group_by(Property.pipeline_status)
        .all()
    )

    # ── Top 3 deals (by deal_score) ──
    top_deals = (
        base.filter(Property.deal_score.isnot(None))
        .order_by(desc(Property.deal_score))
        .limit(3)
        .all()
    )

    # ── Bottom 3 deals ──
    bottom_deals = (
        base.filter(Property.deal_score.isnot(None))
        .order_by(Property.deal_score)
        .limit(3)
        .all()
    )

    # ── Enrichment coverage ──
    enriched_count = (
        db.query(func.count(ZillowEnrichment.id))
        .join(Property, ZillowEnrichment.property_id == Property.id)
        .scalar()
    ) or 0

    # ── Contracts & offers ──
    contract_q = db.query(Contract)
    offer_q = db.query(Offer)
    if agent_id:
        contract_q = contract_q.join(Property).filter(Property.agent_id == agent_id)
        offer_q = offer_q.join(Property).filter(Property.agent_id == agent_id)

    contract_count = contract_q.count()
    offer_count = offer_q.count()

    # ── Recent activity (last 7 days) ──
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_added = base.filter(Property.created_at >= week_ago).count()

    # ── Zestimate vs list price (portfolio-wide equity estimate) ──
    equity_data = (
        db.query(
            func.sum(ZillowEnrichment.zestimate).label("total_zestimate"),
            func.sum(Property.price).label("total_list"),
        )
        .join(Property, ZillowEnrichment.property_id == Property.id)
        .filter(ZillowEnrichment.zestimate.isnot(None))
    )
    if agent_id:
        equity_data = equity_data.filter(Property.agent_id == agent_id)
    equity_row = equity_data.first()

    total_zestimate = equity_row.total_zestimate if equity_row else None
    total_list = equity_row.total_list if equity_row else None
    estimated_equity = None
    if total_zestimate and total_list:
        estimated_equity = total_zestimate - total_list

    def _prop_summary(p: Property) -> dict:
        return {
            "property_id": p.id,
            "address": p.address,
            "city": p.city,
            "price": p.price,
            "deal_score": p.deal_score,
            "score_grade": p.score_grade,
        }

    result = {
        "total_properties": total,
        "total_value": round(total_value, 2),
        "avg_price": round(avg_price, 2),
        "min_price": agg.min_price,
        "max_price": agg.max_price,
        "avg_deal_score": round(avg_deal_score, 1) if avg_deal_score else None,
        "by_status": {(s.value if s else "unknown"): c for s, c in status_counts.items()},
        "by_type": {(t.value if t else "unknown"): c for t, c in type_counts.items()},
        "pipeline": pipeline_counts,
        "enrichment_coverage": f"{enriched_count}/{total}",
        "enrichment_pct": round(100 * enriched_count / total, 1) if total else 0,
        "contracts": contract_count,
        "offers": offer_count,
        "recent_added_7d": recent_added,
        "top_deals": [_prop_summary(p) for p in top_deals],
        "bottom_deals": [_prop_summary(p) for p in bottom_deals],
        "estimated_equity": round(estimated_equity, 2) if estimated_equity else None,
        "total_zestimate": round(total_zestimate, 2) if total_zestimate else None,
        "voice_summary": _build_voice_summary(
            total, total_value, avg_price, avg_deal_score,
            status_counts, enriched_count, contract_count, offer_count,
            recent_added, top_deals, estimated_equity,
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return result


def _build_voice_summary(
    total, total_value, avg_price, avg_deal_score,
    status_counts, enriched_count, contract_count, offer_count,
    recent_added, top_deals, estimated_equity,
) -> str:
    lines = [f"Portfolio snapshot: {total} properties, ${total_value:,.0f} total value, ${avg_price:,.0f} average price."]

    if avg_deal_score:
        grade = _score_to_grade(avg_deal_score)
        lines.append(f"Average deal score: {avg_deal_score:.0f}/100 (Grade {grade}).")

    # Status breakdown
    status_parts = []
    for s, c in status_counts.items():
        label = s.value.replace("_", " ") if s else "unknown"
        status_parts.append(f"{c} {label}")
    if status_parts:
        lines.append(f"Status: {', '.join(status_parts)}.")

    lines.append(f"Enrichment: {enriched_count}/{total} properties enriched with Zillow data.")
    lines.append(f"Pipeline: {contract_count} contracts, {offer_count} offers.")

    if recent_added:
        lines.append(f"Activity: {recent_added} properties added in the last 7 days.")

    if estimated_equity:
        direction = "above" if estimated_equity > 0 else "below"
        lines.append(f"Estimated equity: ${abs(estimated_equity):,.0f} {direction} list prices (Zestimate-based).")

    if top_deals:
        best = top_deals[0]
        lines.append(f"Top deal: {best.address}, {best.city} (Grade {best.score_grade or '?'}, score {best.deal_score:.0f}).")

    return "\n".join(lines)


def _score_to_grade(score: float) -> str:
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    if score >= 35:
        return "D"
    return "F"
