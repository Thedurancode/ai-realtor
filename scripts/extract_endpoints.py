#!/usr/bin/env python3
"""
Extract all API endpoints from routers and analyze authentication requirements.
"""

import ast
import os
import re
from collections import defaultdict
from pathlib import Path

# Public paths (from main.py)
PUBLIC_PATHS = frozenset(("/", "/docs", "/redoc", "/openapi.json", "/health", "/setup", "/rate-limit"))
PUBLIC_PREFIXES = frozenset(("/webhooks/", "/ws", "/cache/", "/agents/register", "/api/setup", "/composio/", "/portal/"))

# Router prefixes
ROUTER_PREFIXES = {
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
    "telnyx": "/telnyx",
    "photo_orders": "/photo-orders",
    "direct_mail_router": "/direct-mail",
    "contact_lists_router": "/contact-lists",
    "portal": "/portal",
    "document_extraction": "/document-extraction",
    "calendar": "/calendar",
    "property_videos": "/property-videos",
    "predictive_intelligence": "/intelligence/predictive",
    "market_opportunities": "/intelligence/opportunities",
    "relationship_intelligence": "/intelligence/relationship",
    "intelligence": "/intelligence",
    "workspace": "/workspace",
    "cron_scheduler": "/cron",
    "hybrid_search": "/hybrid-search",
    "web_scraper": "/scrape",
}


def extract_endpoints_from_file(file_path: Path) -> list:
    """Extract endpoints from a router file."""
    endpoints = []

    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Find all @router.get/post/put/delete/patch decorators
        pattern = r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
        matches = re.findall(pattern, content)

        for method, path in matches:
            endpoints.append({
                "method": method.upper(),
                "path": path,
                "file": file_path.name,
            })

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return endpoints


def is_public_path(path: str, method: str) -> bool:
    """Check if a path is public (no auth required)."""
    # Check exact public paths
    if path in PUBLIC_PATHS:
        return True

    # Check public prefixes
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return True

    # OPTIONS requests are always public (CORS)
    if method == "OPTIONS":
        return True

    return False


def main():
    """Main function."""
    routers_dir = Path("app/routers")
    all_endpoints = defaultdict(list)

    print("🔍 Scanning routers for endpoints...\n")

    # Scan all router files
    for router_file in routers_dir.glob("*.py"):
        if router_file.name == "__init__.py":
            continue

        endpoints = extract_endpoints_from_file(router_file)
        for endpoint in endpoints:
            all_endpoints[router_file.name].append(endpoint)

    # Categorize endpoints
    public_endpoints = []
    protected_endpoints = []

    for router_name, endpoints in sorted(all_endpoints.items()):
        for endpoint in endpoints:
            full_path = endpoint["path"]

            # Check if public
            if is_public_path(full_path, endpoint["method"]):
                public_endpoints.append({
                    **endpoint,
                    "router": router_name,
                    "auth": "❌ None (Public)"
                })
            else:
                protected_endpoints.append({
                    **endpoint,
                    "router": router_name,
                    "auth": "✅ X-API-Key header"
                })

    # Print summary
    print("=" * 80)
    print("📊 ENDPOINT SUMMARY")
    print("=" * 80)
    print(f"Total Endpoints: {len(public_endpoints) + len(protected_endpoints)}")
    print(f"  ✅ Public (No Auth):  {len(public_endpoints)}")
    print(f"  🔒 Protected (API Key): {len(protected_endpoints)}")
    print()

    # Print authentication info
    print("=" * 80)
    print("🔐 AUTHENTICATION")
    print("=" * 80)
    print("Protected endpoints require API key in header:")
    print()
    print("  X-API-Key: sk_live_...")
    print()
    print("Or via Bearer token:")
    print()
    print("  Authorization: Bearer sk_live_...")
    print()
    print("Get an API key by registering:")
    print('  curl -X POST http://localhost:8000/agents/register \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"email":"test@example.com","name":"Test Agent"}\'')
    print()

    # Print public endpoints
    if public_endpoints:
        print("=" * 80)
        print("🌐 PUBLIC ENDPOINTS (No Authentication Required)")
        print("=" * 80)
        print()

        # Group by router
        by_router = defaultdict(list)
        for ep in public_endpoints:
            by_router[ep["router"]].append(ep)

        for router_name in sorted(by_router.keys()):
            print(f"📁 {router_name}")
            for ep in sorted(by_router[router_name], key=lambda x: x["path"]):
                print(f"  {ep['method']:6} {ep['path']:40} # {ep['auth']}")
            print()

    # Print protected endpoints
    if protected_endpoints:
        print("=" * 80)
        print("🔒 PROTECTED ENDPOINTS (API Key Required)")
        print("=" * 80)
        print()
        print("All these endpoints require: X-API-Key: sk_live_...")
        print()

        # Group by category
        categories = {
            "Property Management": ["properties_router", "address_router", "property_recap_router", "property_notes_router"],
            "Contracts & Deals": ["contracts_router", "contract_templates_router", "offers_router", "deal_types_router"],
            "Contacts & Skip Tracing": ["contacts_router", "skip_trace_router"],
            "Direct Mail & Campaigns": ["direct_mail_router", "contact_lists_router", "voice_campaigns_router", "campaigns_router"],
            "Marketing": ["facebook_ads_router", "zuckerbot_router", "facebook_targeting_router", "postiz_router", "agent_brand_router"],
            "Analytics & Intelligence": ["analytics_router", "insights_router", "predictive_intelligence_router", "market_opportunities_router", "relationship_intelligence_router", "intelligence_router", "property_scoring_router"],
            "Research": ["research_router", "agentic_research_router", "exa_research_router", "research_templates_router"],
            "Workflow & Automation": ["workflows_router", "bulk_router", "scheduled_tasks_router", "pipeline_router", "cron_scheduler_router"],
            "Calendar": ["calendar_router"],
            "Web Scraper": ["web_scraper_router"],
            "Media & Video": ["renders_router", "property_videos_router", "videogen_router", "elevenlabs_router"],
            "Integrations": ["telnyx", "composio_router", "photo_orders"],
            "Documents": ["document_analysis_router", "document_extraction_router"],
            "Knowledge & Compliance": ["compliance_router", "compliance_knowledge_router"],
            "Search & Discovery": ["search_router", "hybrid_search_router"],
            "Notifications & Activity": ["notifications_router", "activities_router", "activity_timeline_router", "daily_digest_router", "follow_ups_router"],
            "Market & Comparables": ["comps_router", "market_watchlist_router", "deal_calculator_router"],
            "Agent & Settings": ["agents_router", "agent_preferences_router", "skills_router", "observer_router", "workspace_router"],
            "Other": ["todos_router", "context_router", "approval_router", "credential_scrubbing_router", "sqlite_tuning_router", "setup_router"],
        }

        for category, routers in categories.items():
            category_endpoints = []
            for ep in protected_endpoints:
                if ep["router"] in routers:
                    category_endpoints.append(ep)

            if category_endpoints:
                print(f"\n{'=' * 80}")
                print(f"📂 {category}")
                print('=' * 80)

                for ep in sorted(category_endpoints, key=lambda x: (x["file"], x["path"])):
                    print(f"  {ep['method']:6} {ep['path']:50} # {ep['file']}")


if __name__ == "__main__":
    main()
