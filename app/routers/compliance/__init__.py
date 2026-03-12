"""Compliance domain routers."""

from app.routers.compliance.compliance import router as compliance_router
from app.routers.compliance.compliance_knowledge import router as compliance_knowledge_router

__all__ = ["compliance_router", "compliance_knowledge_router"]
