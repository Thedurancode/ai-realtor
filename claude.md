# AI Realtor Platform - Complete Feature Guide

## Overview

AI Realtor is an intelligent real estate management platform that combines property data enrichment, AI-powered analysis, voice-controlled operations, automated contract management, phone call automation, and autonomous goal execution. Built with FastAPI, PostgreSQL, and integrated with Claude AI, Zillow, DocuSeal, VAPI, and ElevenLabs.

**Live API:** https://ai-realtor.fly.dev
**Documentation:** https://ai-realtor.fly.dev/docs
**GitHub:** https://github.com/Thedurancode/ai-realtor

---

## Core Features

### 1. Property Management

**Create properties with intelligent address lookup**
- Google Places API integration for accurate address autocomplete
- Automatic geocoding and full address details
- Support for all property types: house, condo, townhouse, apartment, land, commercial, multi-family
- Advanced filtering by type, city, price range, bedrooms, and status

**Property data structure:**
- Basic info: address, city, state, ZIP, price, bedrooms, bathrooms, square footage
- Status tracking: new_property, enriched, researched, waiting_for_contracts, complete
- Deal scoring with grade (A-F) and pipeline status
- Agent assignment and session tracking
- Automatic activity logging

**API Endpoints:**
- `POST /properties/` - Create property with place_id
- `GET /properties/` - List properties with filters (status, property_type, city, min_price, max_price, bedrooms)
- `GET /properties/{id}` - Get property details
- `PUT /properties/{id}` - Update property
- `DELETE /properties/{id}` - Delete property and all related data

**MCP Tools:**
- `create_property` - Voice: "Create a property at 123 Main St, New York for $850,000"
- `list_properties` - Voice: "Show me all condos under 500k in Miami"
- `get_property` - Voice: "Get details for property 5" or "Get the Hillsborough property"
- `delete_property` - Voice: "Delete property 3"
- `update_property` - Voice: "Update property 5 status to complete"

---

### 2. Zillow Data Enrichment

**Comprehensive property enrichment from Zillow**
- High-resolution property photos (up to 10)
- Zestimate (current market value estimate)
- Rent Zestimate (monthly rental value)
- Tax assessment history
- Price history (past sales)
- Nearby schools with ratings and test scores
- Detailed property features (year built, lot size, parking, heating/cooling)
- Market statistics and comparables

**Enrichment triggers:**
- Manual via API or voice command
- Auto-recap regeneration after enrichment
- Background processing for performance

**API Endpoints:**
- `POST /properties/{id}/enrich` - Enrich property with Zillow data
- `GET /properties/{id}` - Includes enrichment data in response

**MCP Tools:**
- `enrich_property` - Voice: "Enrich property 5 with Zillow data"

---

### 3. Skip Trace Integration

**Owner contact discovery for lead generation**
- Finds property owner name
- Discovers phone numbers (mobile and landline)
- Email addresses
- Mailing address
- Auto-recap regeneration after skip trace

**MCP Tools:**
- `skip_trace_property` - Voice: "Skip trace property 5"
- `call_property_owner_skip_trace` - Voice: "Call the owner of property 5 and ask if they want to sell"

---

### 4. Contact Management

**Track all property stakeholders**
- Multiple contacts per property
- Role-based organization: buyer, seller, lawyer, attorney, contractor, inspector, appraiser, lender, mortgage_broker, title_company, tenant, landlord, property_manager, handyman, plumber, electrician, photographer, stager, other
- Contact info: name, email, phone
- Link contacts to specific properties
- Automatic contact creation from skip trace
- Auto-recap regeneration after contact added

**MCP Tools:**
- `add_contact` - Voice: "Add John Smith as a buyer for property 5, email john@example.com"

---

### 5. AI-Powered Contract Management

**Three-tier contract requirement system:**

#### A. Automatic Template Matching
- 15+ pre-configured contract templates for NY, CA, FL, TX
- State-specific requirements (disclosure laws, purchase agreements)
- Property type filtering (residential vs commercial)
- Price range filtering (high-value properties get additional contracts)
- City-specific contracts (NYC seller disclosure, etc.)
- `required_signer_roles` maps contracts to contact roles

#### B. AI-Suggested Contracts
- Claude AI analyzes property details
- Recommends required vs optional contracts
- Provides reasoning for each suggestion

#### C. Manual Control
- Override any automatic or AI suggestion
- Mark contracts as required or optional
- Set deadlines for contract completion

**Contract statuses:** DRAFT, SENT, IN_PROGRESS, PENDING_SIGNATURE, COMPLETED, CANCELLED, EXPIRED, ARCHIVED

**MCP Tools:**
```
check_property_contract_readiness         - Check if ready to close
check_property_contract_readiness_voice   - Voice version with natural response
check_contract_status                     - Check specific contract status
check_contract_status_voice               - Voice version
attach_required_contracts                 - Auto-attach matching templates
ai_suggest_contracts                      - Get AI contract suggestions
apply_ai_contract_suggestions             - Apply AI suggestions
mark_contract_required                    - Mark as required/optional
list_contracts                            - List all contracts
list_contracts_voice                      - Voice version
send_contract                             - Send contract for signature
smart_send_contract                       - Smart multi-party send
get_signing_status                        - Check signing status
```

---

### 6. DocuSeal Webhook Integration

**Real-time contract status synchronization**

When someone signs a contract in DocuSeal:
1. DocuSeal sends webhook to `POST /webhooks/docuseal`
2. API verifies HMAC-SHA256 signature for security
3. Updates contract status in database
4. Regenerates property recap in background
5. AI agent instantly knows contract is signed

**MCP Tools:**
- `test_webhook_configuration` - Check webhook setup

---

### 7. AI Property Recaps

**Intelligent property summaries with auto-regeneration**

Each property gets an AI-generated recap that includes:
- Comprehensive property overview
- Zestimate and market analysis
- Contract status and readiness
- Skip trace information
- Contact details
- Property notes
- Next steps and recommendations

**Three recap formats:**
1. **Detailed recap** (3-4 paragraphs) - For human reading
2. **Voice summary** (2-3 sentences) - For text-to-speech
3. **Structured context** (JSON) - For AI assistants and VAPI

**Auto-regeneration triggers (background):**
- Contract signed via webhook: `trigger="contract_signed"`
- Property enriched: `trigger="enrichment_updated"`
- Skip trace completed: `trigger="skip_trace_completed"`
- Note added: `trigger="note_added"`
- Contact added: `trigger="contact_added"`
- Property updated: `trigger="property_updated"`
- Manual regeneration: `trigger="manual"`

**MCP Tools:**
- `generate_property_recap` - Voice: "Generate recap for property 5"
- `get_property_recap` - Voice: "Get the recap for property 5"

---

### 8. VAPI Phone Call Automation

**AI-powered phone calls with full property context**

**Five call types:**
1. **Property Update** - Share property details
2. **Contract Reminder** - Remind about pending contracts
3. **Closing Ready** - Celebrate all contracts complete
4. **Specific Contract Reminder** - Call about one contract
5. **Skip Trace Outreach** - Cold call property owner

**MCP Tools:**
- `make_property_phone_call` - Voice: "Call John about property 5"
- `call_contact_about_contract` - Voice: "Call contact 3 about the Purchase Agreement"
- `call_property_owner_skip_trace` - Voice: "Call the owner of property 5"
- `elevenlabs_call` - Voice: "Call +14155551234 using ElevenLabs"
- `elevenlabs_setup` - Configure ElevenLabs voice
- `elevenlabs_status` - Check call status

---

### 9. Voice Goal Planner

**Autonomous multi-step goal execution**

Say a natural language goal and the planner builds and executes a plan automatically.

**26 supported actions:**
- `resolve_property` - Find the target property
- `inspect_property` - Load property context
- `enrich_property` - Pull Zillow data
- `skip_trace_property` - Find owner contacts
- `attach_required_contracts` - Auto-attach templates
- `ai_suggest_contracts` - Get AI suggestions
- `apply_ai_suggestions` - Create suggested contracts
- `check_compliance` - Run compliance check
- `generate_recap` - Generate AI recap
- `make_phone_call` - Call via VAPI
- `send_notification` - Send alert
- `update_property_status` - Change status
- `add_note` - Save a note to the property
- `summarize_next_actions` - Summary and next steps
- `check_contract_readiness` - Check closing readiness
- `create_property` - Create new property
- `check_insights` - Scan for alerts and issues
- `schedule_task` - Create reminders and recurring tasks
- `get_analytics` - Pull portfolio-wide analytics
- `check_follow_ups` - Get AI-prioritized follow-up queue
- `get_comps` - Pull comparable sales dashboard
- `bulk_operation` - Execute operations across multiple properties
- `get_activity_timeline` - Fetch unified activity timeline
- `score_property` - Run 4-dimension property scoring engine
- `check_watchlists` - List and manage market watchlists

