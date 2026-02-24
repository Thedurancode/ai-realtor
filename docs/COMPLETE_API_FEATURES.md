# AI Realtor API - Complete Feature Catalog

**Total API Endpoints: 321**
**Categorized into 50+ Feature Groups**

---

## 📊 Core Property Management (15 endpoints)

### Property CRUD
- `POST /properties/` - Create property
- `GET /properties/` - List all properties (with filters)
- `GET /properties/{id}` - Get property details
- `PATCH /properties/{id}` - Update property
- `DELETE /properties/{id}` - Delete property
- `POST /properties/voice` - Voice-based property creation

### Property Enrichment
- `POST /properties/{id}/enrich` - Enrich with Zillow data
- `POST /skip-trace/property/{id}` - Skip trace to find owner
- `POST /skip-trace/property/{id}/refresh` - Refresh skip trace data
- `GET /skip-trace/voice` - Voice-based skip trace

### Property Intelligence
- `GET /properties/{id}/heartbeat` - Property health & pipeline status
- `GET /properties/{id}/deal-status` - Current deal status
- `POST /properties/{id}/set-deal-type` - Set deal type (flip, rental, etc.)

### Property Search
- `GET /search/properties` - Semantic property search
- `GET /search/similar/{id}` - Find similar properties
- `GET /search/research` - AI-powered research search

---

## 🏠 Address & Location (3 endpoints)

### Google Places Integration
- `POST /address/autocomplete` - Address autocomplete suggestions
- `POST /address/details` - Get full address details with lat/lng

---

## 👥 Contact Management (10 endpoints)

### Contact CRUD
- `POST /contacts/` - Create contact
- `GET /contacts/property/{id}` - Get contacts for property
- `GET /contacts/property/{id}/role/{role}` - Get contacts by role
- `GET /contacts/{id}` - Get contact details
- `PATCH /contacts/{id}` - Update contact
- `DELETE /contacts/{id}` - Delete contact

### Voice Features
- `GET /contacts/voice` - Voice-based contact list
- `GET /contacts/voice/search` - Voice search contacts

### Contact Actions
- `POST /contacts/{id}/send-pending-contracts` - Send contracts to contact

**Contact Roles**: buyer, seller, lawyer, attorney, contractor, inspector, appraiser, lender, mortgage_broker, title_company, tenant, landlord, property_manager, handyman, plumber, electrician, photographer, stager, other

---

## 📝 Property Notes (4 endpoints)

- `POST /property-notes/` - Create note
- `GET /property-notes/property/{id}` - Get notes for property
- `GET /property-notes/{id}` - Get note details
- `DELETE /property-notes/{id}` - Delete note

**Note Sources**: voice, manual, ai, phone_call, system

---

## 📄 Contract Management (42 endpoints)

### Contract CRUD
- `GET /contracts/` - List contracts
- `POST /contracts/` - Create contract
- `GET /contracts/{id}` - Get contract details
- `PATCH /contracts/{id}` - Update contract
- `DELETE /contracts/{id}` - Delete contract
- `GET /contracts/property/{id}` - Get contracts for property
- `GET /contracts/contact/{id}` - Get contracts for contact

### Contract Templates
- `GET /contract-templates/` - List templates
- `POST /contract-templates/` - Create template
- `GET /contract-templates/{id}` - Get template
- `PATCH /contract-templates/{id}` - Update template
- `DELETE /contract-templates/{id}` - Delete template
- `POST /contract-templates/{id}/activate` - Activate template
- `POST /contract-templates/{id}/deactivate` - Deactivate template

### Contract Intelligence
- `GET /contracts/property/{id}/ai-suggest` - AI suggests contracts
- `POST /contracts/property/{id}/ai-apply-suggestions` - Apply AI suggestions
- `GET /contracts/property/{id}/ai-analyze-gaps` - Analyze contract gaps
- `POST /contracts/property/{id}/auto-attach` - Auto-attach matching templates
- `GET /contracts/property/{id}/required-status` - Check required contracts
- `GET /contracts/property/{id}/missing-contracts` - List missing contracts
- `POST /contracts/property/{id}/set-required-contracts` - Mark contracts required
- `POST /contracts/{id}/mark-required` - Mark contract as required

