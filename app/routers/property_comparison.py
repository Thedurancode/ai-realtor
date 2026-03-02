"""Property Comparison router — compare 2-5 properties side by side."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.property_comparison_service import compare_properties

router = APIRouter(prefix="/property-comparison", tags=["property-comparison"])


@router.get("/compare")
def compare(
    property_ids: str = Query(
        ...,
        description="Comma-separated property IDs (2-5), e.g. '1,3,7'",
        examples=["1,3,7"],
    ),
    db: Session = Depends(get_db),
):
    """Compare 2-5 properties side by side with deal metrics, enrichment data,
    and a winner recommendation."""
    try:
        ids = [int(x.strip()) for x in property_ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="property_ids must be comma-separated integers")

    try:
        return compare_properties(db, ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/compare")
def compare_post(
    payload: dict,
    db: Session = Depends(get_db),
):
    """Compare properties (POST). Body: {"property_ids": [1, 3, 7]}"""
    ids = payload.get("property_ids", [])
    if not isinstance(ids, list):
        raise HTTPException(status_code=400, detail="property_ids must be a list of integers")

    try:
        ids = [int(x) for x in ids]
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="property_ids must be integers")

    try:
        return compare_properties(db, ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
