"""Property scoring router — multi-dimensional deal quality scoring."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.rate_limit import limiter, premium_limit
from app.services.property_scoring_service import property_scoring_service

router = APIRouter(prefix="/scoring", tags=["scoring"])


class BulkScoreRequest(BaseModel):
    property_ids: list[int] | None = None
    filters: dict | None = None


@router.post("/property/{property_id}")
@limiter.limit(limit_value=premium_limit("medium"))
def score_property(
    request: Request,
    property_id: int,
    db: Session = Depends(get_db),
):
    """Score a single property (recalculates and saves)."""
    return property_scoring_service.score_property(db, property_id)


@router.get("/property/{property_id}")
def get_score_breakdown(
    property_id: int,
    db: Session = Depends(get_db),
):
    """Get stored score breakdown for a property (no recalculation)."""
    from app.models.property import Property
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        return {"error": f"Property {property_id} not found"}

    if prop.deal_score is None:
        return {"error": "Property has not been scored yet. Use POST to score."}

    return {
        "property_id": prop.id,
        "address": prop.address,
        "score": prop.deal_score,
        "grade": prop.score_grade,
        "breakdown": prop.score_breakdown,
    }


@router.post("/bulk")
@limiter.limit(limit_value=premium_limit("high"))
def bulk_score(
    request: Request,
    body: BulkScoreRequest,
    db: Session = Depends(get_db),
):
    """Score multiple properties."""
    return property_scoring_service.bulk_score(
        db,
        property_ids=body.property_ids,
        filters=body.filters,
    )


@router.get("/top")
def get_top_properties(
    limit: int = Query(10, ge=1, le=100),
    min_score: float = Query(0, ge=0, le=100),
    db: Session = Depends(get_db),
):
    """Get top-scored properties."""
    return property_scoring_service.get_top_properties(db, limit=limit, min_score=min_score)
