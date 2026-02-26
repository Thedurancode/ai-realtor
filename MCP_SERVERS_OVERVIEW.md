# AI Realtor - MCP Servers Overview

## MCP Server Architecture

The AI Realtor platform has **2 main MCP servers** that provide voice and API access to the entire platform.

---

## 🎯 Server 1: Property Management MCP Server

**Location:** `mcp_server/property_mcp.py`
**Entry Point:** `mcp_server/server.py`
**Transport:** stdio (for Claude Desktop) and SSE (for remote HTTP access)

### Total Tools: **207 MCP Tools** across 32 modules

---

## 📊 Tool Breakdown by Category

### **1. Core Property Management (7 tools)**
`properties.py`
- `list_properties` - List properties with filters
- `get_property` - Get property details
- `create_property` - Create new property
- `update_property` - Update property
- `delete_property` - Delete property
- `enrich_property` - Enrich with Zillow data
- `skip_trace_property` - Find owner contacts

### **2. Contacts & Skip Tracing (3 tools)**
`contacts_skip_trace.py`
- `add_contact` - Add property contact
- `call_property_owner_skip_trace` - Cold call owner
- `contact_property_owner_by_name` - Contact specific person

### **3. Contracts Management (15 tools)**

**`contracts.py` (9 tools)**
- `check_property_contract_readiness` - Check closing readiness
- `check_property_contract_readiness_voice` - Voice version
- `check_contract_status` - Check contract status
- `check_contract_status_voice` - Voice version
- `attach_required_contracts` - Auto-attach templates
- `mark_contract_required` - Mark as required
- `list_contracts` - List all contracts
- `list_contracts_voice` - Voice version
- `send_contract` - Send for signature

**`contracts_ai.py` (6 tools)**
- `ai_suggest_contracts` - Get AI suggestions
- `apply_ai_contract_suggestions` - Apply suggestions
- `smart_send_contract` - Multi-party send
- `get_signing_status` - Check signing status
- `get_template` - Get contract template
- `list_templates` - List all templates

### **4. Property Recaps & Phone Calls (6 tools)**
`recaps_calls.py`
- `generate_property_recap` - Generate AI recap
- `get_property_recap` - Get recap
- `make_property_phone_call` - VAPI call
- `call_contact_about_contract` - Call about contract
- `send_property_report` - Send property report
- `generate_property_recap_bulk` - Bulk generate recaps

### **5. Deal Calculator & Types (14 tools)**

**`deal_calculator.py` (4 tools)**
- `calculate_deal` - Calculate ROI, cash flow
- `calculate_mao` - Maximum allowable offer
- `what_if_deal` - Scenario modeling
- `compare_strategies` - Compare strategies

**`deal_types.py` (10 tools)**
- `preview_deal_type` - Preview deal config
- `set_deal_type` - Set property deal type
- `get_deal_status` - Get deal status
- `create_deal_type_config` - Create config
- `update_deal_type_config` - Update config
- `delete_deal_type_config` - Delete config
- `list_deal_types` - List all types
- `reset_property_deal` - Reset deal
- `get_deal_type_template` - Get template
- `apply_deal_type_template` - Apply template

### **6. Offers (10 tools)**
`offers.py`
- `create_offer` - Create offer
- `list_offers` - List offers
- `get_offer_details` - Get offer details
- `accept_offer` - Accept offer
- `reject_offer` - Reject offer
- `counter_offer` - Counter offer
- `withdraw_offer` - Withdraw offer
- `draft_offer_letter` - Generate letter
- `update_offer_status` - Update status
- `get_offer_summary` - Get summary

### **7. Research & Search (9 tools)**

**`research.py` (5 tools)**
- `research_property` - Deep research
- `research_property_async` - Background research
- `get_research_status` - Check progress
- `get_research_dossier` - Get completed research
- `search_research` - Search past research

**`vector_search.py` (4 tools)**
- `semantic_search` - Semantic property search
- `find_similar_properties` - Find similar
- `vector_search_properties` - Vector search
- `search_by_description` - Description search

### **8. Conversation History (5 tools)**
`conversation.py`
- `get_conversation_history` - Get session history
- `what_did_we_discuss` - Voice summary
- `clear_conversation_history` - Clear history
- `get_property_history` - Get property timeline
- `search_conversation_history` - Search history

### **9. Property Notes (3 tools)**
`property_notes.py`
- `add_property_note` - Add note
- `list_property_notes` - List notes
- `delete_property_note` - Delete note

### **10. ElevenLabs Voice (4 tools)**
`elevenlabs.py`
- `elevenlabs_call` - Make call via ElevenLabs
- `elevenlabs_setup` - Configure voice
- `elevenlabs_status` - Check call status
- `elevenlabs_webhook` - Handle webhook

### **11. Voice Campaigns (7 tools)**
`voice_campaigns.py`
- `create_voice_campaign` - Create campaign
- `start_voice_campaign` - Start campaign
- `pause_voice_campaign` - Pause campaign
- `get_campaign_status` - Get status
- `list_voice_campaigns` - List campaigns
- `add_campaign_targets` - Add targets
- `stop_voice_campaign` - Stop campaign

