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
    """Auto-advance property status through the pipeline stages.

    Pipeline: NEW_PROPERTY → ENRICHED → RESEARCHED → WAITING_FOR_CONTRACTS → COMPLETE
    """

    MANUAL_GRACE_HOURS = 24

    def run_pipeline_check(self, db: Session) -> dict:
        """Check all non-complete properties for auto-transitions."""
        properties = db.query(Property).filter(
            Property.status != PropertyStatus.COMPLETE
        ).all()

        transitions = []
        for prop in properties:
            if self._should_skip(db, prop):
                continue

            new_status = None
            reason = ""

            if prop.status == PropertyStatus.NEW_PROPERTY:
                if self._check_new_to_enriched(db, prop):
                    new_status = PropertyStatus.ENRICHED
                    reason = "Zillow enrichment data available"
            elif prop.status == PropertyStatus.ENRICHED:
                if self._check_enriched_to_researched(db, prop):
                    new_status = PropertyStatus.RESEARCHED
                    reason = "Skip trace completed"
            elif prop.status == PropertyStatus.RESEARCHED:
                if self._check_researched_to_waiting(db, prop):
                    new_status = PropertyStatus.WAITING_FOR_CONTRACTS
                    reason = "Contract(s) attached"
            elif prop.status == PropertyStatus.WAITING_FOR_CONTRACTS:
                if self._check_waiting_to_complete(db, prop):
                    new_status = PropertyStatus.COMPLETE
                    reason = "All required contracts completed"

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

    def _check_new_to_enriched(self, db: Session, prop: Property) -> bool:
        """NEW_PROPERTY → ENRICHED: ZillowEnrichment exists."""
        return db.query(ZillowEnrichment).filter(
            ZillowEnrichment.property_id == prop.id
        ).first() is not None

    def _check_enriched_to_researched(self, db: Session, prop: Property) -> bool:
        """ENRICHED → RESEARCHED: SkipTrace exists."""
        return db.query(SkipTrace).filter(
            SkipTrace.property_id == prop.id
        ).first() is not None

    def _check_researched_to_waiting(self, db: Session, prop: Property) -> bool:
        """RESEARCHED → WAITING_FOR_CONTRACTS: at least 1 contract attached."""
        return db.query(Contract).filter(
            Contract.property_id == prop.id
        ).first() is not None

    def _check_waiting_to_complete(self, db: Session, prop: Property) -> bool:
        """WAITING_FOR_CONTRACTS → COMPLETE: ALL required contracts COMPLETED."""
        required_contracts = db.query(Contract).filter(
            Contract.property_id == prop.id,
            Contract.is_required.is_(True),
        ).all()

        if not required_contracts:
            return False

        return all(c.status == ContractStatus.COMPLETED for c in required_contracts)

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
