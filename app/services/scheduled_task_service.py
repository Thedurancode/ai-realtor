"""CRUD service for scheduled tasks."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.scheduled_task import ScheduledTask, TaskStatus, TaskType


class ScheduledTaskService:

    def create_task(
        self,
        db: Session,
        title: str,
        task_type: str = "reminder",
        scheduled_at: datetime = None,
        description: str = None,
        property_id: int = None,
        action: str = None,
        action_params: dict = None,
        repeat_interval_hours: int = None,
        created_by: str = "voice",
    ) -> ScheduledTask:
        task = ScheduledTask(
            task_type=TaskType(task_type),
            status=TaskStatus.PENDING,
            title=title,
            description=description,
            scheduled_at=scheduled_at or datetime.now(timezone.utc),
            repeat_interval_hours=repeat_interval_hours,
            next_run_at=scheduled_at or datetime.now(timezone.utc),
            property_id=property_id,
            action=action,
            action_params=action_params,
            created_by=created_by,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def list_tasks(
        self,
        db: Session,
        status: Optional[str] = None,
        property_id: Optional[int] = None,
        limit: int = 50,
    ) -> list[ScheduledTask]:
        query = db.query(ScheduledTask).order_by(ScheduledTask.scheduled_at.asc())
        if status:
            query = query.filter(ScheduledTask.status == TaskStatus(status))
        if property_id:
            query = query.filter(ScheduledTask.property_id == property_id)
        return query.limit(limit).all()

    def get_task(self, db: Session, task_id: int) -> Optional[ScheduledTask]:
        return db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()

    def cancel_task(self, db: Session, task_id: int) -> Optional[ScheduledTask]:
        task = self.get_task(db, task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            db.commit()
            db.refresh(task)
        return task

    def get_due_tasks(self, db: Session) -> list[ScheduledTask]:
        now = datetime.now(timezone.utc)
        return (
            db.query(ScheduledTask)
            .filter(
                ScheduledTask.status == TaskStatus.PENDING,
                ScheduledTask.scheduled_at <= now,
            )
            .order_by(ScheduledTask.scheduled_at.asc())
            .all()
        )

    def mark_running(self, db: Session, task: ScheduledTask):
        task.status = TaskStatus.RUNNING
        db.commit()

    def mark_completed(self, db: Session, task: ScheduledTask):
        task.status = TaskStatus.COMPLETED
        task.last_run_at = datetime.now(timezone.utc)
        db.commit()

    def mark_failed(self, db: Session, task: ScheduledTask):
        task.status = TaskStatus.FAILED
        db.commit()

    def create_next_occurrence(self, db: Session, task: ScheduledTask) -> Optional[ScheduledTask]:
        if not task.repeat_interval_hours:
            return None
        next_at = datetime.now(timezone.utc) + timedelta(hours=task.repeat_interval_hours)
        return self.create_task(
            db=db,
            title=task.title,
            task_type=task.task_type.value,
            scheduled_at=next_at,
            description=task.description,
            property_id=task.property_id,
            action=task.action,
            action_params=task.action_params,
            repeat_interval_hours=task.repeat_interval_hours,
            created_by=task.created_by,
        )


scheduled_task_service = ScheduledTaskService()
