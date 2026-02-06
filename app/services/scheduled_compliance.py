"""
Scheduled Compliance Check

Runs a compliance check automatically after a configurable delay
following property creation.
"""
import asyncio
import logging

from app.database import SessionLocal
from app.models.property import Property
from app.services.compliance_engine import compliance_engine

logger = logging.getLogger(__name__)

COMPLIANCE_DELAY_SECONDS = 20 * 60  # 20 minutes


async def schedule_compliance_check(property_id: int, delay_seconds: int = COMPLIANCE_DELAY_SECONDS):
    """
    Wait for delay_seconds then run a compliance check on the property.
    Uses its own DB session since the original request session will be closed.
    """
    logger.info(f"Compliance check scheduled for property {property_id} in {delay_seconds}s")
    await asyncio.sleep(delay_seconds)

    db = SessionLocal()
    try:
        property = db.query(Property).filter(Property.id == property_id).first()
        if not property:
            logger.warning(f"Scheduled compliance: property {property_id} not found (deleted?)")
            return

        logger.info(f"Running scheduled compliance check for property {property_id} ({property.address})")
        check = await compliance_engine.run_compliance_check(
            db=db,
            property=property,
            check_type="full",
        )

        logger.info(
            f"Scheduled compliance check complete for property {property_id}: "
            f"status={check.status}, passed={check.passed_count}, "
            f"failed={check.failed_count}, warnings={check.warning_count}"
        )

        # Log activity event
        try:
            from app.models.activity_event import ActivityEvent
            activity = ActivityEvent(
                event_type="compliance_auto_check",
                tool_name="scheduled_compliance",
                user_source="System (Auto)",
                description=(
                    f"Auto compliance check for {property.address}: "
                    f"{check.passed_count} passed, {check.failed_count} failed, "
                    f"{check.warning_count} warnings"
                ),
                status="success" if check.status != "failed" else "warning",
                metadata={
                    "property_id": property.id,
                    "property_address": property.address,
                    "check_id": check.id,
                    "check_status": check.status,
                    "passed": check.passed_count,
                    "failed": check.failed_count,
                    "warnings": check.warning_count,
                    "trigger": "scheduled_20min",
                },
            )
            db.add(activity)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to log compliance activity: {e}")

        # Send notification if failed
        if check.status == "failed":
            try:
                from app.services.notification_service import notification_service
                await notification_service.notify_compliance_failed(
                    db=db,
                    manager=None,
                    property_id=property.id,
                    property_address=property.address,
                    failed_count=check.failed_count,
                    check_id=check.id,
                    agent_id=property.agent_id,
                )
            except Exception as e:
                logger.warning(f"Failed to send compliance notification: {e}")

    except Exception as e:
        logger.error(f"Scheduled compliance check failed for property {property_id}: {e}")
    finally:
        db.close()
