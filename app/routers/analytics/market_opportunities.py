"""Market Opportunity Scanner API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.services.market_opportunity_scanner import market_opportunity_scanner

router = APIRouter(prefix="/opportunities", tags=["market-opportunities"])


class ScanRequest(BaseModel):
    agent_id: int
    limit: int = 10
    min_score: float = 70
    property_types: Optional[List[str]] = None
    cities: Optional[List[str]] = None
    max_price: Optional[float] = None


class MarketShiftsRequest(BaseModel):
    agent_id: int
    cities: Optional[List[str]] = None


@router.post("/scan")
async def scan_market_opportunities(request: ScanRequest, db: Session = Depends(get_db)):
    """Scan for opportunities matching agent's success patterns.

    Returns top properties that match:
    - Agent's historical best property types
    - Agent's best cities
    - High deal scores
    - Market ROI potential
    """
    result = await market_opportunity_scanner.scan_market_opportunities(
        db=db,
        agent_id=request.agent_id,
        limit=request.limit,
        min_score=request.min_score,
        property_types=request.property_types,
        cities=request.cities,
        max_price=request.max_price,
    )
    return result


@router.post("/market-shifts")
async def detect_market_shifts(request: MarketShiftsRequest, db: Session = Depends(get_db)):
    """Detect significant market condition changes.

    Monitors for:
    - Price drops/surges (>10% change)
    - Inventory shifts
    - Actionable alerts
    """
    result = await market_opportunity_scanner.detect_market_shifts(
        db=db,
        agent_id=request.agent_id,
        cities=request.cities,
    )
    return result


@router.get("/property/{property_id}/similar")
async def find_similar_deals(
    property_id: int,
    agent_id: Optional[int] = None,
    limit: int = 5,
    db: Session = Depends(get_db),
):
    """Find similar properties for comparison.

    Useful for:
    - Comparing deal terms
    - Understanding market positioning
    - Learning from similar outcomes
    """
    result = await market_opportunity_scanner.find_similar_deals(
        db=db,
        property_id=property_id,
        agent_id=agent_id,
        limit=limit,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
