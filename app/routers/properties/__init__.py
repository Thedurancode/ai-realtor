"""Properties-extended domain routers — videos, websites, comps, etc."""

from app.routers.properties import property_videos
from app.routers.properties import property_websites
from app.routers.properties.comps import router as comps_router
from app.routers.properties.market_watchlist import router as market_watchlist_router
from app.routers.properties import enhanced_property_videos
from app.routers.properties.photo_orders import router as photo_orders_router

__all__ = [
    "property_videos", "property_websites", "comps_router",
    "market_watchlist_router", "enhanced_property_videos", "photo_orders_router",
]
