---
name: ai-realtor
description: Complete AI-powered real estate operations platform - 200+ endpoints for property management, contracts, deal scoring, marketing, and voice automation
version: 1.0.0
author: AI Realtor Team
metadata:
  openclaw:
    emoji: "🏠"
    category: "real-estate"
    tags: ["properties", "contracts", "ai", "automation", "marketing", "voice"]
    requires:
      env: ["AI_REALTOR_API_URL", "AI_REALTOR_API_KEY"]
      bins: ["curl"]
    priority: 90
    heartbeat:
      enabled: true
      interval: 3600
      check_endpoint: "/health"
---

# 🏠 AI Realtor Platform

**Complete backend for AI-powered real estate operations.**

The AI Realtor API is a production-ready platform that turns any AI assistant into a full real estate operations center. Built for Clawbot/OpenClaw with 200+ endpoints, 135 voice commands, and 40 feature categories.

## 🚀 Quick Start

### Prerequisites

Set these environment variables:

```bash
export AI_REALTOR_API_URL="http://localhost:8000"  # or your deployed URL
export AI_REALTOR_API_KEY="your-api-key-here"
```

### Live Deployment

- **API:** https://ai-realtor.fly.dev
- **Docs:** https://ai-realtor.fly.dev/docs
- **GitHub:** https://github.com/Thedurancode/ai-realtor

### Basic Usage

```bash
# Health check
curl $AI_REALTOR_API_URL/health

# List properties
curl -H "X-API-Key: $AI_REALTOR_API_KEY" \
  $AI_REALTOR_API_URL/properties/

# Get specific property
curl -H "X-API-Key: $AI_REALTOR_API_KEY" \
  $AI_REALTOR_API_URL/properties/1
```

## 🎯 Core Concepts

### Property Pipeline (5 Stages)

Properties automatically progress through these stages:

1. **NEW_PROPERTY** - Just created, needs enrichment
2. **ENRICHED** - Zillow data added
3. **RESEARCHED** - Skip trace completed
4. **WAITING_FOR_CONTRACTS** - Contracts attached, awaiting signatures
5. **COMPLETE** - All required contracts signed

Properties auto-advance based on activity. Manual changes have 24-hour grace period.

### Deal Scoring (4 Dimensions)

Every property gets scored across 4 dimensions:

| Dimension | Weight | Signals |
|-----------|--------|---------|
| **Market** | 30% | Zestimate spread, days on market, price trend, schools, tax gap |
| **Financial** | 25% | Zestimate upside, rental yield, price per sqft |
| **Readiness** | 25% | Contract completion %, contacts, skip trace reachability |
| **Engagement** | 20% | Recent activity, notes, tasks, notifications |

**Grade Scale:** A (80+), B (60+), C (40+), D (20+), F (<20)

### Property Heartbeat

