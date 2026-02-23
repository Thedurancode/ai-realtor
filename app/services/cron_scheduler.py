"""Cron-based task scheduler with retry logic.

Replaces simple loop-based scheduler with professional cron expressions
and automatic retry with exponential backoff.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Callable, Awaitable, Dict, Any
from enum import Enum

from croniter import croniter
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.scheduled_task import ScheduledTask, TaskStatus, TaskType

logger = logging.getLogger(__name__)


class CronScheduler:
    """Professional cron-based task scheduler."""

    def __init__(self, db: Session = None):
        """Initialize scheduler.

        Args:
            db: Database session (creates new one if None)
        """
        self.db = db or SessionLocal()
        self.running = False
        self.task_handlers: Dict[str, Callable] = {}

        # Register built-in task handlers
        self._register_builtin_handlers()

    def _register_builtin_handlers(self):
        """Register built-in task handlers."""
        from app.services.cron_tasks import (
            heartbeat_cycle_handler,
            portfolio_scan_handler,
            market_intelligence_handler,
            relationship_health_handler,
            predictive_insights_handler
        )

        self.task_handlers = {
            "heartbeat_cycle": heartbeat_cycle_handler,
            "portfolio_scan": portfolio_scan_handler,
            "market_intelligence": market_intelligence_handler,
            "relationship_health": relationship_health_handler,
            "predictive_insights": predictive_insights_handler,
        }

    def register_handler(self, name: str, handler: Callable):
        """Register a custom task handler.

        Args:
            name: Task name
            handler: Async function to execute
        """
        self.task_handlers[name] = handler
        logger.info(f"Registered task handler: {name}")

    async def start(self):
        """Start scheduler loop."""
        self.running = True
        logger.info("Cron scheduler started")

        while self.running:
            try:
                await self._check_due_tasks()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)  # Wait before retry

    def stop(self):
        """Stop scheduler loop."""
        self.running = False
        logger.info("Cron scheduler stopped")

    async def _check_due_tasks(self):
        """Find and execute due tasks."""
        now = datetime.now(timezone.utc)

        try:
            # Get due tasks
            due_tasks = self.db.query(ScheduledTask).filter(
                ScheduledTask.enabled == True,
                ScheduledTask.next_run_at <= now,
                ScheduledTask.status.in_([TaskStatus.SCHEDULED, TaskStatus.RETRYING])
            ).all()

            if due_tasks:
                logger.info(f"Found {len(due_tasks)} due tasks")

            # Execute tasks concurrently
            tasks = [
                self._execute_task(task)
                for task in due_tasks
            ]

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Error checking due tasks: {e}")

    async def _execute_task(self, task: ScheduledTask):
        """Execute a single task with retry logic.

        Args:
            task: ScheduledTask to execute
        """
        logger.info(f"Executing task: {task.name}")

        try:
            # Get handler
            handler = self.task_handlers.get(task.handler_name)
            if not handler:
                logger.error(f"No handler found for: {task.handler_name}")
                await self._mark_failed(task, f"No handler found: {task.handler_name}")
                return

            # Execute handler
            start_time = datetime.now(timezone.utc)

            if asyncio.iscoroutinefunction(handler):
                result = await handler(self.db, task.metadata or {})
            else:
                result = handler(self.db, task.metadata or {})

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            # Mark as completed
            task.last_run_at = start_time
            task.status = TaskStatus.COMPLETED
            task.next_run_at = self._calculate_next_run(task.cron_expression)
            task.retry_count = 0
            task.last_result = {"success": True, "duration_seconds": duration}

            self.db.commit()

            logger.info(
                f"Task completed: {task.name} "
                f"(duration: {duration:.2f}s, next_run: {task.next_run_at})"
            )

        except Exception as e:
            logger.error(f"Task execution failed: {task.name} - {e}")

            # Retry logic with exponential backoff
            task.retry_count += 1

            if task.retry_count < task.max_retries:
                # Calculate backoff: 2^retry_count minutes
                backoff_minutes = 2 ** task.retry_count
                next_run = datetime.now(timezone.utc) + timedelta(minutes=backoff_minutes)

                task.next_run_at = next_run
                task.status = TaskStatus.RETRYING
                task.last_result = {
                    "success": False,
                    "error": str(e),
                    "retry_count": task.retry_count
                }

                logger.info(
                    f"Task will retry in {backoff_minutes} minutes "
                    f"(attempt {task.retry_count}/{task.max_retries})"
                )
            else:
                # Max retries exceeded
                task.status = TaskStatus.FAILED
                task.last_result = {
                    "success": False,
                    "error": str(e),
                    "failed_after": task.retry_count
                }

                logger.error(f"Task failed permanently after {task.retry_count} retries: {task.name}")

            self.db.commit()

    async def _mark_failed(self, task: ScheduledTask, reason: str):
        """Mark task as failed.

        Args:
            task: Task to mark
            reason: Failure reason
        """
        task.status = TaskStatus.FAILED
        task.last_result = {"success": False, "error": reason}
        self.db.commit()

    def _calculate_next_run(self, cron_expression: str) -> datetime:
        """Calculate next run time from cron expression.

        Args:
            cron_expression: Cron expression (e.g., "0 8 * * *")

        Returns:
            Next run datetime
        """
        try:
            cron = croniter(cron_expression, datetime.now(timezone.utc))
            return cron.get_next(datetime)
        except Exception as e:
            logger.error(f"Invalid cron expression '{cron_expression}': {e}")
            # Default to 1 hour from now
            return datetime.now(timezone.utc) + timedelta(hours=1)

    async def schedule_task(
        self,
        name: str,
        handler_name: str,
        cron_expression: str,
        metadata: Optional[Dict[str, Any]] = None,
        task_type: TaskType = TaskType.RECURRING,
        enabled: bool = True
    ) -> ScheduledTask:
        """Schedule a new cron task.

        Args:
            name: Task name (unique)
            handler_name: Name of registered handler
            cron_expression: Cron expression
            metadata: Optional metadata for handler
            task_type: Task type
            enabled: Whether to enable immediately

        Returns:
            Created task
        """
        # Check if handler exists
        if handler_name not in self.task_handlers:
            raise ValueError(f"Unknown handler: {handler_name}")

        # Calculate next run time
        next_run = self._calculate_next_run(cron_expression)

        # Create task
        task = ScheduledTask(
            name=name,
            handler_name=handler_name,
            cron_expression=cron_expression,
            next_run_at=next_run,
            metadata=metadata or {},
            task_type=task_type,
            enabled=enabled,
            status=TaskStatus.SCHEDULED if enabled else TaskStatus.CANCELLED
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        logger.info(
            f"Scheduled task '{name}' with handler '{handler_name}', "
            f"cron: {cron_expression}, next_run: {next_run}"
        )

        return task

    async def run_task_now(self, task_id: int) -> bool:
        """Run a task immediately (manual trigger).

        Args:
            task_id: Task ID

        Returns:
            True if task was found and executed
        """
        task = self.db.query(ScheduledTask).filter(
            ScheduledTask.id == task_id
        ).first()

        if not task:
            logger.warning(f"Task not found: {task_id}")
            return False

        logger.info(f"Manual trigger for task: {task.name}")

        await self._execute_task(task)

        return True

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status.

        Returns:
            Scheduler status info
        """
        total_tasks = self.db.query(ScheduledTask).count()
        enabled_tasks = self.db.query(ScheduledTask).filter(
            ScheduledTask.enabled == True
        ).count()

        scheduled = self.db.query(ScheduledTask).filter(
            ScheduledTask.status == TaskStatus.SCHEDULED
        ).count()

        retrying = self.db.query(ScheduledTask).filter(
            ScheduledTask.status == TaskStatus.RETRYING
        ).count()

        failed = self.db.query(ScheduledTask).filter(
            ScheduledTask.status == TaskStatus.FAILED
        ).count()

        return {
            "running": self.running,
            "total_tasks": total_tasks,
            "enabled_tasks": enabled_tasks,
            "scheduled": scheduled,
            "retrying": retrying,
            "failed": failed,
            "registered_handlers": list(self.task_handlers.keys())
        }


# Global scheduler instance
cron_scheduler = CronScheduler()


# Common cron expressions
CRON_EXPRESSIONS = {
    "every_minute": "* * * * *",
    "every_5_minutes": "*/5 * * * *",
    "every_15_minutes": "*/15 * * * *",
    "every_30_minutes": "*/30 * * * *",
    "every_hour": "0 * * * *",
    "every_6_hours": "0 */6 * * *",
    "daily_midnight": "0 0 * * *",
    "daily_8am": "0 8 * * *",
    "daily_6pm": "0 18 * * *",
    "weekdays_8am": "0 8 * * 1-5",
    "weekends_10am": "0 10 * * 6,0",
    "weekly_monday_8am": "0 8 * * 1",
    "monthly_1st_8am": "0 8 1 * *",
    "hourly": "0 * * * *",
}
