"""Portfolio Dashboard router — bird's-eye view of the entire portfolio."""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.rate_limit import limiter, premium_limit
from app.services.portfolio_dashboard_service import get_portfolio_dashboard

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/dashboard")
@limiter.limit(limit_value=premium_limit("standard"))
def dashboard(
    request: Request,
    agent_id: int | None = Query(None, description="Filter by agent ID"),
    db: Session = Depends(get_db),
):
    """Full portfolio snapshot: totals, breakdown by status/type, top deals,
    enrichment coverage, equity estimate, and voice summary."""
    return get_portfolio_dashboard(db, agent_id=agent_id)
