"""Property Scoring Engine — 4-dimension deal quality scoring."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.property import Property, PropertyStatus
from app.models.zillow_enrichment import ZillowEnrichment
from app.models.skip_trace import SkipTrace
from app.models.contract import Contract, ContractStatus
from app.models.contact import Contact
from app.models.conversation_history import ConversationHistory
from app.models.property_note import PropertyNote
from app.models.scheduled_task import ScheduledTask, TaskStatus
from app.models.notification import Notification


# Dimension weights (must sum to 1.0)
DIMENSION_WEIGHTS = {
    "market": 0.30,
    "financial": 0.25,
    "readiness": 0.25,
    "engagement": 0.20,
}


class PropertyScoringService:
    """Multi-dimensional property scoring across Market, Financial, Readiness, and Engagement."""

    def score_property(self, db: Session, property_id: int, save: bool = True) -> dict:
        """Score a single property. Returns score, grade, breakdown, and dimensions."""
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return {"error": f"Property {property_id} not found"}

        enrichment = (
            db.query(ZillowEnrichment)
            .filter(ZillowEnrichment.property_id == prop.id)
            .first()
        )

        # Calculate each dimension
        dimensions: dict[str, dict] = {}
        available_dimensions: list[tuple[str, float, float]] = []  # (name, weight, score)

        market_score, market_detail = self._market_score(prop, enrichment)
        if market_score is not None:
            dimensions["market"] = {"score": market_score, "weight": DIMENSION_WEIGHTS["market"], **market_detail}
            available_dimensions.append(("market", DIMENSION_WEIGHTS["market"], market_score))

        financial_score, financial_detail = self._financial_score(prop, enrichment)
        if financial_score is not None:
            dimensions["financial"] = {"score": financial_score, "weight": DIMENSION_WEIGHTS["financial"], **financial_detail}
            available_dimensions.append(("financial", DIMENSION_WEIGHTS["financial"], financial_score))

        readiness_score, readiness_detail = self._readiness_score(db, prop)
        if readiness_score is not None:
            dimensions["readiness"] = {"score": readiness_score, "weight": DIMENSION_WEIGHTS["readiness"], **readiness_detail}
            available_dimensions.append(("readiness", DIMENSION_WEIGHTS["readiness"], readiness_score))

        engagement_score, engagement_detail = self._engagement_score(db, prop)
        if engagement_score is not None:
            dimensions["engagement"] = {"score": engagement_score, "weight": DIMENSION_WEIGHTS["engagement"], **engagement_detail}
            available_dimensions.append(("engagement", DIMENSION_WEIGHTS["engagement"], engagement_score))

        # Compute weighted score (re-normalize when dimensions are missing)
        if not available_dimensions:
            final_score = 0.0
        else:
            total_weight = sum(w for _, w, _ in available_dimensions)
            final_score = round(sum(w * s for _, w, s in available_dimensions) / total_weight, 1)

        grade = self._compute_grade(final_score)

        # Flatten breakdown for backward compatibility with deal_score system
        breakdown = {}
        for dim_name, dim_data in dimensions.items():
            for key, val in dim_data.items():
                if key not in ("score", "weight") and isinstance(val, (int, float)):
                    breakdown[f"{dim_name}_{key}"] = round(val, 1) if isinstance(val, float) else val

        if save:
            prop.deal_score = final_score
            prop.score_grade = grade
            prop.score_breakdown = {
                "dimensions": {k: {"score": v["score"], "weight": v["weight"]} for k, v in dimensions.items()},
                "components": breakdown,
            }
            db.commit()

        voice_summary = self._build_voice_summary(prop, final_score, grade, dimensions)

        return {
            "property_id": prop.id,
            "address": prop.address,
            "score": final_score,
            "grade": grade,
            "dimensions": dimensions,
            "breakdown": breakdown,
            "voice_summary": voice_summary,
        }

    def bulk_score(
        self,
        db: Session,
        property_ids: list[int] | None = None,
        filters: dict | None = None,
    ) -> dict:
        """Score multiple properties. Returns summary + per-property results."""
        query = db.query(Property)

        if property_ids:
            query = query.filter(Property.id.in_(property_ids))
        if filters:
            if filters.get("status"):
                query = query.filter(Property.status == PropertyStatus(filters["status"]))
            if filters.get("city"):
                query = query.filter(Property.city.ilike(f"%{filters['city']}%"))

        properties = query.limit(100).all()
        results = []
        grade_counts: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        total_score = 0.0

        for prop in properties:
            try:
                result = self.score_property(db, prop.id, save=True)
                results.append(result)
                grade_counts[result["grade"]] = grade_counts.get(result["grade"], 0) + 1
                total_score += result["score"]
            except Exception as exc:
                results.append({"property_id": prop.id, "error": str(exc)})

        avg_score = round(total_score / len(results), 1) if results else 0
        scored_count = len([r for r in results if "score" in r])

        voice = f"Scored {scored_count} properties. Average score: {avg_score}. "
        top_grades = [f"{cnt} {g}-grade" for g, cnt in grade_counts.items() if cnt > 0]
        if top_grades:
            voice += f"Distribution: {', '.join(top_grades)}."

        return {
            "total": len(properties),
            "scored": scored_count,
            "average_score": avg_score,
            "grade_distribution": grade_counts,
            "results": results,
            "voice_summary": voice,
        }

    def get_top_properties(
        self,
        db: Session,
        limit: int = 10,
        min_score: float = 0,
    ) -> list[dict]:
        """Get top-scored properties from stored deal_score."""
        properties = (
            db.query(Property)
            .filter(Property.deal_score.isnot(None))
            .filter(Property.deal_score >= min_score)
            .order_by(Property.deal_score.desc())
            .limit(limit)
            .all()
        )

        results = []
        for prop in properties:
            results.append({
                "property_id": prop.id,
                "address": prop.address,
                "city": prop.city,
                "state": prop.state,
                "price": prop.price,
                "score": prop.deal_score,
                "grade": prop.score_grade,
                "status": prop.status.value if prop.status else None,
                "breakdown": prop.score_breakdown,
            })

        return results

    # ── Dimension scorers ──

    def _market_score(self, prop: Property, enrichment: ZillowEnrichment | None) -> tuple[float | None, dict]:
        """Market dimension: property value, trends, location quality."""
        components: list[tuple[str, float, float]] = []  # (name, weight, score)
        detail: dict[str, Any] = {}

        if not enrichment and not prop.price:
            return None, detail

        # Zestimate spread (40% of market dimension)
        if enrichment and enrichment.zestimate and prop.price and prop.price > 0:
            spread = (enrichment.zestimate - prop.price) / prop.price
            score = max(0.0, min(100.0, 50 + spread * 250))
            components.append(("zestimate_spread", 40, score))
            detail["zestimate_spread"] = score

        # Days on market (20%)
        if enrichment and enrichment.days_on_zillow is not None:
            dom = enrichment.days_on_zillow
            score = max(0.0, min(100.0, dom / 90 * 100))
            components.append(("days_on_market", 20, score))
            detail["days_on_market"] = score

        # Price trend (20%)
        if enrichment and enrichment.price_history:
            prices = [
                p["price"] for p in enrichment.price_history
                if p.get("price") and p.get("event") in ("Listed for sale", "Price change", None)
            ]
            if len(prices) >= 2:
                newest, oldest = prices[0], prices[-1]
                if oldest > 0:
                    change = (newest - oldest) / oldest
                    score = max(0.0, min(100.0, 50 - change * 250))
                    components.append(("price_trend", 20, score))
                    detail["price_trend"] = score

        # School quality (10%)
        if enrichment and enrichment.schools:
            ratings = [s["rating"] for s in enrichment.schools if s.get("rating")]
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                score = max(0.0, min(100.0, avg_rating * 10))
                components.append(("school_quality", 10, score))
                detail["school_quality"] = score

        # Tax gap (10%)
        if enrichment and enrichment.tax_history and prop.price and prop.price > 0:
            latest_tax = enrichment.tax_history[0] if enrichment.tax_history else None
            if latest_tax and latest_tax.get("value") and latest_tax["value"] > 0:
                gap = (prop.price - latest_tax["value"]) / prop.price
                score = max(0.0, min(100.0, gap * 333))
                components.append(("tax_gap", 10, score))
                detail["tax_gap"] = score

        if not components:
            return None, detail

        total_w = sum(w for _, w, _ in components)
        final = round(sum(w * s for _, w, s in components) / total_w, 1)
        return final, detail

    def _financial_score(self, prop: Property, enrichment: ZillowEnrichment | None) -> tuple[float | None, dict]:
        """Financial dimension: ROI potential, rental yield."""
        components: list[tuple[str, float, float]] = []
        detail: dict[str, Any] = {}

        if not prop.price or prop.price <= 0:
            return None, detail

        # Zestimate upside (40%)
        if enrichment and enrichment.zestimate:
            upside = (enrichment.zestimate - prop.price) / prop.price
            # +30% upside → 100, 0% → 50, -30% → 0
            score = max(0.0, min(100.0, 50 + upside * 167))
            components.append(("zestimate_upside", 40, score))
            detail["zestimate_upside"] = score

        # Rental yield (30%)
        if enrichment and enrichment.rent_zestimate and enrichment.rent_zestimate > 0:
            annual_rent = enrichment.rent_zestimate * 12
            gross_yield = (annual_rent / prop.price) * 100
            # 12%+ yield → 100, 6% → 50, 0% → 0
            score = max(0.0, min(100.0, gross_yield / 12 * 100))
            components.append(("rental_yield", 30, score))
            detail["rental_yield"] = score
            detail["gross_yield_pct"] = round(gross_yield, 2)

        # Price per sqft (30%) — compare to a reasonable baseline
        if prop.square_feet and prop.square_feet > 0:
            price_per_sqft = prop.price / prop.square_feet
            # Under $100/sqft → 100, $200/sqft → 50, $300+ → 0 (rough heuristic)
            score = max(0.0, min(100.0, (300 - price_per_sqft) / 2))
            components.append(("price_per_sqft", 30, score))
            detail["price_per_sqft"] = score
            detail["actual_price_per_sqft"] = round(price_per_sqft, 2)

        if not components:
            return None, detail

        total_w = sum(w for _, w, _ in components)
        final = round(sum(w * s for _, w, s in components) / total_w, 1)
        return final, detail

    def _readiness_score(self, db: Session, prop: Property) -> tuple[float | None, dict]:
        """Readiness dimension: contracts, contacts, skip trace."""
        detail: dict[str, Any] = {}
        components: list[tuple[str, float, float]] = []

        # Contract completion (40%)
        contracts = db.query(Contract).filter(Contract.property_id == prop.id).all()
        required = [c for c in contracts if c.is_required]
        if required:
            completed = len([c for c in required if c.status == ContractStatus.COMPLETED])
            pct = (completed / len(required)) * 100
            components.append(("contracts_completed", 40, pct))
            detail["contracts_completed"] = pct
            detail["required_total"] = len(required)
            detail["required_done"] = completed
        elif contracts:
            # Has contracts but none required — partial credit
            components.append(("contracts_completed", 40, 30.0))
            detail["contracts_completed"] = 30.0

        # Contact coverage (30%)
        contacts = db.query(Contact).filter(Contact.property_id == prop.id).all()
        if contacts:
            key_roles = {"buyer", "seller", "lawyer", "attorney", "lender"}
            has_key = any(c.role and c.role.value in key_roles for c in contacts)
            score = 60.0 + (40.0 if has_key else 0.0)
            components.append(("contact_coverage", 30, min(100.0, score)))
            detail["contact_coverage"] = min(100.0, score)
            detail["contact_count"] = len(contacts)
        else:
            components.append(("contact_coverage", 30, 0.0))
            detail["contact_coverage"] = 0.0

        # Skip trace reachability (30%)
        skip_trace = (
            db.query(SkipTrace)
            .filter(SkipTrace.property_id == prop.id)
            .order_by(SkipTrace.created_at.desc())
            .first()
        )
        if skip_trace:
            score = 0.0
            if skip_trace.owner_name and skip_trace.owner_name != "Unknown Owner":
                score += 40
            if skip_trace.phone_numbers and len(skip_trace.phone_numbers) > 0:
                score += 30
            if skip_trace.emails and len(skip_trace.emails) > 0:
                score += 30
            components.append(("skip_trace_reachability", 30, score))
            detail["skip_trace_reachability"] = score
        else:
            components.append(("skip_trace_reachability", 30, 0.0))
            detail["skip_trace_reachability"] = 0.0

        if not components:
            return None, detail

        total_w = sum(w for _, w, _ in components)
        final = round(sum(w * s for _, w, s in components) / total_w, 1)
        return final, detail

    def _engagement_score(self, db: Session, prop: Property) -> tuple[float | None, dict]:
        """Engagement dimension: how actively the property is being worked."""
        detail: dict[str, Any] = {}
        components: list[tuple[str, float, float]] = []
        cutoff_7d = datetime.now(timezone.utc) - timedelta(days=7)

        # Recent activity (last 7 days) — 40%
        activity_count = (
            db.query(func.count(ConversationHistory.id))
            .filter(
                ConversationHistory.property_id == prop.id,
                ConversationHistory.created_at >= cutoff_7d,
            )
            .scalar() or 0
        )
        # 10+ actions → 100, 5 → 50, 0 → 0
        score = max(0.0, min(100.0, activity_count * 10))
        components.append(("recent_activity", 40, score))
        detail["recent_activity"] = score
        detail["activity_count_7d"] = activity_count

        # Notes count — 20%
        notes_count = (
            db.query(func.count(PropertyNote.id))
            .filter(PropertyNote.property_id == prop.id)
            .scalar() or 0
        )
        score = max(0.0, min(100.0, notes_count * 20))
        components.append(("notes", 20, score))
        detail["notes"] = score
        detail["notes_count"] = notes_count

        # Active tasks — 20%
        tasks_count = (
            db.query(func.count(ScheduledTask.id))
            .filter(
                ScheduledTask.property_id == prop.id,
                ScheduledTask.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING]),
            )
            .scalar() or 0
        )
        score = max(0.0, min(100.0, tasks_count * 25))
        components.append(("active_tasks", 20, score))
        detail["active_tasks"] = score
        detail["tasks_count"] = tasks_count

        # Recent notifications — 20%
        notif_count = (
            db.query(func.count(Notification.id))
            .filter(
                Notification.property_id == prop.id,
                Notification.created_at >= cutoff_7d,
            )
            .scalar() or 0
        )
        score = max(0.0, min(100.0, notif_count * 20))
        components.append(("recent_notifications", 20, score))
        detail["recent_notifications"] = score
        detail["notification_count_7d"] = notif_count

        total_w = sum(w for _, w, _ in components)
        final = round(sum(w * s for _, w, s in components) / total_w, 1)
        return final, detail

    # ── Helpers ──

    @staticmethod
    def _compute_grade(score: float) -> str:
        if score >= 80:
            return "A"
        if score >= 60:
            return "B"
        if score >= 40:
            return "C"
        if score >= 20:
            return "D"
        return "F"

    @staticmethod
    def _build_voice_summary(
        prop: Property, score: float, grade: str, dimensions: dict[str, dict],
    ) -> str:
        parts = [f"Property {prop.address} scores {score} out of 100, grade {grade}."]

        # Highlight best and worst dimensions
        if dimensions:
            sorted_dims = sorted(dimensions.items(), key=lambda x: x[1]["score"], reverse=True)
            best_name, best_data = sorted_dims[0]
            parts.append(f"Strongest: {best_name} ({best_data['score']}).")
            if len(sorted_dims) > 1:
                worst_name, worst_data = sorted_dims[-1]
                if worst_data["score"] < 50:
                    parts.append(f"Needs work: {worst_name} ({worst_data['score']}).")

        return " ".join(parts)


property_scoring_service = PropertyScoringService()
