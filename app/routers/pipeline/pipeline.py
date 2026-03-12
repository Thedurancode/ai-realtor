"""Pipeline automation router — status and manual trigger."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.pipeline_automation_service import pipeline_automation_service

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/status")
def get_pipeline_status(db: Session = Depends(get_db)):
    """Get recent auto-transitions and pipeline status."""
    from app.models.notification import Notification, NotificationType
    from sqlalchemy import desc

    recent = (
        db.query(Notification)
        .filter(Notification.type == NotificationType.PIPELINE_AUTO_ADVANCE)
        .order_by(desc(Notification.created_at))
        .limit(20)
        .all()
    )

    transitions = []
    for n in recent:
        transitions.append({
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "property_id": n.property_id,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        })

    return {
        "recent_transitions": transitions,
        "total_recent": len(transitions),
    }


@router.post("/check")
def trigger_pipeline_check(db: Session = Depends(get_db)):
    """Manually trigger a pipeline automation check."""
    result = pipeline_automation_service.run_pipeline_check(db)
    return result