Every property has a heartbeat showing:
- Pipeline stage (1-5)
- 4-item checklist: enrich, skip trace, contracts attached, contracts complete
- Health status: healthy, stale (inactive too long), blocked (can't advance)
- Next action to advance deal

**Stale thresholds:** New 3d → Enriched 5d → Researched 7d → Waiting 10d → Complete never

---

## 📱 Voice Commands (135 Total)

### Property Management (7 commands)

```
"Create a property at 123 Main St in Miami for $750,000"
"Show me all condos under 500k in Miami"
"Get details for property 5"
"Update property 5 status to complete"
"Delete property 3"
"Enrich property 5 with Zillow data"
"Skip trace property 5"
```

### Contract Management (13 commands)

```
"Is property 5 ready to close?"
"Suggest contracts for property 5 using AI"
"Apply AI contract suggestions for property 5"
"Send the Purchase Agreement for signing"
"Who hasn't signed yet?"
"Check contract status for property 5"
"Attach required contracts to property 5"
"Mark contract 3 as required"
"List all contracts"
"Send contract 5 to the seller"
"Smart send all required contracts"
"Get signing status for property 5"
"Check readiness for property 5"
```

### Deal Scoring (4 commands)

```
"Score property 5"
"Show me the score breakdown for property 5"
"Score all my properties"
"What are my best deals?"
```

### Analytics (3 commands)

```
"How's my portfolio doing?"
"How many properties in each status?"
"How are my contracts looking?"
```

### Research (7 commands)

```
"Research property 5 in depth"
"Find properties similar to property 5"
"Get research status for property 5"
"Get the research dossier for property 5"
"Search past research for Miami condos"
"Semantic search for modern properties"
```

### Marketing (12 commands)

```
"Set up my brand with Emprezario Inc"
"Apply the Luxury Gold color scheme"
"Generate a preview of my brand"
"Create a Facebook ad for property 5"
"Generate market research for Miami"
"Analyze competitor ads"
"Launch my campaign to Meta"
"Track my Facebook ad performance"
"Create a social media post for this property"
"Schedule posts for next week"
"Generate Instagram content with AI"
"Create a 10-post campaign"
```

### Phone Calls (6 commands)

```
"Call John about property 5"
"Call the owner of property 5"
"Call contact 3 about the Purchase Agreement"
"Call +14155551234 using ElevenLabs"
"Set up ElevenLabs voice"
"Check call status"
```

### Notes & History (4 commands)

```
"Note that property 5 has a new fence installed"
"Show me notes for property 5"
"What have we done on property 5?"
"What did we talk about?"
```

### Workflows (2 commands)

```
"What workflows are available?"
"Run the new lead workflow on property 5"
```

### Campaigns (6 commands)

```
"Create a cold calling campaign"
"Start campaign 3"
"Pause campaign 3"
"How is campaign 3 doing?"
"Show me all campaigns"
"Add properties 5-10 to campaign 3"
```

### Notifications (5 commands)

```
"Send notification about property 5"
"Show me notifications"
"Mark notification 3 as read"
"Any notifications?"
"Poll for updates"
```

### Scheduled Tasks (3 commands)

```
"Remind me to follow up on property 5 in 3 days"
"What tasks are scheduled?"
"Cancel task 3"
```

### Pipeline Automation (2 commands)

```
"What's the pipeline status?"
"Run pipeline automation now"
```

### Daily Digest (2 commands)

```
"What's my daily digest?"
"Generate a fresh digest now"
```

### Follow-Up Queue (3 commands)

```
"What should I work on next?"
"Show me my follow-up queue"
"Snooze property 5 for 48 hours"
```

### Comparable Sales (3 commands)

```
"Show me comps for property 5"
"What are nearby sales for property 5?"
"What are rental comps for property 5?"
```

### Bulk Operations (2 commands)

```
"Enrich all Miami properties"
"Skip trace properties 1 through 5"
```

### Activity Timeline (3 commands)

```
"Show me the timeline"
"What happened today?"
"What's the activity on property 5?"
```

### Watchlists (5 commands)

```
"Watch for Miami condos under 500k"
"Show me my watchlists"
"Pause watchlist 1"
"Delete watchlist 3"
"Does property 5 match any watchlists?"
```

### Property Heartbeat (1 command)

```
"What's the heartbeat on property 5?"
```

### Web Scraper (6 commands)

```
"Scrape this Zillow listing URL"
"What data can we extract from this URL?"
"Add this property from the URL"
"Show me properties from this Zillow search"
"Import these 10 listings"
"Scrape this Redfin property"
```

### Predictive Intelligence (6 commands)

```
"Predict the outcome for property 5"
"What's the closing probability?"
"What should I do next with property 5?"
"Recommend next action for property 5"
"Predict outcomes for all my deals"
"Record that property 5 closed successfully"
```

### Market Opportunities (3 commands)

```
"Scan for opportunities matching my patterns"
"Any market shifts in Austin?"
"Show me properties similar to 123 Main St"
```

### Relationship Intelligence (3 commands)

```
"How's my relationship with John Smith?"
"Score relationship health for contact 3"
"Predict the best way to reach Sarah"
```

### Negotiation (3 commands)

```
"Analyze this $400,000 offer"
"Generate a counter-offer for $425,000"
"Suggest an offer price for property 3"
```

### Document Analysis (2 commands)

```
"Analyze this inspection report"
"Extract terms from this contract"
```

### Competitive Intelligence (3 commands)

```
"Who are the top agents in Miami?"
"Is there competition for property 5?"
"What's the market saturation in Denver?"
```

### Deal Sequencing (3 commands)

```
"Set up a 1031 exchange for property 5"
"Sequence buying properties 1, 2, and 3"
"I need to sell 5 and buy 10"
```

---

## 🔌 API Endpoints by Category

### Health & Base

```
GET  /health                    - Health check
GET  /docs                      - Interactive API documentation
GET  /openapi.json             - OpenAPI specification
```

### Properties (6 endpoints)

```
POST   /properties/                    - Create property
GET    /properties/                    - List properties (with filters)
GET    /properties/{id}                - Get property details
PUT    /properties/{id}                - Update property
DELETE /properties/{id}                - Delete property
GET    /properties/{id}/heartbeat      - Get property heartbeat
```

**Filters for GET /properties/:**
- `status` - new_property, enriched, researched, waiting_for_contracts, complete
- `property_type` - house, condo, townhouse, apartment, land, commercial, multi_family
- `city` - Case-insensitive partial match
- `min_price` / `max_price` - Price range
- `bedrooms` - Minimum bedrooms
- `include_heartbeat` - true/false (default true)

### Zillow Enrichment (1 endpoint)

```
POST /properties/{id}/enrich    - Enrich with Zillow data
```

**Returns:** Photos (up to 10), Zestimate, Rent Zestimate, tax history, price history, schools with ratings, property features, market statistics.

### Skip Tracing (1 endpoint)

```
POST /properties/{id}/skip-trace    - Find property owner
```

**Returns:** Owner name, phone numbers, email addresses, mailing address. Auto-creates contact.

### Contacts (1 endpoint)

```
POST /contacts/    - Add contact to property
```

**Roles:** buyer, seller, lawyer, attorney, contractor, inspector, appraiser, lender, mortgage_broker, title_company, tenant, landlord, property_manager, handyman, plumber, electrician, photographer, stager, other

### Contracts (13 endpoints)

```
POST   /contracts/                              - Create contract
GET    /contracts/                              - List contracts
GET    /contracts/{id}                          - Get contract
PUT    /contracts/{id}                          - Update contract
DELETE /contracts/{id}                          - Delete contract
POST   /contracts/{id}/send                     - Send for signature
GET    /contracts/property/{property_id}        - Get property contracts
POST   /contracts/check-readiness               - Check if ready to close
POST   /contracts/ai-suggest                    - AI suggests contracts
POST   /contracts/attach-required               - Auto-attach templates
POST   /contracts/smart-send                    - Multi-party send
GET    /contracts/signing-status/{property_id}  - Check who signed
POST   /contracts/{id}/mark-required            - Mark required/optional
POST   /contracts/apply-ai-suggestions          - Apply AI suggestions
```

**Contract Statuses:** draft, sent, in_progress, pending_signature, completed, cancelled, expired, archived

**Contract Roles:** buyer, seller, attorney, title_company, witness, other

### DocuSeal Webhooks (1 endpoint)

```
POST /webhooks/docuseal    - DocuSeal signature events
```

**Security:** HMAC-SHA256 signature verification with constant-time comparison.

**Events:** document.completed, document.viewed, document.sent, document.signed

### Property Recaps (2 endpoints)

```
POST /properties/{id}/recaps/generate    - Generate AI recap
GET  /properties/{id}/recaps              - Get latest recap
```

**Recap includes:** Property overview, market analysis, contract status, contacts, notes, next steps.

**Auto-regeneration triggers:** contract_signed, enrichment_updated, skip_trace_completed, note_added, contact_added, property_updated, manual

### Phone Calls (3 endpoints)

```
POST /phone-calls/property/{property_id}           - Call about property
POST /phone-calls/contact/{contact_id}             - Call contact
POST /phone-calls/contract/{contract_id}           - Call about contract
POST /phone-calls/elevenlabs                       - ElevenLabs call
GET  /phone-calls/status/{call_id}                 - Get call status
POST /phone-calls/elevenlabs/setup                 - Configure ElevenLabs
```

**Call Types:** property_update, contract_reminder, closing_ready, specific_contract, skip_trace_outreach

**VAPI integration:** Automated AI phone calls with conversation tracking.

### Property Notes (5 endpoints)

```
POST   /property-notes/                    - Create note
GET    /property-notes/?property_id={id}    - List notes for property
GET    /property-notes/{id}                - Get specific note
PUT    /property-notes/{id}                - Update note
DELETE /property-notes/{id}                - Delete note
```

**Note Sources:** voice, manual, ai, phone_call, system

### Conversation History (4 endpoints)

```
POST /context/history/log                    - Log conversation entry
GET  /context/history                        - Get session history
GET  /context/history/property/{property_id} - Get property timeline
DELETE /context/history                      - Clear history
```

**Auto-tracking:** Every MCP tool call with property_id is automatically logged.

### Workflows (2 endpoints)

```
GET  /workflows/                   - List available workflows
POST /workflows/{template}/execute - Execute workflow
```

**Workflow Templates:** new_lead_setup, deal_closing, property_enrichment, skip_trace_outreach, ai_contract_setup

### Voice Campaigns (6 endpoints)

```
POST   /campaigns/                      - Create campaign
GET    /campaigns/                      - List campaigns
GET    /campaigns/{id}                  - Get campaign details
POST   /campaigns/{id}/start            - Start campaign
POST   /campaigns/{id}/pause            - Pause campaign
POST   /campaigns/{id}/targets          - Add targets
GET    /campaigns/{id}/status           - Get status
```

### Notifications (5 endpoints)

```
POST   /notifications/                 - Create notification
GET    /notifications/                 - List notifications
POST   /notifications/{id}/acknowledge  - Mark as read
GET    /notifications/summary          - Get summary
GET    /notifications/poll             - Poll for updates
```

**Priorities:** urgent, high, medium, low

### Insights (2 endpoints)

```
GET /insights/                      - All alerts (optional ?priority= filter)
GET /insights/property/{property_id} - Property-specific alerts
```

**6 Alert Rules:**
1. Stale properties (7+ days no activity)
2. Contract deadlines approaching
3. Unsigned required contracts (3+ days)
4. Missing enrichment
5. Missing skip trace
6. High score deals with no action

### Scheduled Tasks (5 endpoints)

```
POST   /scheduled-tasks/              - Create task
GET    /scheduled-tasks/              - List tasks
GET    /scheduled-tasks/{id}          - Get specific task
DELETE /scheduled-tasks/{id}/cancel   - Cancel task
GET    /scheduled-tasks/due           - Get due tasks
```

**Task Types:** reminder, recurring, follow_up, contract_check

**Status:** pending, in_progress, completed, cancelled, skipped

### Analytics (3 endpoints)

```
GET /analytics/portfolio    - Full portfolio dashboard
GET /analytics/pipeline     - Pipeline breakdown
GET /analytics/contracts    - Contract statistics
```

**6 Metric Categories:** pipeline stats, portfolio value, contract stats, activity stats, deal scores, enrichment coverage

### Pipeline Automation (2 endpoints)

```
GET  /pipeline/status    - Recent auto-transitions
POST /pipeline/check     - Manual trigger
```

### Daily Digest (3 endpoints)

```
GET  /digest/latest           - Most recent digest
POST /digest/generate         - Manual trigger
GET  /digest/history?days=7   - Past digests
```

**Auto-generated:** Daily at 8 AM (configurable)

### Follow-Up Queue (3 endpoints)

```
GET  /follow-ups/queue?limit=10&priority=high    - Get ranked queue
POST /follow-ups/{property_id}/complete          - Mark complete
POST /follow-ups/{property_id}/snooze?hours=72   - Snooze property
```

**Priority scoring:** 7 weighted signals (days since activity, deal grade, deadlines, tasks, contracts, skip trace, contacts)

### Comparable Sales (3 endpoints)

```
GET /comps/{property_id}          - Full dashboard
GET /comps/{property_id}/sales    - Sales comps only
GET /comps/{property_id}/rentals  - Rental comps only
```

**3 Data Sources:** Agentic research, Zillow price history, internal portfolio

### Bulk Operations (2 endpoints)

```
POST /bulk/execute      - Execute bulk operation
GET  /bulk/operations   - List operations
```

**6 Operations:** enrich, skip_trace, attach_contracts, generate_recaps, update_status, check_compliance

**Max properties:** 50 per operation

**Selection:** Explicit IDs AND/OR filters (city, status, type, price, bedrooms)

### Activity Timeline (3 endpoints)

```
GET /activity-timeline/                        - Full timeline
GET /activity-timeline/property/{property_id}  - Property timeline
GET /activity-timeline/recent?hours=24         - Recent activity
```

**7 Data Sources:** ConversationHistory, Notification, PropertyNote, ScheduledTask, Contract, ZillowEnrichment, SkipTrace

**Filters:** event_type, start_date, end_date, search_text, offset, limit

### Property Scoring (4 endpoints)

```
POST /scoring/property/{property_id}    - Score property
POST /scoring/bulk                      - Bulk score
GET  /scoring/property/{property_id}    - Get breakdown
GET  /scoring/top?limit=10              - Top properties
```

### Market Watchlists (5 endpoints)

```
POST   /watchlists/                     - Create watchlist
GET    /watchlists/                     - List watchlists
GET    /watchlists/{id}                 - Get watchlist
PUT    /watchlists/{id}                 - Update watchlist
DELETE /watchlists/{id}                 - Delete watchlist
POST   /watchlists/{id}/toggle          - Pause/resume
POST   /watchlists/check/{property_id}  - Check matches
```

**Criteria:** city, state, property_type, min_price, max_price, min_bedrooms, min_bathrooms, min_sqft

### Web Scraper (8 endpoints)

```
POST /scrape/url                    - Scrape and preview
POST /scrape/multiple               - Scrape multiple URLs
POST /scrape/scrape-and-create      - Scrape and create property
POST /scrape/zillow-listing         - Scrape Zillow URL
POST /scrape/redfin-listing         - Scrape Redfin URL
POST /scrape/realtor-listing        - Scrape Realtor.com URL
POST /scrape/zillow-search          - Scrape Zillow search page
POST /scrape/scrape-and-enrich-batch - Bulk import with enrichment
```

**Specialized scrapers:** Zillow, Redfin, Realtor.com

**Generic scraper:** Any website using Claude Sonnet 4

### Deal Calculator & Offers (18 endpoints)

```
POST /deals/calculate              - Calculate deal metrics
POST /deals/mao                    - Maximum allowable offer
POST /deals/what-if                - Scenario modeling
POST /deals/compare-strategies     - Compare strategies
POST /deals/preview-type           - Preview deal type
POST /deals/set-type               - Set deal type
GET  /deals/status/{property_id}   - Get deal status
POST /deals/types/create           - Create deal type config
PUT  /deals/types/{id}             - Update deal type config
DELETE /deals/types/{id}           - Delete deal type config
GET  /deals/types                  - List deal types
POST /offers/create                - Create offer
GET  /offers/                      - List offers
GET  /offers/{id}                  - Get offer details
POST /offers/{id}/accept           - Accept offer
POST /offers/{id}/reject           - Reject offer
POST /offers/{id}/counter          - Counter offer
POST /offers/{id}/withdraw         - Withdraw offer
POST /offers/{id}/draft-letter     - Draft offer letter
```

### Research (7 endpoints)

```
POST /research/property/{property_id}    - Start research
GET  /research/status/{property_id}      - Get research status
GET  /research/dossier/{property_id}     - Get research dossier
POST /research/search                    - Search past research
```

### Compliance (2 endpoints)

```
POST /compliance/check              - Run compliance check
GET  /compliance/requirements       - Get requirements
```

### Intelligence (30 endpoints)

#### Predictive Intelligence (6)
```
POST /intelligence/predict/{property_id}      - Predict outcome
GET  /intelligence/prediction/{property_id}   - Get prediction
POST /intelligence/predict/batch               - Batch predict
POST /intelligence/outcome/record              - Record outcome
GET  /intelligence/patterns/{agent_id}         - Success patterns
GET  /intelligence/accuracy/{agent_id}         - Prediction accuracy
```

#### Market Opportunities (3)
```
POST /intelligence/opportunities/scan         - Scan for deals
POST /intelligence/market/detect-shifts        - Detect shifts
POST /intelligence/similar/{property_id}       - Find similar
```

#### Relationship Intelligence (3)
```
POST /intelligence/relationships/score         - Score relationship
POST /intelligence/relationships/best-method   - Best contact method
POST /intelligence/relationships/sentiment     - Sentiment analysis
```

#### Negotiation Agent (3)
```
POST /intelligence/negotiation/analyze-offer   - Analyze offer
POST /intelligence/negotiation/counter         - Generate counter
POST /intelligence/negotiation/suggest-price   - Suggest price
```

#### Document Analysis (3)
```
POST /intelligence/documents/inspection        - Analyze inspection
POST /intelligence/documents/extract-terms     - Extract terms
POST /intelligence/documents/compare-appraisals - Compare appraisals
```

#### Competitive Intelligence (3)
```
POST /intelligence/competition/analyze         - Analyze competition
POST /intelligence/competition/detect-activity  - Detect activity
POST /intelligence/competition/saturation      - Market saturation
```

#### Deal Sequencer (3)
```
POST /intelligence/sequence/1031               - 1031 exchange
POST /intelligence/sequence/portfolio          - Portfolio acquisition
POST /intelligence/sequence/sell-buy           - Sell and buy
```

### Marketing Hub (39 endpoints)

#### Agent Branding (12)
```
POST   /agent-brand/{id}                  - Create brand
GET    /agent-brand/{id}                  - Get brand
PUT    /agent-brand/{id}                  - Update brand
DELETE /agent-brand/{id}                  - Delete brand
GET    /agent-brand/colors/presets        - Get presets
POST   /agent-brand/{id}/apply-preset     - Apply preset
POST   /agent-brand/{id}/generate-preview - Generate preview
GET    /agent-brand/{id}/preview          - Get preview
POST   /agent-brand/{id}/validate         - Validate
GET    /agent-brand/{id}/guidelines       - Get guidelines
POST   /agent-brand/{id}/export           - Export brand kit
```

#### Facebook Ads (13)
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

#### Postiz Social Media (14)
```
POST /social/accounts/connect              - Connect account
GET  /social/accounts                      - List accounts
POST /social/posts/create                  - Create post
POST /social/posts/{id}/schedule           - Schedule post
GET  /social/posts                         - List posts
GET  /social/posts/{id}                    - Get post
PUT  /social/posts/{id}                    - Update post
POST /social/ai/generate                   - AI content
POST /social/campaigns/create              - Create campaign
GET  /social/campaigns                     - List campaigns
POST /social/templates/create              - Create template
GET  /social/templates                     - List templates
GET  /social/analytics/overview            - Analytics
GET  /social/calendar                      - Content calendar
```

### Property Videos (4 endpoints)

```
POST /property-videos/generate          - Generate video
GET  /property-videos/voices             - List available voices
POST /property-videos/script-preview     - Preview script
POST /property-videos/voiceover          - Generate standalone audio
```

**Video features:** Logo intro (3s), photo slideshow (4s per photo), property details overlay, ElevenLabs AI voiceover.

---

## 🎓 Common Workflows

### New Lead Setup (One voice command)

```
"Set up property 5 as a new lead"
```

**Automatically executes:**
1. Property enrichment with Zillow data
2. Skip tracing to find owner
3. State-specific contracts attached
4. AI recap generated
5. Summary presented

### Portfolio Review

```
"What needs attention?"
```

**Returns:**
- Priority-ranked stale properties
- Contracts approaching deadlines
- Unsigned required contracts
- High-score deals with no activity
- Best contacts for follow-up

### Marketing Campaign

```
"Create a Facebook ad for property 5"
```

**Generates:**
- Ad copy with brand voice
- Target audience recommendations
- Campaign ready for Meta Ads Manager

### Deal Analysis

```
"Score property 5"
```

**Provides:**
- 4-dimension score breakdown
- A-F grade
- Strengths and weaknesses
- Improvement recommendations

---

## 🔐 Authentication

All endpoints (except /health, /docs) require API key authentication:

```bash
curl -H "X-API-Key: $AI_REALTOR_API_KEY" \
  $AI_REALTOR_API_URL/properties/
```

Or via query parameter:

```bash
curl "$AI_REALTOR_API_URL/properties/?api_key=$AI_REALTOR_API_KEY"
```

---

## 📊 Response Formats

### Property Response

```json
{
  "id": 1,
  "address": "123 Main St",
  "city": "Miami",
  "state": "FL",
  "zip_code": "33101",
  "price": 750000,
  "bedrooms": 3,
  "bathrooms": 2,
  "square_footage": 1800,
  "property_type": "house",
  "status": "enriched",
  "deal_score": 85,
  "score_grade": "A",
  "heartbeat": {
    "stage": "Enriched",
    "stage_index": 2,
    "checklist": {
      "enrichment_complete": true,
      "skip_trace_complete": false,
      "contracts_attached": false,
      "contracts_completed": false
    },
    "health_status": "healthy",
    "next_action": "Skip trace the property to find owner"
  }
}
```

### Contract Response

```json
{
  "id": 1,
  "property_id": 5,
  "template_name": "Florida Residential Purchase Agreement",
  "status": "pending_signature",
  "document_url": "https://docuseal.com/...",
  "signer_roles": ["buyer", "seller"],
  "required": true,
  "deadline": "2026-03-01"
}
```

---

## 🚀 Advanced Features

### Auto-Recap Regeneration

Property recaps automatically regenerate when:
- Contract signed via webhook
- Property enriched
- Skip trace completed
- Note added
- Contact added
- Property updated

### Pipeline Automation

Properties auto-advance every 5 minutes:
- NEW_PROPERTY → ENRICHED (when Zillow data exists)
- ENRICHED → RESEARCHED (when skip trace exists)
- RESEARCHED → WAITING_FOR_CONTRACTS (when 1+ contract attached)
- WAITING_FOR_CONTRACTS → COMPLETE (when all required contracts completed)

### Daily Digest

Auto-generated at 8 AM daily:
- Portfolio snapshot
- Urgent alerts
- Contract status
- Activity summary
- Top recommendations

### Smart Follow-Up Queue

AI-scored priority ranking:
- Days since last activity (base score)
- Deal grade multiplier (A=2x, F=0.5x)
- Contract deadlines (+40)
- Overdue tasks (+35)
- Unsigned contracts (+30)
- Skip trace without outreach (+25)
- Missing contacts (+15)

### Watchlist Auto-Firing

New properties automatically checked against all active watchlists. Matches create HIGH priority notifications.

---

## 🛠️ Integration Examples

### Create Property from Zillow URL

```bash
# Scrape and create
curl -X POST "$AI_REALTOR_API_URL/scrape/scrape-and-create" \
  -H "X-API-Key: $AI_REALTOR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.zillow.com/homedetails/...",
    "auto_enrich": true
  }'
```

### Send Contract for Signature

```bash
curl -X POST "$AI_REALTOR_API_URL/contracts/1/send" \
  -H "X-API-Key: $AI_REALTOR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "signer_roles": ["buyer", "seller"],
    "subject": "Purchase Agreement for 123 Main St",
    "message": "Please review and sign"
  }'
```

### Score Property

```bash
curl -X POST "$AI_REALTOR_API_URL/scoring/property/5" \
  -H "X-API-Key: $AI_REALTOR_API_KEY"
```

### Create Voice Campaign

```bash
curl -X POST "$AI_REALTOR_API_URL/campaigns" \
  -H "X-API-Key: $AI_REALTOR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cold Calling Campaign",
    "call_type": "skip_trace_outreach",
    "target_property_ids": [1, 2, 3]
  }'
```

---

## 📚 Additional Resources

See `/references/` directory for:
- `api-endpoints.md` - Complete endpoint reference
- `voice-commands.md` - All 135 voice commands
- `workflows.md` - Workflow templates
- `integration-guide.md` - Integration best practices

---

## 🆕 Troubleshooting

### Property not auto-advancing?

Check heartbeat:
```bash
curl "$AI_REALTOR_API_URL/properties/5/heartbeat?api_key=$AI_REALTOR_API_KEY"
```

Manual pipeline check:
```bash
curl -X POST "$AI_REALTOR_API_URL/pipeline/check?api_key=$AI_REALTOR_API_KEY"
```

### Contracts not sending?

Check signing status:
```bash
curl "$AI_REALTOR_API_URL/contracts/signing-status/5?api_key=$AI_REALTOR_API_KEY"
```

Test DocuSeal webhook:
```bash
curl -X POST "$AI_REALTOR_API_URL/webhooks/test?api_key=$AI_REALTOR_API_KEY"
```

### Missing enrichment?

Re-enrich property:
```bash
curl -X POST "$AI_REALTOR_API_URL/properties/5/enrich?api_key=$AI_REALTOR_API_KEY"
```

---

**Built for the future of real estate. Ready for today.** 🏠✨
