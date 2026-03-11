"""Central router registration — keeps main.py clean."""

from fastapi import FastAPI

from app.routers import (
    shotstack_enhanced_router,
    agents_router, properties_router, address_router, skip_trace_router,
    contacts_router, todos_router, contracts_router, contract_templates_router,
    agent_preferences_router, context_router, notifications_router,
    compliance_knowledge_router, compliance_router, activities_router,
    property_recap_router, webhooks_router, deal_types_router, research_router,
    research_templates_router, ai_agents_router, elevenlabs_router,
    agentic_research_router, exa_research_router, voice_campaigns_router,
    offers_router, search_router, deal_calculator_router, workflows_router,
    insights_router, scheduled_tasks_router,
    pipeline_router, daily_digest_router,
    comps_router, bulk_router, activity_timeline_router,
    market_watchlist_router, web_scraper, approval_router,
    credential_scrubbing_router, observer_router, agent_brand_router,
    postiz_router, videogen_router, sqlite_tuning_router, skills_router,
    setup_router, campaigns_router, document_analysis_router, zuckerbot_router,
    facebook_targeting_router, composio_router, renders_router,
    photo_orders_router, direct_mail_router, contact_lists_router,
    products_router, pvc_router, video_chat_router, knowledge_base_router,
    webhook_listeners_router, voice_agent_router, email_triage_router,
    follow_up_sequences_router, deal_journal_router, listing_presentation_router,
    cma_report_router, morning_brief_router,
)
from app.routers import (
    portal, document_extraction, calendar, analytics_dashboard,
    analytics_alerts, property_videos, predictive_intelligence,
    market_opportunities, relationship_intelligence, intelligence,
    workspace, cron_scheduler, hybrid_search, onboarding,
    enhanced_property_videos, property_websites, telnyx,
    orchestration_router, transaction_coordinator_router, timeline,
)
# Sub-routers merged into larger files
from app.routers.analytics_dashboard import _portfolio_router
from app.routers.voice_agent import _memo_router
from app.routers.property_recap import _notes_router, _scoring_router
from app.routers.follow_up_sequences import _queue_router


def register_routers(app: FastAPI) -> None:
    """Register all routers on the FastAPI app."""

    # Core
    app.include_router(agents_router)
    app.include_router(properties_router)
    app.include_router(address_router)
    app.include_router(skip_trace_router)
    app.include_router(contacts_router)
    app.include_router(todos_router)
    app.include_router(contracts_router)
    app.include_router(contract_templates_router)
    app.include_router(agent_preferences_router)
    app.include_router(context_router)
    app.include_router(notifications_router)

    # Compliance
    app.include_router(compliance_knowledge_router)
    app.include_router(compliance_router)

    # Activity & Pipeline
    app.include_router(activities_router)
    app.include_router(property_recap_router)
    app.include_router(webhooks_router)
    app.include_router(deal_types_router)
    app.include_router(pipeline_router)
    app.include_router(activity_timeline_router)

    # Research
    app.include_router(research_router)
    app.include_router(research_templates_router)
    app.include_router(agentic_research_router)
    app.include_router(exa_research_router)

    # AI & Voice
    app.include_router(ai_agents_router)
    app.include_router(elevenlabs_router)
    app.include_router(voice_campaigns_router)
    app.include_router(voice_agent_router)
    app.include_router(_memo_router)  # merged from voice_memo.py
    app.include_router(telnyx.router)

    # Deals & Offers
    app.include_router(offers_router)
    app.include_router(search_router)
    app.include_router(deal_calculator_router)
    app.include_router(deal_journal_router)
    app.include_router(transaction_coordinator_router)

    # Workflows & Scheduling
    app.include_router(workflows_router)
    app.include_router(scheduled_tasks_router)
    app.include_router(daily_digest_router)
    app.include_router(_queue_router)  # merged from follow_ups.py
    app.include_router(follow_up_sequences_router)
    app.include_router(morning_brief_router)

    # Analytics & Intelligence
    app.include_router(_portfolio_router)  # merged from analytics.py
    app.include_router(analytics_dashboard.router)
    app.include_router(analytics_alerts.router)
    app.include_router(insights_router)
    app.include_router(predictive_intelligence.router)
    app.include_router(market_opportunities.router)
    app.include_router(relationship_intelligence.router)
    app.include_router(intelligence.router)

    # Properties extended
    app.include_router(_notes_router)  # merged from property_notes.py
    app.include_router(_scoring_router)  # merged from property_scoring.py
    app.include_router(property_videos.router)
    app.include_router(property_websites.router)
    app.include_router(comps_router)
    app.include_router(market_watchlist_router)

    # Marketing & Campaigns
    app.include_router(campaigns_router)
    app.include_router(postiz_router)
    app.include_router(zuckerbot_router)
    app.include_router(facebook_targeting_router)
    app.include_router(contact_lists_router)
    app.include_router(direct_mail_router)
    app.include_router(listing_presentation_router)
    app.include_router(cma_report_router)

    # Video
    app.include_router(videogen_router)
    app.include_router(enhanced_property_videos.router)
    app.include_router(renders_router)
    app.include_router(video_chat_router)
    app.include_router(pvc_router)
    app.include_router(timeline.router)

    # Operations
    app.include_router(bulk_router)
    app.include_router(approval_router)
    app.include_router(credential_scrubbing_router)
    app.include_router(observer_router)
    app.include_router(agent_brand_router)
    app.include_router(photo_orders_router)
    app.include_router(email_triage_router)

    # Platform
    app.include_router(knowledge_base_router)
    app.include_router(webhook_listeners_router)
    app.include_router(document_analysis_router)
    app.include_router(composio_router)
    app.include_router(skills_router)
    app.include_router(setup_router)
    app.include_router(sqlite_tuning_router)
    app.include_router(web_scraper)
    app.include_router(workspace.router)
    app.include_router(cron_scheduler.router)
    app.include_router(hybrid_search.router)
    app.include_router(onboarding.router)
    app.include_router(products_router, prefix="/v1", tags=["Products"])
    app.include_router(portal.router)
    app.include_router(document_extraction.router)
    app.include_router(calendar.router)

    # Shotstack Enhanced Video
    app.include_router(shotstack_enhanced_router)

    # Orchestration
    app.include_router(orchestration_router.router)