### **12. Workflows (3 tools)**
`workflows.py`
- `list_workflows` - List workflows
- `execute_workflow` - Execute workflow
- `get_workflow_status` - Get status

### **13. Notifications (6 tools)**
`notifications.py`
- `send_notification` - Send notification
- `list_notifications` - List notifications
- `acknowledge_notification` - Mark as read
- `get_notification_summary` - Get summary
- `poll_for_updates` - Check updates
- `create_notification` - Create notification

### **14. Proactive Intelligence (7 tools)**

**`insights.py` (3 tools)**
- `get_insights` - Get alerts
- `get_property_insights` - Property alerts
- `check_insights` - Check insights

**`daily_digest.py` (3 tools)**
- `get_daily_digest` - Get digest
- `trigger_daily_digest` - Generate digest
- `get_digest_history` - Get history

**`pipeline.py` (3 tools)**
- `get_pipeline_status` - Get status
- `trigger_pipeline_check` - Run automation
- `get_pipeline_history` - Get history

### **15. Scheduled Tasks (4 tools)**
`scheduled_tasks.py`
- `create_scheduled_task` - Create task
- `list_scheduled_tasks` - List tasks
- `cancel_scheduled_task` - Cancel task
- `get_task_details` - Get details

### **16. Cross-Property Analytics (4 tools)**
`analytics.py`
- `get_portfolio_summary` - Portfolio overview
- `get_pipeline_summary` - Pipeline breakdown
- `get_contract_summary` - Contract stats
- `get_activity_summary` - Activity stats

### **17. Follow-Up Queue (4 tools)**
`follow_ups.py`
- `get_follow_up_queue` - Get queue
- `complete_follow_up` - Mark complete
- `snooze_follow_up` - Snooze property
- `get_follow_up_stats` - Get stats

### **18. Comparable Sales (4 tools)**
`comps.py`
- `get_comps_dashboard` - Full dashboard
- `get_comp_sales` - Sales comps
- `get_comp_rentals` - Rental comps
- `get_comp_summary` - Get summary

### **19. Bulk Operations (3 tools)**
`bulk.py`
- `execute_bulk_operation` - Execute operation
- `list_bulk_operations` - List operations
- `get_bulk_operation_status` - Get status

### **20. Activity Timeline (4 tools)**
`activity_timeline.py`
- `get_activity_timeline` - Full timeline
- `get_property_timeline` - Property timeline
- `get_recent_activity` - Recent activity
- `search_activity_timeline` - Search timeline

### **21. Property Scoring (5 tools)**
`property_scoring.py`
- `score_property` - Score property
- `get_score_breakdown` - Get breakdown
- `bulk_score_properties` - Bulk score
- `get_top_properties` - Get top deals
- `reset_property_score` - Reset score

### **22. Market Watchlist (6 tools)**
`market_watchlist.py`
- `create_watchlist` - Create watchlist
- `list_watchlists` - List watchlists
- `toggle_watchlist` - Pause/resume
- `delete_watchlist` - Delete watchlist
- `check_watchlist_matches` - Check matches
- `get_watchlist_stats` - Get stats

### **23. Property Heartbeat (2 tools)**
`heartbeat.py`
- `get_property_heartbeat` - Get heartbeat
- `refresh_property_heartbeat` - Refresh heartbeat

### **24. Reports (2 tools)**
`reports.py`
- `generate_report` - Generate report
- `list_reports` - List reports

### **25. Intelligence Layer (22 tools)**
`intelligence.py`

**Predictive Intelligence (6 tools)**
- `predict_property_outcome` - Predict closing probability
- `recommend_next_action` - AI recommended actions
- `batch_predict_outcomes` - Batch predictions
- `record_deal_outcome` - Record actual outcome
- `get_agent_success_patterns` - Success patterns
- `get_prediction_accuracy` - Model accuracy

**Market Opportunities (3 tools)**
- `scan_market_opportunities` - Scan for deals
- `detect_market_shifts` - Detect market changes
- `find_similar_deals` - Find similar deals

**Relationship Intelligence (3 tools)**
- `score_relationship_health` - Score relationships
- `predict_best_contact_method` - Best contact method
- `analyze_contact_sentiment` - Sentiment analysis

**Negotiation Agent (3 tools)**
- `analyze_offer` - Analyze offers
- `generate_counter_offer` - Generate counter-offer
- `suggest_offer_price` - Suggest price

**Document Analysis (2 tools)**
- `analyze_inspection_report` - Analyze inspection
- `extract_contract_terms` - Extract terms

**Competitive Intelligence (3 tools)**
- `analyze_market_competition` - Analyze competition
- `detect_competitive_activity` - Detect competition
- `get_market_saturation` - Market saturation

**Deal Sequencing (2 tools)**
- `sequence_1031_exchange` - Orchestrate 1031
- `sequence_portfolio_acquisition` - Portfolio acquisition

### **26. Voice Assistant (8 tools)**
`voice_assistant.py`
- `create_phone_number` - Create phone number
- `list_phone_numbers` - List numbers
- `get_phone_number` - Get number details
- `update_phone_number` - Update number
- `delete_phone_number` - Delete number
- `make_phone_call` - Make call
- `get_call_transcript` - Get transcript
- `list_phone_calls` - List calls

