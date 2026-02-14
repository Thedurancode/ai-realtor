"""Pipeline automation — auto-advance property status based on activity."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.contract import Contract, ContractStatus
from app.models.conversation_history import ConversationHistory
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.models.property import Property, PropertyStatus
from app.models.skip_trace import SkipTrace
from app.models.zillow_enrichment import ZillowEnrichment

logger = logging.getLogger(__name__)


class PipelineAutomationService:
    """Auto-advance property status based on enrichment, contracts, and activity."""

    STALE_DAYS = 30
    MANUAL_GRACE_HOURS = 24

    def run_pipeline_check(self, db: Session) -> dict:
        """Check all properties for auto-transitions."""
        properties = db.query(Property).filter(
            Property.status.in_([PropertyStatus.AVAILABLE, PropertyStatus.PENDING])
        ).all()

        transitions = []
        for prop in properties:
            if self._should_skip(db, prop):
                continue

            new_status = None
            reason = ""

            if prop.status == PropertyStatus.AVAILABLE:
                if self._check_available_to_pending(db, prop):
                    new_status = PropertyStatus.PENDING
                    reason = "Enrichment + skip trace + contract(s) attached"
                elif self._check_stale(db, prop):
                    new_status = PropertyStatus.OFF_MARKET
                    reason = f"No activity in {self.STALE_DAYS}+ days"
            elif prop.status == PropertyStatus.PENDING:
                if self._check_pending_to_sold(db, prop):
                    new_status = PropertyStatus.SOLD
                    reason = "All required contracts completed"
                elif self._check_stale(db, prop):
                    new_status = PropertyStatus.OFF_MARKET
                    reason = f"No activity in {self.STALE_DAYS}+ days"

            if new_status:
                self._transition(db, prop, new_status, reason)
                transitions.append({
                    "property_id": prop.id,
                    "address": prop.address,
                    "from_status": prop.status.value if hasattr(prop.status, 'value') else str(prop.status),
                    "to_status": new_status.value,
                    "reason": reason,
                })

        result = {
            "checked": len(properties),
            "transitioned": len(transitions),
            "transitions": transitions,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

        if transitions:
            logger.info("Pipeline check: %d transitions out of %d properties", len(transitions), len(properties))
        return result

    def _should_skip(self, db: Session, prop: Property) -> bool:
        """Skip if status was manually changed in last 24h."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.MANUAL_GRACE_HOURS)
        recent_manual = (
            db.query(ConversationHistory)
            .filter(
                ConversationHistory.property_id == prop.id,
                ConversationHistory.tool_name == "update_property",
                ConversationHistory.created_at >= cutoff,
            )
            .first()
        )
        # Also check for input containing "status" to be specific
        if recent_manual and recent_manual.input_summary and "status" in recent_manual.input_summary.lower():
            return True
        return False

    def _check_available_to_pending(self, db: Session, prop: Property) -> bool:
        """AVAILABLE → PENDING: has enrichment + skip trace + at least 1 contract."""
        has_enrichment = db.query(ZillowEnrichment).filter(
            ZillowEnrichment.property_id == prop.id
        ).first() is not None

        has_skip_trace = db.query(SkipTrace).filter(
            SkipTrace.property_id == prop.id
        ).first() is not None

        has_contract = db.query(Contract).filter(
            Contract.property_id == prop.id
        ).first() is not None

        return has_enrichment and has_skip_trace and has_contract

    def _check_pending_to_sold(self, db: Session, prop: Property) -> bool:
        """PENDING → SOLD: ALL required contracts have status COMPLETED."""
        required_contracts = db.query(Contract).filter(
            Contract.property_id == prop.id,
            Contract.is_required.is_(True),
        ).all()

        if not required_contracts:
            return False

        return all(c.status == ContractStatus.COMPLETED for c in required_contracts)

    def _check_stale(self, db: Session, prop: Property) -> bool:
        """Check if property has no activity in STALE_DAYS."""
        from sqlalchemy import func
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.STALE_DAYS)

        last_activity = (
            db.query(func.max(ConversationHistory.created_at))
            .filter(ConversationHistory.property_id == prop.id)
            .scalar()
        )
        last_touch = last_activity or prop.created_at
        if last_touch is None:
            return False
        if last_touch.tzinfo is None:
            last_touch = last_touch.replace(tzinfo=timezone.utc)
        return last_touch < cutoff

    def _transition(self, db: Session, prop: Property, new_status: PropertyStatus, reason: str):
        """Update status, create notification, log to conversation_history."""
        old_status = prop.status.value if hasattr(prop.status, 'value') else str(prop.status)
        prop.status = new_status
        db.add(prop)

        # Create notification
        notif = Notification(
            type=NotificationType.PIPELINE_AUTO_ADVANCE,
            priority=NotificationPriority.MEDIUM,
            title=f"Pipeline: {prop.address}",
            message=f"Auto-advanced {old_status} → {new_status.value}. {reason}",
            property_id=prop.id,
            auto_dismiss_seconds=15,
        )
        db.add(notif)

        # Log to conversation history
        history = ConversationHistory(
            session_id="pipeline_automation",
            property_id=prop.id,
            tool_name="pipeline_auto_advance",
            input_summary=f"Auto-check: {reason}",
            output_summary=f"Status changed {old_status} → {new_status.value}",
            success=1,
        )
        db.add(history)

        db.commit()

        # Regenerate recap in background
        try:
            import asyncio
            from app.database import SessionLocal
            from app.services.property_recap_service import property_recap_service

            async def _regen():
                rdb = SessionLocal()
                try:
                    p = rdb.query(Property).filter(Property.id == prop.id).first()
                    if p:
                        await property_recap_service.generate_recap(rdb, p, trigger="pipeline_auto_advance")
                finally:
                    rdb.close()

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_regen())
            except RuntimeError:
                pass
        except Exception as e:
            logger.warning("Failed to schedule recap regeneration for property %d: %s", prop.id, e)

        logger.info("Pipeline: property %d (%s) transitioned %s → %s: %s",
                     prop.id, prop.address, old_status, new_status.value, reason)


pipeline_automation_service = PipelineAutomationService()
