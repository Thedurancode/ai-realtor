# 📡 Complete API Endpoint Catalog

## AI Realtor Platform - 250+ Endpoints

**Generated:** February 25, 2026
**Version:** 1.0
**Base URL:** `http://localhost:8000` (or `https://ai-realtor.fly.dev`)

---

## 📊 Quick Stats

| Category | Endpoints | Router File |
|----------|-----------|-------------|
| **Property Management** | 9 | `properties.py` |
| **Contracts** | 40+ | `contracts.py` |
| **Contract Templates** | 7 | `contract_templates.py` |
| **Contacts** | 10 | `contacts.py` |
| **Skip Trace** | 4 | `skip_trace.py` |
| **Property Notes** | 3 | `property_notes.py` |
| **Property Recap & Calls** | 6 | `property_recap.py` |
| **Webhooks** | 3 | `webhooks.py` |
| **Workflows** | 2 | `workflows.py` |
| **Insights** | 2 | `insights.py` |
| **Analytics** | 3 | `analytics.py` |
| **Scheduled Tasks** | 5 | `scheduled_tasks.py` |
| **Pipeline Automation** | 2 | `pipeline.py` |
| **Daily Digest** | 3 | `daily_digest.py` |
| **Follow-Up Queue** | 3 | `follow_ups.py` |
| **Comparable Sales** | 3 | `comps.py` |
| **Bulk Operations** | 2 | `bulk.py` |
| **Activity Timeline** | 3 | `activity_timeline.py` |
| **Property Scoring** | 4 | `property_scoring.py` |
| **Market Watchlist** | 9 | `market_watchlist.py` |
| **Web Scraper** | 8 | `web_scraper.py` |
| **Facebook Ads** | 13 | `facebook_ads.py` |
| **Postiz Social Media** | 14 | `postiz.py` |
| **Agent Branding** | 12 | `agent_brand.py` |
| **Other Features** | 50+ | Various |
| **TOTAL** | **250+** | **67 router files** |

---

## 🏠 Core Property Management (9 endpoints)

**Router:** `properties.py`
**Prefix:** `/properties`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/properties/` | Create a new property with auto-attach contracts and watchlist checking |
| POST | `/properties/voice` | Voice-optimized property creation using Google Places API |
| GET | `/properties/` | List properties with filters (status, type, city, price, bedrooms) |
| GET | `/properties/{property_id}` | Get property details with optional heartbeat |
| GET | `/properties/{property_id}/heartbeat` | Get pipeline heartbeat for a property |
| PATCH | `/properties/{property_id}` | Update property with notifications and recap regeneration |
| DELETE | `/properties/{property_id}` | Delete a property and all related data |
| POST | `/properties/{property_id}/set-deal-type` | Set deal type on property and trigger workflow |
| GET | `/properties/{property_id}/deal-status` | Check deal progress (contracts, checklist, missing contacts) |

**Voice Commands:**
- "Create a property at 123 Main St for $850,000"
- "Show me all condos under 500k in Miami"
- "Get details for property 5"
- "Delete property 3"

---

## 📄 Contract Management (40+ endpoints)

**Router:** `contracts.py`
**Prefix:** `/contracts`

### Basic Contract CRUD (7)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/contracts/` | List all contracts with optional status filter |
| POST | `/contracts/` | Create a contract for a property |
| GET | `/contracts/property/{property_id}` | List all contracts for a property |
| GET | `/contracts/contact/{contact_id}` | List all contracts for a contact |
| GET | `/contracts/{contract_id}` | Get a contract by ID |
| PATCH | `/contracts/{contract_id}` | Update a contract |
| DELETE | `/contracts/{contract_id}` | Delete a contract |

