"""Platform domain routers — knowledge, webhooks, docs, tools, etc."""

from app.routers.platform.knowledge_base import router as knowledge_base_router
from app.routers.platform.webhook_listeners import router as webhook_listeners_router
from app.routers.platform.document_analysis import router as document_analysis_router
from app.routers.platform import document_extraction
from app.routers.platform.composio import router as composio_router
from app.routers.platform.skills import router as skills_router
from app.routers.platform.setup import router as setup_router
from app.routers.platform.sqlite_tuning import router as sqlite_tuning_router
from app.routers.platform.web_scraper import router as web_scraper
from app.routers.platform import workspace
from app.routers.platform import hybrid_search
from app.routers.platform import onboarding
from app.routers.platform.products import router as products_router
from app.routers.platform import portal
from app.routers.platform import calendar
from app.routers.platform import orchestration_router

__all__ = [
    "knowledge_base_router", "webhook_listeners_router",
    "document_analysis_router", "document_extraction",
    "composio_router", "skills_router", "setup_router",
    "sqlite_tuning_router", "web_scraper", "workspace",
    "hybrid_search", "onboarding", "products_router",
    "portal", "calendar", "orchestration_router",
]
