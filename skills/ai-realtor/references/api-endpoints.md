# API Endpoints Reference

Complete reference for all 200+ AI Realtor API endpoints.

## Base URL

```
Production: https://ai-realtor.fly.dev
Local: http://localhost:8000
```

## Authentication

All endpoints require API key via header or query parameter:

```bash
# Header method
curl -H "X-API-Key: YOUR_KEY" https://ai-realtor.fly.dev/properties/

# Query parameter method
curl "https://ai-realtor.fly.dev/properties/?api_key=YOUR_KEY"
```

---

## Health & Documentation

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-02-26T10:00:00Z"
}
```

### GET /docs
Interactive API documentation (Swagger UI).

### GET /openapi.json
OpenAPI specification JSON.

---

## Properties

### POST /properties/
Create a new property.

**Request Body:**
```json
{
  "address": "123 Main St",
  "city": "Miami",
  "state": "FL",
  "zip_code": "33101",
  "price": 750000,
  "bedrooms": 3,
  "bathrooms": 2,
  "square_footage": 1800,
  "property_type": "house",
  "agent_id": 1,
  "place_id": "optional_google_places_id"
}
```

**Response:** Property object with heartbeat

### GET /properties/
List properties with filtering.

**Query Parameters:**
- `status` - Filter by status (new_property, enriched, researched, waiting_for_contracts, complete)
- `property_type` - Filter by type (house, condo, townhouse, apartment, land, commercial, multi_family)
- `city` - Filter by city (case-insensitive partial match)
- `min_price` - Minimum price
- `max_price` - Maximum price
- `bedrooms` - Minimum bedrooms
- `include_heartbeat` - Include heartbeat data (default: true)

**Example:**
```
GET /properties/?city=Miami&status=enriched&min_price=500000&bedrooms=3
```

### GET /properties/{id}
Get single property details.

**Response:** Property object with heartbeat, enrichment, contacts, contracts, notes

### PUT /properties/{id}
Update property.

**Request Body:** Same as POST /properties/ (all fields optional)

### DELETE /properties/{id}
Delete property and all related data.

### GET /properties/{id}/heartbeat
Get detailed property heartbeat.

**Response:**
```json
{
  "property_id": 5,
  "stage": "Enriched",
  "stage_index": 2,
  "progress": "40%",
  "checklist": {
    "enrichment_complete": true,
    "skip_trace_complete": false,
    "contracts_attached": false,
    "contracts_completed": false
  },
  "health_status": "healthy",
  "days_in_stage": 2,
  "stale_threshold_days": 5,
  "next_action": "Skip trace the property to find owner information",
  "voice_summary": "Property 5 is enriched and researched. Next action is skip trace."
}
```

---

## Zillow Enrichment

### POST /properties/{id}/enrich
Enrich property with Zillow data.

**Triggers:** Auto-recap regeneration

**Returns:**
- Photos (up to 10 high-res images)
- Zestimate (current market value)
- Rent Zestimate (monthly rent estimate)
- Tax assessment history
- Price history (past sales)
- Nearby schools (ratings, test scores, grades)
- Property features (year built, lot size, parking, heating/cooling)
- Market statistics

**Response:**
```json
{
  "property_id": 5,
  "photos": ["url1", "url2", ...],
  "zestimate": 785000,
  "rent_zestimate": 3500,
  "tax_history": [...],
  "price_history": [...],
  "schools": [...],
  "features": {...}
}
```

---

## Skip Tracing

### POST /properties/{id}/skip-trace
Find property owner contact information.

**Returns:**
- Owner name
- Phone numbers (mobile, landline)
- Email addresses
- Mailing address

**Side effects:**
- Auto-creates contact linked to property
- Auto-recap regeneration

**Response:**
```json
{
  "property_id": 5,
  "owner_name": "John Smith",
  "phone_numbers": ["+14155551234"],
  "email_addresses": ["john@example.com"],
  "mailing_address": "123 Main St, Miami, FL 33101"
}
```

---

## Contacts

### POST /contacts/
Add contact to property.

**Request Body:**
```json
{
  "property_id": 5,
  "name": "John Smith",
  "email": "john@example.com",
  "phone": "+14155551234",
  "role": "buyer",
  "agent_id": 1
}
```

**Roles:** buyer, seller, lawyer, attorney, contractor, inspector, appraiser, lender, mortgage_broker, title_company, tenant, landlord, property_manager, handyman, plumber, electrician, photographer, stager, other

---

## Contracts

### POST /contracts/
Create contract manually.

**Request Body:**
```json
{
  "property_id": 5,
  "template_name": "Purchase Agreement",
  "status": "draft",
  "content": "Contract text or template ID",
  "signer_roles": ["buyer", "seller"],
  "required": true,
  "deadline": "2026-03-01"
}
```

### GET /contracts/
List all contracts (optional ?property_id= filter)

### GET /contracts/{id}
Get contract details

### PUT /contracts/{id}
Update contract

### DELETE /contracts/{id}
Delete contract

### POST /contracts/{id}/send
Send contract for signature via DocuSeal.

**Request Body:**
```json
{
  "signer_roles": ["buyer", "seller"],
  "subject": "Purchase Agreement for 123 Main St",
  "message": "Please review and sign the attached contract"
}
```

### GET /contracts/property/{property_id}
Get all contracts for a property

### POST /contracts/check-readiness
Check if property is ready to close.

**Response:**
```json
{
  "property_id": 5,
  "ready_to_close": false,
  "required_contracts": ["Purchase Agreement", "Lead Disclosure"],
  "completed_contracts": ["Property Condition Disclosure"],
  "pending_contracts": ["Purchase Agreement", "Lead Disclosure"],
  "all_required_signed": false
}
```

### POST /contracts/ai-suggest
Get AI-recommended contracts for property.

**Response:**
```json
{
  "property_id": 5,
  "recommended_contracts": [
    {
      "template_name": "Florida Residential Purchase Agreement",
      "reason": "Required for Florida residential property",
      "required": true
    }
  ]
}
```

### POST /contracts/attach-required
Auto-attach contract templates based on property requirements.

### POST /contracts/smart-send
Multi-party contract sending with optimal order.

### GET /contracts/signing-status/{property_id}
Check who has signed what.

**Response:**
```json
{
  "property_id": 5,
  "contracts": [
    {
      "contract_id": 1,
      "template_name": "Purchase Agreement",
      "status": "pending_signature",
      "signers": [
        {"name": "John Buyer", "signed": false},
        {"name": "Jane Seller", "signed": true}
      ]
    }
  ]
}
```

### POST /contracts/{id}/mark-required
Mark contract as required or optional.

### POST /contracts/apply-ai-suggestions
Apply AI-suggested contracts to property.

---

## DocuSeal Webhooks

### POST /webhooks/docuseal
Handle DocuSeal signature events.

**Security:** HMAC-SHA256 signature verification

**Events:**
- document.completed
- document.viewed
- document.sent
- document.signed

**Side effects:**
- Updates contract status
- Auto-recap regeneration
- Pipeline automation check

---

## Property Recaps

### POST /properties/{id}/recaps/generate
Generate AI property recap.

**Trigger:** manual

**Recap includes:**
- Property overview
- Market analysis
- Contract status
- Contact information
- Property notes
- Next steps and recommendations

### GET /properties/{id}/recaps
Get latest property recap.

**Response:**
```json
{
  "property_id": 5,
  "detailed_recap": "Full 3-4 paragraph recap...",
  "voice_summary": "Property 5 is a 3-bed house in Miami priced at $750K. Enriched with Zillow data, skip trace pending.",
  "structured_context": {...}
}
```

---

## Phone Calls

### POST /phone-calls/property/{property_id}
Initiate phone call about property.

**Request Body:**
```json
{
  "call_type": "property_update",
  "recipient_phone": "+14155551234"
}
```

**Call Types:** property_update, contract_reminder, closing_ready, specific_contract, skip_trace_outreach

### POST /phone-calls/contact/{contact_id}
Call specific contact.

### POST /phone-calls/contract/{contract_id}
Call about specific contract.

### POST /phone-calls/elevenlabs
Make ElevenLabs voice call.

### GET /phone-calls/status/{call_id}
Get call status.

### POST /phone-calls/elevenlabs/setup
Configure ElevenLabs voice.

---

## Property Notes

### POST /property-notes/
Create note on property.

**Request Body:**
```json
{
  "property_id": 5,
  "content": "Property has new fence installed",
  "source": "voice",
  "agent_id": 1
}
```

**Sources:** voice, manual, ai, phone_call, system

### GET /property-notes/
List notes (optional ?property_id= filter)

### GET /property-notes/{id}
Get specific note

### PUT /property-notes/{id}
Update note

### DELETE /property-notes/{id}
Delete note

---

## Conversation History

### POST /context/history/log
Log conversation entry.

**Request Body:**
```json
{
  "agent_id": 1,
  "role": "user",
  "content": "Created property 5",
  "property_id": 5,
  "tool_name": "create_property"
}
```

### GET /context/history
Get session history (optional ?property_id= filter)

### GET /context/history/property/{property_id}
Get full property timeline

### DELETE /context/history
Clear conversation history

---

## Workflows

### GET /workflows/
List available workflow templates.

**Templates:**
- new_lead_setup
- deal_closing
- property_enrichment
- skip_trace_outreach
- ai_contract_setup

### POST /workflows/{template}/execute
Execute workflow template.

---

## Voice Campaigns

### POST /campaigns/
Create voice campaign.

**Request Body:**
```json
{
  "name": "Cold Calling Campaign",
  "call_type": "skip_trace_outreach",
  "target_property_ids": [1, 2, 3]
}
```

### GET /campaigns/
List campaigns

### GET /campaigns/{id}
Get campaign details

### POST /campaigns/{id}/start
Start campaign

### POST /campaigns/{id}/pause
Pause campaign

### POST /campaigns/{id}/targets
Add targets to campaign

### GET /campaigns/{id}/status
Get campaign status

---

## Notifications

### POST /notifications/
Create notification.

**Request Body:**
```json
{
  "agent_id": 1,
  "title": "Property needs attention",
  "message": "Property 5 has no activity in 7 days",
  "priority": "high",
  "property_id": 5
}
```

**Priorities:** urgent, high, medium, low

### GET /notifications/
List notifications

### POST /notifications/{id}/acknowledge
Mark as read

### GET /notifications/summary
Get notification summary

### GET /notifications/poll
Poll for new updates

---

## Insights

### GET /insights/
Get all alerts (optional ?priority= filter)

**6 Alert Rules:**
1. Stale properties (7+ days no activity, 14+ = high priority)
2. Contract deadlines approaching or overdue
3. Unsigned required contracts (3+ days in draft/sent)
4. Missing enrichment
5. Missing skip trace
6. High score deals (80+) with no recent activity

**Response:**
```json
{
  "urgent": [...],
  "high": [...],
  "medium": [...],
  "low": [...]
}
```

### GET /insights/property/{property_id}
Get property-specific alerts.

---

## Scheduled Tasks

### POST /scheduled-tasks/
Create scheduled task.

**Request Body:**
```json
{
  "agent_id": 1,
  "task_type": "reminder",
  "title": "Follow up on property 5",
  "due_date": "2026-03-01T10:00:00Z",
  "property_id": 5,
  "recurring": false
}
```

**Task Types:** reminder, recurring, follow_up, contract_check

### GET /scheduled-tasks/
List tasks (optional ?status= filter)

### GET /scheduled-tasks/{id}
Get task details

### DELETE /scheduled-tasks/{id}/cancel
Cancel task

### GET /scheduled-tasks/due
Get due tasks

---

## Analytics

### GET /analytics/portfolio
Full portfolio analytics.

**6 Categories:**
1. Pipeline stats (properties by status/type)
2. Portfolio value (total price, avg price, total Zestimate, equity)
3. Contract stats (by status, unsigned count)
4. Activity stats (last 24h/7d/30d actions)
5. Deal scores (avg score, grade distribution, top 5)
6. Enrichment coverage (Zillow %, skip trace %)

### GET /analytics/pipeline
Pipeline breakdown only.

### GET /analytics/contracts
Contract statistics only.

---

## Pipeline Automation

### GET /pipeline/status
Get recent auto-transitions.

**Response:**
```json
{
  "recent_transitions": [
    {
      "property_id": 5,
      "from_status": "new_property",
      "to_status": "enriched",
      "reason": "Zillow enrichment data available",
      "timestamp": "2026-02-26T10:00:00Z"
    }
  ]
}
```

### POST /pipeline/check
Manual pipeline check trigger.

---

## Daily Digest

### GET /digest/latest
Get most recent daily digest.

**Response:**
```json
{
  "generated_at": "2026-02-26T08:00:00Z",
  "full_briefing": "5 paragraph briefing...",
  "voice_summary": "Portfolio has 25 properties worth $15M. 3 urgent alerts need attention."
}
```

### POST /digest/generate
Manually generate digest.

### GET /digest/history?days=7
Get past digests.

---

## Follow-Up Queue

### GET /follow-ups/queue
Get AI-scored priority queue.

**Query Parameters:**
- `limit` - Max results (default 10)
- `priority` - Filter by priority (urgent, high, medium, low)

**Scoring Algorithm:**
- Days since last activity (base score, capped at 300)
- Deal grade multiplier (A=2x through F=0.5x)
- Contract deadline approaching (+40)
- Overdue tasks (+35)
- Unsigned required contracts (+30)
- Skip trace without outreach (+25)
- Missing contacts (+15)

**Priority Mapping:**
- 300+ = urgent
- 200+ = high
- 100+ = medium
- Below = low

### POST /follow-ups/{property_id}/complete
Mark follow-up complete.

### POST /follow-ups/{property_id}/snooze
Snooze property for N hours (default 72).

---

## Comparable Sales

### GET /comps/{property_id}
Full comps dashboard.

**3 Data Sources:**
1. Agentic research (CompSale records)
2. Zillow price_history
3. Internal portfolio (same city/state)

**Includes:**
- Market metrics (avg/median prices, price per sqft)
- 6-month trend analysis
- Subject vs market comparison
- Pricing recommendation

### GET /comps/{property_id}/sales
Sales comps only.

### GET /comps/{property_id}/rentals
Rental comps only.

---

## Bulk Operations

### POST /bulk/execute
Execute bulk operation.

**Request Body:**
```json
{
  "operation": "enrich",
  "property_ids": [1, 2, 3],
  "filters": {
    "city": "Miami",
    "status": "new_property"
  },
  "force": false
}
```

**6 Operations:**
- enrich - Zillow enrichment (skip if already enriched unless force=true)
- skip_trace - Owner discovery (skip if already traced unless force=true)
- attach_contracts - Auto-attach templates (always run)
- generate_recaps - AI recaps (always run)
- update_status - Change status (skip if already target status)
- check_compliance - Regulatory check (always run)

**Max properties:** 50

**Selection:** Union of property_ids AND filters

**Response:**
```json
{
  "operation": "enrich",
  "total_properties": 10,
  "succeeded": 8,
  "failed": 2,
  "errors": [...]
}
```

### GET /bulk/operations
List available operations.

---

## Activity Timeline

### GET /activity-timeline/
Full unified timeline.

**Query Parameters:**
- `event_type` - Filter by type
- `start_date` - Start date
- `end_date` - End date
- `search_text` - Text search
- `offset` - Pagination offset
- `limit` - Max results

**7 Data Sources:**
1. ConversationHistory
2. Notification
3. PropertyNote
4. ScheduledTask
5. Contract
6. ZillowEnrichment
7. SkipTrace

### GET /activity-timeline/property/{property_id}
Property-specific timeline.

### GET /activity-timeline/recent?hours=24
Last N hours of activity.

---

## Property Scoring

### POST /scoring/property/{property_id}
Score property (recalculates).

**4 Dimensions:**
1. Market (30%) - Zestimate spread, days on market, price trend, schools, tax gap
2. Financial (25%) - Zestimate upside, rental yield, price per sqft
3. Readiness (25%) - Contract completion %, contacts, skip trace reachability
4. Engagement (20%) - Recent activity (7d), notes, tasks, notifications

**Grade Scale:** A (80+), B (60+), C (40+), D (20+), F (<20)

### POST /scoring/bulk
Bulk score multiple properties.

### GET /scoring/property/{property_id}
Get stored score breakdown.

### GET /scoring/top?limit=10&min_score=0
Get top-scored properties.

---

## Market Watchlists

### POST /watchlists/
Create watchlist.

**Request Body:**
```json
{
  "agent_id": 1,
  "name": "Miami Condos Under 500k",
  "criteria": {
    "city": "Miami",
    "property_type": "condo",
    "max_price": 500000,
    "min_bedrooms": 2
  },
  "is_active": true
}
```

**Criteria (AND logic):**
- city - Case-insensitive partial match
- state - Exact match
- property_type - Exact match
- min_price / max_price - Price range
- min_bedrooms / min_bathrooms - Minimum rooms
- min_sqft - Minimum square footage

### GET /watchlists/
List watchlists (optional ?agent_id= & ?is_active=)

### GET /watchlists/{id}
Get watchlist details

### PUT /watchlists/{id}
Update watchlist

### DELETE /watchlists/{id}
Delete watchlist

### POST /watchlists/{id}/toggle
Pause/resume watchlist

### POST /watchlists/check/{property_id}
Check if property matches any watchlists.

---

## Web Scraper

### POST /scrape/url
Scrape URL and preview data.

**Request Body:**
```json
{
  "url": "https://www.zillow.com/homedetails/..."
}
```

### POST /scrape/multiple
Scrape multiple URLs concurrently.

### POST /scrape/scrape-and-create
Scrape and auto-create property.

### POST /scrape/zillow-listing
Scrape Zillow URL (convenience).

### POST /scrape/redfin-listing
Scrape Redfin URL (convenience).

### POST /scrape/realtor-listing
Scrape Realtor.com URL (convenience).

### POST /scrape/zillow-search
Scrape Zillow search results page.

### POST /scrape/scrape-and-enrich-batch
Bulk import with auto-enrichment.

**Request Body:**
```json
{
  "urls": ["url1", "url2", ...],
  "auto_enrich": true
}
```

---

## Deal Calculator & Offers

### POST /deals/calculate
Calculate deal metrics.

**Returns:** ROI, cash flow, cap rate, cash on cash return

### POST /deals/mao
Calculate maximum allowable offer.

### POST /deals/what-if
Scenario modeling.

### POST /deals/compare-strategies
Compare investment strategies.

### POST /deals/preview-type
Preview deal type configuration.

### POST /deals/set-type
Set property deal type.

### GET /deals/status/{property_id}
Get deal status.

### POST /deals/types/create
Create deal type config.

### PUT /deals/types/{id}
Update deal type config.

### DELETE /deals/types/{id}
Delete deal type config.

### GET /deals/types
List deal types.

### POST /offers/create
Create offer.

**Request Body:**
```json
{
  "property_id": 5,
  "offer_amount": 700000,
  "buyer_name": "John Smith",
  "offer_type": "standard"
}
```

### GET /offers/
List all offers.

### GET /offers/{id}
Get offer details.

### POST /offers/{id}/accept
Accept offer.

### POST /offers/{id}/reject
Reject offer.

### POST /offers/{id}/counter
Counter offer.

### POST /offers/{id}/withdraw
Withdraw offer.

### POST /offers/{id}/draft-letter
Draft offer letter.

---

## Research

### POST /research/property/{property_id}
Start deep property research.

**Returns:** Research ID for status checking

### GET /research/status/{property_id}
Get research status.

### GET /research/dossier/{property_id}
Get completed research dossier.

### POST /research/search
Search past research.

---

## Compliance

### POST /compliance/check
Run compliance check.

**Checks:** Federal (RESPA, TILA, Fair Housing), state, local regulations

### GET /compliance/requirements
Get requirements for state/type.

---

## Intelligence Layer

### Predictive Intelligence (6 endpoints)

#### POST /intelligence/predict/{property_id}
Predict closing probability (0-100%) with confidence.

**Returns:** Probability, confidence interval, risk factors, strengths, time-to-close estimate

#### GET /intelligence/prediction/{property_id}
Get stored prediction.

#### POST /intelligence/predict/batch
Batch predict multiple properties.

#### POST /intelligence/outcome/record
Record actual deal outcome (for learning).

**Request Body:**
```json
{
  "property_id": 5,
  "outcome": "closed",
  "final_price": 720000,
  "days_to_close": 45
}
```

#### GET /intelligence/patterns/{agent_id}
Get agent's success patterns.

**Returns:** Top property types, cities, price ranges, win rates

#### GET /intelligence/accuracy/{agent_id}
Get prediction accuracy metrics.

**Returns:** MAE, directional accuracy, calibration

### Market Opportunities (3 endpoints)

#### POST /intelligence/opportunities/scan
Scan for deals matching agent's success patterns.

#### POST /intelligence/market/detect-shifts
Detect market shifts (>10% price changes).

#### POST /intelligence/similar/{property_id}
Find similar properties.

### Relationship Intelligence (3 endpoints)

#### POST /intelligence/relationships/score
Score relationship health (0-100) with trend.

#### POST /intelligence/relationships/best-method
Predict best contact method (phone/email/text).

#### POST /intelligence/relationships/sentiment
Analyze sentiment trend over time.

### Negotiation Agent (3 endpoints)

#### POST /intelligence/negotiation/analyze-offer
Analyze offer against deal metrics.

#### POST /intelligence/negotiation/counter
Generate AI counter-offer letter.

#### POST /intelligence/negotiation/suggest-price
Suggest optimal offer price (conservative/moderate/aggressive).

### Document Analysis (3 endpoints)

#### POST /intelligence/documents/inspection
Extract issues from inspection report.

#### POST /intelligence/documents/extract-terms
Extract contract terms.

#### POST /intelligence/documents/compare-appraisals
Compare appraisals and flag discrepancies.

### Competitive Intelligence (3 endpoints)

#### POST /intelligence/competition/analyze
Analyze competing agents in market.

#### POST /intelligence/competition/detect-activity
Detect competitive activity on property.

#### POST /intelligence/competition/saturation
Get market saturation assessment.

### Deal Sequencer (3 endpoints)

#### POST /intelligence/sequence/1031
Set up 1031 exchange with deadline management.

#### POST /intelligence/sequence/portfolio
Sequence portfolio acquisition.

#### POST /intelligence/sequence/sell-buy
Manage sale-and-buy with contingencies.

---

## Marketing Hub

### Agent Branding (12 endpoints)

#### POST /agent-brand/{id}
Create brand identity.

**Request Body:**
```json
{
  "company_name": "Emprezario Inc",
  "tagline": "Your Dream Home Awaits",
  "primary_color": "#B45309",
  "secondary_color": "#D97706",
  "accent_color": "#F59E0B",
  "background_color": "#FFFBEB",
  "text_color": "#78350F",
  "logo_url": "https://example.com/logo.png",
  "website_url": "https://emprezario.com",
  "bio": "Luxury real estate specialist",
  "social_links": {
    "facebook": "https://facebook.com/emprezario",
    "instagram": "https://instagram.com/emprezario"
  }
}
```

#### GET /agent-brand/{id}
Get brand details.

#### PUT /agent-brand/{id}
Update brand.

#### DELETE /agent-brand/{id}
Delete brand.

#### GET /agent-brand/colors/presets
Get 6 pre-defined color presets.

#### POST /agent-brand/{id}/apply-preset
Apply color preset.

#### POST /agent-brand/{id}/generate-preview
Generate brand preview.

#### GET /agent-brand/{id}/preview
Get brand preview.

#### POST /agent-brand/{id}/validate
Validate brand data.

#### GET /agent-brand/{id}/guidelines
Get brand guidelines.

#### POST /agent-brand/{id}/export
Export brand kit.

### Facebook Ads (13 endpoints)

#### POST /facebook-ads/campaigns/generate
Generate campaign from property URL.

**Request Body:**
```json
{
  "url": "https://emprezario.com/properties/123",
  "campaign_objective": "leads",
  "daily_budget": 100
}
```

#### POST /facebook-ads/campaigns/{id}/launch
Launch to Meta Ads Manager.

#### POST /facebook-ads/campaigns/{id}/track
Track campaign performance.

#### GET /facebook-ads/campaigns
List campaigns.

#### GET /facebook-ads/campaigns/{id}
Get campaign details.

#### PUT /facebook-ads/campaigns/{id}
Update campaign.

#### POST /facebook-ads/research/generate
Generate market research.

#### POST /facebook-ads/competitors/analyze
Analyze competitor ads.

#### POST /facebook-ads/reviews/extract
Extract insights from Google/Yelp reviews.

#### POST /facebook-ads/audiences/recommend
Get audience recommendations.

#### POST /facebook-ads/audiences/{id}/create
Create custom audience.

#### GET /facebook-ads/analytics/campaign/{id}
Campaign analytics.

#### GET /facebook-ads/analytics/account
Account-level analytics.

### Postiz Social Media (14 endpoints)

#### POST /social/accounts/connect
Connect social media account.

#### GET /social/accounts
List connected accounts.

#### POST /social/posts/create
Create social media post.

**Request Body:**
```json
{
  "content_type": "property_promo",
  "caption": "🏠 Stunning luxury condo!",
  "hashtags": ["#luxuryliving", "#nyc", "#realestate"],
  "platforms": ["facebook", "instagram", "linkedin"],
  "use_branding": true,
  "scheduled_at": "2026-02-27T10:00:00Z"
}
```

#### POST /social/posts/{id}/schedule
Schedule post.

#### GET /social/posts
List posts.

#### GET /social/posts/{id}
Get post details.

#### PUT /social/posts/{id}
Update post.

#### POST /social/ai/generate
Generate AI content.

#### POST /social/campaigns/create
Create multi-post campaign.

#### GET /social/campaigns
List campaigns.

#### POST /social/templates/create
Create reusable template.

#### GET /social/templates
List templates.

#### GET /social/analytics/overview
Get analytics.

#### GET /social/calendar
Get content calendar.

---

## Property Videos

### POST /property-videos/generate
Generate property showcase video.

**Request Body:**
```json
{
  "property_id": 5,
  "voice_id": "elevenlabs_voice_id",
  "use_logo_intro": true,
  "show_property_details": true
}
```

**Video structure:**
- Logo intro (3 seconds)
- Photo slideshow (4 seconds per photo)
- Property details overlay
- AI voiceover narration

### GET /property-videos/voices
List available ElevenLabs voices.

### POST /property-videos/script-preview
Preview video script before generating.

### POST /property-videos/voiceover
Generate standalone audio (for podcasts).

---

**Total: 200+ endpoints across 40+ feature categories**