### Contract Sending
- `POST /contracts/{id}/send` - Send for signature
- `POST /contracts/{id}/send-multi-party` - Multi-party signing
- `POST /contracts/{id}/send-to-contact` - Send to specific contact
- `GET /contracts/property/{id}/signing-status` - Check signing status

### Contract Status
- `GET /contracts/{id}/status` - Get contract status
- `POST /contracts/{id}/cancel` - Cancel contract

### Voice Features
- `GET /contracts/voice/check-contracts` - Voice contract check
- `GET /contracts/voice/send` - Voice-based contract sending
- `GET /contracts/voice/smart-send` - Smart multi-party send
- `GET /contracts/voice/send-multi-party` - Voice multi-party send

### Webhooks
- `POST /contracts/webhook/docuseal` - DocuSeal signature webhook
- `POST /webhooks/docuseal` - DocuSeal webhook endpoint
- `POST /webhooks/docuseal/test` - Test webhook configuration
- `POST /webhooks/vapi` - VAPI phone webhook

---

## 🧠 Deal Calculator (5 endpoints)

- `POST /deal-calculator/calculate` - Calculate deal (3 strategies)
- `POST /deal-calculator/compare` - Compare investment strategies
- `GET /deal-calculator/property/{id}` - Get deal analysis
- `GET /deal-calculator/voice` - Voice-based deal calc

**Strategies**: Wholesale, Flip, Rental, BRRRR

---

## 💰 Offer Management (12 endpoints)

### Offer CRUD
- `GET /offers/` - List offers
- `POST /offers/` - Create offer
- `GET /offers/{id}` - Get offer details
- `PATCH /offers/{id}` - Update offer
- `DELETE /offers/{id}` - Delete offer
- `GET /offers/property/{id}/summary` - Offers for property

### Offer Actions
- `POST /offers/{id}/accept` - Accept offer
- `POST /offers/{id}/reject` - Reject offer
- `POST /offers/{id}/counter` - Counter offer
- `POST /offers/{id}/withdraw` - Withdraw offer
- `GET /offers/{id}/chain` - Offer chain analysis
- `GET /offers/property/{id}/draft-letter` - Draft offer letter
- `GET /offers/{id}/draft-letter` - Offer letter for specific offer
- `GET /offers/property/{id}/mao` - Maximum allowable offer

---

## 📈 Analytics (3 endpoints)

- `GET /analytics/portfolio` - Full portfolio analytics
- `GET /analytics/pipeline` - Pipeline breakdown
- `GET /analytics/contracts` - Contract statistics

**Metrics Included**:
- Pipeline stats (by status, type)
- Portfolio value (total, average, equity)
- Contract stats (by status, unsigned required)
- Activity stats (24h, 7d, 30d)
- Deal scores (average, distribution, top 5)
- Enrichment coverage (Zillow, skip trace)

---

## 🔍 Insights & Alerts (2 endpoints)

- `GET /insights/` - All insights with priority
- `GET /insights/property/{id}` - Property-specific insights

**Alert Types**:
- Stale properties (no activity 7+ days)
- Contract deadlines (approaching/overdue)
- Unsigned contracts (3+ days in draft)
- Missing enrichment (no Zillow data)
- Missing skip trace (no owner info)
- High score no action (80+ score, no contracts)

**Priorities**: urgent, high, medium, low

---

## 🎯 Property Scoring (4 endpoints)

- `POST /scoring/property/{id}` - Score a property
- `GET /scoring/top` - Get top scored properties
- `POST /scoring/bulk` - Score multiple properties
- `GET /scoring/property/{id}` - Get stored score breakdown

**4 Dimensions**:
- Market (30%): Zestimate spread, price trend, school quality
- Financial (25%): Zestimate upside, rental yield
- Readiness (25%): Contracts, contacts, skip trace
- Engagement (20%): Recent activity, notes, tasks

**Grades**: A (80+), B (60+), C (40+), D (20+), F (<20)

---

## 📊 Comparable Sales (3 endpoints)

