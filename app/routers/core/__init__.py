"""Core domain routers — agents, properties, contacts, etc."""

from app.routers.core.agents import router as agents_router
from app.routers.core.properties import router as properties_router
from app.routers.core.address import router as address_router
from app.routers.core.skip_trace import router as skip_trace_router
from app.routers.core.contacts import router as contacts_router
from app.routers.core.todos import router as todos_router
from app.routers.core.contracts import router as contracts_router
from app.routers.core.contract_templates import router as contract_templates_router
from app.routers.core.agent_preferences import router as agent_preferences_router
from app.routers.core.context import router as context_router
from app.routers.core.notifications import router as notifications_router

__all__ = [
    "agents_router", "properties_router", "address_router",
    "skip_trace_router", "contacts_router", "todos_router",
    "contracts_router", "contract_templates_router",
    "agent_preferences_router", "context_router", "notifications_router",
]
