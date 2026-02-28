"""Background task runner — checks for due scheduled tasks every minute."""

import asyncio
import logging
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models.scheduled_task import TaskType

logger = logging.getLogger(__name__)

TASK_LOOP_INTERVAL = 60  # seconds
PIPELINE_CHECK_INTERVAL = 300  # 5 minutes
ALERT_CHECK_INTERVAL = 600  # 10 minutes

_last_pipeline_check = datetime.now(timezone.utc)
_last_alert_check = datetime.now(timezone.utc)


async def run_task_loop(interval_seconds: int = TASK_LOOP_INTERVAL):
    """Background loop that checks for due tasks."""
    global _last_pipeline_check, _last_alert_check
    from app.services.scheduled_task_service import scheduled_task_service
    from app.services.pipeline_automation_service import pipeline_automation_service

    print(f"→ Task runner loop started (interval={interval_seconds}s)")
    logger.info("Scheduled task runner started (interval=%ds)", interval_seconds)

    iteration = 0
    while True:
        iteration += 1
        print(f"→ Task loop iteration #{iteration} at {datetime.now(timezone.utc)}")
        await asyncio.sleep(interval_seconds)
        await asyncio.sleep(interval_seconds)
        db = SessionLocal()
        try:
            due_tasks = scheduled_task_service.get_due_tasks(db)
            if due_tasks:
                logger.info("Found %d due task(s)", len(due_tasks))
            for task in due_tasks:
                try:
                    await _execute_task(db, task, scheduled_task_service)
                except Exception as e:
                    logger.error("Task %d failed: %s", task.id, e)
                    scheduled_task_service.mark_failed(db, task)

            # Pipeline automation check every 5 minutes
            now = datetime.now(timezone.utc)
            if (now - _last_pipeline_check).total_seconds() >= PIPELINE_CHECK_INTERVAL:
                try:
                    result = pipeline_automation_service.run_pipeline_check(db)
                    if result.get("transitioned", 0) > 0:
                        logger.info("Pipeline check: %d transitions", result["transitioned"])
                except Exception as e:
                    logger.error("Pipeline check error: %s", e)
                _last_pipeline_check = now

            # Analytics alert check every 10 minutes
            if (now - _last_alert_check).total_seconds() >= ALERT_CHECK_INTERVAL:
                try:
                    from app.services.analytics_alert_service import AnalyticsAlertService
                    alert_service = AnalyticsAlertService(db)
                    triggers = alert_service.check_alert_rules()
                    if triggers:
                        logger.info("Alert check: %d alerts triggered", len(triggers))
                        for trigger in triggers:
                            logger.info("  - Triggered: %s (rule %d)", trigger.message, trigger.alert_rule_id)
                except Exception as e:
                    logger.error("Alert check error: %s", e)
                _last_alert_check = now
        except Exception as e:
            logger.error("Task loop error: %s", e)
        finally:
            db.close()


async def _execute_task(db, task, service):
    """Execute a single scheduled task."""
    service.mark_running(db, task)

    if task.task_type == TaskType.REMINDER:
        _create_notification(db, task)
    elif task.task_type == TaskType.FOLLOW_UP:
        _create_notification(db, task, notification_type="follow_up_due", priority="high")
    elif task.task_type == TaskType.CONTRACT_CHECK:
        _create_notification(db, task, notification_type="contract_deadline", priority="high")
    elif task.task_type == TaskType.RECURRING:
        if task.action == "generate_daily_digest":
            await _execute_daily_digest(db, task)
        else:
            _create_notification(db, task)

    service.mark_completed(db, task)

    # Create next occurrence for recurring tasks
    if task.repeat_interval_hours:
        next_task = service.create_next_occurrence(db, task)
        if next_task:
            logger.info("Created next occurrence: task %d at %s", next_task.id, next_task.scheduled_at)


def _create_notification(db, task, notification_type="scheduled_task", priority="medium"):
    """Create a notification from a scheduled task."""
    try:
        from app.models.notification import Notification, NotificationType, NotificationPriority

        type_map = {
            "scheduled_task": NotificationType.SCHEDULED_TASK,
            "follow_up_due": NotificationType.FOLLOW_UP_DUE,
            "contract_deadline": NotificationType.CONTRACT_DEADLINE,
        }
        priority_map = {
            "low": NotificationPriority.LOW,
            "medium": NotificationPriority.MEDIUM,
            "high": NotificationPriority.HIGH,
            "urgent": NotificationPriority.URGENT,
        }

        notif = Notification(
            type=type_map.get(notification_type, NotificationType.GENERAL),
            priority=priority_map.get(priority, NotificationPriority.MEDIUM),
            title=task.title,
            message=task.description or task.title,
            property_id=task.property_id,
            auto_dismiss_seconds=15,
        )
        db.add(notif)
        db.commit()
        logger.info("Notification created for task %d: %s", task.id, task.title)
    except Exception as e:
        logger.warning("Failed to create notification for task %d: %s", task.id, e)


async def _execute_daily_digest(db, task):
    """Generate a daily digest via the digest service."""
    try:
        from app.services.daily_digest_service import daily_digest_service
        digest = await daily_digest_service.generate_digest(db)
        logger.info("Daily digest generated: %d highlights", len(digest.get("key_highlights", [])))
    except Exception as e:
        logger.error("Daily digest generation failed: %s", e)
