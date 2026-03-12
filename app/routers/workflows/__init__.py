"""Workflow / scheduling domain routers."""

from app.routers.workflows.workflows import router as workflows_router
from app.routers.workflows.scheduled_tasks import router as scheduled_tasks_router
from app.routers.workflows.daily_digest import router as daily_digest_router
from app.routers.workflows.follow_up_sequences import router as follow_up_sequences_router
from app.routers.workflows.follow_up_sequences import _queue_router
from app.routers.workflows.morning_brief import router as morning_brief_router
from app.routers.workflows import cron_scheduler

__all__ = [
    "workflows_router", "scheduled_tasks_router", "daily_digest_router",
    "follow_up_sequences_router", "_queue_router", "morning_brief_router",
    "cron_scheduler",
]
