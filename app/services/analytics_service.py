"""Analytics service — cross-property portfolio intelligence."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.models.contract import Contract, ContractStatus
from app.models.conversation_history import ConversationHistory
from app.models.property import Property, PropertyStatus, PropertyType
from app.models.skip_trace import SkipTrace
from app.models.zillow_enrichment import ZillowEnrichment


class AnalyticsService:
    """Portfolio-level analytics aggregated from existing data."""

    def get_portfolio_summary(self, db: Session) -> dict:
        pipeline = self._pipeline_stats(db)
        value = self._portfolio_value(db)
        contracts = self._contract_stats(db)
        activity = self._activity_stats(db)
        scores = self._deal_score_stats(db)
        coverage = self._enrichment_coverage(db)

        voice_summary = self._build_voice_summary(pipeline, value, contracts, scores)

        return {
            "pipeline": pipeline,
            "portfolio_value": value,
            "contracts": contracts,
            "activity": activity,
            "deal_scores": scores,
            "enrichment_coverage": coverage,
            "voice_summary": voice_summary,
        }

    def get_pipeline_summary(self, db: Session) -> dict:
        pipeline = self._pipeline_stats(db)
        total = pipeline.get("total", 0)
        parts = [f"{total} total properties."]
        for status, count in pipeline.get("by_status", {}).items():
            if count > 0:
                parts.append(f"{count} {status}.")
        return {
            "pipeline": pipeline,
            "voice_summary": " ".join(parts),
        }

    def get_contract_summary(self, db: Session) -> dict:
        contracts = self._contract_stats(db)
        total = contracts.get("total", 0)
        unsigned = contracts.get("unsigned_required", 0)
        parts = [f"{total} total contracts."]
        if unsigned:
            parts.append(f"{unsigned} required contracts still need signatures.")
        for status, count in contracts.get("by_status", {}).items():
            if count > 0:
                parts.append(f"{count} {status}.")
        return {
            "contracts": contracts,
            "voice_summary": " ".join(parts),
        }

    # ── Stats helpers ──

    def _pipeline_stats(self, db: Session) -> dict:
        total = db.query(func.count(Property.id)).scalar() or 0

        by_status = {}
        for status in PropertyStatus:
            count = db.query(func.count(Property.id)).filter(Property.status == status).scalar() or 0
            if count > 0:
                by_status[status.value] = count

        by_type = {}
        for ptype in PropertyType:
            count = db.query(func.count(Property.id)).filter(Property.property_type == ptype).scalar() or 0
            if count > 0:
                by_type[ptype.value] = count

        return {"total": total, "by_status": by_status, "by_type": by_type}

    def _portfolio_value(self, db: Session) -> dict:
        total_price = db.query(func.sum(Property.price)).scalar() or 0
        avg_price = db.query(func.avg(Property.price)).scalar() or 0
        total_zestimate = (
            db.query(func.sum(ZillowEnrichment.zestimate))
            .join(Property)
            .scalar()
        ) or 0

        return {
            "total_price": round(total_price, 2),
            "avg_price": round(avg_price, 2),
            "total_zestimate": round(total_zestimate, 2),
            "equity": round(total_zestimate - total_price, 2),
        }

    def _contract_stats(self, db: Session) -> dict:
        total = db.query(func.count(Contract.id)).scalar() or 0

        by_status = {}
        for status in ContractStatus:
            count = db.query(func.count(Contract.id)).filter(Contract.status == status).scalar() or 0
            if count > 0:
                by_status[status.value] = count

        unsigned_required = (
            db.query(func.count(Contract.id))
            .filter(
                Contract.is_required.is_(True),
                Contract.status.in_([ContractStatus.DRAFT, ContractStatus.SENT, ContractStatus.PENDING_SIGNATURE]),
            )
            .scalar()
        ) or 0

        return {
            "total": total,
            "by_status": by_status,
            "unsigned_required": unsigned_required,
        }

    def _activity_stats(self, db: Session) -> dict:
        now = datetime.now(timezone.utc)

        def count_since(hours):
            cutoff = now - timedelta(hours=hours)
            return db.query(func.count(ConversationHistory.id)).filter(
                ConversationHistory.created_at >= cutoff
            ).scalar() or 0

        # Most active properties (last 7 days)
        week_ago = now - timedelta(days=7)
        most_active = (
            db.query(
                ConversationHistory.property_id,
                func.count(ConversationHistory.id).label("action_count"),
            )
            .filter(
                ConversationHistory.property_id.isnot(None),
                ConversationHistory.created_at >= week_ago,
            )
            .group_by(ConversationHistory.property_id)
            .order_by(func.count(ConversationHistory.id).desc())
            .limit(5)
            .all()
        )

        most_active_list = []
        for row in most_active:
            prop = db.query(Property).filter(Property.id == row.property_id).first()
            most_active_list.append({
                "property_id": row.property_id,
                "address": prop.address if prop else "Unknown",
                "action_count": row.action_count,
            })

        return {
            "last_24h": count_since(24),
            "last_7d": count_since(168),
            "last_30d": count_since(720),
            "most_active_properties": most_active_list,
        }

    def _deal_score_stats(self, db: Session) -> dict:
        scored = db.query(Property).filter(Property.deal_score.isnot(None)).all()
        if not scored:
            return {"avg_score": None, "distribution": {}, "top_5": []}

        avg = sum(p.deal_score for p in scored) / len(scored)

        distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for p in scored:
            grade = p.score_grade or "F"
            if grade in distribution:
                distribution[grade] += 1

        top_5 = sorted(scored, key=lambda p: p.deal_score or 0, reverse=True)[:5]
        top_5_list = [
            {
                "property_id": p.id,
                "address": p.address,
                "deal_score": p.deal_score,
                "grade": p.score_grade,
            }
            for p in top_5
        ]

        return {
            "avg_score": round(avg, 1),
            "distribution": distribution,
            "top_5": top_5_list,
        }

    def _enrichment_coverage(self, db: Session) -> dict:
        total = db.query(func.count(Property.id)).scalar() or 0
        if total == 0:
            return {"total": 0, "zillow_pct": 0, "skip_trace_pct": 0}

        with_zillow = (
            db.query(func.count(ZillowEnrichment.id))
            .join(Property)
            .scalar()
        ) or 0

        with_skip = (
            db.query(func.count(func.distinct(SkipTrace.property_id)))
            .scalar()
        ) or 0

        return {
            "total": total,
            "with_zillow": with_zillow,
            "zillow_pct": round(with_zillow / total * 100, 1),
            "with_skip_trace": with_skip,
            "skip_trace_pct": round(with_skip / total * 100, 1),
        }

    # ── Voice summary ──

    def _build_voice_summary(self, pipeline, value, contracts, scores) -> str:
        total = pipeline.get("total", 0)
        if total == 0:
            return "Your portfolio is empty. Add some properties to get started."

        parts = [f"You have {total} properties worth ${value['total_price']:,.0f} total."]

        pending = pipeline.get("by_status", {}).get("pending", 0)
        if pending:
            parts.append(f"{pending} pending.")

        unsigned = contracts.get("unsigned_required", 0)
        if unsigned:
            parts.append(f"{unsigned} contracts need signatures.")

        if scores.get("top_5"):
            top = scores["top_5"][0]
            parts.append(
                f"Best deal: property #{top['property_id']} at {top['address']} "
                f"(score {top['deal_score']:.0f}, grade {top['grade']})."
            )

        return " ".join(parts)


analytics_service = AnalyticsService()
