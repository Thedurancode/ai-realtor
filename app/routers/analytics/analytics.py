"""Analytics router — cross-property portfolio intelligence."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/portfolio")
def get_portfolio_summary(db: Session = Depends(get_db)):
    return analytics_service.get_portfolio_summary(db)


@router.get("/pipeline")
def get_pipeline_summary(db: Session = Depends(get_db)):
    return analytics_service.get_pipeline_summary(db)


@router.get("/contracts")
def get_contract_summary(db: Session = Depends(get_db)):
    return analytics_service.get_contract_summary(db)
