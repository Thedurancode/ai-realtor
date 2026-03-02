# 🚀 AI Realtor API - Complete Feature Overview

## API Statistics

- **Total Endpoints:** 364 API routes
- **Categories:** 25+ major feature groups
- **Documentation:** http://localhost:8000/docs
- **OpenAPI Spec:** http://localhost:8000/openapi.json

---

## 📋 Complete Feature List

### 1. 🏠 Properties (12 endpoints)
**Property Management Core**

| Endpoint | Description |
|----------|-------------|
| `GET /properties/` | List all properties (with filters) |
| `POST /properties/` | Create new property |
| `POST /properties/voice` | Create property via voice |
| `GET /properties/{id}` | Get property details |
| `PUT /properties/{id}` | Update property |
| `DELETE /properties/{id}` | Delete property |
| `GET /properties/{id}/heartbeat` | Get property status/health |
| `GET /properties/{id}/deal-status` | Get deal status |
| `POST /properties/{id}/set-deal-type` | Set deal type |

**Features:**
- Full CRUD operations
- Filtering (status, city, price, bedrooms, type)
- Property heartbeat (health monitoring)
- Deal type management
- Voice-native property creation

---

### 2. 📄 Contracts (30+ endpoints)
**Contract Management System**

| Endpoint | Description |
|----------|-------------|
| `GET /contracts/` | List all contracts |
| `POST /contracts/` | Create contract |
| `GET /contracts/{id}` | Get contract details |
| `PUT /contracts/{id}` | Update contract |
| `DELETE /contracts/{id}` | Delete contract |
| `GET /contracts/property/{id}` | Get property contracts |
| `POST /contracts/{id}/send` | Send for signature |
| `POST /contracts/{id}/send-multi-party` | Multi-party send |
| `POST /contracts/voice/send` | Send via voice command |
| `POST /contracts/voice/smart-send` | Smart send with AI |
| `GET /contracts/{id}/status` | Check signing status |
| `POST /contracts/{id}/cancel` | Cancel contract |
| `POST /contracts/property/{id}/auto-attach` | Auto-attach templates |
| `GET /contracts/property/{id}/required-status` | Check required contracts |
| `GET /contracts/property/{id}/signing-status` | Signing progress |
| `GET /contracts/property/{id}/missing-contracts` | Identify gaps |
| `POST /contracts/property/{id}/ai-suggest` | AI contract suggestions |
| `POST /contracts/property/{id}/ai-apply-suggestions` | Apply AI suggestions |
| `POST /contracts/property/{id}/ai-analyze-gaps` | AI gap analysis |
| `POST /contracts/property/{id}/set-required-contracts` | Mark required |
| `POST /contracts/contracts/{id}/mark-required` | Mark single required |
| `POST /contracts/voice/check-contracts` | Voice contract check |
| `POST /contracts/webhook/docuseal` | DocuSeal webhook |
| `GET /contract-templates/` | List templates |
| `POST /contract-templates/` | Create template |
| `POST /contract-templates/{id}/activate` | Activate template |
| `POST /contract-templates/{id}/deactivate` | Deactivate template |

**Features:**
- Contract template system
- AI-powered contract suggestions
- Auto-attach based on property criteria
- DocuSeal integration (e-signatures)
- Multi-party signing workflows
- Contract readiness checking
- Required contract tracking
- Voice-native commands

---

### 3. 👥 Contacts (8 endpoints)
**Contact Management**

| Endpoint | Description |
|----------|-------------|
| `GET /contacts/` | List all contacts |
| `POST /contacts/` | Create contact |
| `POST /contacts/voice` | Create via voice |
| `GET /contacts/property/{id}` | Get property contacts |
| `POST /contacts/property/{id}/role/{role}` | Create by role |
| `POST /contacts/voice/search` | Search via voice |
| `GET /contacts/{id}` | Get contact details |
| `PUT /contacts/{id}` | Update contact |
| `DELETE /contacts/{id}` | Delete contact |
| `POST /contacts/{id}/send-pending-contracts` | Send pending contracts |

**Features:**
- Role-based organization (buyer, seller, lender, etc.)
- Property-linked contacts
- Auto-send contracts to contacts
- Voice search and creation

---

