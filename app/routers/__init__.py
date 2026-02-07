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
from app.routers.webhooks import router as webhooks_router
from app.routers.deal_types import router as deal_types_router
from app.routers.research import router as research_router
from app.routers.research_templates import router as research_templates_router
from app.routers.ai_agents import router as ai_agents_router
from app.routers.elevenlabs import router as elevenlabs_router
from app.routers.agentic_research import router as agentic_research_router
from app.routers.exa_research import router as exa_research_router
from app.routers.voice_campaigns import router as voice_campaigns_router
from app.routers.offers import router as offers_router

__all__ = ["agents_router", "properties_router", "address_router", "skip_trace_router", "contacts_router", "todos_router", "contracts_router", "contract_templates_router", "agent_preferences_router", "context_router", "notifications_router", "compliance_knowledge_router", "compliance_router", "activities_router", "property_recap_router", "webhooks_router", "deal_types_router", "research_router", "research_templates_router", "ai_agents_router", "elevenlabs_router", "agentic_research_router", "exa_research_router", "voice_campaigns_router", "offers_router"]
