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
from app.routers.search import router as search_router
from app.routers.deal_calculator import router as deal_calculator_router
from app.routers.workflows import router as workflows_router
from app.routers.property_notes import router as property_notes_router
from app.routers.insights import router as insights_router
from app.routers.scheduled_tasks import router as scheduled_tasks_router
from app.routers.analytics import router as analytics_router
from app.routers.pipeline import router as pipeline_router
from app.routers.daily_digest import router as daily_digest_router
from app.routers.follow_ups import router as follow_ups_router
from app.routers.comps import router as comps_router
from app.routers.bulk import router as bulk_router
from app.routers.activity_timeline import router as activity_timeline_router
from app.routers.property_scoring import router as property_scoring_router
from app.routers.market_watchlist import router as market_watchlist_router
# New intelligence routers
from app.routers.predictive_intelligence import router as predictive_intelligence_router
from app.routers.market_opportunities import router as market_opportunities_router
from app.routers.relationship_intelligence import router as relationship_intelligence_router
from app.routers.intelligence import router as intelligence_router
# Web scraper router
from app.routers.web_scraper import router as web_scraper
# ZeroClaw-inspired features
from app.routers.workspace import router as workspace_router
from app.routers.cron_scheduler import router as cron_scheduler_router
from app.routers.hybrid_search import router as hybrid_search_router
# Onboarding
from app.routers.onboarding import router as onboarding_router
# Approval Manager
from app.routers.approval import router as approval_router
# Credential Scrubbing
from app.routers.credential_scrubbing import router as credential_scrubbing_router
# Observer Pattern
from app.routers.observer import router as observer_router
# Agent Branding
from app.routers.agent_brand import router as agent_brand_router
# Facebook Ads Management
from app.routers.facebook_ads import router as facebook_ads_router
# Postiz Social Media Marketing
from app.routers.postiz import router as postiz_router
# SQLite Tuning
from app.routers.sqlite_tuning import router as sqlite_tuning_router
# Skills System
from app.routers.skills import router as skills_router

__all__ = ["agents_router", "properties_router", "address_router", "skip_trace_router", "contacts_router", "todos_router", "contracts_router", "contract_templates_router", "agent_preferences_router", "context_router", "notifications_router", "compliance_knowledge_router", "compliance_router", "activities_router", "property_recap_router", "webhooks_router", "deal_types_router", "research_router", "research_templates_router", "ai_agents_router", "elevenlabs_router", "agentic_research_router", "exa_research_router", "voice_campaigns_router", "offers_router", "search_router", "deal_calculator_router", "workflows_router", "property_notes_router", "insights_router", "scheduled_tasks_router", "analytics_router", "pipeline_router", "daily_digest_router", "follow_ups_router", "comps_router", "bulk_router", "activity_timeline_router", "property_scoring_router", "market_watchlist_router", "predictive_intelligence_router", "market_opportunities_router", "relationship_intelligence_router", "intelligence_router", "web_scraper", "workspace_router", "cron_scheduler_router", "hybrid_search_router", "onboarding_router", "approval_router", "credential_scrubbing_router", "observer_router", "agent_brand_router", "facebook_ads_router", "postiz_router", "sqlite_tuning_router", "skills_router"]