### 4. 🔍 Skip Tracing (4 endpoints)
**Owner Discovery**

| Endpoint | Description |
|----------|-------------|
| `POST /skip-trace/property/{id}` | Skip trace property |
| `POST /skip-trace/property/{id}/refresh` | Refresh data |
| `POST /skip-trace/voice` | Skip trace via voice |

**Features:**
- Find property owner
- Discover phone numbers
- Find email addresses
- Mailing address discovery

---

### 5. 📊 Zillow Enrichment (Built-in)
**Property Data Enrichment**

| Endpoint | Description |
|----------|-------------|
| `POST /properties/{id}/enrich` | Enrich with Zillow data |

**Features:**
- High-resolution photos (up to 10)
- Zestimate (market value)
- Rent Zestimate
- Tax assessment history
- Price history
- School data with ratings
- Property features and specs
- Market statistics

---

### 6. 📝 Property Notes (4 endpoints)
**Knowledge Base**

| Endpoint | Description |
|----------|-------------|
| `GET /property-notes/` | List all notes |
| `POST /property-notes/` | Create note |
| `GET /property-notes/property/{id}` | Get property notes |
| `PUT /property-notes/{id}` | Update note |
| `DELETE /property-notes/{id}` | Delete note |

**Features:**
- Multiple sources (voice, manual, AI, phone_call, system)
- Knowledge base for properties
- Auto-recap regeneration on new notes

---

### 7. 💰 Offers (13 endpoints)
**Offer Management**

| Endpoint | Description |
|----------|-------------|
| `GET /offers/` | List all offers |
| `POST /offers/` | Create offer |
| `GET /offers/property/{id}` | Get property offers |
| `POST /offers/{id}/accept` | Accept offer |
| `POST /offers/{id}/reject` | Reject offer |
| `POST /offers/{id}/counter` | Counter offer |
| `POST /offers/{id}/withdraw` | Withdraw offer |
| `POST /offers/property/{id}/mao` | Calculate MAO |
| `POST /offers/property/{id}/draft-letter` | Generate offer letter |
| `GET /offers/{id}/chain` | View offer chain |

**Features:**
- Offer chain tracking (counter-offers)
- MAO (Maximum Allowable Offer) calculation
- Offer letter generation
- Multiple offer comparison
- Offer status management

---

### 8. 🧠 Property Recaps (6 endpoints)
**AI-Generated Summaries**

| Endpoint | Description |
|----------|-------------|
| `GET /property-recap/property/{id}` | Get property recap |
| `POST /property-recap/property/{id}/generate` | Generate recap |
| `POST /property-recap/property/{id}/call` | Start recap call |
| `POST /property-recap/property/{id}/send-report` | Send recap report |
| `GET /property-recap/call/{id}/status` | Call status |

**Features:**
- 3-4 paragraph detailed recap
- 2-3 sentence voice summary
- Structured JSON context
- Auto-regeneration on events
- Phone call integration

---

### 9. 📈 Analytics (3 endpoints)
**Portfolio Analytics**

| Endpoint | Description |
|----------|-------------|
| `GET /analytics/portfolio` | Portfolio dashboard |
| `GET /analytics/pipeline` | Pipeline breakdown |
| `GET /analytics/contracts` | Contract stats |

**Features:**
- Pipeline statistics
- Portfolio value tracking
- Deal score distribution
- Contract completion rates
- Activity metrics

---

### 10. ⚡ Insights (2 endpoints)
**Proactive Monitoring**

| Endpoint | Description |
|----------|-------------|
| `GET /insights/` | All alerts |
| `GET /insights/property/{id}` | Property alerts |

**Alerts:**
- Stale properties
- Contract deadlines
- Unsigned contracts
- Missing enrichment
- Missing skip trace
- High score, no action

---

### 11. 📅 Scheduled Tasks (5 endpoints)
**Reminders & Follow-ups**

| Endpoint | Description |
|----------|-------------|
| `GET /scheduled-tasks/` | List tasks |
| `POST /scheduled-tasks/` | Create task |
| `GET /scheduled-tasks/due` | Due tasks |
| `DELETE /scheduled-tasks/{id}` | Cancel task |

**Features:**
- Reminders
- Follow-ups
- Recurring tasks
- Property-linked tasks
- Background task runner