- `GET /comps/{id}` - Full comps dashboard
- `GET /comps/{id}/sales` - Sales comps only
- `GET /comps/{id}/rentals` - Rental comps only

**Data Sources**:
- Agentic research comp sales
- Zillow price history
- Internal portfolio

**Metrics**: Average/median price, price per sqft, price trend, subject vs market, pricing recommendation

---

## 🔄 Bulk Operations (2 endpoints)

- `GET /bulk/operations` - List available operations
- `POST /bulk/execute` - Execute bulk operation

**Operations**:
- `enrich` - Zillow enrichment
- `skip_trace` - Owner discovery
- `attach_contracts` - Auto-attach templates
- `generate_recaps` - AI property recaps
- `update_status` - Change property status
- `check_compliance` - Compliance checks

**Batch Size**: Up to 50 properties with filters

---

## ⏰ Activity Timeline (3 endpoints)

- `GET /activity-timeline/` - Full timeline
- `GET /activity-timeline/property/{id}` - Property timeline
- `GET /activity-timeline/recent` - Recent activity

**Event Sources**: ConversationHistory, Notification, PropertyNote, ScheduledTask, Contract, ZillowEnrichment, SkipTrace

---

## 📋 Follow-Up Queue (3 endpoints)

- `GET /follow-ups/queue` - Get ranked queue
- `POST /follow-ups/{id}/complete` - Mark follow-up done
- `POST /follow-ups/{id}/snooze` - Snooze property

**Scoring**: 7 weighted signals, priority-based (urgent/high/medium/low)

---

## 📅 Scheduled Tasks (3 endpoints)

- `GET /scheduled-tasks/` - List tasks
- `GET /scheduled-tasks/due` - Get due tasks
- `DELETE /scheduled-tasks/{id}/cancel` - Cancel task

**Task Types**: REMINDER, RECURRING, FOLLOW_UP, CONTRACT_CHECK

---

## 📰 Daily Digest (3 endpoints)

- `GET /digest/latest` - Get latest digest
- `POST /digest/generate` - Generate new digest
- `GET /digest/history` - Get past digests

**Content**: Portfolio snapshot, urgent alerts, contract status, activity summary, recommendations

---

## 🚀 Pipeline Automation (2 endpoints)

- `GET /pipeline/status` - Get automation status
- `POST /pipeline/check` - Trigger pipeline check

**Auto-Transitions**:
- NEW_PROPERTY → ENRICHED (Zillow data added)
- ENRICHED → RESEARCHED (Skip trace complete)
- RESEARCHED → WAITING_FOR_CONTRACTS (Contracts attached)
- WAITING_FOR_CONTRACTS → COMPLETE (All contracts signed)

---

## 👀 Market Watchlist (5 endpoints)

- `GET /watchlists/` - List watchlists
- `POST /watchlists/` - Create watchlist
- `GET /watchlists/{id}` - Get watchlist details
- `PATCH /watchlists/{id}` - Update watchlist
- `DELETE /watchlists/{id}` - Delete watchlist
- `POST /watchlists/{id}/toggle` - Pause/resume
- `POST /watchlists/check/{id}` - Check if property matches

**Criteria**: City, state, property_type, price range, bedrooms, bathrooms, sqft

---

## 🔬 Property Research (8 endpoints)

### Research Operations
- `GET /research/` - List research
- `POST /research/` - Start research
- `GET /research/{id}` - Get research dossier
- `POST /research/ai-research` - AI-powered research
- `POST /research/api-research` - API-based research

### Property Research
- `GET /research/property/{id}/deep-dive` - Deep property research
- `GET /research/property/{id}/latest` - Latest research
- `GET /research/property/{id}/compliance` - Compliance research
- `GET /research/property/{id}/market-analysis` - Market analysis

### Agentic Research
- `GET /agentic/research` - Start agentic research
- `GET /agentic/jobs` - List research jobs
- `GET /agentic/jobs/{id}` - Get job status
- `GET /agentic/properties/{id}` - Get property research
- `GET /agentic/properties/{id}/dossier` - Full dossier
- `GET /agentic/properties/{id}/enrichment-status` - Enrichment status

---

## 🔍 Semantic Search (4 endpoints)

