#!/usr/bin/env python3
"""
Comprehensive endpoint listing with authentication requirements.
"""

import os
import re
from collections import defaultdict
from pathlib import Path


# Public paths (from main.py)
PUBLIC_PATHS = frozenset((
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
    "/setup",
    "/rate-limit",
))

PUBLIC_PREFIXES = frozenset((
    "/webhooks/",
    "/ws",
    "/cache/",
    "/agents/register",
    "/api/setup",
    "/composio/",
    "/portal/",
))


def get_router_prefix(router_name: str) -> str:
    """Get the URL prefix for a router."""
    prefixes = {
        "agents_router": "/agents",
        "properties_router": "/properties",
        "address_router": "/address",
        "skip_trace_router": "/skip-trace",
        "contacts_router": "/contacts",
        "todos_router": "/todos",
        "contracts_router": "/contracts",
        "contract_templates_router": "/contract-templates",
        "agent_preferences_router": "/agent-preferences",
        "context_router": "/context",
        "notifications_router": "/notifications",
        "compliance_knowledge_router": "/compliance-knowledge",
        "compliance_router": "/compliance",
        "activities_router": "/activities",
        "property_recap_router": "/property-recap",
        "webhooks_router": "/webhooks",
        "deal_types_router": "/deal-types",
        "research_router": "/research",
        "research_templates_router": "/research-templates",
        "ai_agents_router": "/ai-agents",
        "elevenlabs_router": "/elevenlabs",
        "agentic_research_router": "/agentic-research",
        "exa_research_router": "/exa-research",
        "voice_campaigns_router": "/voice-campaigns",
        "offers_router": "/offers",
        "search_router": "/search",
        "deal_calculator_router": "/deal-calculator",
        "workflows_router": "/workflows",
        "property_notes_router": "/property-notes",
        "insights_router": "/insights",
        "scheduled_tasks_router": "/scheduled-tasks",
        "analytics_router": "/analytics",
        "pipeline_router": "/pipeline",
        "daily_digest_router": "/daily-digest",
        "follow_ups_router": "/follow-ups",
        "comps_router": "/comps",
        "bulk_router": "/bulk",
        "activity_timeline_router": "/activity-timeline",
        "property_scoring_router": "/scoring",
        "market_watchlist_router": "/watchlists",
        "approval_router": "/approval",
        "credential_scrubbing_router": "/credential-scrubbing",
        "observer_router": "/observer",
        "agent_brand_router": "/agent-brand",
        "facebook_ads_router": "/facebook-ads",
        "postiz_router": "/social",
        "videogen_router": "/videogen",
        "sqlite_tuning_router": "/sqlite-tuning",
        "skills_router": "/skills",
        "setup_router": "/api/setup",
        "campaigns_router": "/campaigns",
        "document_analysis_router": "/document-analysis",
        "zuckerbot_router": "/zuckerbot",
        "facebook_targeting_router": "/facebook-targeting",
        "composio_router": "/composio",
        "renders_router": "/renders",
        "telnyx_router": "/telnyx",
        "photo_orders_router": "/photo-orders",
        "direct_mail_router": "/direct-mail",
        "contact_lists_router": "/contact-lists",
        "portal_router": "/portal",
        "document_extraction_router": "/document-extraction",
        "calendar_router": "/calendar",
        "property_videos_router": "/property-videos",
        "predictive_intelligence_router": "/intelligence/predictive",
        "market_opportunities_router": "/intelligence/opportunities",
        "relationship_intelligence_router": "/intelligence/relationship",
        "intelligence_router": "/intelligence",
        "workspace_router": "/workspace",
        "cron_scheduler_router": "/cron",
        "hybrid_search_router": "/hybrid-search",
        "web_scraper_router": "/scrape",
    }
    return prefixes.get(router_name, "")


def is_public_path(path: str) -> bool:
    """Check if a path is public (no auth required)."""
    # Check exact public paths
    if path in PUBLIC_PATHS:
        return True

    # Check public prefixes
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return True

    return False