---

### 12. 🔄 Pipeline Automation (2 endpoints)
**Auto-Advance Properties**

| Endpoint | Description |
|----------|-------------|
| `GET /pipeline/status` | Pipeline status |
| `POST /pipeline/check` | Manual check |

**Features:**
- Auto-advance property status
- 5-stage pipeline tracking
- Per-stage stale detection
- 24-hour manual grace period

---

### 13. 📋 Daily Digest (3 endpoints)
**AI Morning Briefing**

| Endpoint | Description |
|----------|-------------|
| `GET /digest/latest` | Latest digest |
| `POST /digest/generate` | Generate digest |
| `GET /digest/history` | Past digests |

**Features:**
- AI-generated daily summary
- Portfolio snapshot
- Urgent alerts
- Activity summary
- Top recommendations

---

### 14. 🎯 Follow-Up Queue (3 endpoints)
**AI-Prioritized Queue**

| Endpoint | Description |
|----------|-------------|
| `GET /follow-ups/queue` | Get ranked queue |
| `POST /follow-ups/{id}/complete` | Mark complete |
| `POST /follow-ups/{id}/snooze` | Snooze property |

**Features:**
- AI scoring algorithm
- Priority-based queue
- Snooze functionality
- Best contact finder

---

### 15. 🏘️ Comparable Sales (3 endpoints)
**Comps Dashboard**

| Endpoint | Description |
|----------|-------------|
| `GET /comps/{id}` | Full comps dashboard |
| `GET /comps/{id}/sales` | Sales comps only |
| `GET /comps/{id}/rentals` | Rental comps only |

**Features:**
- 3-source aggregation (research, Zillow, portfolio)
- Market metrics
- Price recommendations
- Similarity scoring

---

### 16. 📦 Bulk Operations (2 endpoints)
**Multi-Property Actions**

| Endpoint | Description |
|----------|-------------|
| `GET /bulk/operations` | List operations |
| `POST /bulk/execute` | Execute operation |

**Operations:**
- `enrich` - Zillow enrichment
- `skip_trace` - Owner discovery
- `attach_contracts` - Auto-attach templates
- `generate_recaps` - AI recaps
- `update_status` - Change status
- `check_compliance` - Compliance check

**Features:**
- Batch processing (up to 50 properties)
- Dynamic filters
- Error isolation
- Progress tracking

---

### 17. 📊 Activity Timeline (3 endpoints)
**Unified Event Feed**

| Endpoint | Description |
|----------|-------------|
| `GET /activity-timeline/` | Full timeline |
| `GET /activity-timeline/property/{id}` | Property timeline |
| `GET /activity-timeline/recent` | Recent activity |

**Data Sources:**
- Conversation history
- Notifications
- Property notes
- Scheduled tasks
- Contracts
- Zillow enrichments
- Skip traces

---

### 18. 🎯 Property Scoring (4 endpoints)
**Deal Quality Scoring**

| Endpoint | Description |
|----------|-------------|
| `POST /scoring/property/{id}` | Score property |
| `GET /scoring/top` | Top properties |
| `POST /scoring/bulk` | Bulk score |

**Features:**
- 4-dimension scoring (Market, Financial, Readiness, Engagement)
- A-F grade scale
- 15+ individual metrics
- Weighted scoring algorithm

---

### 19. 🔍 Market Watchlists (6 endpoints)
**Saved Search Alerts**

| Endpoint | Description |
|----------|-------------|
| `GET /watchlists/` | List watchlists |
| `POST /watchlists/` | Create watchlist |
| `GET /watchlists/{id}` | Get watchlist |
| `PUT /watchlists/{id}` | Update watchlist |
| `DELETE /watchlists/{id}` | Delete watchlist |
| `POST /watchlists/{id}/toggle` | Pause/resume |
| `POST /watchlists/check/{id}` | Check property |

**Features:**
- Flexible criteria (city, state, type, price, beds, baths, sqft)
- Auto-check on property creation
- HIGH priority alerts
- Easy pause/resume

---

### 20. 🌐 Web Scraper (8 endpoints)
**Property Data Extraction**

