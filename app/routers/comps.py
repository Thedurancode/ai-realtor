"""Comparable Sales Dashboard router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.comps_dashboard_service import comps_dashboard_service

router = APIRouter(prefix="/comps", tags=["comps"])


@router.get("/{property_id}")
def get_comps_dashboard(property_id: int, db: Session = Depends(get_db)):
    """Full comparable sales dashboard for a property."""
    try:
        return comps_dashboard_service.get_dashboard(db, property_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{property_id}/sales")
def get_comp_sales(property_id: int, db: Session = Depends(get_db)):
    """Sales comparables and market metrics."""
    try:
        return comps_dashboard_service.get_sales(db, property_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{property_id}/rentals")
def get_comp_rentals(property_id: int, db: Session = Depends(get_db)):
    """Rental comparables."""
    try:
        return comps_dashboard_service.get_rentals(db, property_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