def main():
    """Main function."""
    print("=" * 100)
    print("RealtorClaw API - Endpoint Authentication Guide")
    print("=" * 100)
    print()

    # Authentication info
    print("🔐 AUTHENTICATION")
    print("-" * 100)
    print()
    print("Most endpoints require an API key. There are two ways to provide it:")
    print()
    print("  Method 1: X-API-Key header")
    print("    X-API-Key: sk_live_...")
    print()
    print("  Method 2: Authorization Bearer header")
    print("    Authorization: Bearer sk_live_...")
    print()
    print("Get an API key by registering:")
    print('  $ curl -X POST http://localhost:8000/agents/register \\')
    print('      -H "Content-Type: application/json" \\')
    print('      -d \'{"email":"your@email.com","name":"Your Name"}\'')
    print()
    print("Response:")
    print('  {')
    print('    "id": 1,')
    print('    "name": "Your Name",')
    print('    "email": "your@email.com",')
    print('    "api_key": "sk_live_abc123...",')
    print('    "created_at": "2026-02-27T..."')
    print('  }')
    print()

    # List public endpoints
    print()
    print("=" * 100)
    print("🌐 PUBLIC ENDPOINTS (No Authentication Required)")
    print("=" * 100)
    print()
    print("These endpoints can be called without an API key:")
    print()

    public_endpoints = [
        ("GET", "/", "Root endpoint with API info"),
        ("GET", "/docs", "Interactive API documentation (Swagger UI)"),
        ("GET", "/redoc", "Alternative API documentation (ReDoc)"),
        ("GET", "/openapi.json", "OpenAPI schema"),
        ("GET", "/health", "Health check endpoint"),
        ("GET", "/rate-limit", "Rate limiting configuration"),
        ("POST", "/agents/register", "Register new agent and get API key"),
        ("GET|POST", "/agents/", "List/create agents (check your specific router)"),
        ("", "/webhooks/*", "Webhook endpoints (DocuSeal, Lob, etc.)"),
        ("", "/ws", "WebSocket connections"),
        ("", "/portal/*", "Customer portal endpoints"),
        ("", "/api/setup/*", "Setup wizard endpoints"),
        ("", "/composio/*", "Composio integration endpoints"),
    ]

    for method, path, description in public_endpoints:
        if method:
            print(f"  {method:20} {path:40} # {description}")
        else:
            print(f"  {'':20} {path:40} # {description}")

    print()
    print()
    print("=" * 100)
    print("🔒 PROTECTED ENDPOINTS (API Key Required)")
    print("=" * 100)
    print()
    print("All other endpoints require: X-API-Key: sk_live_...")
    print()
    print("Key Categories:")
    print()

    categories = [
        ("Property Management", "/properties", [
            ("GET", "/properties/", "List all properties"),
            ("POST", "/properties/", "Create new property"),
            ("GET", "/properties/{id}", "Get property details"),
            ("PUT|PATCH", "/properties/{id}", "Update property"),
            ("DELETE", "/properties/{id}", "Delete property"),
            ("POST", "/properties/{id}/enrich", "Enrich with Zillow data"),
            ("POST", "/properties/{id}/skip-trace", "Skip trace property"),
            ("GET", "/properties/{id}/heartbeat", "Get property heartbeat"),
            ("POST", "/properties/voice", "Create property via voice"),
        ]),
        ("Contracts", "/contracts", [
            ("GET", "/contracts/", "List all contracts"),
            ("POST", "/contracts/", "Create contract"),
            ("GET", "/contracts/{id}", "Get contract details"),
            ("PUT|PATCH", "/contracts/{id}", "Update contract"),
            ("DELETE", "/contracts/{id}", "Delete contract"),
            ("POST", "/contracts/{id}/send", "Send for signature"),
            ("GET", "/contracts/{id}/status", "Check signing status"),
            ("POST", "/properties/{id}/attach-contracts", "Auto-attach templates"),
        ]),
        ("Contacts", "/contacts", [
            ("GET", "/contacts/", "List all contacts"),
            ("POST", "/contacts/", "Create new contact"),
            ("GET", "/contacts/{id}", "Get contact details"),
            ("PUT|PATCH", "/contacts/{id}", "Update contact"),
            ("DELETE", "/contacts/{id}", "Delete contact"),
        ]),
        ("Direct Mail", "/direct-mail", [
            ("POST", "/direct-mail/postcards", "Send postcard"),
            ("POST", "/direct-mail/letters", "Send letter"),
            ("POST", "/direct-mail/campaigns", "Create campaign"),
            ("GET", "/direct-mail/postcards/{id}", "Check mail status"),
            ("POST", "/direct-mail/import-csv", "Import CSV contacts"),
            ("GET", "/direct-mail/templates", "List templates"),
        ]),
        ("Contact Lists", "/contact-lists", [
            ("GET", "/contact-lists/", "List all lists"),
            ("POST", "/contact-lists/", "Create list"),
            ("GET", "/contact-lists/{id}", "Get list details"),
            ("PUT|PATCH", "/contact-lists/{id}", "Update list"),
            ("DELETE", "/contact-lists/{id}", "Delete list"),
            ("POST", "/contact-lists/{id}/create-campaign", "Create campaign from list"),
        ]),
        ("Facebook Ads", "/facebook-ads", [
            ("POST", "/facebook-ads/campaigns/generate", "Generate ad campaign"),
            ("POST", "/facebook-ads/campaigns/{id}/launch", "Launch to Meta"),
            ("GET", "/facebook-ads/campaigns", "List campaigns"),
            ("POST", "/facebook-ads/audiences/recommend", "Get audience recommendations"),
        ]),
        ("Social Media", "/social", [
            ("POST", "/social/posts/create", "Create social post"),
            ("POST", "/social/posts/{id}/schedule", "Schedule post"),
            ("GET", "/social/posts", "List posts"),
            ("POST", "/social/ai/generate", "AI content generation"),
            ("GET", "/social/analytics/overview", "Get analytics"),
        ]),
        ("Calendar", "/calendar", [
            ("POST", "/calendar/connect", "Connect Google Calendar"),
            ("POST", "/calendar/events", "Create event"),
            ("GET", "/calendar/events", "List events"),
            ("POST", "/calendar/sync", "Sync to calendar"),
            ("GET", "/calendar/calendars", "List connected calendars"),
        ]),
        ("Analytics", "/analytics", [
            ("GET", "/analytics/portfolio", "Portfolio summary"),
            ("GET", "/analytics/pipeline", "Pipeline breakdown"),
            ("GET", "/analytics/contracts", "Contract stats"),
        ]),
        ("Web Scraper", "/scrape", [
            ("POST", "/scrape/url", "Scrape URL for property data"),
            ("POST", "/scrape/scrape-and-create", "Scrape and create property"),
            ("POST", "/scrape/zillow-search", "Scrape Zillow search"),
        ]),
        ("Pipeline", "/pipeline", [
            ("GET", "/pipeline/status", "Get pipeline status"),
            ("POST", "/pipeline/check", "Trigger pipeline check"),
        ]),
        ("Insights", "/insights", [
            ("GET", "/insights/", "Get all insights"),
            ("GET", "/insights/property/{id}", "Property-specific insights"),
        ]),
        ("Rate Limiting", "", [
            ("GET", "/rate-limit", "Check rate limit status"),
        ]),
    ]

    for category, prefix, endpoints in categories:
        print(f"\n📂 {category} ({prefix})")
        print("-" * 100)
        for method, path, description in endpoints:
            print(f"  {method:25} {path:50} # {description}")

    print()
    print()
    print("=" * 100)
    print("📊 SUMMARY")
    print("=" * 100)
    print()
    print("  Total Endpoints:  ~585")
    print("  Public (No Auth):  ~41")
    print("  Protected (API):   ~544")
    print()
    print("  Authentication:    X-API-Key or Authorization: Bearer")
    print("  Rate Limiting:      20 requests/hour per agent (default)")
    print()
    print()
    print("=" * 100)
    print("💡 QUICK TEST")
    print("=" * 100)
    print()
    print("# Register and get API key")
    print('API_KEY=$(curl -s -X POST http://localhost:8000/agents/register \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"email":"test@example.com","name":"Test"}\' \\')
    print('  | jq -r \'.api_key\')')
    print()
    print("# Use API key")
    print('curl -H "X-API-Key: $API_KEY" http://localhost:8000/properties')
    print()
    print("# Or with Bearer token")
    print('curl -H "Authorization: Bearer $API_KEY" http://localhost:8000/properties')
    print()


if __name__ == "__main__":
    main()