| Endpoint | Description |
|----------|-------------|
| `POST /scrape/url` | Scrape URL |
| `POST /scrape/scrape-and-create` | Scrape & create |
| `POST /scrape/zillow-listing` | Scrape Zillow |
| `POST /scrape/redfin-listing` | Scrape Redfin |
| `POST /scrape/realtor-listing` | Scrape Realtor.com |
| `POST /scrape/zillow-search` | Scrape Zillow search |
| `POST /scrape/multiple` | Scrape multiple |
| `POST /scrape/scrape-and-enrich-batch` | Batch import |

**Features:**
- Specialized scrapers (Zillow, Redfin, Realtor.com)
- Generic AI-powered scraper
- Concurrent processing
- Duplicate detection
- Auto-enrichment option

---

### 21. 🧪 Compliance Engine (10+ endpoints)
**Regulatory Compliance Checking**

| Endpoint | Description |
|----------|-------------|
| `POST /compliance/properties/{id}/check` | Run compliance check |
| `GET /compliance/properties/{id}/quick-check` | Quick check |
| `GET /compliance/properties/{id}/latest-check` | Latest check |
| `GET /compliance/checks/{id}` | Get check details |
| `GET /compliance/checks/{id}/violations` | Get violations |
| `GET /compliance/knowledge/rules` | List rules |
| `POST /compliance/knowledge/rules/ai-generate` | AI generate rule |
| `POST /compliance/knowledge/rules/import-csv` | Import rules |
| `POST /compliance/knowledge/voice/add-rule` | Voice add rule |
| `GET /compliance/knowledge/states` | Supported states |
| `GET /compliance/knowledge/categories` | Rule categories |
| `POST /compliance/violations/{id}/resolve` | Resolve violation |

**Features:**
- Federal, state, local regulations
- RESPA, TILA, Fair Housing
- Rule violation tracking
- AI-powered rule generation
- Custom rule management

---

### 22. 🤖 AI Intelligence (23+ endpoints)
**Predictive & Adaptive Intelligence**

#### Predictive Intelligence
| Endpoint | Description |
|----------|-------------|
| `POST /predictive/property/{id}/predict` | Predict outcome |
| `GET /predictive/property/{id}/recommend` | Recommend action |
| `POST /predictive/batch/predict` | Batch predict |
| `POST /predictive/outcomes/{id}/record` | Record outcome |
| `GET /predictive/agents/{id}/patterns` | Success patterns |
| `GET /predictive/accuracy` | Prediction accuracy |

#### Market Intelligence
| Endpoint | Description |
|----------|-------------|
| `POST /opportunities/scan` | Scan for deals |
| `POST /opportunities/market-shifts` | Detect market shifts |
| `POST /opportunities/property/{id}/similar` | Find similar properties |

#### Relationship Intelligence
| Endpoint | Description |
|----------|-------------|
| `GET /relationships/contact/{id}/health` | Relationship health |
| `POST /relationships/contact/{id}/best-method` | Best contact method |
| `GET /relationships/contact/{id}/sentiment` | Sentiment analysis |

#### Negotiation Agent
| Endpoint | Description |
|----------|-------------|
| `POST /intelligence/negotiation/property/{id}/analyze-offer` | Analyze offer |
| `POST /intelligence/negotiation/property/{id}/counter-offer` | Generate counter |
| `POST /intelligence/negotiation/property/{id}/suggest-price` | Suggest price |

#### Document Analysis
| Endpoint | Description |
|----------|-------------|
| `POST /intelligence/documents/inspection` | Analyze inspection |
| `POST /intelligence/documents/appraisals/compare` | Compare appraisals |
| `POST /intelligence/documents/contract/extract` | Extract terms |

#### Competitive Intelligence
| Endpoint | Description |
|----------|-------------|
| `POST /intelligence/competition/market/{city}/{state}` | Analyze market |
| `GET /intelligence/competition/market/{city}/{state}/saturation` | Market saturation |
| `POST /intelligence/competition/property/{id}/activity` | Competitive activity |

#### Deal Sequencing
| Endpoint | Description |
|----------|-------------|
| `POST /intelligence/sequencing/1031-exchange` | 1031 exchange |
| `POST /intelligence/sequencing/portfolio-acquisition` | Portfolio acquisition |
| `POST /intelligence/sequencing/sell-and-buy` | Sell and buy |

---

