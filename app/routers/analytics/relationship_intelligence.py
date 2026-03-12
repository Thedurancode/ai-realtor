"""Relationship Intelligence API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.relationship_intelligence_service import relationship_intelligence_service

router = APIRouter(prefix="/relationships", tags=["relationship-intelligence"])


@router.get("/contact/{contact_id}/health")
async def score_relationship_health(contact_id: int, db: Session = Depends(get_db)):
    """Get relationship health score for a contact.

    Returns health score (0-100), trend, sentiment analysis,
    and recommended next actions.
    """
    result = await relationship_intelligence_service.score_relationship_health(db, contact_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/contact/{contact_id}/best-method")
async def predict_best_contact_method(
    contact_id: int,
    message_type: str = "check_in",
    db: Session = Depends(get_db),
):
    """Predict the best contact method: phone, email, or text.

    Analyzes historical response rates and sentiment by method.
    """
    result = await relationship_intelligence_service.predict_best_contact_method(
        db, contact_id, message_type
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/contact/{contact_id}/sentiment")
async def analyze_contact_sentiment(
    contact_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """Analyze sentiment trend for a contact over time.

    Useful for detecting cooling relationships, measuring campaign
    effectiveness, and identifying upset contacts.
    """
    result = await relationship_intelligence_service.analyze_contact_sentiment(
        db, contact_id, days
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