- `POST /search/research` - Semantic search
- `GET /search/health` - Search index health
- `POST /search/index/{id}` - Index property
- `POST /search/backfill` - Backfill search index

---

## 🧹 Web Scraper (7 endpoints)

### Scraping Operations
- `POST /scrape/url` - Scrape URL (preview)
- `POST /scrape/scrape-and-create` - Scrape and create property
- `POST /scrape/multiple` - Scrape multiple URLs
- `POST /scrape/scrape-and-enrich-batch` - Batch import with enrichment

### Specialized Scrapers
- `POST /scrape/zillow-listing` - Scrape Zillow listing
- `POST /scrape/zillow-search` - Scrape Zillow search results
- `POST /scrape/redfin-listing` - Scrape Redfin listing
- `POST /scrape/realtor-listing` - Scrape Realtor.com listing

---

## 🤖 AI Agents & Voice Goals (7 endpoints)

### AI Agent Execution
- `GET /ai-agents/` - List agents
- `POST /ai-agents/execute` - Execute agent
- `GET /ai-agents/{id}` - Get conversation
- `POST /ai-agents/property/{id}/analyze` - Analyze property
- `POST /ai-agents/templates/{id}/execute` - Execute template

### Voice Goal Planner
- `POST /ai-agents/voice-goals/execute` - Execute voice goal
- `POST /ai-agents/voice-goals/memory/event` - Log memory event
- `GET /ai-agents/voice-goals/memory/{id}` - Get session memory

---

## 📢 Voice Campaigns (10 endpoints)

### Campaign Management
- `GET /voice-campaigns/` - List campaigns
- `POST /voice-campaigns/` - Create campaign
- `GET /voice-campaigns/{id}` - Get campaign details
- `PATCH /voice-campaigns/{id}` - Update campaign
- `DELETE /voice-campaigns/{id}` - Delete campaign

### Campaign Execution
- `POST /voice-campaigns/{id}/start` - Start campaign
- `POST /voice-campaigns/{id}/pause` - Pause campaign
- `POST /voice-campaigns/{id}/resume` - Resume campaign
- `POST /voice-campaigns/process` - Process campaigns
- `GET /voice-campaigns/{id}/analytics` - Campaign analytics
- `POST /voice-campaigns/{id}/targets` - Add targets
- `POST /voice-campaigns/{id}/targets/from-filters` - Add from filters

---

## 📞 ElevenLabs Integration (8 endpoints)

- `GET /elevenlabs/setup` - Setup ElevenLabs
- `GET /elevenlabs/agent` - Get agent info
- `GET /elevenlabs/agent/prompt` - Get agent prompt
- `GET /elevenlabs/widget` - Get widget code
- `GET /elevenlabs/phone-numbers` - List phone numbers
- `POST /elevenlabs/import-twilio-number` - Import Twilio number
- `POST /elevenlabs/assign-phone/{id}` - Assign phone number
- `POST /elevenlabs/call` - Make call

---

## 🔔 Notifications (6 endpoints)

- `GET /notifications/` - List notifications
- `POST /notifications/` - Create notification
- `GET /notifications/{id}` - Get notification
- `POST /notifications/{id}/read` - Mark as read
- `POST /notifications/{id}/dismiss` - Dismiss notification

### Demo Notifications
- `POST /notifications/demo/new-lead` - Demo new lead
- `POST /notifications/demo/contract-signed` - Demo contract signed
- `POST /notifications/demo/appointment` - Demo appointment
- `POST /notifications/demo/price-change` - Demo price change

---

## ✅ Todos (7 endpoints)

- `GET /todos/` - List todos
- `POST /todos/` - Create todo
- `GET /todos/{id}` - Get todo
- `PATCH /todos/{id}` - Update todo
- `DELETE /todos/{id}` - Delete todo
- `GET /todos/property/{id}` - Get todos for property
- `GET /todos/contact/{id}` - Get todos for contact

### Voice Features
- `GET /todos/voice` - Voice todo list
- `GET /todos/voice/search` - Voice search todos

---

## 🔐 Compliance Engine (23 endpoints)