### 23. 📞 Phone & Voice (15+ endpoints)
**VAPI & ElevenLabs Integration**

#### VAPI Phone Calls
| Endpoint | Description |
|----------|-------------|
| `POST /vapi/calls` | Make phone call |
| `POST /vapi/calls/property/{id}/update` | Property update call |
| `POST /vapi/calls/contract/{id}/reminder` | Contract reminder |

#### ElevenLabs
| Endpoint | Description |
|----------|-------------|
| `POST /elevenlabs/call` | Make ElevenLabs call |
| `POST /elevenlabs/setup` | Setup ElevenLabs |
| `GET /elevenlabs/phone-numbers` | List phone numbers |
| `POST /elevenlabs/import-twilio-number` | Import Twilio number |
| `POST /elevenlabs/assign-phone/{id}` | Assign phone |
| `GET /elevenlabs/agent` | Get agent info |
| `POST /elevenlabs/agent/prompt` | Set agent prompt |
| `GET /elevenlabs/widget` | Get widget code |

---

### 24. 📣 Marketing Hub (39 endpoints)
**Brand, Facebook Ads, Social Media**

#### Agent Branding (12 endpoints)
| Endpoint | Description |
|----------|-------------|
| `GET /agent-brand/{id}` | Get brand |
| `POST /agent-brand/{id}` | Create brand |
| `PUT /agent-brand/{id}` | Update brand |
| `DELETE /agent-brand/{id}` | Delete brand |
| `GET /agent-brand/colors/presets` | Color presets |
| `POST /agent-brand/{id}/apply-preset` | Apply preset |
| `POST /agent-brand/{id}/generate-preview` | Generate preview |
| `GET /agent-brand/{id}/preview` | Get preview |
| `POST /agent-brand/{id}/logo` | Upload logo |
| `GET /agent-brand/{id}/colors` | Get colors |
| `GET /agent-brand/public/{id}` | Public brand |
| `POST /agent-brand/{id}/validate` | Validate brand |

#### Facebook Ads (13 endpoints)
| Endpoint | Description |
|----------|-------------|
| `POST /facebook-ads/campaigns/generate` | Generate campaign |
| `POST /facebook-ads/campaigns/{id}/launch` | Launch to Meta |
| `POST /facebook-ads/campaigns/{id}/sync` | Sync performance |
| `POST /facebook-ads/campaigns/{id}/pause` | Pause campaign |
| `POST /facebook-ads/campaigns/{id}/resume` | Resume campaign |
| `GET /facebook-ads/campaigns` | List campaigns |
| `GET /facebook-ads/campaigns/{id}` | Get campaign |
| `POST /facebook-ads/research/generate` | Market research |
| `POST /facebook-ads/competitors/analyze` | Analyze competitors |
| `POST /facebook-ads/reviews/extract` | Review intelligence |

#### Postiz Social Media (14 endpoints)
| Endpoint | Description |
|----------|-------------|
| `POST /postiz/accounts/connect` | Connect account |
| `GET /postiz/accounts` | List accounts |
| `POST /postiz/posts/create` | Create post |
| `POST /postiz/posts/{id}/schedule` | Schedule post |
| `GET /postiz/posts` | List posts |
| `POST /postiz/campaigns/create` | Create campaign |
| `GET /postiz/analytics/overview` | Get analytics |
| `GET /postiz/calendar` | Content calendar |

---

### 25. 🔔 Notifications (6 endpoints)
**Alert System**

| Endpoint | Description |
|----------|-------------|
| `GET /notifications/` | List notifications |
| `POST /notifications/` | Create notification |
| `GET /notifications/{id}` | Get notification |
| `POST /notifications/{id}/read` | Mark read |
| `POST /notifications/{id}/dismiss` | Dismiss |

**Demo Notifications:**
- Contract signed
- New lead
- Price change
- Appointment

---

### 26. ✅ Todos (5 endpoints)
**Task Management**

| Endpoint | Description |
|----------|-------------|
| `GET /todos/` | List todos |
| `POST /todos/` | Create todo |
| `GET /todos/property/{id}` | Property todos |
| `GET /todos/contact/{id}` | Contact todos |
| `POST /todos/voice` | Voice todo |

---

### 27. 🧪 Research (6 endpoints)
**Deep Property Research**