### Contract Sending (6)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/contracts/{contract_id}/send` | Send contract via DocuSeal to email |
| POST | `/contracts/{contract_id}/send-to-contact` | Send contract to existing contact |
| POST | `/contracts/{contract_id}/send-multi-party` | Send to multiple parties with order control |
| POST | `/contracts/voice/send` | Voice-optimized contract sending |
| POST | `/contracts/voice/smart-send` | Auto-determine signers and send |
| POST | `/contracts/voice/send-multi-party` | Voice-optimized multi-party sending |

### Contract Status & Management (4)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/contracts/{contract_id}/status` | Get contract signing status from DocuSeal |
| POST | `/contracts/{contract_id}/cancel` | Cancel/archive a contract |
| GET | `/contracts/property/{property_id}/signing-status` | Get signing status across all contracts |
| POST | `/contracts/webhook/docuseal` | DocuSeal webhook handler |

### Auto-Attach & Requirements (4)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/contracts/property/{property_id}/auto-attach` | Manually trigger auto-attach of required contracts |
| GET | `/contracts/property/{property_id}/required-status` | Get required contracts status |
| GET | `/contracts/property/{property_id}/missing-contracts` | Get list of missing contracts |
| POST | `/contracts/voice/check-contracts` | Voice-friendly contract status check |

### AI-Powered Contracts (3)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/contracts/property/{property_id}/ai-suggest` | Use AI to suggest required contracts |
| POST | `/contracts/property/{property_id}/ai-apply-suggestions` | Apply AI suggestions by creating contracts |
| GET | `/contracts/property/{property_id}/ai-analyze-gaps` | AI analyzes missing contracts |

### Manual Requirement Management (2)

| Method | Endpoint | Description |
|--------|----------|-------------|
| PATCH | `/contracts/contracts/{contract_id}/mark-required` | Manually mark contract as required/optional |
| POST | `/contracts/property/{property_id}/set-required-contracts` | Set which contracts are required for property |

**Voice Commands:**
- "Is property 5 ready to close?"
- "Suggest contracts for property 5"
- "Send the Purchase Agreement for signing"
- "Check contract status"

---

## 📋 Contract Templates (7 endpoints)

**Router:** `contract_templates.py`
**Prefix:** `/contract-templates`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/contract-templates/` | Create a new contract template |
| GET | `/contract-templates/` | List templates with filters (state, category, requirement) |
| GET | `/contract-templates/{template_id}` | Get template by ID |
| PATCH | `/contract-templates/{template_id}` | Update a template |
| DELETE | `/contract-templates/{template_id}` | Delete a template |
| POST | `/contract-templates/{template_id}/activate` | Activate a template |
| POST | `/contract-templates/{template_id}/deactivate` | Deactivate a template |

---

## 👥 Contact Management (10 endpoints)

**Router:** `contacts.py`
**Prefix:** `/contacts`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/contacts/` | Create a contact for a property |
| POST | `/contacts/voice` | Voice-optimized contact creation |
| GET | `/contacts/property/{property_id}` | List all contacts for a property |
| GET | `/contacts/property/{property_id}/role/{role}` | Get contacts by role |
| GET | `/contacts/voice/search` | Voice search for contacts |
| GET | `/contacts/{contact_id}` | Get a contact by ID |
| PATCH | `/contacts/{contact_id}` | Update a contact |
| POST | `/contacts/{contact_id}/send-pending-contracts` | Send pending contracts to contact |
| DELETE | `/contacts/{contact_id}` | Delete a contact |

**Contact Roles:**
- `buyer`, `seller`, `lawyer`, `attorney`, `contractor`, `inspector`, `appraiser`, `lender`, `mortgage_broker`, `title_company`, `tenant`, `landlord`, `property_manager`, `handyman`, `plumber`, `electrician`, `photographer`, `stager`, `other`

**Voice Commands:**
- "Add John Smith as a buyer for property 5"
- "Who are the contacts for property 3?"

---

## 🔍 Skip Trace (4 endpoints)

