from app.routers.agents import router as agents_router
from app.routers.properties import router as properties_router
from app.routers.address import router as address_router
from app.routers.skip_trace import router as skip_trace_router
from app.routers.contacts import router as contacts_router
from app.routers.todos import router as todos_router
from app.routers.contracts import router as contracts_router
from app.routers.contract_templates import router as contract_templates_router
from app.routers.agent_preferences import router as agent_preferences_router
from app.routers.context import router as context_router
from app.routers.notifications import router as notifications_router
from app.routers.compliance_knowledge import router as compliance_knowledge_router
from app.routers.compliance import router as compliance_router
from app.routers.activities import router as activities_router
from app.routers.property_recap import router as property_recap_router

__all__ = ["agents_router", "properties_router", "address_router", "skip_trace_router", "contacts_router", "todos_router", "contracts_router", "contract_templates_router", "agent_preferences_router", "context_router", "notifications_router", "compliance_knowledge_router", "compliance_router", "activities_router", "property_recap_router"]