| Endpoint | Description |
|----------|-------------|
| `GET /research/` | List research |
| `POST /research/ai-research` | AI research |
| `POST /research/api-research` | API research |
| `POST /research/property/{id}/deep-dive` | Deep dive |
| `POST /research/property/{id}/market-analysis` | Market analysis |
| `POST /research/property/{id}/compliance` | Compliance research |

---

### 28. 🗂️ Address & Location (2 endpoints)
**Google Places Integration**

| Endpoint | Description |
|----------|-------------|
| `POST /address/autocomplete` | Address autocomplete |
| `POST /address/details` | Address details |

---

### 29. 📚 Deal Calculator (4 endpoints)
**Investment Analysis**

| Endpoint | Description |
|----------|-------------|
| `POST /deal-calculator/calculate` | Calculate deal |
| `POST /deal-calculator/compare` | Compare strategies |
| `POST /deal-calculator/property/{id}` | Property deal calc |
| `POST /deal-calculator/voice` | Voice deal calc |

---

### 30. 🎭 Skills Marketplace (10 endpoints)
**Plugin System**

| Endpoint | Description |
|----------|-------------|
| `GET /skills/marketplace` | Browse skills |
| `POST /skills/create` | Create skill |
| `POST /skills/install` | Install skill |
| `GET /skills/installed/{id}` | Installed skills |
| `POST /skills/rate/{name}` | Rate skill |
| `GET /skills/discover` | Discover skills |

---

### 31. 🔐 Authentication & Permissions
**Multi-Tenant System**

| Endpoint | Description |
|----------|-------------|
| `POST /agents/register` | Register agent |
| `GET /agents/` | List agents |
| `GET /workspaces/` | List workspaces |
| `POST /workspaces/{id}/api-keys` | Create API key |
| `GET /workspaces/scopes` | List scopes |

---

### 32. 🧰 Context & Memory (6 endpoints)
**Conversation History**

| Endpoint | Description |
|----------|-------------|
| `GET /context/history` | Get history |
| `POST /context/history/log` | Log entry |
| `GET /context/history/property/{id}` | Property history |
| `POST /context/property/create` | Create property context |
| `POST /context/skip-trace` | Skip trace context |
| `DELETE /context/clear` | Clear history |

---

### 33. 🤖 AI Agent Execution (7 endpoints)
**Autonomous Agent**

| Endpoint | Description |
|----------|-------------|
| `POST /ai-agents/execute` | Execute agent |
| `POST /ai-agents/voice-goals/execute` | Voice goal execution |
| `POST /ai-agents/property/{id}/analyze` | Analyze property |
| `GET /ai-agents/{conversation_id}` | Get conversation |

---

### 34. 📺 Observer (5 endpoints)
**Real-time Event Monitoring**

| Endpoint | Description |
|----------|-------------|
| `GET /observer/stats` | Observer stats |
| `GET /observer/history` | Event history |
| `POST /observer/enable` | Enable observer |
| `POST /observer/disable` | Disable observer |

---

### 35. 🧪 Utilities (15+ endpoints)
**System Tools**

**Database Performance:**
- `GET /sqlite/stats` - Database stats
- `POST /sqlite/optimize` - Optimize DB
- `GET /sqlite/slow-queries` - Slow queries
- `GET /sqlite/table-stats` - Table stats

**Cache:**
- `POST /cache/clear` - Clear cache
- `GET /cache/stats` - Cache stats

**Search:**
- `POST /search/properties` - Semantic search
- `POST /search/backfill` - Backfill search
- `POST /search/index/{id}` - Index property

**Scheduler:**
- `GET /scheduler/status` - Scheduler status
- `GET /scheduler/tasks` - List tasks
- `POST /scheduler/tasks/{id}/run` - Run task

**Workflows:**
- `GET /workflows/templates` - List templates
- `POST /workflows/execute` - Execute workflow

**Data Scrubbing:**
- `POST /scrub/text` - Scrub text
- `POST /scrub/json` - Scrub JSON
- `POST /scrub/test` - Test scrubbing

---

### 36. 🎭 Voice Campaigns (8 endpoints)
**Automated Calling**

