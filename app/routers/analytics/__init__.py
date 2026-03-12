"""Analytics / intelligence domain routers."""

from app.routers.analytics import analytics_dashboard
from app.routers.analytics import analytics_alerts
from app.routers.analytics.analytics_dashboard import _portfolio_router
from app.routers.analytics.insights import router as insights_router
from app.routers.analytics import predictive_intelligence
from app.routers.analytics import market_opportunities
from app.routers.analytics import relationship_intelligence
from app.routers.analytics import intelligence

__all__ = [
    "analytics_dashboard", "analytics_alerts", "_portfolio_router",
    "insights_router", "predictive_intelligence", "market_opportunities",
    "relationship_intelligence", "intelligence",
]
