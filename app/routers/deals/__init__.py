"""Deals domain routers — offers, search, deal calculator, etc."""

from app.routers.deals.offers import router as offers_router
from app.routers.deals.search import router as search_router
from app.routers.deals.deal_calculator import router as deal_calculator_router
from app.routers.deals.deal_journal import router as deal_journal_router
from app.routers.deals.transaction_coordinator import router as transaction_coordinator_router

__all__ = [
    "offers_router", "search_router", "deal_calculator_router",
    "deal_journal_router", "transaction_coordinator_router",
]
