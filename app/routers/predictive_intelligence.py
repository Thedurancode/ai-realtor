"""Predictive Intelligence API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.predictive_intelligence_service import predictive_intelligence_service
from app.services.learning_system_service import learning_system_service
from app.models.deal_outcome import OutcomeStatus

router = APIRouter(prefix="/predictive", tags=["predictive-intelligence"])


@router.post("/property/{property_id}/predict")
async def predict_property_outcome(property_id: int, db: Session = Depends(get_db)):
    """Predict closing probability and recommend actions for a property."""
    result = await predictive_intelligence_service.predict_property_outcome(db, property_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/property/{property_id}/recommend")
async def recommend_next_action(
    property_id: int,
    context: str | None = None,
    db: Session = Depends(get_db),
):
    """Get AI-recommended next action for a property."""
    result = await predictive_intelligence_service.recommend_next_action(
        db, property_id, context
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/batch/predict")
async def batch_predict_outcomes(
    property_ids: list[int] | None = None,
    db: Session = Depends(get_db),
):
    """Predict outcomes for multiple properties, sorted by priority (lowest probability first)."""
    result = await predictive_intelligence_service.batch_predict_outcomes(db, property_ids)
    return result


@router.post("/outcomes/{property_id}/record")
async def record_deal_outcome(
    property_id: int,
    status: OutcomeStatus,
    final_sale_price: float | None = None,
    outcome_reason: str | None = None,
    lessons_learned: str | None = None,
    db: Session = Depends(get_db),
):
    """Record actual deal outcome for learning.

    Call this when a deal is won, lost, or withdrawn.
    """
    result = await learning_system_service.record_outcome(
        db,
        property_id,
        status,
        final_sale_price,
        outcome_reason,
        lessons_learned,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/agents/{agent_id}/patterns")
async def get_agent_success_patterns(
    agent_id: int,
    period: str = "month",
    db: Session = Depends(get_db),
):
    """Get agent's success patterns from historical performance.

    Period options: week, month, quarter, year
    """
    result = await learning_system_service.get_agent_success_patterns(
        db, agent_id, period
    )
    return result


@router.get("/accuracy")
async def evaluate_prediction_accuracy(
    agent_id: int | None = None,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """Evaluate prediction accuracy over time.

    Returns MAE, directional accuracy, and confidence calibration.
    """
    result = await learning_system_service.evaluate_prediction_accuracy(
        db, agent_id, days
    )
    return result