**Router:** `skip_trace.py`
**Prefix:** `/skip-trace`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/skip-trace/voice` | Voice-optimized skip trace by address |
| POST | `/skip-trace/property/{property_id}` | Run skip trace on property by ID |
| GET | `/skip-trace/property/{property_id}` | Get existing skip trace results |
| POST | `/skip-trace/property/{property_id}/refresh` | Force a new skip trace |

**Voice Commands:**
- "Skip trace property 5"
- "Find the owner of 123 Main St"

---

## 📝 Property Notes (3 endpoints)

**Router:** `property_notes.py`
**Prefix:** `/property-notes`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/property-notes/` | Add a note to a property |
| GET | `/property-notes/property/{property_id}` | List notes for a property |
| DELETE | `/property-notes/{note_id}` | Delete a note |

**Note Sources:** `voice`, `manual`, `ai`, `phone_call`, `system`

**Voice Commands:**
- "Note that property 5 has a new fence"
- "Show me notes for property 3"

---

## 📞 Property Recap & Phone Calls (6 endpoints)

**Router:** `property_recap.py`
**Prefix:** `/property-recap`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/property-recap/property/{property_id}/generate` | Generate AI recap for property |
| GET | `/property-recap/property/{property_id}` | Get existing property recap |
| POST | `/property-recap/property/{property_id}/send-report` | Generate PDF report and email it |
| POST | `/property-recap/property/{property_id}/call` | Make phone call about property via VAPI |
| GET | `/property-recap/call/{call_id}/status` | Get VAPI call status |
| POST | `/property-recap/call/{call_id}/end` | End an ongoing VAPI call |
| GET | `/property-recap/call/{call_id}/recording` | Get call recording URL |

**Voice Commands:**
- "Generate recap for property 5"
- "Call John about property 5"
- "What's the status of call 3?"

---

## 🔗 Webhooks (3 endpoints)

**Router:** `webhooks.py`
**Prefix:** `/webhooks`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhooks/docuseal` | Receive DocuSeal webhook events |
| POST | `/webhooks/vapi` | Receive Vapi webhook events |
| GET | `/webhooks/docuseal/test` | Test webhook configuration |

**Integrations:**
- **DocuSeal** - Contract signing notifications
- **VAPI** - Phone call events (answered, completed, failed)

---

## ⚙️ Workflows (2 endpoints)

**Router:** `workflows.py`
**Prefix:** `/workflows`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/workflows/templates` | List all available workflow templates |
| POST | `/workflows/execute` | Execute a named workflow template |

**Workflow Templates:**
1. **new_lead_setup** - Enrich → Skip trace → Contracts → Recap
2. **deal_closing** - Check readiness → Final contracts → Recap
3. **property_enrichment** - Zillow data → Recap
4. **skip_trace_outreach** - Skip trace → Cold call
5. **ai_contract_setup** - AI suggest → Apply → Check readiness

**Voice Commands:**
- "What workflows are available?"
- "Run the new lead workflow on property 5"

---

## 🔔 Insights (2 endpoints)

**Router:** `insights.py`
**Prefix:** `/insights`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/insights/` | Get all insights (with optional priority filter) |
| GET | `/insights/property/{property_id}` | Get insights for specific property |

**Alert Rules:**
1. Stale properties (no activity 7+ days)
2. Contract deadlines (approaching or overdue)
3. Unsigned contracts (in DRAFT/SENT for 3+ days)
4. Missing enrichment (no Zillow data)
5. Missing skip trace (unknown owners)
6. High score, no action (80+ score, no contracts)

**Voice Commands:**
- "What needs attention?"
- "Show me alerts"

---

## 📈 Analytics (3 endpoints)