### **27. Web Scraper (7 tools)**
`web_scraper.py`
- `scrape_url` - Scrape property URL
- `scrape_and_create` - Scrape and create property
- `scrape_zillow_search` - Scrape Zillow search
- `scrape_and_create_batch` - Batch import
- `scrape_redfin` - Scrape Redfin
- `scrape_realtor` - Scrape Realtor.com
- `test_scraper` - Test scraper

---

## 🚀 Server 2: Intelligence MCP Server

**Location:** `mcp_server/intelligence_mcp.py`
**Purpose:** FastMCP-based server for AI intelligence features
**Tools:** 23 tools (included in the 207 total above)

The intelligence server provides specialized AI tools for:
- Predictive analytics
- Market scanning
- Relationship analysis
- Negotiation assistance
- Document analysis
- Competitive intelligence
- Deal sequencing

---

## 📡 Server Transports

### stdio (default)
For local Claude Desktop usage:
```bash
python mcp_server/property_mcp.py
```

### SSE (Server-Sent Events)
For remote HTTP access:
```bash
python mcp_server/property_mcp.py --transport sse --port 8001
```

Deployed on Fly.io at:
- **SSE Endpoint:** `https://ai-realtor-mcp.fly.dev/sse`
- **Health Check:** `https://ai-realtor-mcp.fly.dev/health`

---

## 🔧 Server Configuration

### Claude Desktop Config
```json
{
  "mcpServers": {
    "property-management": {
      "command": "python3",
      "args": ["/path/to/ai-realtor/mcp_server/property_mcp.py"]
    }
  }
}
```

### Environment Variables Required
- `DATABASE_URL` - PostgreSQL connection string
- `ANTHROPIC_API_KEY` - Claude API key
- `GOOGLE_PLACES_API_KEY` - Google Places API
- `ZILLOW_API_KEY` - Zillow API
- And more (see .env.example)

---

## 🎯 Key Features

### Automatic Context Enrichment
Every MCP tool response is automatically enriched with:
- Related property data
- Recent activity
- Conversation history
- Agent preferences

### Activity Logging
All tool calls are automatically logged to:
- `activity_events` table for audit trail
- `conversation_history` for per-property tracking
- Real-time WebSocket feed

### Property Resolver
Natural language property resolution:
- Property ID
- Full address
- City name
- "The Hillsborough property"
- First/last/next property

### Voice-Native Responses
All tools return both detailed data and voice summaries for text-to-speech.

---

## 📊 Tool Categories Summary

| Category | Modules | Tools |
|----------|---------|-------|
| Property Management | 1 | 7 |
| Contacts & Skip Trace | 1 | 3 |
| Contracts | 2 | 15 |
| Recaps & Calls | 1 | 6 |
| Deals & Offers | 2 | 14 |
| Research & Search | 2 | 9 |
| Conversation | 1 | 5 |
| Property Notes | 1 | 3 |
| ElevenLabs | 1 | 4 |
| Voice Campaigns | 1 | 7 |
| Workflows | 1 | 3 |
| Notifications | 1 | 6 |
| Intelligence | 1 | 22 |
| Scheduled Tasks | 1 | 4 |
| Analytics | 1 | 4 |
| Pipeline | 1 | 3 |
| Daily Digest | 1 | 3 |
| Follow-Ups | 1 | 4 |
| Comps | 1 | 4 |
| Bulk Operations | 1 | 3 |
| Activity Timeline | 1 | 4 |
| Property Scoring | 1 | 5 |
| Market Watchlist | 1 | 6 |
| Heartbeat | 1 | 2 |
| Reports | 1 | 2 |
| Voice Assistant | 1 | 8 |
| Web Scraper | 1 | 7 |
| **TOTAL** | **32** | **207** |

---

## 🌐 Integration Points

### External APIs Integrated
- **Google Places** - Address autocomplete
- **Zillow** - Property enrichment
- **Skip Trace** - Owner discovery
- **DocuSeal** - E-signatures
- **VAPI** - Phone calls
- **ElevenLabs** - Voice synthesis
- **Exa** - Research
- **Anthropic Claude** - AI analysis
- **Meta Ads** - Facebook advertising
- **Postiz** - Social media management

---

## 📝 Usage Examples

### Voice Commands
```
"Create a property at 123 Main St for $850,000"
"Enrich property 5 with Zillow data"
"Is property 5 ready to close?"
"Call the owner of property 5"
"Show me my follow-up queue"
"Predict the outcome for property 5"
"Score property 5"
"Generate a recap for property 5"
```

### API Integration
```python
# Via MCP
result = await mcp.call_tool("list_properties", {"city": "Miami", "max_price": 500000})

# Via HTTP API
response = requests.get("https://ai-realtor.fly.dev/properties/?city=Miami&max_price=500000")
```

---

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

**Last Updated:** 2026-02-25
**Total MCP Tools:** 207
**Total Modules:** 32
**Total Servers:** 2 (Property Management + Intelligence)
