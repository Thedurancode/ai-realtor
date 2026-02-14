"""Insights router — predictive follow-up alerts."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.insights_service import insights_service

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/")
def get_insights(
    priority: Optional[str] = Query(None, description="Filter by priority: urgent, high, medium, low"),
    db: Session = Depends(get_db),
):
    result = insights_service.get_insights(db)
    if priority:
        filtered = result.get(priority, [])
        return {
            "total_alerts": len(filtered),
            "priority": priority,
            "alerts": filtered,
            "voice_summary": result["voice_summary"],
        }
    return result


@router.get("/property/{property_id}")
def get_property_insights(property_id: int, db: Session = Depends(get_db)):
    return insights_service.get_insights(db, property_id=property_id)