**Router:** `analytics.py`
**Prefix:** `/analytics`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/portfolio` | Get full portfolio dashboard |
| GET | `/analytics/pipeline` | Get pipeline breakdown only |
| GET | `/analytics/contracts` | Get contract stats only |

**Voice Commands:**
- "How's my portfolio doing?"
- "Show me the numbers"

---

## ⏰ Scheduled Tasks (5 endpoints)

**Router:** `scheduled_tasks.py`
**Prefix:** `/scheduled-tasks`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/scheduled-tasks/` | Create a task (reminder, recurring, follow-up) |
| GET | `/scheduled-tasks/` | List tasks (with optional filters) |
| GET | `/scheduled-tasks/due` | List due tasks |
| GET | `/scheduled-tasks/{task_id}` | Get specific task |
| DELETE | `/scheduled-tasks/{task_id}/cancel` | Cancel a task |

**Task Types:** `REMINDER`, `RECURRING`, `FOLLOW_UP`, `CONTRACT_CHECK`

**Voice Commands:**
- "Remind me to follow up on property 5 in 3 days"
- "What tasks are scheduled?"
- "Cancel task 3"

---

## 🔄 Pipeline Automation (2 endpoints)

**Router:** `pipeline.py`
**Prefix:** `/pipeline`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/pipeline/status` | Get recent auto-transitions and pipeline status |
| POST | `/pipeline/check` | Manually trigger a pipeline automation check |

**Pipeline Stages:**
1. `NEW_PROPERTY` → `ENRICHED` → `RESEARCHED` → `WAITING_FOR_CONTRACTS` → `COMPLETE`

**Voice Commands:**
- "What's the pipeline status?"
- "Show recent auto-transitions"

---

## 📰 Daily Digest (3 endpoints)

**Router:** `daily_digest.py`
**Prefix:** `/digest`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/digest/latest` | Get the most recent daily digest |
| POST | `/digest/generate` | Manually trigger a daily digest generation |
| GET | `/digest/history` | Get past digests |

**Voice Commands:**
- "What's my daily digest?"
- "Morning summary"

---

## 🎯 Follow-Up Queue (3 endpoints)

**Router:** `follow_ups.py`
**Prefix:** `/follow-ups`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/follow-ups/queue` | Get AI-prioritized follow-up queue |
| POST | `/follow-ups/{property_id}/complete` | Mark follow-up as complete |
| POST | `/follow-ups/{property_id}/snooze` | Snooze a property for N hours |

**Voice Commands:**
- "What should I work on next?"
- "Show me my follow-up queue"
- "Snooze property 5 for 48 hours"

---

## 📊 Comparable Sales (3 endpoints)

**Router:** `comps.py`
**Prefix:** `/comps`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/comps/{property_id}` | Full comparable sales dashboard |
| GET | `/comps/{property_id}/sales` | Sales comparables and market metrics |
| GET | `/comps/{property_id}/rentals` | Rental comparables |

**Voice Commands:**
- "Show me comps for property 5"
- "What have similar properties sold for?"
- "What are rental comps for property 5?"

---

## 🔧 Bulk Operations (2 endpoints)

**Router:** `bulk.py`
**Prefix:** `/bulk`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/bulk/execute` | Execute an operation across multiple properties |
| GET | `/bulk/operations` | List available bulk operations |

**Operations:** `enrich`, `skip_trace`, `attach_contracts`, `generate_recaps`, `update_status`, `check_compliance`

**Voice Commands:**
- "Enrich all Miami properties"
- "Skip trace properties 1 through 5"

---

## 📋 Activity Timeline (3 endpoints)

**Router:** `activity_timeline.py`
**Prefix:** `/activity-timeline`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/activity-timeline/` | Get unified activity timeline with filters |
| GET | `/activity-timeline/property/{property_id}` | Get property-specific timeline |
| GET | `/activity-timeline/recent` | Get recent activity (last N hours) |

**Voice Commands:**
- "Show me the timeline"
- "What happened today?"
- "What's the activity on property 5?"

---

## 🎯 Property Scoring (4 endpoints)

