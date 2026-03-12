"""Cron scheduler API router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.database import get_db
from app.services.cron_scheduler import cron_scheduler, CRON_EXPRESSIONS
from app.models.scheduled_task import ScheduledTask

router = APIRouter(prefix="/scheduler", tags=["Cron Scheduler"])


# Request/Response schemas
class ScheduleTaskRequest(BaseModel):
    name: str
    handler_name: str
    cron_expression: str
    metadata: Optional[Dict[str, Any]] = None
    enabled: bool = True


class ScheduleTaskResponse(BaseModel):
    id: int
    name: str
    handler_name: str
    cron_expression: str
    next_run_at: str
    enabled: bool
    status: str


@router.get("/status")
async def get_scheduler_status():
    """Get scheduler status and statistics."""
    status = cron_scheduler.get_status()

    return status


@router.get("/tasks", response_model=List[ScheduleTaskResponse])
async def list_scheduled_tasks(
    enabled: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all scheduled tasks."""
    query = db.query(ScheduledTask)

    if enabled is not None:
        query = query.filter(ScheduledTask.enabled == enabled)

    tasks = query.order_by(ScheduledTask.created_at.desc()).all()

    return [
        ScheduleTaskResponse(
            id=t.id,
            name=t.name,
            handler_name=t.handler_name,
            cron_expression=t.cron_expression,
            next_run_at=t.next_run_at.isoformat() if t.next_run_at else None,
            enabled=t.enabled,
            status=t.status.value
        )
        for t in tasks
    ]


@router.post("/tasks")
async def schedule_task(
    request: ScheduleTaskRequest,
    db: Session = Depends(get_db)
):
    """Schedule a new cron task."""
    try:
        task = await cron_scheduler.schedule_task(
            name=request.name,
            handler_name=request.handler_name,
            cron_expression=request.cron_expression,
            metadata=request.metadata,
            enabled=request.enabled
        )

        return ScheduleTaskResponse(
            id=task.id,
            name=task.name,
            handler_name=task.handler_name,
            cron_expression=task.cron_expression,
            next_run_at=task.next_run_at.isoformat() if task.next_run_at else None,
            enabled=task.enabled,
            status=task.status.value
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/run")
async def run_task_now(
    task_id: int,
    db: Session = Depends(get_db)
):
    """Manually trigger a task to run now."""
    success = await cron_scheduler.run_task_now(task_id)

    if not success:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"message": f"Task {task_id} triggered successfully"}


@router.get("/handlers")
async def list_available_handlers():
    """List all available task handlers."""
    return {
        "handlers": list(cron_scheduler.task_handlers.keys())
    }


@router.get("/cron-expressions")
async def list_common_cron_expressions():
    """List common cron expressions."""
    return CRON_EXPRESSIONS