### Compliance Checks
- `POST /compliance/properties/{id}/check` - Run compliance check
- `GET /compliance/properties/{id}/checks` - List checks
- `GET /compliance/properties/{id}/latest-check` - Latest check
- `POST /compliance/properties/{id}/quick-check` - Quick check
- `GET /compliance/properties/{id}/report` - Compliance report
- `GET /compliance/checks/{id}` - Get check details
- `GET /compliance/checks/{id}/violations` - Get violations

### Knowledge Base
- `GET /compliance/knowledge/rules` - List rules
- `POST /compliance/knowledge/rules/ai-generate` - AI generate rule
- `GET /compliance/knowledge/rules/code/{code}` - Get rule by code
- `POST /compliance/knowledge/rules/import-csv` - Import rules
- `POST /compliance/knowledge/rules/bulk` - Bulk operations
- `POST /compliance/knowledge/rules/clone-state-rules` - Clone state rules
- `GET /compliance/knowledge/rules/{id}` - Get rule
- `PATCH /compliance/knowledge/rules/{id}` - Update rule
- `DELETE /compliance/knowledge/rules/{id}` - Delete rule
- `POST /compliance/knowledge/rules/{id}/activate` - Activate rule
- `POST /compliance/knowledge/rules/{id}/deactivate` - Deactivate rule
- `POST /compliance/knowledge/rules/{id}/clone` - Clone rule
- `GET /compliance/knowledge/rules/{id}/history` - Rule history
- `POST /compliance/knowledge/rules/{id}/publish` - Publish rule

### Templates & Categories
- `GET /compliance/knowledge/categories` - List categories
- `GET /compliance/knowledge/states` - List states
- `GET /compliance/knowledge/templates` - List templates
- `POST /compliance/knowledge/templates/{id}/use` - Use template

### Voice Features
- `GET /compliance/voice/check` - Voice compliance check
- `GET /compliance/voice/status` - Voice status
- `GET /compliance/voice/issues` - Voice issues
- `POST /compliance/knowledge/voice/add-rule` - Voice add rule
- `POST /compliance/knowledge/voice/search-rules` - Voice search

### Violations
- `GET /compliance/violations/{id}` - Get violation
- `POST /compliance/violations/{id}/resolve` - Resolve violation

---

## 🧠 Predictive Intelligence (7 endpoints)

### Outcome Prediction
- `POST /predictive/property/{id}/predict` - Predict closing probability
- `POST /predictive/batch/predict` - Batch predict outcomes
- `POST /predictive/outcomes/{id}/record` - Record actual outcome
- `GET /predictive/accuracy` - Get prediction accuracy

### Recommendations
- `POST /predictive/property/{id}/recommend` - Get next action recommendation

### Agent Patterns
- `GET /predictive/agents/{id}/patterns` - Get agent success patterns

---

## 🎯 Market Opportunities (4 endpoints)

- `POST /opportunities/scan` - Scan for opportunities
- `GET /opportunities/market-shifts` - Detect market shifts
- `GET /opportunities/property/{id}/similar` - Find similar properties

---

## 💑 Relationship Intelligence (3 endpoints)

- `GET /relationships/contact/{id}/health` - Relationship health score
- `GET /relationships/contact/{id}/best-method` - Best contact method
- `GET /relationships/contact/{id}/sentiment` - Sentiment analysis

---

## 🤝 Negotiation Agent (3 endpoints)

- `POST /intelligence/negotiation/property/{id}/analyze-offer` - Analyze offer
- `POST /intelligence/negotiation/property/{id}/counter-offer` - Generate counter
- `POST /intelligence/negotiation/property/{id}/suggest-price` - Suggest price

---

## 📄 Document Intelligence (3 endpoints)

- `POST /intelligence/documents/inspection` - Analyze inspection report
- `POST /intelligence/documents/appraisals/compare` - Compare appraisals
- `POST /intelligence/documents/contract/extract` - Extract contract terms

---

## 🏢 Competitive Intelligence (3 endpoints)

- `GET /intelligence/competition/market/{city}/{state}` - Market competition
- `GET /intelligence/competition/market/{city}/{state}/saturation` - Market saturation
- `GET /intelligence/competition/property/{id}/activity` - Property competition

