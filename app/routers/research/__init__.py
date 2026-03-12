"""Research domain routers."""

from app.routers.research.research import router as research_router
from app.routers.research.research_templates import router as research_templates_router
from app.routers.research.agentic_research import router as agentic_research_router
from app.routers.research.exa_research import router as exa_research_router

__all__ = [
    "research_router", "research_templates_router",
    "agentic_research_router", "exa_research_router",
]