**Router:** `property_scoring.py`
**Prefix:** `/scoring`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/scoring/property/{property_id}` | Score a single property (recalculates) |
| GET | `/scoring/property/{property_id}` | Get stored score breakdown |
| POST | `/scoring/bulk` | Score multiple properties |
| GET | `/scoring/top` | Get top-scored properties |

**Voice Commands:**
- "Score property 5"
- "What are my best deals?"
- "Score all my properties"

---

## 👀 Market Watchlist (9 endpoints)

**Router:** `market_watchlist.py`
**Prefix:** `/watchlists`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/watchlists/` | Create a watchlist |
| GET | `/watchlists/` | List watchlists |
| GET | `/watchlists/{watchlist_id}` | Get specific watchlist |
| PUT | `/watchlists/{watchlist_id}` | Update watchlist |
| DELETE | `/watchlists/{watchlist_id}` | Delete watchlist |
| POST | `/watchlists/{watchlist_id}/toggle` | Pause/resume watchlist |
| POST | `/watchlists/check/{property_id}` | Check property against watchlists |
| POST | `/watchlists/scan/all` | Manually trigger scan of all watchlists |
| POST | `/watchlists/scan/{watchlist_id}` | Manually trigger scan of specific watchlist |
| GET | `/watchlists/scan/status` | Get recent scan results |

**Voice Commands:**
- "Watch for Miami condos under 500k"
- "Show me my watchlists"
- "Pause watchlist 1"

---

## 🌐 Web Scraper (8 endpoints)

**Router:** `web_scraper.py`
**Prefix:** `/scrape`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/scrape/url` | Scrape a single URL (preview only) |
| POST | `/scrape/multiple` | Scrape multiple URLs concurrently |
| POST | `/scrape/scrape-and-create` | Scrape URL and auto-create property |
| POST | `/scrape/zillow-listing` | Scrape Zillow listing and create property |
| POST | `/scrape/redfin-listing` | Scrape Redfin listing and create property |
| POST | `/scrape/realtor-listing` | Scrape Realtor.com listing and create property |
| POST | `/scrape/zillow-search` | Scrape Zillow search results for multiple properties |
| POST | `/scrape/scrape-and-enrich-batch` | Bulk import with auto-enrichment |

**Voice Commands:**
- "Scrape this Zillow listing"
- "Add this property from the URL"
- "Import these 10 Zillow listings"

---

## 📱 Facebook Ads (13 endpoints)

**Router:** `facebook_ads.py`
**Prefix:** `/facebook-ads`

### Campaign Management (7)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/facebook-ads/campaigns/generate` | Generate full Facebook ad campaign from URL |
| POST | `/facebook-ads/campaigns/{campaign_id}/launch` | Launch campaign to Meta Ads Manager |
| GET | `/facebook-ads/campaigns` | List all campaigns |
| GET | `/facebook-ads/campaigns/{campaign_id}` | Get campaign details |
| POST | `/facebook-ads/campaigns/{campaign_id}/sync` | Sync campaign metrics from Meta |
| PUT | `/facebook-ads/campaigns/{campaign_id}/pause` | Pause active campaign |
| PUT | `/facebook-ads/campaigns/{campaign_id}/resume` | Resume paused campaign |

### Market Research & Intelligence (6)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/facebook-ads/research/generate` | Generate market research for targeting |
| GET | `/facebook-ads/research` | List all market research |
| POST | `/facebook-ads/competitors/analyze` | Analyze competitor ads |
| GET | `/facebook-ads/competitors` | List competitor analyses |
| POST | `/facebook-ads/reviews/extract` | Extract sentiment from reviews |
| GET | `/facebook-ads/reviews` | List review intelligence |

**Voice Commands:**
- "Create a Facebook ad for property 5"
- "Generate market research for Miami condos"
- "Launch my campaign to Meta"

---

## 📸 Postiz Social Media (14 endpoints)

**Router:** `postiz.py`
**Prefix:** `/postiz`

### Account Management (3)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/postiz/accounts/connect` | Connect Postiz account for social media |
| GET | `/postiz/accounts` | List all connected accounts |
| GET | `/postiz/accounts/{account_id}` | Get account details |