---

## 🔗 Deal Sequencer (3 endpoints)

- `POST /intelligence/sequencing/1031-exchange` - 1031 exchange sequencing
- `POST /intelligence/sequencing/portfolio-acquisition` - Portfolio acquisition
- `POST /intelligence/sequencing/sell-and-buy` - Sell-and-buy sequencing

---

## 📊 Campaign Intelligence (2 endpoints)

- `POST /intelligence/campaigns/autonomous` - Autonomous campaign execution
- `POST /intelligence/campaigns/{id}/optimize` - Optimize campaign
- `GET /intelligence/campaigns/{id}/roi` - Campaign ROI

---

## 🗄️ Workspaces & Security (8 endpoints)

### Workspaces
- `GET /workspaces/` - List workspaces
- `POST /workspaces/` - Create workspace
- `GET /workspaces/{id}` - Get workspace
- `PATCH /workspaces/{id}` - Update workspace
- `DELETE /workspaces/{id}` - Delete workspace

### API Keys
- `GET /workspaces/{id}/api-keys` - List API keys
- `POST /workspaces/{id}/api-keys` - Create API key
- `POST /workspaces/api-keys/{id}/revoke` - Revoke API key

### Permissions
- `GET /workspaces/scopes` - List available scopes
- `GET /workspaces/{id}/permissions` - Get permissions

### Stats
- `GET /workspaces/{id}/stats` - Workspace stats

---

## 🔐 Approval System (7 endpoints)

- `GET /approval/config` - Get approval config
- `POST /approval/request` - Request approval
- `POST /approval/grant` - Grant approval
- `POST /approval/deny` - Deny approval
- `GET /approval/allowlist/{id}` - Check allowlist
- `GET /approval/autonomy-level` - Get autonomy level
- `GET /approval/risk-categories` - Get risk categories
- `GET /approval/audit-log` - Audit log

---

## 📚 Onboarding (5 endpoints)

- `POST /onboarding/welcome` - Welcome message
- `GET /onboarding/categories` - Get categories
- `GET /onboarding/questions` - Get questions
- `POST /onboarding/submit` - Submit onboarding
- `POST /onboarding/preview` - Preview onboarding
- `GET /onboarding/status/{id}` - Get onboarding status

---

## 🗂️ Context & Memory (10 endpoints)

### Context Management
- `GET /context/summary` - Get context summary
- `POST /context/enrich` - Enrich context
- `POST /context/clear` - Clear context
- `POST /context/property/create` - Create property from context
- `POST /context/skip-trace` - Skip trace from context

### History
- `GET /context/history` - Get conversation history
- `POST /context/history/log` - Log conversation
- `GET /context/history/property/{id}` - Get property history

---

## 🧪 Observer System (6 endpoints)

- `GET /observer/stats` - Observer statistics
- `GET /observer/event-types` - Event types
- `GET /observer/subscribers` - List subscribers
- `GET /observer/history` - Observer history
- `POST /observer/enable` - Enable observer
- `POST /observer/disable` - Disable observer

---

## 🔍 Search Index Management (3 endpoints)

- `POST /search/backfill` - Backfill search index
- `GET /search/health` - Search health check
- `POST /search/index/{id}` - Index property

---

## 🗃️ SQLite Optimization (8 endpoints)

- `GET /sqlite/stats` - Database statistics
- `POST /sqlite/stats/reset` - Reset stats
- `GET /sqlite/performance-report` - Performance report
- `GET /sqlite/slow-queries` - Slow queries
- `GET /sqlite/table-stats` - Table statistics
- `GET /sqlite/index-suggestions` - Index suggestions
- `GET /sqlite/optimizations` - Optimization suggestions
- `POST /sqlite/optimize` - Run optimizations

---

## 🎤 Skills System (10 endpoints)

- `GET /skills/categories` - Skill categories
- `GET /skills/marketplace` - Skills marketplace
- `POST /skills/create` - Create skill
- `GET /skills/discover` - Discover skills
- `POST /skills/install` - Install skill
- `GET /skills/installed/{id}` - Installed skills
- `GET /skills/detail/{name}` - Skill details
- `POST /skills/uninstall/{name}` - Uninstall skill
- `POST /skills/rate/{name}` - Rate skill
- `POST /skills/sync` - Sync skills
- `GET /skills/instructions/{id}` - Get instructions