**Heuristic plan matching:**
- "Set up property 5 as a new lead" → resolve → enrich → skip trace → contracts → recap → summarize
- "Close the deal on property 3" → resolve → check readiness → recap → summarize
- "Note that property 2 has a new fence" → resolve → add note → summarize
- "Enrich property 5" → resolve → enrich → recap → summarize
- "Skip trace property 5" → resolve → skip trace → summarize
- "Call the owner of property 5" → resolve → skip trace → call → summarize
- "Show me comps for property 5" → resolve → get comps → summarize
- "Enrich all Miami properties" → bulk operation → summarize
- "What should I work on next?" → check follow-ups → summarize
- "What happened today?" → resolve → get activity timeline → summarize
- "What needs attention?" → check insights → summarize
- "Remind me to follow up on property 5 in 3 days" → resolve → schedule task → summarize
- "How's my portfolio doing?" → get analytics → summarize
- "Score property 5" → resolve → score property → summarize
- "How good is this deal?" → resolve → score property → summarize
- "What are my best deals?" → resolve → score property → summarize
- "Watch for Miami condos under 500k" → check watchlists → summarize
- "Show me my watchlists" → check watchlists → summarize

**Safety features:**
- Checkpoint/rollback after each step
- Failure isolation (one step failing doesn't crash the plan)
- Memory graph persistence of relationships

---

### 10. Property Notes

**Freeform notes attached to properties**

- Sources: voice, manual, ai, phone_call, system
- Full CRUD API
- Integrated into AI recaps
- Voice goal planner can add notes
- Auto-recap regeneration on new notes

**API Endpoints:**
```
POST   /property-notes/                    - Create note
GET    /property-notes/?property_id=5      - List notes for property
GET    /property-notes/{id}                - Get specific note
PUT    /property-notes/{id}                - Update note
DELETE /property-notes/{id}                - Delete note
```

**MCP Tools:**
- `add_property_note` - Voice: "Note that property 5 has a new fence installed"
- `list_property_notes` - Voice: "Show me notes for property 5"

---

### 11. Property Audit Trail (Conversation History)

**Per-property action tracking**

Every MCP tool call that includes a `property_id` is automatically logged to that property's audit trail. Zero configuration required.

**What gets tracked:**
- Enrichments, skip traces, notes, contracts, phone calls, contacts, status changes
- Tool name, input summary, output summary, duration, success/failure
- Timestamp for chronological timeline

**API Endpoints:**
```
POST /context/history/log                        - Log conversation entry
GET  /context/history                            - Get session history (with optional property_id filter)
GET  /context/history/property/{property_id}     - Get full property timeline
DELETE /context/history                           - Clear history
```

**MCP Tools:**
- `get_property_history` - Voice: "What have we done on property 5?"
- `get_conversation_history` - Voice: "What did we talk about?"
- `what_did_we_discuss` - Voice: "Remind me what we discussed"
- `clear_conversation_history` - Voice: "Start fresh"

---

### 12. Workflow Templates

**Pre-built multi-step workflows**

5 workflow templates for common real estate operations:
1. **New Lead Setup** - Enrich → Skip trace → Contracts → Recap
2. **Deal Closing** - Check readiness → Final contracts → Recap
3. **Property Enrichment** - Zillow data → Recap generation
4. **Skip Trace & Outreach** - Skip trace → Cold call owner
5. **AI Contract Setup** - AI suggest → Apply suggestions → Check readiness

**API Endpoints:**
```
GET  /workflows/                   - List available workflows
POST /workflows/{template}/execute - Execute a workflow
```

**MCP Tools:**
- `list_workflows` - Voice: "What workflows are available?"
- `execute_workflow` - Voice: "Run the new lead workflow on property 5"

---

### 13. Voice Campaign Management

**Bulk outreach campaigns**

Create and manage automated phone call campaigns targeting multiple properties/contacts.

**MCP Tools:**
- `create_voice_campaign` - Voice: "Create a campaign for cold calling owners"
- `start_voice_campaign` - Voice: "Start campaign 3"
- `pause_voice_campaign` - Voice: "Pause campaign 3"
- `get_campaign_status` - Voice: "How is campaign 3 doing?"
- `list_voice_campaigns` - Voice: "Show me all campaigns"
- `add_campaign_targets` - Voice: "Add properties 5-10 to campaign 3"

---

### 14. Proactive Notifications

**Alerts and summaries pushed to the agent**

**MCP Tools:**
- `send_notification` - Send custom alerts
- `list_notifications` - View recent notifications
- `acknowledge_notification` - Mark as read
- `get_notification_summary` - Voice: "Any notifications?"
- `poll_for_updates` - Check for new updates
- `send_property_report` - Generate and send property report

---

### 15. Context Auto-Injection

**Automatic context enrichment for MCP responses**

Every MCP tool response is automatically enriched with relevant property context (from `mcp_server/utils/context_enrichment.py`). The AI always has awareness of related data without being asked.

---

### 16. Deal Calculator & Offers

**Investment analysis and offer management**

**MCP Tools:**
```
calculate_deal          - Run deal analysis (ROI, cash flow, cap rate)
calculate_mao           - Calculate maximum allowable offer
what_if_deal            - What-if scenario modeling
compare_strategies      - Compare investment strategies
preview_deal_type       - Preview deal type configuration
set_deal_type           - Set property deal type
get_deal_status         - Get current deal status
create_deal_type_config - Create deal type config
update_deal_type_config - Update deal type config
delete_deal_type_config - Delete deal type config
list_deal_types         - List all deal types

create_offer            - Create offer on property
list_offers             - List all offers
get_offer_details       - Get offer details
accept_offer            - Accept an offer
reject_offer            - Reject an offer
counter_offer           - Counter an offer
withdraw_offer          - Withdraw an offer
draft_offer_letter      - Generate offer letter
```

---

### 17. Research & Semantic Search

**AI-powered property research**

**MCP Tools:**
- `research_property` - Deep research on a property
- `research_property_async` - Background research
- `get_research_status` - Check research progress
- `get_research_dossier` - Get completed research
- `search_research` - Search past research
- `semantic_search` - Semantic search across properties
- `find_similar_properties` - Find similar properties

---

### 18. Compliance Engine

**AI-powered real estate compliance checking**

Ensures transactions comply with federal (RESPA, TILA, Fair Housing), state, and local regulations.

**API Endpoints:**
```
POST /compliance/check          - Run compliance check
GET  /compliance/requirements   - Get requirements for state/type
```

---

### 19. Real-time Activity Feed

**Live event tracking via WebSocket**

Track all events in real-time: property CRUD, enrichments, skip traces, contracts, phone calls, MCP tool executions.

**WebSocket:** `ws://localhost:8000/ws`
**Display commands:** `POST /display/command`

---

### 20. Proactive Insights

**On-demand intelligence that surfaces problems before they escalate**

6 alert rules scan your properties:
1. **Stale properties** — No activity in 7+ days (14+ = high priority)
2. **Contract deadlines** — Required contracts approaching or overdue deadlines
3. **Unsigned contracts** — Required contracts sitting in DRAFT/SENT for 3+ days
4. **Missing enrichment** — Properties without Zillow data
5. **Missing skip trace** — Properties with unknown owners
6. **High score, no action** — Deal score 80+ but no contracts started

Alerts are grouped by priority (urgent/high/medium/low) with voice summaries.

**API Endpoints:**
```
GET /insights/                      - All alerts (optional ?priority= filter)
GET /insights/property/{property_id} - Alerts for one property
```

**MCP Tools:**
- `get_insights` - Voice: "What needs attention?" or "Show me alerts"
- `get_property_insights` - Voice: "Any issues with property 5?"

---

### 21. Scheduled Tasks

**Persistent reminders, follow-ups, and recurring tasks**

DB-backed task system with background runner (60-second loop).

**Task types:** REMINDER, RECURRING, FOLLOW_UP, CONTRACT_CHECK

**Features:**
- Automatic notification creation when tasks are due
- Recurring tasks auto-create next occurrence
- Property-linked tasks for context
- Background asyncio loop processes due tasks

**API Endpoints:**
```
POST   /scheduled-tasks/              - Create task
GET    /scheduled-tasks/              - List tasks (optional ?status= filter)
GET    /scheduled-tasks/{id}          - Get specific task
DELETE /scheduled-tasks/{id}/cancel   - Cancel task
GET    /scheduled-tasks/due           - List due tasks
```

**MCP Tools:**
- `create_scheduled_task` - Voice: "Remind me to follow up on property 5 in 3 days"
- `list_scheduled_tasks` - Voice: "What tasks are scheduled?"
- `cancel_scheduled_task` - Voice: "Cancel task 3"

---

### 22. Cross-Property Analytics

**Portfolio-level intelligence aggregated from existing data**

6 metric categories:
1. **Pipeline stats** — Properties by status and type
2. **Portfolio value** — Total price, average price, total Zestimate, equity
3. **Contract stats** — By status, unsigned required count
4. **Activity stats** — Actions in last 24h/7d/30d, most active properties
5. **Deal scores** — Average score, grade distribution (A-F), top 5 deals
6. **Enrichment coverage** — Zillow and skip trace percentages

**API Endpoints:**
```
GET /analytics/portfolio  - Full portfolio dashboard
GET /analytics/pipeline   - Pipeline breakdown only
GET /analytics/contracts  - Contract stats only
```

**MCP Tools:**
- `get_portfolio_summary` - Voice: "How's my portfolio?" or "Give me the numbers"
- `get_pipeline_summary` - Voice: "How many properties in each status?"
- `get_contract_summary` - Voice: "How are my contracts looking?"

---

### 23. Pipeline Automation

**Auto-advance property status based on activity**

Properties automatically move through your pipeline:

| From | To | Condition |
|---|---|---|
| NEW_PROPERTY | ENRICHED | Zillow enrichment data available |
| ENRICHED | RESEARCHED | Skip trace completed |
| RESEARCHED | WAITING_FOR_CONTRACTS | At least 1 contract attached |
| WAITING_FOR_CONTRACTS | COMPLETE | All required contracts COMPLETED |

**Safety features:**
- 24-hour grace period after manual status changes
- Notifications created for every auto-transition
- Conversation history logged for audit trail
- Recap auto-regenerated after status change
- Runs every 5 minutes in the background

**API Endpoints:**
```
GET  /pipeline/status  - Recent auto-transitions
POST /pipeline/check   - Manual trigger for testing
```

**MCP Tools:**
- `get_pipeline_status` - Voice: "What's the pipeline status?" or "Show recent auto-transitions"
- `trigger_pipeline_check` - Voice: "Run pipeline automation now"

---

### 24. Daily Digest

**AI-generated morning briefing combining insights + analytics + notifications**

Claude AI generates a daily digest every morning at 8 AM (configurable) that includes:
- Portfolio snapshot (total properties, value, changes)
- Urgent alerts from insights
- Contract status summary
- Activity summary (last 24h)
- Top recommendations

**Two outputs:**
1. **Full briefing** (3-5 paragraphs) — For reading
2. **Voice summary** (2-3 sentences) — For text-to-speech

Auto-scheduled as a recurring task on server startup. Stored as DAILY_DIGEST notification.

**API Endpoints:**
```
GET  /digest/latest           - Most recent digest
POST /digest/generate         - Manual trigger
GET  /digest/history?days=7   - Past digests
```

**MCP Tools:**
- `get_daily_digest` - Voice: "What's my daily digest?" or "Morning summary"
- `trigger_daily_digest` - Voice: "Generate a fresh digest now"

---

### 25. Smart Follow-Up Queue

**AI-prioritized queue ranking properties by urgency**

Scoring algorithm combines weighted signals:
- Days since last activity (base score, capped at 300)
- Deal grade multiplier (A=2x through F=0.5x)
- Contract deadline approaching (+40)
- Overdue tasks (+35)
- Unsigned required contracts (+30)
- Skip trace with no outreach (+25)
- Missing contacts (+15)

Priority mapping: 300+ = urgent, 200+ = high, 100+ = medium, below = low

**Features:**
- Batch signal queries to avoid N+1
- Snooze via ScheduledTask (default 72h)
- Complete action logs to ConversationHistory
- Best contact finder (prefers buyer → seller → skip trace owner)

**API Endpoints:**
```
GET  /follow-ups/queue?limit=10&priority=high   - Get ranked queue
POST /follow-ups/{property_id}/complete          - Mark follow-up done
POST /follow-ups/{property_id}/snooze?hours=72   - Snooze property
```

**MCP Tools:**
- `get_follow_up_queue` - Voice: "What should I work on next?" or "Show me my follow-up queue"
- `complete_follow_up` - Voice: "Mark follow-up done for property 5"
- `snooze_follow_up` - Voice: "Snooze property 5 for 48 hours"

---

### 26. Comparable Sales Dashboard

**Comp aggregation from 3 data sources with market metrics**

**Data sources:**
1. **Agentic research** — CompSale/CompRental records from deep property research
2. **Zillow price_history** — Historical sales from enrichment data
3. **Internal portfolio** — Same city/state properties with similarity scoring

**Market metrics:**
- Average/median sale prices
- Price per square foot
- 6-month price trend analysis
- Subject vs market comparison
- Zestimate vs comps analysis
- Pricing recommendation (rules-based, no LLM)

**API Endpoints:**
```
GET /comps/{property_id}          - Full dashboard (all sources + metrics)
GET /comps/{property_id}/sales    - Sales comps only
GET /comps/{property_id}/rentals  - Rental comps only
```

**MCP Tools:**
- `get_comps_dashboard` - Voice: "Show me comps for property 5"
- `get_comp_sales` - Voice: "What are nearby sales for property 5?"
- `get_comp_rentals` - Voice: "What are rental comps for property 5?"

---

### 27. Bulk Operations Engine

**Execute operations across multiple properties at once**

**6 supported operations:**

| Operation | What it does | Skip Logic |
|---|---|---|
| `enrich` | Zillow enrichment | Skip if already enriched (unless force=true) |
| `skip_trace` | Owner contact discovery | Skip if already traced (unless force=true) |
| `attach_contracts` | Auto-attach contract templates | Always run |
| `generate_recaps` | AI property recaps | Always run |
| `update_status` | Change property status | Skip if already target status |
| `check_compliance` | Regulatory compliance check | Always run |

**Features:**
- Property selection via explicit IDs AND/OR dynamic filters (city, status, property_type, price range, bedrooms)
- Union of both selection methods, capped at 50 properties
- Per-property error isolation with individual commits
- Voice summary of results

**API Endpoints:**
```
POST /bulk/execute      - Execute a bulk operation
GET  /bulk/operations   - List available operations
```

**MCP Tools:**
- `execute_bulk_operation` - Voice: "Enrich all Miami properties" or "Skip trace properties 1 through 5"
- `list_bulk_operations` - Voice: "What bulk operations are available?"

---

### 28. Activity Timeline Dashboard

**Unified chronological event feed from 7 data sources**

**Data sources aggregated:**
1. **ConversationHistory** — MCP tool calls and voice commands
2. **Notification** — System alerts and task completions
3. **PropertyNote** — Freeform notes from all sources
4. **ScheduledTask** — Reminders, follow-ups, recurring tasks
5. **Contract** — Lifecycle events (created, sent, completed)
6. **ZillowEnrichment** — Enrichment completions
7. **SkipTrace** — Skip trace completions

**Features:**
- Per-property AND portfolio-wide views
- Filter by event types, date range, text search
- Contracts emit 3 events from different timestamps (created, sent, completed)
- Pagination with offset/limit
- Voice summaries with type counts and latest event

**API Endpoints:**
```
GET /activity-timeline/                        - Full timeline with all filters
GET /activity-timeline/property/{property_id}  - Property-specific timeline
GET /activity-timeline/recent?hours=24         - Last N hours of activity
```

**MCP Tools:**
- `get_activity_timeline` - Voice: "Show me the timeline" or "What's the activity on property 5?"
- `get_property_timeline` - Voice: "Show me everything on property 3"
- `get_recent_activity` - Voice: "What happened today?" or "What's new?"

---

### 29. Property Scoring Engine

**Multi-dimensional deal quality scoring across 4 dimensions**

Replaces the old 6-component scorer with a richer 4-dimension engine. Uses existing `deal_score`, `score_grade`, `score_breakdown` columns (no migration needed).

**4 Scoring Dimensions:**

| Dimension | Weight | What It Measures |
|---|---|---|
| **Market** | 30% | Zestimate spread, days on market, price trend, school quality, tax gap |
| **Financial** | 25% | Zestimate upside, rental yield, price per sqft |
| **Readiness** | 25% | Contract completion %, contact coverage, skip trace reachability |
| **Engagement** | 20% | Recent activity (7d), notes count, active tasks, recent notifications |

Each dimension produces a sub-score (0-100). Final score = weighted average with re-normalization when data is missing.

**Grade scale:** A (80+), B (60+), C (40+), D (20+), F (<20)

**Data sources:** ZillowEnrichment, Property, Contract, Contact, SkipTrace, ConversationHistory, PropertyNote, ScheduledTask, Notification

**API Endpoints:**
```
POST /scoring/property/{property_id}    - Score a single property (recalculates)
POST /scoring/bulk                      - Score multiple properties
GET  /scoring/property/{property_id}    - Get stored score breakdown
GET  /scoring/top?limit=10&min_score=0  - Get top-scored properties
```

**MCP Tools:**
- `score_property` - Voice: "Score property 5" or "Rate this deal" or "How good is property 5?"
- `get_score_breakdown` - Voice: "Show me the score breakdown for property 5"
- `bulk_score_properties` - Voice: "Score all my properties" or "Rate everything"
- `get_top_properties` - Voice: "What are my best deals?" or "Top properties" or "Show me A-grade deals"

---

### 30. Market Watchlist

**Saved-search alerts that fire when new matching properties are added**

Create watchlists with criteria (city, state, property type, price range, bedrooms, bathrooms, sqft). When any new property is created via `POST /properties/` or `POST /properties/voice`, all active watchlists are checked. Matches create HIGH priority notifications.

**Criteria (AND logic — all provided criteria must match):**
- `city` — case-insensitive partial match
- `state` — case-insensitive exact match
- `property_type` — exact match (house, condo, townhouse, etc.)
- `min_price` / `max_price` — price range
- `min_bedrooms` / `min_bathrooms` — minimum rooms
- `min_sqft` — minimum square footage

**API Endpoints:**
```
POST   /watchlists/                     - Create watchlist
GET    /watchlists/                     - List watchlists (optional ?agent_id= ?is_active=)
GET    /watchlists/{id}                 - Get specific watchlist
PUT    /watchlists/{id}                 - Update watchlist
DELETE /watchlists/{id}                 - Delete watchlist
POST   /watchlists/{id}/toggle          - Pause/resume watchlist
POST   /watchlists/check/{property_id}  - Manual check against all watchlists
```

**MCP Tools:**
- `create_watchlist` - Voice: "Watch for Miami condos under 500k"
- `list_watchlists` - Voice: "Show me my watchlists"
- `toggle_watchlist` - Voice: "Pause watchlist 1"
- `delete_watchlist` - Voice: "Delete watchlist 3"
- `check_watchlist_matches` - Voice: "Does property 5 match any watchlists?"

---

### 31. Property Heartbeat

**At-a-glance pipeline stage, checklist, and health status for every property**

Each property gets a computed heartbeat showing:
- **Pipeline stage**: Which of the 5 stages it's in (with progress index)
- **Checklist**: 4 items tracking enrichment, skip trace, contracts attached, contracts completed
- **Health status**: healthy (progressing), stale (stuck too long), or blocked (can't advance)
- **Next action**: What to do next to advance the pipeline
- **Voice summary**: 1-2 sentence summary for text-to-speech

**Per-stage stale thresholds:**
| Stage | Threshold |
|-------|-----------|
| New Property | 3 days |
| Enriched | 5 days |
| Researched | 7 days |
| Waiting for Contracts | 10 days |
| Complete | never |

Heartbeat is auto-included in all property responses (`GET /properties/` and `GET /properties/{id}`). Opt out with `?include_heartbeat=false`.

**API Endpoints:**
```
GET /properties/{id}/heartbeat  - Dedicated heartbeat endpoint
GET /properties/{id}            - Includes heartbeat by default
GET /properties/                - Includes heartbeat for all properties (batch-optimized)
```

**MCP Tools:**
- `get_property_heartbeat` - Voice: "What's the heartbeat on property 5?", "How is property 3 doing?", "Is property 5 stuck?"

---

### 32. Web Scraper

**Automated property data extraction from any website**

Point the AI at any property listing URL (Zillow, Redfin, Realtor.com, or any generic site) and automatically extract structured property data. Create properties directly from URLs with voice commands.

**Features:**
- Specialized scrapers for Zillow, Redfin, Realtor.com with accurate selectors
- Generic AI-powered scraper for any website using Claude Sonnet 4
- Concurrent scraping with rate limiting (respectful to servers)
- Duplicate detection before creating properties
- Auto-enrichment option after scraping
- Batch import from search results (Zillow search pages)

**Data extracted:**
- Address, city, state, ZIP
- Price, bedrooms, bathrooms, square footage
- Year built, lot size, property type
- Property description
- Photo URLs (when available)

**API Endpoints:**
```
POST /scrape/url                    - Scrape URL and preview data
POST /scrape/multiple               - Scrape multiple URLs concurrently
POST /scrape/scrape-and-create      - Scrape and create property
POST /scrape/zillow-listing         - Convenience for Zillow URLs
POST /scrape/redfin-listing         - Convenience for Redfin URLs
POST /scrape/realtor-listing        - Convenience for Realtor.com URLs
POST /scrape/zillow-search          - Scrape Zillow search results
POST /scrape/scrape-and-enrich-batch - Bulk import with enrichment
```

**MCP Tools:**
- `scrape_url` - Voice: "Scrape this Zillow listing", "What data can we get from this URL?"
- `scrape_and_create` - Voice: "Add this property from the URL", "Create property from this Redfin link"
- `scrape_zillow_search` - Voice: "Show me properties from this Zillow search"
- `scrape_and_create_batch` - Voice: "Import these 10 Zillow listings and enrich them all"
- `scrape_redfin` - Voice: "Add this Redfin property to my portfolio"
- `scrape_realtor` - Voice: "Import this Realtor.com listing"

---

## MCP Tools — Complete List (135 tools)

**Property Tools (7):**
`list_properties`, `get_property`, `create_property`, `update_property`, `delete_property`, `enrich_property`, `skip_trace_property`

**Contact Tools (1):**
`add_contact`

**Contract Tools (13):**
`check_property_contract_readiness`, `check_property_contract_readiness_voice`, `check_contract_status`, `check_contract_status_voice`, `attach_required_contracts`, `ai_suggest_contracts`, `apply_ai_contract_suggestions`, `mark_contract_required`, `list_contracts`, `list_contracts_voice`, `send_contract`, `smart_send_contract`, `get_signing_status`

**Recap & Call Tools (9):**
`generate_property_recap`, `get_property_recap`, `make_property_phone_call`, `call_contact_about_contract`, `call_property_owner_skip_trace`, `elevenlabs_call`, `elevenlabs_setup`, `elevenlabs_status`, `send_property_report`

**Deal & Offer Tools (18):**
`calculate_deal`, `calculate_mao`, `what_if_deal`, `compare_strategies`, `preview_deal_type`, `set_deal_type`, `get_deal_status`, `create_deal_type_config`, `update_deal_type_config`, `delete_deal_type_config`, `list_deal_types`, `create_offer`, `list_offers`, `get_offer_details`, `accept_offer`, `reject_offer`, `counter_offer`, `draft_offer_letter`, `withdraw_offer`

**Research & Search Tools (7):**
`research_property`, `research_property_async`, `get_research_status`, `get_research_dossier`, `search_research`, `semantic_search`, `find_similar_properties`

**Conversation & History Tools (4):**
`get_conversation_history`, `what_did_we_discuss`, `clear_conversation_history`, `get_property_history`

**Property Notes Tools (2):**
`add_property_note`, `list_property_notes`

**🆕 NEW: Intelligence Tools (23):**

**Predictive Intelligence (6):**
`predict_property_outcome` - Predict closing probability (0-100%) with confidence
`recommend_next_action` - AI-recommended next action with reasoning
`batch_predict_outcomes` - Batch predict across multiple properties
`record_deal_outcome` - Record actual outcome for machine learning
`get_agent_success_patterns` - Get agent's success patterns (type/city/price)
`get_prediction_accuracy` - Evaluate prediction accuracy (MAE, directional)

**Market Opportunity Scanner (3):**
`scan_market_opportunities` - Find deals matching agent's success patterns
`detect_market_shifts` - Detect market shifts (price drops/surges >10%)
`find_similar_properties` - Find similar properties for comparison

**Relationship Intelligence (3):**
`score_relationship_health` - Score relationship health (0-100) with trend
`predict_best_contact_method` - Predict best contact method (phone/email/text)
`analyze_contact_sentiment` - Analyze sentiment trend over time

**Negotiation Agent (3):**
`analyze_offer` - Analyze offers against deal metrics and market
`generate_counter_offer` - Generate AI counter-offer letter with justification
`suggest_offer_price` - Suggest optimal offer (conservative/moderate/aggressive)

**Document Analysis (2):**
`analyze_inspection_report` - Extract issues from inspection with NLP
`extract_contract_terms` - Extract contract terms automatically

**Competitive Intelligence (3):**
`analyze_market_competition` - Analyze competing agents in market
`detect_competitive_activity` - Alert if competition interested in property
`get_market_saturation` - Assess inventory levels and demand

**Deal Sequencer (3):**
`sequence_1031_exchange` - Orchestrate 1031 exchange with deadline management
`sequence_portfolio_acquisition` - Sequence buying multiple properties
`sequence_sell_and_buy` - Manage sale-and-buy with contingencies

**Workflow Tools (2):**
`list_workflows`, `execute_workflow`

**Campaign Tools (6):**
`create_voice_campaign`, `start_voice_campaign`, `pause_voice_campaign`, `get_campaign_status`, `list_voice_campaigns`, `add_campaign_targets`

**Notification Tools (5):**
`send_notification`, `list_notifications`, `acknowledge_notification`, `get_notification_summary`, `poll_for_updates`

**Insights Tools (2):**
`get_insights`, `get_property_insights`

**Scheduled Task Tools (3):**
`create_scheduled_task`, `list_scheduled_tasks`, `cancel_scheduled_task`

**Analytics Tools (3):**
`get_portfolio_summary`, `get_pipeline_summary`, `get_contract_summary`

**Pipeline Automation Tools (2):**
`get_pipeline_status`, `trigger_pipeline_check`

**Daily Digest Tools (2):**
`get_daily_digest`, `trigger_daily_digest`

**Follow-Up Queue Tools (3):**
`get_follow_up_queue`, `complete_follow_up`, `snooze_follow_up`

**Comparable Sales Tools (3):**
`get_comps_dashboard`, `get_comp_sales`, `get_comp_rentals`

**Bulk Operations Tools (2):**
`execute_bulk_operation`, `list_bulk_operations`

**Activity Timeline Tools (3):**
`get_activity_timeline`, `get_property_timeline`, `get_recent_activity`

**Property Scoring Tools (4):**
`score_property`, `get_score_breakdown`, `bulk_score_properties`, `get_top_properties`

**Market Watchlist Tools (5):**
`create_watchlist`, `list_watchlists`, `toggle_watchlist`, `delete_watchlist`, `check_watchlist_matches`

**Heartbeat Tools (1):**
`get_property_heartbeat`

**Webhook Tools (1):**
`test_webhook_configuration`

**🆕 NEW: Web Scraper Tools (6):**
`scrape_url` - Scrape a property URL and extract data (preview only)
`scrape_and_create` - Scrape URL and auto-create property in database
`scrape_zillow_search` - Scrape Zillow search results for multiple properties
`scrape_and_create_batch` - Bulk import multiple URLs with auto-enrichment
`scrape_redfin` - Scrape Redfin listing and create property
`scrape_realtor` - Scrape Realtor.com listing and create property

**Total: 135 MCP tools** for complete voice control of the entire platform.

---

## Voice Examples

```
# Property Management
"Create a property at 123 Main St, New York for $850,000 with 2 bedrooms"
"Show me all condos under 500k in Miami"
"Show me houses with 3+ bedrooms"
"Update property 5 status to complete"

# Data Enrichment
"Enrich property 5 with Zillow data"
"Skip trace property 5 to find the owner"

# Contracts
"Is property 5 ready to close?"
"Suggest contracts for property 5 using AI"
"Apply AI contract suggestions for property 5"
"Send the Purchase Agreement for signing"

# Phone Calls
"Call John about property 5"
"Call the owner of property 5 and ask if they want to sell"
"Call contact 3 about the Purchase Agreement"

# Notes & History
"Note that property 5 has a new fence installed"
"What have we done on property 5?"
"What did we talk about?"

# Autonomous Goals
"Set up property 5 as a new lead"
"Close the deal on property 3"
"Run the new lead workflow on property 5"

# Deals & Offers
"Calculate the deal on property 5"
"Create an offer for $800,000 on property 5"
"What's the MAO for property 5?"

# Campaigns
"Create a cold calling campaign for Brooklyn properties"
"Start campaign 3"
"How is campaign 3 doing?"

# Research
"Research property 5 in depth"
"Find properties similar to property 5"

# Insights & Alerts
"What needs attention?"
"Any issues with property 5?"
"Show me alerts"

# Scheduling
"Remind me to follow up on property 5 in 3 days"
"What tasks are scheduled?"
"Cancel task 3"

# Analytics
"How's my portfolio doing?"
"How many properties in each status?"
"How are my contracts looking?"

# Pipeline Automation
"What's the pipeline status?"
"Run pipeline automation now"
"Show recent auto-transitions"

# Daily Digest
"What's my daily digest?"
"Morning summary"
"Generate a fresh digest now"

# Follow-Up Queue
"What should I work on next?"
"Show me my follow-up queue"
"Snooze property 5 for 48 hours"

# Comparable Sales
"Show me comps for property 5"
"What are nearby sales for property 5?"
"What are rental comps for property 5?"

# Bulk Operations
"Enrich all Miami properties"
"Skip trace properties 1 through 5"
"Generate recaps for all available properties"
"What bulk operations are available?"

# Activity Timeline
"Show me the timeline"
"What happened today?"
"What's the activity on property 5?"
"Show me everything on property 3"
"What's new?"

# Property Scoring
"Score property 5"
"Rate this deal"
"How good is property 3?"
"Grade this property"
"Score all my properties"
"What are my best deals?"
"Show me A-grade deals"
"Show me the score breakdown for property 5"

# Market Watchlists
"Watch for Miami condos under 500k"
"Set up alerts for Brooklyn 3-bedrooms"
"Alert me when houses under 300k in Austin come up"
"Show me my watchlists"
"What am I watching?"
"Pause watchlist 1"
"Delete watchlist 3"
"Does property 5 match any watchlists?"

# Property Heartbeat
"What's the heartbeat on property 5?"
"How is property 3 doing?"
"Is property 5 stuck?"
"Check the pulse on the Hillsborough property"

# 🆕 Web Scraper
"Scrape this Zillow listing URL"
"What data can we extract from this Redfin page?"
"Add this property from the URL"
"Create property from this Realtor.com link"
"Import these 10 Zillow listings and enrich them all"
"Show me properties from this Zillow search page"
"Batch import these URLs into my portfolio"
"Scrape this Redfin property and auto-enrich it"

# 🆕 Predictive Intelligence
"Predict the outcome for property 5"
"What's the closing probability for property 3?"
"What should I do next with property 5?"
"Recommend next action for the Hillsborough property"
"Predict outcomes for all my active deals"
"Record that property 5 closed successfully for $450,000"
"What are my success patterns as an agent?"
"How accurate are my predictions?"

# 🆕 Market Opportunities
"Scan for opportunities matching my patterns"
"Find deals like my winners in Miami"
"Any market shifts in Austin?"
"Show me properties similar to 123 Main St"
"Detect market changes in my watchlist cities"

# 🆕 Relationship Intelligence
"How's my relationship with John Smith?"
"Score relationship health for contact 3"
"Predict the best way to reach Sarah"
"Should I call or email the buyer?"
"Analyze sentiment for contact 5"
"Is my relationship with the seller improving?"

# 🆕 Negotiation
"Analyze this $400,000 offer on property 5"
"What's the acceptance probability?"
"Generate a counter-offer for $425,000"
"Suggest an offer price for property 3"
"What should I offer? Be aggressive"
"Calculate walkaway price for property 5"

# 🆕 Document Analysis
"Analyze this inspection report for property 5"
"Extract issues from this inspection text"
"Do these appraisals match?"
"Extract terms from this contract"
"What are the key issues in this report?"

# 🆕 Competitive Intelligence
"Who are the top agents in Miami?"
"Analyze competition in Austin, Texas"
"Is there competition for property 5?"
"Detect competitive activity on 123 Main St"
"What's the market saturation in Denver?"
"Is it a buyer's or seller's market in Austin?"

# 🆕 Deal Sequencing
"Set up a 1031 exchange for property 5"
"Find replacement properties for my 1031 exchange"
"Sequence buying properties 1, 2, and 3"
"I need to sell 5 and buy 10 with contingencies"
"Orchestrate a portfolio acquisition parallel"
```

---

## Technology Stack

**Backend:**
- FastAPI (Python 3.11)
- PostgreSQL (via Fly.io)
- SQLAlchemy ORM
- Alembic migrations
- Pydantic v2 validation

**AI & ML:**
- Anthropic Claude Sonnet 4 (contract analysis, recaps, compliance)
- GPT-4 Turbo (VAPI phone calls)
- Semantic search / vector embeddings

**External APIs:**
- Google Places API (address lookup)
- Zillow API (property enrichment)
- Skip Trace API (owner discovery)
- DocuSeal API (e-signatures)
- VAPI API (phone calls)
- ElevenLabs API (voice synthesis)
- Exa API (research)
- Anthropic Claude (AI analysis)

**Voice & Communication:**
- MCP Server (Claude Desktop integration) — 135 tools
- VAPI (voice AI platform)
- ElevenLabs (text-to-speech)
- WebSocket (real-time updates)

**Deployment:**
- Fly.io (cloud hosting)
- Docker containers
- Depot (fast builds)
- PostgreSQL on Fly.io
- Supervisor for process management

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Claude Desktop                          │
│                    (Voice Interface)                         │
└────────────────────────┬────────────────────────────────────┘
                         │ MCP Protocol
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   MCP Server (Python)                        │
│             135 Tools for Voice Control                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Context Auto-Injection • Activity Logging            │   │
│  │ Property-Linked Conversation History                 │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP API
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Routers: Properties, Contracts, Webhooks, Recaps,    │   │
│  │   Notes, Workflows, Contacts, Compliance, Offers,   │   │
│  │   Insights, Analytics, Pipeline, Digest, Tasks,     │   │
│  │   Scoring, Watchlists                               │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Services: Voice Goal Planner, AI Recap, VAPI,        │   │
│  │   Enrichment, Skip Trace, Compliance, Workflows,    │   │
│  │   Insights, Analytics, Pipeline, Daily Digest,      │   │
│  │   Property Scoring, Watchlist                       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Auto-Recap: Background regeneration on key events    │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Background: Task Runner (60s) + Pipeline Check (5m) │   │
│  │ + Daily Digest (8 AM) + Campaign Worker             │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────┬────────────────────────┬───────────────────────┘
             │                        │
             ▼                        ▼
┌────────────────────┐    ┌─────────────────────────────────┐
│   PostgreSQL DB    │    │    External APIs                │
│   (Fly.io)         │    │  • Google Places                │
│                    │    │  • Zillow                       │
│  • properties      │    │  • Skip Trace                   │
│  • contracts       │    │  • DocuSeal                     │
│  • contacts        │    │  • VAPI / ElevenLabs            │
│  • recaps          │    │  • Anthropic Claude             │
│  • templates       │    │  • Exa Research                 │
│  • activities      │    └─────────────────────────────────┘
│  • enrichments     │
│  • property_notes  │
│  • conversation_   │
│    history         │
│  • offers          │
└────────────────────┘
             ▲
             │ WebSocket
             ▼
┌────────────────────────────────────────────────────────────┐
│                  Frontend (Next.js)                         │
│              Real-time Activity Feed                        │
└────────────────────────────────────────────────────────────┘
```

---

## Database Schema

**Core tables:**
- `agents` - Real estate agents
- `properties` - Property listings
- `contacts` - Buyers, sellers, stakeholders (with ContactRole enum)
- `contracts` - Contract documents
- `contract_templates` - Reusable templates with signer roles
- `skip_traces` - Owner contact info
- `zillow_enrichments` - Zillow data
- `property_recaps` - AI-generated summaries
- `property_notes` - Freeform notes (with NoteSource enum)
- `conversation_history` - Per-property audit trail (with property_id FK)
- `activity_events` - Event log
- `offers` - Property offers
- `scheduled_tasks` - Reminders, recurring tasks, follow-ups (with TaskType/TaskStatus enums)
- `todos` - Tasks
- `market_watchlists` - Saved-search alerts with JSON criteria
- `agent_preferences` - Agent settings

**Key relationships:**
- Property → many Contracts, Contacts, Notes, ConversationHistory entries
- Property → one ZillowEnrichment, SkipTrace, PropertyRecap
- ConversationHistory → optional Property (property_id FK for audit trail)

---

## Environment Variables

```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
GOOGLE_PLACES_API_KEY=your-key
ZILLOW_API_KEY=your-key
SKIP_TRACE_API_KEY=your-key
ANTHROPIC_API_KEY=sk-ant-your-key
DOCUSEAL_API_KEY=your-key
DOCUSEAL_WEBHOOK_SECRET=your-webhook-secret
VAPI_API_KEY=your-vapi-key
VAPI_PHONE_NUMBER=+14155551234
ELEVENLABS_API_KEY=your-key
EXA_API_KEY=your-key
```

---

## Getting Started

```bash
# 1. Clone and install
git clone https://github.com/Thedurancode/ai-realtor.git
cd ai-realtor
pip install -r requirements.txt

# 2. Configure
cp .env.example .env  # Edit with your API keys

# 3. Database
alembic upgrade head

# 4. Start server
uvicorn app.main:app --reload

# 5. Start MCP server (for voice)
python mcp_server/property_mcp.py
```

**Claude Desktop config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
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

---

## Deployment

**Platform:** Fly.io

```bash
fly deploy                                          # Deploy
fly secrets set KEY=value --app ai-realtor          # Set secrets
fly logs --app ai-realtor                           # View logs
fly ssh console --app ai-realtor                    # SSH in
fly postgres connect -a ai-realtor-db               # DB console
```

---

### 33. Complete Marketing Hub

**All-in-one marketing platform with brand management, Facebook Ads, and social media**

Three integrated systems enable agents to handle **ALL their marketing** through the AI Realtor platform:

1. **Agent Branding** - Set up your brand identity once
2. **Facebook Ads** - Run paid advertising campaigns
3. **Postiz Social Media** - Manage organic social media posting

**Unified Brand Integration:**
- Set brand colors, logo, tagline once
- Automatically applied to all marketing materials
- Consistent across Facebook Ads, Instagram, Twitter, LinkedIn, TikTok
- Platform-specific optimization with unified brand voice

---

#### Agent Branding System

**5-color slots for complete brand identity:**
- `primary_color` - Main brand color (CTAs, headlines)
- `secondary_color` - Supporting color (subheadlines, borders)
- `accent_color` - Highlight color (buttons, badges)
- `background_color` - Page backgrounds
- `text_color` - Main text color

**Brand assets:**
- Company logo URL
- Tagline/slogan
- Website URL
- Bio/about text
- Social media links

**6 Pre-defined Color Presets:**
1. **Professional Blue** - Corporate, trustworthy (#1E40AF, #3B82F6, #60A5FA, #F8FAFC, #1E293B)
2. **Modern Green** - Growth, eco-friendly (#065F46, #10B981, #34D399, #F0FDF4, #064E3B)
3. **Luxury Gold** - Premium, high-end (#B45309, #D97706, #F59E0B, #FFFBEB, #78350F)
4. **Bold Red** - Urgent, attention-grabbing (#991B1B, #EF4444, #F87171, #FEF2F2, #7F1D1D)
5. **Minimalist Black** - Sleek, modern (#18181B, #27272A, #3F3F46, #FAFAFA, #09090B)
6. **Ocean Teal** - Calm, coastal (#0E7490, #14B8A6, #2DD4BF, #F0FDFA, #164E63)

**API Endpoints:**
```
POST   /agent-brand/{id}                  - Create brand
GET    /agent-brand/{id}                  - Get brand
PUT    /agent-brand/{id}                  - Update brand
DELETE /agent-brand/{id}                  - Delete brand
GET    /agent-brand/colors/presets        - Get color presets
POST   /agent-brand/{id}/apply-preset     - Apply preset
POST   /agent-brand/{id}/generate-preview - Generate preview
GET    /agent-brand/{id}/preview          - Get preview
POST   /agent-brand/{id}/validate         - Validate brand data
GET    /agent-brand/{id}/guidelines       - Get brand guidelines
POST   /agent-brand/{id}/export           - Export brand kit
```

**Voice Commands:**
- "Set up my brand with Emprezario Inc"
- "Apply the Luxury Gold color scheme"
- "Generate a preview of my brand"
- "Update my tagline to Your Dream Home Awaits"

---

#### Facebook Ads Integration

**AI-powered Facebook Ad campaign generation:**
- Analyze property URL → Auto-generate campaign
- Target audience recommendations
- Ad copy with brand voice
- Launch directly to Meta Ads Manager
- Track performance and ROI

**Campaign types:**
- Property promotion
- Open house
- Brand awareness
- Lead generation
- Just listed
- Price reduction

**AI-Powered Features:**
- Market research - Generate market insights for campaigns
- Competitor analysis - Analyze competitor ads
- Review intelligence - Extract insights from Google/Yelp reviews
- Target audience recommendations

**API Endpoints:**
```
POST /facebook-ads/campaigns/generate          - Generate campaign
POST /facebook-ads/campaigns/{id}/launch       - Launch to Meta
POST /facebook-ads/campaigns/{id}/track        - Track performance
GET  /facebook-ads/campaigns                   - List campaigns
GET  /facebook-ads/campaigns/{id}              - Get campaign
PUT  /facebook-ads/campaigns/{id}              - Update campaign
POST /facebook-ads/research/generate           - Market research
POST /facebook-ads/competitors/analyze         - Competitor analysis
POST /facebook-ads/reviews/extract             - Review intelligence
POST /facebook-ads/audiences/recommend         - Audience recommendations
POST /facebook-ads/audiences/{id}/create       - Create audience
GET  /facebook-ads/analytics/campaign/{id}     - Campaign analytics
GET  /facebook-ads/analytics/account           - Account analytics
```

**Voice Commands:**
- "Create a Facebook ad for property 5"
- "Generate market research for Miami condos"
- "Analyze competitor ads"
- "Launch my campaign to Meta"
- "Track my Facebook ad performance"

---

#### Postiz Social Media Integration

**Multi-platform organic social media management:**
- Schedule posts across Facebook, Instagram, Twitter, LinkedIn, TikTok
- AI-powered content generation
- Multi-post campaigns
- Reusable templates
- Content calendar
- Analytics dashboard

**Supported Platforms:**
| Platform | Character Limit | Hashtags | Features |
|----------|----------------|----------|----------|
| Facebook | 63,206 | 3-5 | CTA buttons, long-form |
| Instagram | 2,200 | 10-30 | Visual-heavy, stories |
| Twitter | 280 | 1-3 | Short, timely |
| LinkedIn | 3,000 | 3-5 | Professional tone |
| TikTok | 2,200 | 3-5 | Video-first |

**Content Types:**
- Property promotion
- Open house
- Market update
- Brand awareness
- Educational
- Community highlight
- Client testimonial

**API Endpoints:**
```
POST /social/accounts/connect              - Connect social account
GET  /social/accounts                      - List connected accounts
POST /social/posts/create                  - Create post
POST /social/posts/{id}/schedule           - Schedule post
GET  /social/posts                         - List posts
GET  /social/posts/{id}                    - Get post
PUT  /social/posts/{id}                    - Update post
POST /social/ai/generate                   - AI content generation
POST /social/campaigns/create              - Create campaign
GET  /social/campaigns                     - List campaigns
POST /social/templates/create              - Create template
GET  /social/templates                     - List templates
GET  /social/analytics/overview            - Get analytics
GET  /social/calendar                      - Content calendar
```

**Voice Commands:**
- "Create a social media post for this property"
- "Schedule posts for next week"
- "Generate Instagram content with AI"
- "Create a 10-post campaign for this listing"
- "Get my social media analytics"

---

#### Complete Marketing Workflow

**Step 1: Set Up Brand Identity**
```bash
POST /agent-brand/5
{
  "company_name": "Emprezario Inc",
  "tagline": "Your Dream Home Awaits",
  "primary_color": "#B45309",
  "secondary_color": "#D97706",
  "logo_url": "https://example.com/logo.png",
  "website_url": "https://emprezario.com",
  "bio": "Luxury real estate specialist serving NYC"
}
```

**Step 2: Create Facebook Ad Campaign**
```bash
POST /facebook-ads/campaigns/generate?agent_id=5
{
  "url": "https://emprezario.com/properties/luxury-condo",
  "campaign_objective": "leads",
  "daily_budget": 100
}
```

**Step 3: Launch Paid Ads**
```bash
POST /facebook-ads/campaigns/3/launch
{
  "meta_access_token": "YOUR_TOKEN",
  "ad_account_id": "act_1234567890"
}
```

**Step 4: Create Organic Social Posts**
```bash
POST /social/posts/create?agent_id=5
{
  "content_type": "property_promo",
  "caption": "🏠 Stunning luxury condo in NYC!",
  "hashtags": ["#luxuryliving", "#nyc", "#realestate"],
  "platforms": ["facebook", "instagram", "linkedin"],
  "use_branding": true,
  "scheduled_at": "2026-02-24T10:00:00"
}
```

**Step 5: Create Multi-Post Campaign**
```bash
POST /social/campaigns/create?agent_id=5
{
  "campaign_name": "Property Launch Campaign",
  "campaign_type": "property_launch",
  "start_date": "2026-02-24",
  "end_date": "2026-03-02",
  "platforms": ["facebook", "instagram"],
  "post_count": 10,
  "auto_generate": true
}
```

---

#### Marketing Analytics Dashboard

**Unified view of all marketing performance:**

**Paid Ads (Facebook Ads):**
- Active campaigns
- Total spend
- Impressions, clicks, CTR
- Conversions, cost per conversion
- ROI calculation

**Organic Social (Postiz):**
- Total posts by platform
- Follower counts
- Engagement metrics
- Engagement rate
- Top performing posts

**Brand Reach:**
- Total impressions across all channels
- Unique reach
- Brand recall lift
- Cross-platform performance

**API Endpoints:**
```
GET /facebook-ads/analytics/campaign/{id}   - Campaign analytics
GET /facebook-ads/analytics/account         - Account analytics
GET /social/analytics/overview              - Social media analytics
```

---

#### Database Tables

**Agent Branding (1 table):**
- `agent_brands` - Brand identity with 5 color slots

**Facebook Ads (6 tables):**
- `facebook_ad_campaigns` - Campaign data
- `facebook_ad_sets` - Ad sets
- `facebook_ads` - Individual ads
- `facebook_ad_creatives` - Ad creative assets
- `facebook_audiences` - Target audiences
- `facebook_ad_metrics` - Performance metrics

**Postiz Social Media (5 tables):**
- `postiz_accounts` - Connected social accounts
- `postiz_posts` - Social media posts
- `postiz_campaigns` - Multi-post campaigns
- `postiz_templates` - Reusable post templates
- `postiz_analytics` - Aggregated analytics

**Total Marketing Hub: 12 tables**

---

#### Marketing Hub Summary

**What Agents Can Now Do:**

✅ **Brand Management**
- Set up complete brand identity
- Apply to all marketing automatically
- Consistent across all channels
- 6 pre-defined color presets

✅ **Paid Advertising**
- Create Facebook ad campaigns
- Generate with AI from URLs
- Launch to Meta Ads Manager
- Track performance and ROI

✅ **Social Media Management**
- Schedule posts across platforms
- Generate AI-powered content
- Create multi-post campaigns
- Use reusable templates
- View content calendar

✅ **Analytics & Insights**
- Paid ad performance
- Organic social metrics
- Unified dashboard
- Competitor analysis
- Market research

**All marketing, one platform, fully integrated!**

**Total Marketing Endpoints: 39**
- Agent Branding: 12 endpoints
- Facebook Ads: 13 endpoints
- Postiz Social Media: 14 endpoints

---

## Recent Updates (Feb 2026)

### 🎨 NEW: Complete Marketing Hub (Agent Branding + Facebook Ads + Postiz)

**All-in-one marketing platform:**
- **Agent Branding System** - 5-color slots, logo, tagline, social links
- **Facebook Ads Integration** - AI-powered campaign generation and Meta launch
- **Postiz Social Media** - Multi-platform organic posting (Facebook, Instagram, Twitter, LinkedIn, TikTok)
- **Unified Brand Integration** - Set brand once, apply everywhere
- **39 New Endpoints** across 3 routers
- **12 New Database Tables** for marketing data
- **6 Pre-defined Color Presets** for instant branding
- **AI-Powered Content Generation** for ads and social posts
- **Multi-Platform Publishing** with platform-specific optimization
- **Analytics Dashboard** for paid + organic performance

Voice examples:
- "Set up my brand with Emprezario Inc"
- "Create a Facebook ad for property 5"
- "Schedule social posts for next week"
- "Generate Instagram content with AI"
- "Get my marketing analytics"

### 🌐 NEW: Web Scraper (Automated Property Data Extraction)

**Browser-controlled property import:**
- Specialized scrapers for Zillow, Redfin, Realtor.com
- Generic AI-powered scraper for any website
- Concurrent scraping with rate limiting
- Auto-create properties from URLs
- Duplicate detection and validation
- Batch import from search results
- Auto-enrichment option after scraping
- 6 MCP tools + 8 API endpoints
- ~650 lines of production code

Voice examples:
- "Scrape this Zillow listing"
- "Add this property from the URL"
- "Import these 10 listings and enrich them all"

### 🧠 NEW: AI Intelligence Layer (Phases 1-3 Complete)

**Phase 1: Predictive Intelligence (Quick Wins)**
- **Predictive Intelligence Engine:**
  - Predict closing probability (0-100%) with confidence levels
  - Recommend next actions with AI reasoning
  - Batch predict across multiple properties
  - Risk factors, strengths, and time-to-close estimates
  - 6 MCP tools + 6 API endpoints

- **Market Opportunity Scanner:**
  - Scan for deals matching agent's success patterns
  - Detect market shifts (price drops/surges >10%)
  - Find similar properties for comparison
  - ROI estimation with upside calculations
  - 3 MCP tools + 3 API endpoints

- **Emotional Intelligence & Relationship Scoring:**
  - Score relationship health (0-100) with trend analysis
  - Predict best contact method (phone/email/text)
  - Sentiment analysis without external dependencies
  - Contact responsiveness and engagement tracking
  - 3 MCP tools + 3 API endpoints

**Phase 2: Core Intelligence**
- **Adaptive Learning System:**
  - Learn from deal outcomes to improve predictions
  - Discover agent success patterns (type/city/price)
  - Track prediction accuracy (MAE, directional)
  - Agent performance metrics with pattern insights
  - 3 new database tables (deal_outcomes, agent_performance_metrics, prediction_logs)

- **Autonomous Campaign Manager:**
  - Self-optimizing campaigns based on performance
  - End-to-end autonomous execution from natural language goals
  - Analyze best calling times and message variants
  - Campaign ROI tracking and cost analysis
  - 2 MCP tools + 3 API endpoints

- **Negotiation Agent Service:**
  - Analyze offers against deal metrics and market data
  - Generate AI counter-offer letters with justification
  - Suggest optimal prices (conservative/moderate/aggressive)
  - Walkaway price calculation
  - 3 MCP tools + 3 API endpoints

**Phase 3: Advanced Capabilities**
- **Document Analysis Service:**
  - Extract issues from inspection reports using NLP
  - Compare appraisals and flag discrepancies
  - Extract contract terms automatically
  - Repair cost estimation with severity levels
  - 3 MCP tools + 3 API endpoints

- **Competitive Intelligence Service:**
  - Analyze competing agents in markets
  - Detect competitive activity on properties
  - Market saturation assessment (inventory levels, price trends)
  - Winning bid pattern analysis
  - 3 MCP tools + 3 API endpoints

- **Multi-Property Deal Sequencer:**
  - Orchestrate 1031 exchanges with 45/180 day deadlines
  - Sequence portfolio acquisitions (parallel/sequential)
  - Manage sell-and-buy transactions with contingencies
  - Automated deadline reminders
  - 3 MCP tools + 3 API endpoints

**Intelligence Layer Summary:**
- **9 New Services** spanning predictive, learning, market, relationship, campaign, negotiation, document, competition, and sequencing intelligence
- **23 New MCP Tools** bringing total from 106 to **129 tools**
- **30 New API Endpoints** across 4 new routers
- **3 New Database Tables** for outcome tracking and learning
- **~4,000+ Lines of Code** in production-ready services

**Total MCP Tools: 129** (up from 106)

---

### Previous Updates

- **Property Pipeline Overhaul:**
  - New 5-stage pipeline: NEW_PROPERTY → ENRICHED → RESEARCHED → WAITING_FOR_CONTRACTS → COMPLETE
  - Auto-advance based on enrichment, skip trace, contracts, and contract completion
  - Per-stage stale thresholds (3/5/7/10 days) replace flat 7-day threshold
- **Property Heartbeat:**
  - At-a-glance pipeline stage, 4-item checklist, health status (healthy/stale/blocked), and next action
  - Auto-included in all property responses (opt-out with `?include_heartbeat=false`)
  - Batch-optimized for list endpoints (2 extra queries regardless of property count)
  - Dedicated endpoint `GET /properties/{id}/heartbeat` + MCP tool (106 total)
- **Property Scoring Engine:**
  - 4-dimension scoring (Market 30%, Financial 25%, Readiness 25%, Engagement 20%) with 15+ signals from 9 data sources
  - Weight re-normalization when data is missing, A-F grade scale
  - Bulk scoring, top properties ranking, voice-native commands (4 MCP tools)
  - Replaces old 6-component scorer with backward-compatible delegation
- **Proactive Intelligence Layer:**
  - Insights service with 6 alert rules (stale properties, contract deadlines, unsigned contracts, missing enrichment/skip trace, high deal score)
  - Scheduled tasks system with background runner, reminders, follow-ups, recurring tasks
  - Cross-property analytics with 6 metric categories (pipeline, value, contracts, activity, deal scores, enrichment coverage)
  - Pipeline automation — auto-advance property status (NEW_PROPERTY→ENRICHED→RESEARCHED→WAITING_FOR_CONTRACTS→COMPLETE) with 24h manual grace period
  - Daily digest — AI-generated morning briefing at 8 AM combining insights + analytics + notifications
- **Operational Intelligence Layer:**
  - Smart Follow-Up Queue — AI-scored priority queue with 7 weighted signals, snooze, and best-contact finder (3 MCP tools)
  - Comparable Sales Dashboard — 3-source comp aggregation with market metrics and pricing recommendations (3 MCP tools)
  - Bulk Operations Engine — 6 operations across up to 50 properties with error isolation (2 MCP tools)
  - Activity Timeline Dashboard — 7-source unified chronological feed with filtering and search (3 MCP tools)
- **Market Watchlist:**
  - Saved-search alerts with flexible JSON criteria (city, state, type, price, rooms, sqft)
  - Auto-fires on property creation via both `POST /properties/` and `POST /properties/voice`
  - HIGH priority notifications with watchlist metadata, toggle pause/resume (5 MCP tools)
- Voice Goal Planner with 26 autonomous actions and heuristic plan matching
- Property Notes system with NoteSource enum and voice integration
- Workflow Templates (5 pre-built workflows)
- Voice Campaign Management (6 MCP tools)
- Proactive Notifications (5 MCP tools)
- Context Auto-Injection for all MCP responses
- Auto-Recap Regeneration on key events (notes, enrichment, skip trace, contacts, property updates, pipeline transitions)
- Property-Linked Conversation History with per-property audit trail
- Property filtering by type, city, price range, bedrooms via MCP
- Deal Calculator and Offer Management (18 MCP tools)
- Research and Semantic Search (7 MCP tools)
- ElevenLabs voice integration
- MCP tools expanded from 20 to **106 total**

---

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)
