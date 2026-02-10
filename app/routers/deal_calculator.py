"""Deal Calculator router — underwriting endpoints for any property."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.deal_calculator import (
    DealCalculatorInput,
    DealCalculatorResponse,
    RehabAssumptions,
)
from app.services.deal_calculator_service import calculate_deal

router = APIRouter(prefix="/deal-calculator", tags=["deal-calculator"])


@router.post("/calculate", response_model=DealCalculatorResponse)
def calculate(payload: DealCalculatorInput, db: Session = Depends(get_db)):
    """Full deal calculation with all overrides supported."""
    try:
        return calculate_deal(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/property/{property_id}", response_model=DealCalculatorResponse)
def quick_calculate(property_id: int, db: Session = Depends(get_db)):
    """Calculate with defaults — no body required."""
    try:
        return calculate_deal(db, DealCalculatorInput(property_id=property_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/compare", response_model=DealCalculatorResponse)
def compare_strategies(payload: DealCalculatorInput, db: Session = Depends(get_db)):
    """Side-by-side strategy comparison (same data, different framing)."""
    try:
        return calculate_deal(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/voice", response_model=DealCalculatorResponse)
def voice_calculate(
    property_id: int = Query(..., description="Property ID"),
    rehab_tier: str = Query("medium", description="light, medium, or heavy"),
    arv: float | None = Query(None, description="ARV override"),
    monthly_rent: float | None = Query(None, description="Monthly rent override"),
    db: Session = Depends(get_db),
):
    """Voice-optimized endpoint — query params only, returns voice_summary."""
    try:
        return calculate_deal(
            db,
            DealCalculatorInput(
                property_id=property_id,
                arv_override=arv,
                monthly_rent_override=monthly_rent,
                rehab=RehabAssumptions(tier=rehab_tier),
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
