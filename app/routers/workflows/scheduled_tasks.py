"""Scheduled tasks router — create, list, cancel reminders and recurring tasks."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.scheduled_task import ScheduledTaskCreate, ScheduledTaskResponse
from app.services.scheduled_task_service import scheduled_task_service

router = APIRouter(prefix="/scheduled-tasks", tags=["scheduled-tasks"])


@router.post("/", response_model=ScheduledTaskResponse)
def create_task(payload: ScheduledTaskCreate, db: Session = Depends(get_db)):
    task = scheduled_task_service.create_task(
        db=db,
        title=payload.title,
        task_type=payload.task_type,
        scheduled_at=payload.scheduled_at,
        description=payload.description,
        property_id=payload.property_id,
        action=payload.action,
        action_params=payload.action_params,
        repeat_interval_hours=payload.repeat_interval_hours,
        created_by=payload.created_by,
    )
    return task


@router.get("/", response_model=list[ScheduledTaskResponse])
def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status: pending, completed, cancelled, failed"),
    property_id: Optional[int] = Query(None, description="Filter by property ID"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    return scheduled_task_service.list_tasks(db, status=status, property_id=property_id, limit=limit)


@router.get("/due", response_model=list[ScheduledTaskResponse])
def list_due_tasks(db: Session = Depends(get_db)):
    return scheduled_task_service.get_due_tasks(db)


@router.get("/{task_id}", response_model=ScheduledTaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = scheduled_task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Scheduled task not found")
    return task


@router.delete("/{task_id}", response_model=ScheduledTaskResponse)
def cancel_task(task_id: int, db: Session = Depends(get_db)):
    task = scheduled_task_service.cancel_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Scheduled task not found or not cancellable")
    return task