---

## 🤖 Credential Scrubbing (5 endpoints)

- `GET /scrub/config` - Scrubbing config
- `POST /scrub/text` - Scrub text
- `POST /scrub/json` - Scrub JSON
- `GET /scrub/patterns` - Scrubbing patterns
- `POST /scrub/test` - Test scrubbing

---

## ⏰ Cron Scheduler (5 endpoints)

- `GET /scheduler/status` - Scheduler status
- `GET /scheduler/tasks` - List tasks
- `GET /scheduler/handlers` - List handlers
- `GET /scheduler/cron-expressions` - Cron expressions
- `POST /scheduler/tasks/{id}/run` - Run task manually

---

## 📋 Research Templates (4 endpoints)

- `GET /research-templates/` - List templates
- `POST /research-templates/` - Create template
- `GET /research-templates/{id}` - Get template
- `POST /research-templates/{id}/execute` - Execute template
- `GET /research-templates/categories/list` - List categories

---

## 🗑️ Deal Types (3 endpoints)

- `GET /deal-types/` - List deal types
- `POST /deal-types/` - Create deal type
- `GET /deal-types/{name}` - Get deal type
- `GET /deal-types/{name}/preview` - Preview deal type

---

## 📊 Agent Preferences (3 endpoints)

- `GET /agent-preferences/` - List preferences
- `POST /agent-preferences/` - Create preference
- `GET /agent-preferences/{id}` - Get preference
- `PATCH /agent-preferences/{id}` - Update preference
- `DELETE /agent-preferences/{id}` - Delete preference
- `GET /agent-preferences/agent/{id}` - Get agent preferences
- `GET /agent-preferences/agent/{id}/context` - Get agent context

---

## 👥 Agents (3 endpoints)

- `GET /agents/` - List agents
- `POST /agents/` - Create agent
- `GET /agents/{id}` - Get agent
- `PATCH /agents/{id}` - Update agent
- `DELETE /agents/{id}` - Delete agent
- `POST /agents/register` - Register agent (public)

---

## 💾 Cache Management (2 endpoints)

- `GET /cache/stats` - Cache statistics
- `POST /cache/clear` - Clear cache

---

## 📤 Exa Research (4 endpoints)

- `POST /exa/research` - Start research
- `GET /exa/research/{id}` - Get research status
- `POST /exa/research/property-dossier` - Property dossier
- `POST /exa/research/subdivision-dossier` - Subdivision dossier

---

## 📡 Display Command (1 endpoint)

- `POST /display/command` - Send display command to frontend

---

## 🎬 Workflows (2 endpoints)

- `GET /workflows/templates` - List workflow templates
- `POST /workflows/execute` - Execute workflow

---

## 🔄 Activities Logging (4 endpoints)

- `GET /activities/recent` - Recent activities
- `GET /activities/{id}` - Get activity
- `POST /activities/log` - Log activity

---

## 📞 Property Recap & Calls (7 endpoints)

- `GET /property-recap/property/{id}` - Get property recap
- `POST /property-recap/property/{id}/generate` - Generate recap
- `POST /property-recap/property/{id}/call` - Start recap call
- `GET /property-recap/call/{id}/status` - Call status
- `POST /property-recap/call/{id}/recording` - Call recording
- `POST /property-recap/call/{id}/end` - End call
- `POST /property-recap/property/{id}/send-report` - Send report

---

## 📊 Summary

**Total Features: 50+**
**Total Endpoints: 321**
**Categories:**
- Property Management: 15
- Contacts: 10
- Contracts: 42
- Analytics: 3
- AI/Intelligence: 40+
- Voice/Audio: 20+
- Compliance: 23
- Research: 15
- Automation: 25+
- Search: 10+
- And more...

**All endpoints include:**
- ✅ Voice summaries for TTS
- ✅ Error handling
- ✅ API key authentication
- ✅ Comprehensive responses
- ✅ Cross-property context injection