### Post Creation & Management (7)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/postiz/posts/create` | Create social media post with AI |
| POST | `/postiz/posts/{post_id}/schedule` | Schedule post for specific time |
| GET | `/postiz/posts` | List all posts |
| GET | `/postiz/posts/{post_id}` | Get post details |
| PUT | `/postiz/posts/{post_id}` | Update post |
| DELETE | `/postiz/posts/{post_id}` | Delete post |
| POST | `/postiz/posts/{post_id}/publish` | Immediately publish post |

### AI & Campaigns (2)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/postiz/ai/generate` | Generate social media content with AI |
| POST | `/postiz/campaigns/create` | Create multi-post campaign |
| GET | `/postiz/campaigns` | List all campaigns |

### Templates & Analytics (4)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/postiz/templates/create` | Create reusable post template |
| GET | `/postiz/templates` | List all templates |
| POST | `/postiz/templates/{template_id}/use` | Generate post from template |
| GET | `/postiz/analytics/overview` | Get analytics overview for period |
| GET | `/postiz/analytics/posts/{post_id}` | Get analytics for specific post |
| GET | `/postiz/calendar` | Get content calendar with scheduled posts |

**Voice Commands:**
- "Create a social media post for this property"
- "Schedule posts for next week"
- "Get my social media analytics"

---

## 🎨 Agent Branding (12 endpoints)

**Router:** `agent_brand.py`
**Prefix:** `/agent-brand`

### Brand CRUD (4)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/agent-brand/{agent_id}` | Create or update agent brand profile |
| GET | `/agent-brand/{agent_id}` | Get agent brand profile |
| PUT | `/agent-brand/{agent_id}` | Update agent brand profile |
| DELETE | `/agent-brand/{agent_id}` | Delete agent brand profile |

### Brand Features (8)

| Method | Endpoint | Description |
|--------|----------|-------------|
| PATCH | `/agent-brand/{agent_id}/colors` | Quick update for brand colors |
| POST | `/agent-brand/{agent_id}/logo` | Upload brand logo |
| GET | `/agent-brand/public/{agent_id}` | Get public-facing brand profile |
| GET | `/agent-brand/colors/presets` | Get pre-defined color schemes |
| POST | `/agent-brand/{agent_id}/apply-preset` | Apply a pre-defined color scheme |
| POST | `/agent-brand/{agent_id}/generate-preview` | Generate HTML preview of branded materials |
| GET | `/agent-brand/` | List all agent brands (admin) |

**Color Presets:**
- Professional Blue
- Modern Green
- Luxury Gold
- Bold Red
- Minimalist Black
- Ocean Teal

**Voice Commands:**
- "Set up my brand with Emprezario Inc"
- "Apply the Luxury Gold color scheme"

---

## 🔬 Agentic Research (6 endpoints)

**Router:** `agentic_research.py`
**Prefix:** `/agentic`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/agentic/jobs` | Create async agentic research job |
| GET | `/agentic/jobs/{job_id}` | Get job status and progress |
| GET | `/agentic/properties/{property_id}` | Get property with research output |
| GET | `/agentic/properties/{property_id}/enrichment-status` | Check research freshness |
| GET | `/agentic/properties/{property_id}/dossier` | Get investment dossier (markdown) |
| POST | `/agentic/research` | Run synchronous research (wait for result) |

**Voice Commands:**
- "Do extensive research on 123 Main St"
- "Start researching 456 Oak St in background"
- "What's the status of research job 42?"
- "Get the research dossier for property 15"

---

## 📚 Legacy Research (10 endpoints)

**Router:** `research.py`
**Prefix:** `/research`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/research/` | Create research job |
| GET | `/research/{research_id}` | Get status/results |
| GET | `/research/` | List research jobs |
| DELETE | `/research/{research_id}` | Delete research |
| POST | `/research/property/{property_id}/deep-dive` | Property analysis |
| POST | `/research/property/{property_id}/market-analysis` | Market analysis |
| POST | `/research/property/{property_id}/compliance` | Compliance check |
| GET | `/research/property/{property_id}/latest` | Latest completed |
| POST | `/research/ai-research` | Custom AI analysis |
| POST | `/research/api-research` | Custom API calls |

