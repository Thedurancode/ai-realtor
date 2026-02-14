"""Insights service — scans properties and returns prioritized actionable alerts."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.contract import Contract, ContractStatus
from app.models.conversation_history import ConversationHistory
from app.models.property import Property
from app.models.skip_trace import SkipTrace
from app.models.zillow_enrichment import ZillowEnrichment


class InsightsService:
    """On-demand intelligence that surfaces stale properties, deadlines, and gaps."""

    STALE_DAYS = 7
    DEADLINE_WARN_DAYS = 3
    UNSIGNED_STALE_DAYS = 3

    def get_insights(self, db: Session, property_id: Optional[int] = None) -> dict:
        alerts = []
        alerts.extend(self._stale_properties(db, property_id))
        alerts.extend(self._contract_deadlines(db, property_id))
        alerts.extend(self._unsigned_contracts(db, property_id))
        alerts.extend(self._missing_enrichment(db, property_id))
        alerts.extend(self._missing_skip_trace(db, property_id))
        alerts.extend(self._high_deal_score_no_action(db, property_id))

        # Group by priority
        grouped = {"urgent": [], "high": [], "medium": [], "low": []}
        for a in alerts:
            grouped.get(a["priority"], grouped["low"]).append(a)

        voice_summary = self._build_voice_summary(alerts)

        return {
            "total_alerts": len(alerts),
            "urgent": grouped["urgent"],
            "high": grouped["high"],
            "medium": grouped["medium"],
            "low": grouped["low"],
            "voice_summary": voice_summary,
        }

    # ── Alert rules ──

    def _stale_properties(self, db: Session, property_id: Optional[int]) -> list[dict]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.STALE_DAYS)
        query = db.query(Property).filter(Property.status.in_(["available", "pending"]))
        if property_id:
            query = query.filter(Property.id == property_id)

        alerts = []
        for prop in query.all():
            last_activity = (
                db.query(func.max(ConversationHistory.created_at))
                .filter(ConversationHistory.property_id == prop.id)
                .scalar()
            )
            last_touch = last_activity or prop.created_at
            if last_touch and last_touch.replace(tzinfo=timezone.utc) < cutoff:
                days = (datetime.now(timezone.utc) - last_touch.replace(tzinfo=timezone.utc)).days
                alerts.append({
                    "type": "stale_property",
                    "priority": "high" if days > 14 else "medium",
                    "property_id": prop.id,
                    "property_address": prop.address,
                    "message": f"No activity in {days} days",
                    "suggested_action": "Follow up or update status",
                })
        return alerts

    def _contract_deadlines(self, db: Session, property_id: Optional[int]) -> list[dict]:
        now = datetime.now(timezone.utc)
        warn_cutoff = now + timedelta(days=self.DEADLINE_WARN_DAYS)
        query = (
            db.query(Contract)
            .join(Property)
            .filter(
                Contract.is_required.is_(True),
                Contract.required_by_date.isnot(None),
                Contract.status.notin_([ContractStatus.COMPLETED, ContractStatus.CANCELLED]),
            )
        )
        if property_id:
            query = query.filter(Contract.property_id == property_id)

        alerts = []
        for c in query.all():
            deadline = c.required_by_date.replace(tzinfo=timezone.utc) if c.required_by_date.tzinfo is None else c.required_by_date
            if deadline < now:
                alerts.append({
                    "type": "contract_deadline",
                    "priority": "urgent",
                    "property_id": c.property_id,
                    "property_address": c.property.address if c.property else "Unknown",
                    "message": f"Contract '{c.name}' deadline OVERDUE by {(now - deadline).days} days",
                    "suggested_action": f"Complete or extend contract #{c.id}",
                })
            elif deadline <= warn_cutoff:
                days_left = (deadline - now).days
                alerts.append({
                    "type": "contract_deadline",
                    "priority": "high",
                    "property_id": c.property_id,
                    "property_address": c.property.address if c.property else "Unknown",
                    "message": f"Contract '{c.name}' due in {days_left} day{'s' if days_left != 1 else ''}",
                    "suggested_action": f"Prioritize signing contract #{c.id}",
                })
        return alerts

    def _unsigned_contracts(self, db: Session, property_id: Optional[int]) -> list[dict]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.UNSIGNED_STALE_DAYS)
        query = (
            db.query(Contract)
            .join(Property)
            .filter(
                Contract.is_required.is_(True),
                Contract.status.in_([ContractStatus.DRAFT, ContractStatus.SENT]),
                Contract.created_at < cutoff,
            )
        )
        if property_id:
            query = query.filter(Contract.property_id == property_id)

        alerts = []
        for c in query.all():
            days = (datetime.now(timezone.utc) - c.created_at.replace(tzinfo=timezone.utc)).days
            alerts.append({
                "type": "unsigned_contract",
                "priority": "medium",
                "property_id": c.property_id,
                "property_address": c.property.address if c.property else "Unknown",
                "message": f"Contract '{c.name}' unsigned for {days} days (status: {c.status.value})",
                "suggested_action": "Send or resend for signature",
            })
        return alerts

    def _missing_enrichment(self, db: Session, property_id: Optional[int]) -> list[dict]:
        query = (
            db.query(Property)
            .outerjoin(ZillowEnrichment)
            .filter(ZillowEnrichment.id.is_(None))
        )
        if property_id:
            query = query.filter(Property.id == property_id)

        return [
            {
                "type": "missing_enrichment",
                "priority": "low",
                "property_id": p.id,
                "property_address": p.address,
                "message": "No Zillow enrichment data",
                "suggested_action": "Enrich with Zillow for market data",
            }
            for p in query.all()
        ]

    def _missing_skip_trace(self, db: Session, property_id: Optional[int]) -> list[dict]:
        query = (
            db.query(Property)
            .outerjoin(SkipTrace)
            .filter(SkipTrace.id.is_(None))
        )
        if property_id:
            query = query.filter(Property.id == property_id)

        return [
            {
                "type": "missing_skip_trace",
                "priority": "low",
                "property_id": p.id,
                "property_address": p.address,
                "message": "No skip trace — owner unknown",
                "suggested_action": "Run skip trace to find owner",
            }
            for p in query.all()
        ]

    def _high_deal_score_no_action(self, db: Session, property_id: Optional[int]) -> list[dict]:
        query = (
            db.query(Property)
            .outerjoin(Contract)
            .filter(
                Property.deal_score >= 80,
                Contract.id.is_(None),
            )
        )
        if property_id:
            query = query.filter(Property.id == property_id)

        return [
            {
                "type": "high_score_no_contracts",
                "priority": "high",
                "property_id": p.id,
                "property_address": p.address,
                "message": f"Deal score {p.deal_score:.0f} ({p.score_grade}) but no contracts started",
                "suggested_action": "Attach contracts and move to pending",
            }
            for p in query.all()
        ]

    # ── Voice summary ──

    def _build_voice_summary(self, alerts: list[dict]) -> str:
        if not alerts:
            return "All clear — no issues found across your properties."

        urgent = [a for a in alerts if a["priority"] == "urgent"]
        high = [a for a in alerts if a["priority"] == "high"]

        parts = [f"You have {len(alerts)} alert{'s' if len(alerts) != 1 else ''}."]
        if urgent:
            parts.append(f"{len(urgent)} urgent: {urgent[0]['message']} at {urgent[0]['property_address']}.")
        if high:
            parts.append(f"{len(high)} high priority: {high[0]['message']}.")

        return " ".join(parts)


insights_service = InsightsService()
