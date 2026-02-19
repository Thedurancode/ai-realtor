"""Property Heartbeat — at-a-glance pipeline stage, checklist, and health status."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from app.models.contract import Contract, ContractStatus
from app.models.conversation_history import ConversationHistory
from app.models.property import Property, PropertyStatus
from app.models.skip_trace import SkipTrace
from app.models.zillow_enrichment import ZillowEnrichment

logger = logging.getLogger(__name__)

# ── Constants ──

STAGE_ORDER = [
    PropertyStatus.NEW_PROPERTY,
    PropertyStatus.ENRICHED,
    PropertyStatus.RESEARCHED,
    PropertyStatus.WAITING_FOR_CONTRACTS,
    PropertyStatus.COMPLETE,
]

STAGE_LABELS = {
    PropertyStatus.NEW_PROPERTY: "New Property",
    PropertyStatus.ENRICHED: "Enriched",
    PropertyStatus.RESEARCHED: "Researched",
    PropertyStatus.WAITING_FOR_CONTRACTS: "Waiting for Contracts",
    PropertyStatus.COMPLETE: "Complete",
}

STAGE_STALE_THRESHOLDS: dict[PropertyStatus, int] = {
    PropertyStatus.NEW_PROPERTY: 3,
    PropertyStatus.ENRICHED: 5,
    PropertyStatus.RESEARCHED: 7,
    PropertyStatus.WAITING_FOR_CONTRACTS: 10,
    PropertyStatus.COMPLETE: 999,
}

NEXT_ACTIONS = {
    "enriched": "Enrich with Zillow data",
    "researched": "Run skip trace to find owner",
    "contracts_attached": "Attach required contracts",
    "contracts_completed": "Follow up on unsigned contracts",
}


class HeartbeatService:
    """Compute pipeline heartbeat for properties."""

    def get_heartbeat(self, db: Session, property_id: int) -> dict:
        """Compute heartbeat for a single property."""
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            raise ValueError(f"Property {property_id} not found")

        # Batch-load related data for this single property
        last_activities = self._batch_last_activities(db, [property_id])
        contract_aggs = self._batch_contract_aggregates(db, [property_id])
        enrichment_ids = self._batch_enrichment_check(db, [property_id])
        skip_trace_ids = self._batch_skip_trace_check(db, [property_id])

        return self._build_heartbeat(
            prop, last_activities, contract_aggs, enrichment_ids, skip_trace_ids
        )

    def get_heartbeats_batch(
        self, db: Session, properties: list[Property]
    ) -> dict[int, dict]:
        """Compute heartbeats for multiple properties. Returns {property_id: heartbeat}."""
        if not properties:
            return {}

        prop_ids = [p.id for p in properties]

        last_activities = self._batch_last_activities(db, prop_ids)
        contract_aggs = self._batch_contract_aggregates(db, prop_ids)
        enrichment_ids = self._batch_enrichment_check(db, prop_ids)
        skip_trace_ids = self._batch_skip_trace_check(db, prop_ids)

        result = {}
        for prop in properties:
            try:
                result[prop.id] = self._build_heartbeat(
                    prop, last_activities, contract_aggs, enrichment_ids, skip_trace_ids
                )
            except Exception as e:
                logger.warning("Heartbeat failed for property %d: %s", prop.id, e)
        return result

    # ── Core builder ──

    def _build_heartbeat(
        self,
        prop: Property,
        last_activities: dict[int, datetime],
        contract_aggs: dict[int, tuple],
        enrichment_ids: set[int],
        skip_trace_ids: set[int],
    ) -> dict:
        now = datetime.now(timezone.utc)
        status = prop.status or PropertyStatus.NEW_PROPERTY

        # Stage info
        stage_index = STAGE_ORDER.index(status) if status in STAGE_ORDER else 0
        stage_label = STAGE_LABELS.get(status, status.value.replace("_", " ").title())

        # Checklist
        is_enriched = prop.id in enrichment_ids
        is_traced = prop.id in skip_trace_ids
        total_contracts, required_count, completed_count = contract_aggs.get(
            prop.id, (0, 0, 0)
        )
        has_contracts = total_contracts > 0
        all_required_done = required_count > 0 and completed_count >= required_count

        checklist = [
            {
                "key": "enriched",
                "label": "Zillow Enrichment",
                "done": is_enriched,
                "detail": None,
            },
            {
                "key": "researched",
                "label": "Skip Trace",
                "done": is_traced,
                "detail": None,
            },
            {
                "key": "contracts_attached",
                "label": "Contracts Attached",
                "done": has_contracts,
                "detail": f"{total_contracts} contract{'s' if total_contracts != 1 else ''}",
            },
            {
                "key": "contracts_completed",
                "label": "Required Contracts Completed",
                "done": all_required_done,
                "detail": f"{completed_count} of {required_count}" if required_count > 0 else "no required contracts",
            },
        ]

        # Days in stage / days since activity
        stage_entered = prop.updated_at or prop.created_at
        if stage_entered and stage_entered.tzinfo is None:
            stage_entered = stage_entered.replace(tzinfo=timezone.utc)
        days_in_stage = (now - stage_entered).total_seconds() / 86400 if stage_entered else 0

        last_activity = last_activities.get(prop.id)
        if last_activity and last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=timezone.utc)
        fallback = prop.created_at
        if fallback and fallback.tzinfo is None:
            fallback = fallback.replace(tzinfo=timezone.utc)
        last_touch = last_activity or fallback
        days_since_activity = (now - last_touch).total_seconds() / 86400 if last_touch else 0

        # Stale threshold
        threshold = STAGE_STALE_THRESHOLDS.get(status, 7)

        # Health status
        health, health_reason = self._compute_health(
            status, days_in_stage, threshold, is_enriched, is_traced,
            has_contracts, required_count, all_required_done,
        )

        # Next action
        next_action = self._compute_next_action(
            status, is_enriched, is_traced, has_contracts, all_required_done
        )

        # Voice summary
        voice_summary = self._build_voice_summary(
            prop.id, prop.address, stage_label, health, health_reason,
            days_in_stage, next_action,
        )

        return {
            "property_id": prop.id,
            "address": prop.address,
            "stage": status.value,
            "stage_label": stage_label,
            "stage_index": stage_index,
            "total_stages": len(STAGE_ORDER),
            "checklist": checklist,
            "health": health,
            "health_reason": health_reason,
            "days_in_stage": round(days_in_stage, 1),
            "stale_threshold_days": threshold,
            "days_since_activity": round(days_since_activity, 1),
            "next_action": next_action,
            "deal_score": prop.deal_score,
            "score_grade": prop.score_grade,
            "voice_summary": voice_summary,
        }

    # ── Health logic ──

    def _compute_health(
        self,
        status: PropertyStatus,
        days_in_stage: float,
        threshold: int,
        is_enriched: bool,
        is_traced: bool,
        has_contracts: bool,
        required_count: int,
        all_required_done: bool,
    ) -> tuple[str, Optional[str]]:
        if status == PropertyStatus.COMPLETE:
            return "healthy", None

        # Blocked: can't advance because of a structural issue
        if status == PropertyStatus.WAITING_FOR_CONTRACTS and required_count == 0:
            return "blocked", "No required contracts to complete — mark contracts as required or attach new ones"
        if status == PropertyStatus.WAITING_FOR_CONTRACTS and days_in_stage >= threshold:
            unsigned = required_count - (required_count if all_required_done else 0)
            return "blocked", f"{unsigned} required contract{'s' if unsigned != 1 else ''} still unsigned after {days_in_stage:.0f} days"

        # Stale: sitting too long
        if days_in_stage >= threshold:
            return "stale", f"In '{STAGE_LABELS.get(status, status.value)}' for {days_in_stage:.0f} days (threshold: {threshold})"

        return "healthy", None

    # ── Next action ──

    def _compute_next_action(
        self,
        status: PropertyStatus,
        is_enriched: bool,
        is_traced: bool,
        has_contracts: bool,
        all_required_done: bool,
    ) -> str:
        if status == PropertyStatus.COMPLETE:
            return "All steps complete"

        if not is_enriched:
            return NEXT_ACTIONS["enriched"]
        if not is_traced:
            return NEXT_ACTIONS["researched"]
        if not has_contracts:
            return NEXT_ACTIONS["contracts_attached"]
        if not all_required_done:
            return NEXT_ACTIONS["contracts_completed"]

        return "All steps complete"

    # ── Voice summary ──

    def _build_voice_summary(
        self,
        prop_id: int,
        address: str,
        stage_label: str,
        health: str,
        health_reason: Optional[str],
        days_in_stage: float,
        next_action: str,
    ) -> str:
        addr = address or f"property {prop_id}"

        if health == "healthy":
            if stage_label == "Complete":
                return f"Property #{prop_id} at {addr} is complete. All pipeline steps are done."
            return f"Property #{prop_id} at {addr} is {stage_label} and healthy. Next step: {next_action.lower()}."
        elif health == "stale":
            return f"Property #{prop_id} at {addr} has been in {stage_label} for {days_in_stage:.0f} days. {next_action}."
        else:  # blocked
            return f"Property #{prop_id} at {addr} is blocked at {stage_label}. {health_reason}."

    # ── Batch queries ──

    def _batch_last_activities(self, db: Session, prop_ids: list[int]) -> dict[int, datetime]:
        if not prop_ids:
            return {}
        rows = (
            db.query(
                ConversationHistory.property_id,
                func.max(ConversationHistory.created_at).label("last_at"),
            )
            .filter(ConversationHistory.property_id.in_(prop_ids))
            .group_by(ConversationHistory.property_id)
            .all()
        )
        return {r.property_id: r.last_at for r in rows}

    def _batch_contract_aggregates(
        self, db: Session, prop_ids: list[int]
    ) -> dict[int, tuple[int, int, int]]:
        """Returns {property_id: (total_contracts, required_count, completed_required)}."""
        if not prop_ids:
            return {}
        rows = (
            db.query(
                Contract.property_id,
                func.count(Contract.id).label("total"),
                func.sum(case((Contract.is_required.is_(True), 1), else_=0)).label("required"),
                func.sum(
                    case(
                        (and_(Contract.is_required.is_(True), Contract.status == ContractStatus.COMPLETED), 1),
                        else_=0,
                    )
                ).label("completed"),
            )
            .filter(Contract.property_id.in_(prop_ids))
            .group_by(Contract.property_id)
            .all()
        )
        return {r.property_id: (r.total, int(r.required or 0), int(r.completed or 0)) for r in rows}

    def _batch_enrichment_check(self, db: Session, prop_ids: list[int]) -> set[int]:
        if not prop_ids:
            return set()
        rows = (
            db.query(ZillowEnrichment.property_id)
            .filter(ZillowEnrichment.property_id.in_(prop_ids))
            .all()
        )
        return {r.property_id for r in rows}

    def _batch_skip_trace_check(self, db: Session, prop_ids: list[int]) -> set[int]:
        if not prop_ids:
            return set()
        rows = (
            db.query(SkipTrace.property_id)
            .filter(SkipTrace.property_id.in_(prop_ids))
            .distinct()
            .all()
        )
        return {r.property_id for r in rows}


heartbeat_service = HeartbeatService()