| Endpoint | Description |
|----------|-------------|
| `GET /voice-campaigns/` | List campaigns |
| `POST /voice-campaigns/` | Create campaign |
| `POST /voice-campaigns/{id}/start` | Start campaign |
| `POST /voice-campaigns/{id}/pause` | Pause campaign |
| `POST /voice-campaigns/{id}/process` - Process campaign |
| `GET /voice-campaigns/{id}/targets` - Campaign targets |
| `GET /voice-campaigns/{id}/analytics` - Campaign analytics |

---

### 37. 🎨 Deal Types (3 endpoints)
**Deal Configuration**

| Endpoint | Description |
|----------|-------------|
| `GET /deal-types/` | List deal types |
| `POST /deal-types/{name}` | Create deal type |
| `GET /deal-types/{name}/preview` - Preview deal type |

---

### 38. 🔍 Semantic Search (2 endpoints)
**Vector-based Search**

| Endpoint | Description |
|----------|-------------|
| `POST /search/properties` | Search properties |
| `POST /search/research` | General search |

---

### 39. 🧪 Onboarding (5 endpoints)
**Agent Onboarding**

| Endpoint | Description |
|----------|-------------|
| `GET /onboarding/welcome` | Welcome message |
| `GET /onboarding/status/{id}` | Onboarding status |
| `GET /onboarding/questions` | Onboarding questions |
| `POST /onboarding/submit` - Submit onboarding |

---

### 40. 🔐 Approval System (8 endpoints)
**Approval Workflow**

| Endpoint | Description |
|----------|-------------|
| `POST /approval/request` - Request approval |
| `POST /approval/grant` - Grant approval |
| `POST /approval/deny` - Deny approval |
| `GET /approval/config` - Get config |
| `GET /approval/audit-log` - Audit log |

---

## 🎯 Feature Categories Summary

| Category | Endpoints | Description |
|----------|-----------|-------------|
| **Properties** | 12 | Core property management |
| **Contracts** | 30+ | Contract lifecycle |
| **Contacts** | 8 | Stakeholder management |
| **Skip Tracing** | 4 | Owner discovery |
| **Notes** | 4 | Knowledge base |
| **Offers** | 13 | Offer management |
| **Analytics** | 3 | Portfolio insights |
| **Insights** | 2 | Proactive alerts |
| **Tasks** | 5 | Reminders/follow-ups |
| **Pipeline** | 2 | Automation |
| **Digest** | 3 | Daily briefing |
| **Follow-ups** | 3 | Priority queue |
| **Comps** | 3 | Market data |
| **Bulk Ops** | 2 | Batch processing |
| **Timeline** | 3 | Activity feed |
| **Scoring** | 4 | Deal quality |
| **Watchlists** | 6 | Saved searches |
| **Web Scraper** | 8 | Data extraction |
| **Compliance** | 10+ | Regulation checks |
| **Intelligence** | 23+ | AI predictions |
| **Voice/Phone** | 15+ | Call integration |
| **Marketing** | 39 | Brand + Ads + Social |
| **Notifications** | 6 | Alert system |
| **Research** | 6 | Deep research |
| **AI Agents** | 7 | Autonomous agents |
| **Utilities** | 15+ | System tools |
| **Campaigns** | 8 | Voice campaigns |
| **Search** | 2 | Semantic search |
| **Authentication** | 5+ | Multi-tenant |
| **Memory** | 6 | Conversation history |

---

## 📊 API Statistics

- **Total Endpoints:** 364
- **Major Categories:** 40+
- **HTTP Methods:** GET, POST, PUT, DELETE, PATCH
- **Response Formats:** JSON
- **Authentication:** X-API-Key header

---

## 🔑 Quick Test Commands

```bash
# Health check
curl http://localhost:8000/health

# List properties
curl http://localhost:8000/properties/

# Get API docs
curl http://localhost:8000/docs

# Get OpenAPI spec
curl http://localhost:8000/openapi.json
```

---

## 📚 Documentation

- **Interactive Docs:** http://localhost:8000/docs
- **OpenAPI Spec:** http://localhost:8000/openapi.json
- **Total Endpoints:** 364
- **Coverage:** Complete real estate lifecycle

Your AI Realtor API is a **production-grade, enterprise-level platform** with comprehensive features for every aspect of real estate management! 🚀
