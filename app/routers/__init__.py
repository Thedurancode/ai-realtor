"""Router package — re-exports every named router for backward compatibility.

All router modules now live in domain sub-packages (core/, compliance/, etc.).
Imports like ``from app.routers import agents_router`` continue to work.
"""

# --- Core ---
from app.routers.core import (  # noqa: F401
    agents_router, properties_router, address_router, skip_trace_router,
    contacts_router, todos_router, contracts_router, contract_templates_router,
    agent_preferences_router, context_router, notifications_router,
)

# --- Compliance ---
from app.routers.compliance import (  # noqa: F401
    compliance_router, compliance_knowledge_router,
)

# --- Pipeline ---
from app.routers.pipeline import (  # noqa: F401
    activities_router, property_recap_router, webhooks_router,
    deal_types_router, pipeline_router, activity_timeline_router,
)

# --- Research ---
from app.routers.research import (  # noqa: F401
    research_router, research_templates_router,
    agentic_research_router, exa_research_router,
)

# --- Voice ---
from app.routers.voice import (  # noqa: F401
    ai_agents_router, elevenlabs_router, voice_campaigns_router,
    voice_agent_router,
)

# --- Deals ---
from app.routers.deals import (  # noqa: F401
    offers_router, search_router, deal_calculator_router,
    deal_journal_router, transaction_coordinator_router,
)

# --- Workflows ---
from app.routers.workflows import (  # noqa: F401
    workflows_router, scheduled_tasks_router, daily_digest_router,
    follow_up_sequences_router, morning_brief_router,
)

# --- Analytics ---
from app.routers.analytics import insights_router  # noqa: F401

# --- Properties (extended) ---
from app.routers.properties import (  # noqa: F401
    comps_router, market_watchlist_router, photo_orders_router,
)

# --- Marketing ---
from app.routers.marketing import (  # noqa: F401
    campaigns_router, postiz_router, zuckerbot_router,
    facebook_ads_router, facebook_targeting_router,
    contact_lists_router, direct_mail_router,
    listing_presentation_router, cma_report_router,
)

# --- Video ---
from app.routers.video import (  # noqa: F401
    videogen_router, renders_router, video_chat_router,
    pvc_router, shotstack_enhanced_router, shotstack_create_router,
    agent_brand_router,
)

# --- Operations ---
from app.routers.operations import (  # noqa: F401
    bulk_router, approval_router, credential_scrubbing_router,
    observer_router, email_triage_router,
)

# --- Platform ---
from app.routers.platform import (  # noqa: F401
    knowledge_base_router, webhook_listeners_router,
    document_analysis_router, composio_router, skills_router,
    setup_router, sqlite_tuning_router, web_scraper, products_router,
)

# Module-level re-exports for registry.py (modules imported as namespaces)
from app.routers.analytics import (  # noqa: F401
    analytics_dashboard, analytics_alerts,
    predictive_intelligence, market_opportunities,
    relationship_intelligence, intelligence,
)
from app.routers.properties import (  # noqa: F401
    property_videos, property_websites, enhanced_property_videos,
)
from app.routers.voice import telnyx  # noqa: F401
from app.routers.workflows import cron_scheduler  # noqa: F401
from app.routers.platform import (  # noqa: F401
    workspace, hybrid_search, onboarding, portal,
    document_extraction, calendar, orchestration_router,
)
from app.routers.video import timeline  # noqa: F401

__all__ = [
    "shotstack_enhanced_router", "shotstack_create_router",
    "agents_router", "properties_router", "address_router",
    "skip_trace_router", "contacts_router", "todos_router",
    "contracts_router", "contract_templates_router",
    "agent_preferences_router", "context_router", "notifications_router",
    "compliance_knowledge_router", "compliance_router",
    "activities_router", "property_recap_router", "webhooks_router",
    "deal_types_router", "research_router", "research_templates_router",
    "ai_agents_router", "elevenlabs_router", "agentic_research_router",
    "exa_research_router", "voice_campaigns_router",
    "offers_router", "search_router", "deal_calculator_router",
    "workflows_router", "insights_router", "scheduled_tasks_router",
    "pipeline_router", "daily_digest_router",
    "comps_router", "bulk_router", "activity_timeline_router",
    "market_watchlist_router", "predictive_intelligence",
    "market_opportunities", "relationship_intelligence", "intelligence",
    "web_scraper", "workspace", "cron_scheduler",
    "hybrid_search", "onboarding", "approval_router",
    "credential_scrubbing_router", "observer_router",
    "agent_brand_router", "facebook_ads_router", "postiz_router",
    "videogen_router", "zuckerbot_router", "facebook_targeting_router",
    "composio_router", "campaigns_router", "document_analysis_router",
    "sqlite_tuning_router", "skills_router", "setup_router",
    "renders_router", "property_videos", "photo_orders_router",
    "direct_mail_router", "contact_lists_router", "products_router",
    "pvc_router", "video_chat_router", "knowledge_base_router",
    "webhook_listeners_router", "voice_agent_router",
    "email_triage_router", "follow_up_sequences_router",
    "deal_journal_router", "listing_presentation_router",
    "cma_report_router", "morning_brief_router",
    "transaction_coordinator_router", "timeline",
    "analytics_dashboard", "analytics_alerts",
    "property_websites", "enhanced_property_videos",
    "telnyx", "portal", "document_extraction", "calendar",
    "orchestration_router",
]
