"""Operations domain routers — bulk, approval, scrubbing, etc."""

from app.routers.operations.bulk import router as bulk_router
from app.routers.operations.approval import router as approval_router
from app.routers.operations.credential_scrubbing import router as credential_scrubbing_router
from app.routers.operations.observer import router as observer_router
from app.routers.operations.email_triage import router as email_triage_router

__all__ = [
    "bulk_router", "approval_router", "credential_scrubbing_router",
    "observer_router", "email_triage_router",
]