---

## 🤖 Other Key Routers (50+ endpoints)

### Deal Calculator (11 endpoints)
**Router:** `deal_calculator.py`

- Calculate ROI, cash flow, MAO
- What-if scenarios
- Deal comparisons
- Deal type configuration

### Offers (10 endpoints)
**Router:** `offers.py`

- Create offers
- List offers
- Accept/reject/counter offers
- Withdraw offers
- Generate offer letters

### Intelligence (20+ endpoints)
**Router:** `intelligence.py`, `predictive_intelligence.py`, `relationship_intelligence.py`, `market_opportunities.py`

- Predictive outcomes
- Next action recommendations
- Relationship scoring
- Market opportunity scans
- Negotiation analysis

### Compliance (5 endpoints)
**Router:** `compliance.py`

- Run compliance checks
- Get requirements
- Validate transactions

### Notifications (5 endpoints)
**Router:** `notifications.py`

- Send notifications
- List notifications
- Acknowledge notifications
- Get summaries

### Voice Campaigns (6 endpoints)
**Router:** `voice_campaigns.py`

- Create voice campaigns
- Start/pause campaigns
- Get campaign status
- Add targets

### Document Analysis (8 endpoints)
**Router:** `document_analysis.py`

- Upload documents
- Analyze with AI
- Extract issues
- Compare documents
- Chat with documents

### Agents (5 endpoints)
**Router:** `agents.py`

- Create/manage agents
- Agent preferences
- Agent stats

### Address (3 endpoints)
**Router:** `address.py`

- Google Places autocomplete
- Address validation
- Geocoding

### Todos (5 endpoints)
**Router:** `todos.py`

- Create todos
- List todos
- Update todos
- Complete todos

### And Many More...

---

## 🔐 Authentication

All endpoints require API key authentication:

```bash
# Include in request headers
X-API-Key: nanobot-perm-key-2024
```

---

## 📖 API Documentation

Interactive API documentation available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 🎯 MCP Tools (Voice Commands)

**135+ voice commands** available via MCP Server integration!

Full list in: `CLAUDE.md`

---

## 📊 Endpoint Summary by Category

| Category | Endpoints | % of Total |
|----------|-----------|------------|
| Contracts | 40+ | 16% |
| Marketing (FB + Postiz + Brand) | 39 | 16% |
| Other Features | 50+ | 20% |
| Property Management | 9 | 4% |
| Templates | 7 | 3% |
| Contacts | 10 | 4% |
| Research (Agentic + Legacy) | 16 | 6% |
| Watchlist | 9 | 4% |
| Web Scraper | 8 | 3% |
| Offers | 10 | 4% |
| Intelligence | 20+ | 8% |
| Compliance | 5 | 2% |
| Notifications | 5 | 2% |
| Campaigns (Voice) | 6 | 2% |
| Document Analysis | 8 | 3% |
| Tasks & Todos | 10 | 4% |
| Analytics & Insights | 5 | 2% |
| Pipeline & Follow-ups | 5 | 2% |
| Other | 38+ | 15% |
| **TOTAL** | **250+** | **100%** |

---

## 🚀 Key Features

✅ **250+ REST API endpoints**
✅ **135+ MCP voice commands**
✅ **67 router files**
✅ **Interactive documentation** (`/docs`)
✅ **Webhook integrations** (DocuSeal, VAPI)
✅ **Background task processing**
✅ **AI-powered insights** (Claude)
✅ **Multi-platform support** (Web, Mobile, Voice)

---

**Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)**
