# AI Realtor - Intelligent Real Estate Management Platform

A voice-first AI real estate platform that handles the entire property lifecycle through natural language. From property discovery and agentic research, to deal scoring, offer drafting, contract management, phone call automation, and PDF reporting — all controlled through Claude Desktop via MCP.

**Live API:** https://ai-realtor.fly.dev
**Docs:** https://ai-realtor.fly.dev/docs
**Additional Guides:** See [docs/](docs/) folder for comprehensive documentation

```
61 MCP Tools  ·  223 API Endpoints  ·  31 Models  ·  31 Services  ·  12 External APIs
```

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [MCP Voice Control](#mcp-voice-control--61-tools)
- [API Endpoints](#api-endpoints-223)
- [Deal Calculator](#deal-calculator--scoring)
- [Agentic Research](#agentic-property-research)
- [Phone Call Automation](#phone-call-automation)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Example Workflows](#example-workflows)
- [Deployment](#deployment)
- [Database Schema](#database-schema)

---

## Features

### Property Management
- Create, list, update, and delete properties with Google Places address autocomplete
- Property types: house, condo, townhouse, apartment, land, commercial, multi-family
- Status tracking: available, pending, sold, rented, off_market
- Auto-enrich pipeline: create property -> enrich -> research -> score -> attach contracts
- Voice-optimized creation and lookup (say the address instead of IDs)

### Zillow Data Enrichment
- High-res photos (up to 10), Zestimate, rent estimates
- Tax history, price history, nearby schools with ratings
- Property features: year built, lot size, parking, heating/cooling
- Market statistics and comparables
- Background processing with TV display animation

### Skip Tracing & Owner Discovery
- Find property owner names, phone numbers, emails, mailing addresses
- Relatives and associates
- Direct cold calling integration with VAPI
- Voice-optimized responses with formatted phone numbers

### Contact Management
- 19 contact roles: buyer, seller, lawyer, attorney, contractor, inspector, appraiser, lender, mortgage_broker, title_company, tenant, landlord, property_manager, handyman, plumber, electrician, photographer, stager, other
- Role aliases for voice input (e.g., "attorney" maps to lawyer)
- Auto-contract matching by role

### AI Contract Management
Three-tier requirement system:

| Tier | How It Works |
|---|---|
| **Auto-attach** | Template matching by state, city, price range, property type (15+ templates for NY, CA, FL, TX) |
| **AI Suggestions** | Claude analyzes property and recommends required vs optional contracts with reasoning |
| **Manual Override** | Mark any contract required/optional with deadline and reason |

- DocuSeal e-signature integration with multi-party signing
- Smart sending with role-based signer detection (e.g., buyer + seller for Purchase Agreement)
- Real-time status via DocuSeal webhooks (HMAC-SHA256 verified)
- Contract statuses: draft, sent, in_progress, pending_signature, completed, cancelled, expired, archived

### Offer & Negotiation Engine
- Create, counter, accept, reject, and withdraw offers
- Full negotiation chain tracking with parent/child offer history
- MAO calculation (Maximum Allowable Offer) for wholesale deals
- AI-drafted professional offer letters with negotiation strategy and talking points
- DocuSeal pre-fill for instant buyer signature
- Contingency tracking: inspection, financing, appraisal, sale of buyer's home
- Financing types: cash, conventional, FHA, VA, hard_money, seller_financing

### Deal Calculator & Scoring
Four investment strategies calculated with full underwriting:

| Strategy | Key Metrics |
|---|---|
| **Wholesale** | Offer price, assignment fee, profit, ROI |
| **Fix & Flip** | Purchase + rehab costs, ARV, profit, ROI, hold time |
| **Rental** | Monthly cash flow, cap rate, expense breakdown, debt service |
| **BRRRR** | Initial cash in, refi amount, cash back, infinite return flag, post-refi cash flow |

- Deal scoring (A-F grades) based on market conditions and profitability
- Data fallback chain: user override -> agentic underwriting -> Zestimate -> comp average -> list price
- Rehab cost tiers: light ($15/sqft), medium ($35/sqft), heavy ($60/sqft)
- Side-by-side strategy comparison
- What-if scenario analysis with custom assumptions

### AI Property Recaps
- Three formats: detailed (3-4 paragraphs), voice summary (2-3 sentences), structured context (JSON for VAPI)
- Auto-regenerates when contracts are signed, data is enriched, or skip trace completes
- Version tracking with trigger history
- Embedded for vector search

### PDF Property Reports
- Professional PDF reports generated in-memory with fpdf2
- Property overview report: hero photo, key stats, market analysis, schools table, contract status, contacts, deal score
- Extensible registry pattern (add new report types with one file)
- Emailed as attachment via Resend
- Voice: "Send me the property overview for 123 Main St"

### Agentic Property Research
12+ parallel AI research workers:
- **Property Profile** — parcel facts, owner, geocoding
- **Comparable Sales** — nearby sales with similarity scores
- **Comparable Rentals** — rental comp analysis
- **Underwriting** — ARV, rent estimate, rehab costs, offer price recommendation
- **Neighborhood Intel** — crime, schools, market trends
- **Extensive agents** (optional):
  - EPA environmental hazards and superfund sites
  - Wildfire hazard assessment
  - Seismic hazard and nearby faults
  - Wetlands detection
  - HUD opportunity zone indices
  - Historic places and district detection
- Investor-grade dossier generation with evidence tracking
- Exa AI web research integration

### Semantic Vector Search
- pgvector-powered natural language property search
- OpenAI embeddings (text-embedding-3-small, 1536 dimensions)
- Queries like "Modern condo in Brooklyn under $700k with parking"
- Similar property matching via cosine similarity
- Cross-search: properties, recaps, dossiers, and evidence items

### Phone Call Automation

**VAPI Integration:**
| Call Type | What It Does |
|---|---|
| `property_update` | Shares property details, answers questions |
| `contract_reminder` | Reminds about pending contracts |
| `closing_ready` | Celebrates all contracts complete |
| `specific_contract_reminder` | Calls specific person about specific contract |
| `skip_trace_outreach` | Cold calls owner to ask about selling |

- GPT-4 Turbo + 11Labs voice, full property context injected
- Recording enabled for all calls

**ElevenLabs Conversational AI:**
- Voice agent with live MCP tool access during calls
- Can look up properties, check contracts, calculate deals mid-conversation
- Claude Sonnet 4.5 as the brain + natural 11Labs voice
- Embeddable website widget
- Twilio phone number integration

### Voice Campaign Management
- Bulk outbound calling campaigns with target enrollment
- Target filtering by property, contact role, or manual selection
- Configurable rate limiting, retry logic (exponential backoff), max attempts
- Campaign lifecycle: draft -> active -> paused -> completed -> canceled
- Campaign analytics: success rate, total calls, completions, average attempts
- Background worker with automatic processing every 15 seconds

### Deal Type Workflows
Pre-configured deal types with auto-setup:
- Traditional, short_sale, REO, FSBO, new_construction, wholesale, rental, commercial
- Auto-attach required contracts per deal type
- Create checklist todos per deal type
- Set required contact roles per deal type
- Deal progress tracking with readiness status

### Compliance Engine
- AI-powered checks against federal (RESPA, TILA, Fair Housing), state, and local regulations
- Rule types: disclosure, contract, deadline, documentation, fair_housing, data_privacy
- Violation severity levels: critical, high, medium, low, info
- Claude-generated compliance summary with remediation steps
- Scheduled auto-checks after property creation

### Real-time Activity Feed & Notifications
- WebSocket-powered real-time updates
- TV display integration with animated notifications
- Activity logging for all tool executions, property updates, contract events
- Notification types: contract signed, new lead, price change, status change, compliance alerts
- Priority levels with auto-dismiss

### Todo Management
- Property-specific task tracking with priorities and deadlines
- Categories: contract signing, inspection, appraisal, closing, follow-up, research, compliance
- Agent assignment and reminder notifications

### Agent Preferences
- Per-agent settings: auto-enrich, preferred templates, notification preferences
- API key authentication (X-API-Key header)
- Work hours and communication preferences

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Desktop                           │
│                   (Voice Interface)                          │
└───────────────────────┬─────────────────────────────────────┘
                        │ MCP Protocol (stdio / SSE)
                        v
┌─────────────────────────────────────────────────────────────┐
│                  MCP Server (Python)                         │
│          61 Voice-Controlled Tools (13 modules)             │
│   properties · contacts · contracts · offers · research     │
│   recaps · calls · campaigns · search · reports · deals     │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP API (localhost:8000)
                        v
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  27 Routers · 223 Endpoints · Rate Limiting · CORS    │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  31 Services: AI Analysis, VAPI Calls, ElevenLabs,    │  │
│  │  Enrichment, Skip Trace, Compliance, Offers,          │  │
│  │  Research Pipeline, Campaigns, PDF Reports             │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  31 Models: Property, Contract, Contact, Offer,       │  │
│  │  Recap, Dossier, Evidence, Campaign, Compliance,      │  │
│  │  Agent, Enrichment, SkipTrace, DealType...            │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────┬──────────────────────────┬───────────────────────┘
           │                          │
           v                          v
┌─────────────────────┐   ┌──────────────────────────────────┐
│ PostgreSQL + pgvec  │   │       External APIs (12)          │
│                     │   │  Google Places · Zillow · Exa     │
│ 31 tables           │   │  Skip Trace · DocuSeal · VAPI    │
│ Vector embeddings   │   │  ElevenLabs · Resend · RentCast  │
│ 1536-dim OpenAI     │   │  Anthropic Claude · OpenAI · GPT │
└─────────────────────┘   └──────────────────────────────────┘
           ^
           │ WebSocket
           v
┌─────────────────────────────────────────────────────────────┐
│               Frontend (Next.js 15)                          │
│         Real-time Dashboard · TV Display · Activity Feed     │
└─────────────────────────────────────────────────────────────┘
```

---

## MCP Voice Control — 61 Tools

All features are accessible through natural language via the MCP server for Claude Desktop.

| Category | Tools | Count |
|---|---|---|
| Property | list, get, create, update, delete | 5 |
| Enrichment | enrich_property, skip_trace_property | 2 |
| Contacts | add_contact | 1 |
| Contracts | send, check status, list, signing status, readiness, attach, AI suggest, apply suggestions, mark required, smart send | 13 |
| Recaps & Calls | generate/get recap, phone call, call about contract, cold call owner | 5 |
| Offers | create, get, list, counter, accept, reject, withdraw, calculate MAO | 8 |
| Deal Calculator | calculate, compare strategies, what-if scenario | 3 |
| Research | research (sync/async), status, dossier, search | 5 |
| Search | semantic search, find similar properties | 2 |
| ElevenLabs | call, setup, status | 3 |
| Deal Types | list, get, create, update, delete, preview, set, status | 8 |
| Reports | send_property_report | 1 |
| Notifications | send, list | 2 |
| Webhooks | test configuration | 1 |

**Voice examples:**
```
"Create a property at 123 Main St, New York for $850,000 with 2 bedrooms"
"Enrich property 5 with Zillow data and generate a recap"
"Is the property at 123 Main Street ready to close?"
"Call John about the Purchase Agreement that needs his signature"
"Skip trace property 5 and call the owner to ask if they want to sell"
"What contracts are required for this property based on AI analysis?"
"Submit an offer of $600K on property 3 with inspection contingency"
"Calculate the deal for property 5"
"Compare wholesale vs flip vs rental for property 8"
"Find me properties similar to the Brooklyn condo"
"Run full agentic research on property 8"
"Send me the property overview for 123 Main St"
```

---

## API Endpoints (223)

### Properties
```
POST   /properties/                          Create property
POST   /properties/voice                     Voice-optimized creation
GET    /properties/                          List with filtering
GET    /properties/{id}                      Get details
PATCH  /properties/{id}                      Update
DELETE /properties/{id}                      Delete
POST   /properties/{id}/set-deal-type        Set deal type
GET    /properties/{id}/deal-status          Deal progress
```

### Contracts
```
GET    /contracts/                           List contracts
POST   /contracts/                           Create contract
GET    /contracts/{id}                       Get contract
PATCH  /contracts/{id}                       Update
DELETE /contracts/{id}                       Delete
POST   /contracts/{id}/send                  Send via DocuSeal
POST   /contracts/{id}/send-to-contact       Send to contact
POST   /contracts/{id}/send-multi-party      Multi-party signing
GET    /contracts/{id}/status                DocuSeal status
POST   /contracts/{id}/cancel               Cancel/archive
PATCH  /contracts/{id}/mark-required        Mark required/optional
POST   /contracts/voice/send                Voice send
POST   /contracts/voice/smart-send          Auto-determine signers
POST   /contracts/property/{id}/auto-attach  Auto-attach templates
POST   /contracts/property/{id}/ai-suggest   AI suggestions
POST   /contracts/property/{id}/ai-apply-suggestions  Apply suggestions
GET    /contracts/property/{id}/required-status       Readiness check
GET    /contracts/property/{id}/signing-status         Who signed
GET    /contracts/property/{id}/missing-contracts      What's missing
```

### Offers
```
POST   /offers/                              Create offer
GET    /offers/                              List offers
GET    /offers/{id}                          Get offer
POST   /offers/{id}/counter                  Counter offer
POST   /offers/{id}/accept                   Accept
POST   /offers/{id}/reject                   Reject
POST   /offers/{id}/withdraw                 Withdraw
GET    /offers/{id}/chain                    Negotiation chain
GET    /offers/property/{id}/summary         Property offer summary
POST   /offers/property/{id}/mao             Calculate MAO
POST   /offers/{id}/draft-letter             Draft AI offer letter
POST   /offers/property/{id}/draft-letter    Standalone offer letter
```

### Deal Calculator
```
POST   /deal-calculator/calculate            Full calculation with overrides
GET    /deal-calculator/property/{id}        Quick calculate with defaults
POST   /deal-calculator/compare              Compare strategies side-by-side
POST   /deal-calculator/voice                Voice-optimized calculation
```

### Property Recaps & Reports
```
POST   /property-recap/property/{id}/generate        Generate AI recap
GET    /property-recap/property/{id}                 Get current recap
POST   /property-recap/property/{id}/send-report     Generate and email PDF report
POST   /property-recap/property/{id}/call            VAPI phone call
GET    /property-recap/call/{id}/status              Call status
POST   /property-recap/call/{id}/end                 End call
GET    /property-recap/call/{id}/recording           Get recording
```

### Agentic Research
```
POST   /agentic-research/property/{id}/run           Run full pipeline
GET    /agentic-research/property/{id}/status         Get status
POST   /agentic-research/property/{id}/rerun-worker   Rerun specific worker
GET    /agentic-research/property/{id}/dossier         Get dossier markdown
POST   /agentic-research/voice/run                     Voice research
POST   /exa-research/property/{id}                     Exa web research
GET    /exa-research/property/{id}/results             Exa results
```

### Semantic Search
```
POST   /search/properties                    Natural language property search
POST   /search/research                      Search dossiers and evidence
GET    /search/similar/{id}                  Find similar properties
POST   /search/backfill                      Backfill embeddings
```

### Phone Calls & Campaigns
```
POST   /elevenlabs/setup                              One-time agent setup
POST   /elevenlabs/call                                ElevenLabs outbound call
GET    /elevenlabs/agent                               Agent status
PATCH  /elevenlabs/agent/prompt                        Update agent prompt
GET    /elevenlabs/widget                              Embed widget HTML
POST   /voice-campaigns/                               Create campaign
GET    /voice-campaigns/                               List campaigns
GET    /voice-campaigns/{id}                           Get campaign
PATCH  /voice-campaigns/{id}                           Update campaign
DELETE /voice-campaigns/{id}                           Cancel campaign
POST   /voice-campaigns/{id}/targets                   Add targets manually
POST   /voice-campaigns/{id}/targets/from-filters      Add from property filters
GET    /voice-campaigns/{id}/targets                   List targets
POST   /voice-campaigns/{id}/start                     Start campaign
POST   /voice-campaigns/{id}/pause                     Pause campaign
POST   /voice-campaigns/{id}/resume                    Resume campaign
POST   /voice-campaigns/{id}/process                   Process one campaign
POST   /voice-campaigns/process                        Process all active
GET    /voice-campaigns/{id}/analytics                 Campaign analytics
```

### Compliance
```
POST   /compliance/properties/{id}/check               Full compliance check
POST   /compliance/properties/{id}/quick-check          Quick check
GET    /compliance/properties/{id}/report               Compliance report
POST   /compliance/voice/check                          Voice compliance check
GET    /compliance/voice/status                          Voice status
```

### Contacts, Notifications, Todos, Webhooks
```
POST   /contacts/                            Create contact
POST   /contacts/voice                       Voice creation
GET    /contacts/property/{id}               Property contacts
PUT    /contacts/{id}                        Update contact
DELETE /contacts/{id}                        Delete contact
POST   /notifications/                       Create notification
GET    /notifications/                       List notifications
WS     /ws                                   WebSocket real-time feed
POST   /display/command                      TV display command
POST   /webhooks/docuseal                    DocuSeal signing webhook
GET    /webhooks/docuseal/test               Test webhook config
GET    /todos/                               List todos
POST   /todos/                               Create todo
PUT    /todos/{id}                           Update todo
DELETE /todos/{id}                           Delete todo
```

Full interactive docs at https://ai-realtor.fly.dev/docs

---

## Deal Calculator & Scoring

The deal calculator provides investor-grade underwriting across four strategies:

```
Voice: "Calculate the deal for property 5"
Voice: "Compare wholesale vs flip vs rental for 123 Main St"
Voice: "What if ARV is $400K and rent is $2,800/month?"
```

### Data Fallback Chain
1. User-provided overrides
2. Agentic underwriting results (research job)
3. Zillow Zestimate (for ARV)
4. Comparable sales average
5. List price (last resort)

### Output Per Strategy
- Offer price with reasoning
- Total investment breakdown
- Profit / ROI / monthly cash flow
- Expense line items (property mgmt, vacancy, capex, repairs, insurance, tax, debt service)
- Financing details (loan amount, rate, monthly P&I)
- **Deal score (A-F)** with weighted factors

### BRRRR-Specific
- Initial cash in (down payment + closing costs + rehab)
- Refi at 75% ARV after stabilization
- Cash back at refinance
- Cash left in deal
- Infinite return detection (all cash recovered)
- Post-refi monthly cash flow

---

## Agentic Property Research

Multi-agent AI research pipeline that runs parallel workers:

```
Voice: "Run full agentic research on property 8"
Voice: "Research 123 Main St with extensive environmental analysis"
```

### Research Workers
| Worker | Output |
|---|---|
| Property Profile | Normalized address, geocoding, parcel facts, owner |
| Comp Sales | Nearby sales with price, distance, similarity score |
| Comp Rentals | Rental comps with rent, distance, similarity score |
| Underwriting | ARV estimate (base/low/high), rent estimate, rehab range, offer recommendation |
| Neighborhood | Crime stats, school ratings, market trends, AI summary |
| Risk Score | Title risk %, data confidence %, compliance flags |
| EPA Environmental | Superfund sites, brownfields, toxic releases |
| Wildfire Hazard | Hazard level and description |
| Seismic Hazard | Nearby faults, hazard description |
| Wetlands | Wetlands found, count, types |
| HUD Opportunity | Opportunity zone indices |
| Historic Places | Nearby historic places, district detection |

All findings are stored as searchable **Dossiers** (markdown) and **Evidence Items** (claims with source URLs) with vector embeddings for semantic search.

---

## Phone Call Automation

### VAPI Calls
```
Voice: "Call +14155551234 about property 5"
Voice: "Call John about the Purchase Agreement"
Voice: "Call the owner of property 5 and ask if they want to sell"
```

Each call includes the full property recap as system context. The AI assistant can answer questions about the property, contracts, and next steps.

### ElevenLabs Conversational Agent
```
Voice: "Set up the ElevenLabs voice agent"
Voice: "Make an ElevenLabs call to +14155551234"
```

The ElevenLabs agent connects to the MCP server and has **live access to all 61 tools** during the call. It can look up properties, check contract status, calculate deals, and draft offers mid-conversation.

### Voice Campaigns
```
Voice: "Create a campaign to call all buyers about contract reminders"
Voice: "Start campaign 3"
Voice: "Show me campaign analytics"
```

Automated bulk calling with retry logic, rate limiting, and webhook-driven outcome tracking.

---

## Tech Stack

### Backend
- **FastAPI** (Python 3.11) — Web framework with auto-generated OpenAPI docs
- **SQLAlchemy** — ORM with 31 models
- **PostgreSQL** — Database with pgvector extension for semantic search
- **Alembic** — Database migrations (auto-run on deploy)
- **Pydantic v2** — Data validation (`model_dump`, `from_attributes`)

### AI & ML
- **Anthropic Claude Sonnet 4** — Contract analysis, recaps, compliance, offer letters, research synthesis
- **GPT-4 Turbo** — VAPI phone conversations
- **OpenAI Embeddings** — text-embedding-3-small (1536 dims) for vector search
- **fpdf2** — PDF report generation

### External APIs (12)
| Service | Purpose |
|---|---|
| Google Places | Address autocomplete and geocoding |
| Zillow (RapidAPI) | Property enrichment (photos, Zestimate, schools, tax/price history) |
| Skip Trace (RapidAPI) | Owner contact discovery |
| RentCast | Rental market data |
| DocuSeal | E-signatures with webhook sync |
| VAPI | AI phone calls (GPT-4 + 11Labs voice) |
| ElevenLabs | Conversational AI agent with MCP tool access |
| Exa | AI-powered web research |
| Anthropic Claude | AI analysis across the platform |
| OpenAI | Text embeddings for vector search |
| Resend | Email delivery with PDF attachments |

### Frontend
- **Next.js 15** — React framework
- **TypeScript** — Type safety
- **Zustand** — State management
- **Framer Motion** — Animations
- **Remotion** — Video/animation rendering

### Infrastructure
- **Fly.io** — Cloud hosting (EWR region, 1GB RAM)
- **Docker** — Multi-stage builds with Python 3.11-slim
- **Depot** — Fast container builds
- **WebSocket** — Real-time updates to frontend

---

## Quick Start

### Local Development

```bash
# Clone
git clone https://github.com/Thedurancode/ai-realtor.git
cd ai-realtor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Create database
createdb ai_realtor

# Run database migrations
alembic upgrade head

# Start backend
python3 -m uvicorn app.main:app --reload --port 8000

# Start frontend (separate terminal)
cd frontend && npm install && npm run dev
```

**Visit:**
- Backend API: http://localhost:8000/docs
- Frontend TV Display: http://localhost:3025

### MCP Server Setup

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "property-management": {
      "command": "/path/to/ai-realtor/venv/bin/python3",
      "args": ["/path/to/ai-realtor/mcp_server/property_mcp.py"],
      "env": {
        "MCP_API_BASE_URL": "http://localhost:8000",
        "MCP_API_KEY": "your_api_key"
      }
    }
  }
}
```

Restart Claude Desktop. You should see 61 tools available.

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://localhost:5432/ai_realtor

# Google Places
GOOGLE_PLACES_API_KEY=your_key

# Zillow & Skip Trace (RapidAPI)
RAPIDAPI_KEY=your_key

# Anthropic Claude
ANTHROPIC_API_KEY=your_key

# OpenAI (embeddings)
OPENAI_API_KEY=your_key

# DocuSeal (e-signatures)
DOCUSEAL_API_KEY=your_key
DOCUSEAL_WEBHOOK_SECRET=your_secret

# VAPI (phone calls)
VAPI_API_KEY=your_key
VAPI_PHONE_NUMBER_ID=your_phone_id

# ElevenLabs (voice AI)
ELEVENLABS_API_KEY=your_key

# Exa (web research)
EXA_API_KEY=your_key

# RentCast (rental data)
RENTCAST_API_KEY=your_key

# Resend (email)
RESEND_API_KEY=your_key
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=Real Estate Contracts

# Voice campaigns
CAMPAIGN_WORKER_ENABLED=true
CAMPAIGN_WORKER_INTERVAL_SECONDS=15
CAMPAIGN_WORKER_MAX_CALLS_PER_TICK=5
```

---

## Example Workflows

### New Property — Full Pipeline
```
"Create property at 123 Main St, Brooklyn, NY for $650,000 with 2 bedrooms"
  -> "Enrich it with Zillow data"
  -> "Run full agentic research"
  -> "Calculate the deal"
  -> "Skip trace to find the owner"
  -> "Attach required contracts based on AI analysis"
  -> "Generate a recap"
  -> "Send me the property overview"
  -> "Call the owner and ask if they're interested in selling"
```

### Contract to Close
```
"What contracts are required for property 5?"
  -> "AI suggest contracts for this property"
  -> "Apply the AI suggestions"
  -> "Send the purchase agreement to John Smith"
  -> [DocuSeal webhook fires when signed]
  -> "Is the property ready to close?"
```

### Wholesale Deal Analysis
```
"Set property 3 to wholesale deal type"
  -> "Calculate the deal for property 3"
  -> "Compare wholesale vs flip vs rental"
  -> "What if ARV is $300K and rehab is heavy?"
  -> "Calculate MAO for property 3"
  -> "Submit an offer of $180K with inspection contingency"
  -> "Draft the offer letter"
```

### Lead Generation Campaign
```
"Skip trace property 8"
  -> "Generate a recap with market analysis"
  -> "Create a voice campaign for skip trace outreach"
  -> "Add all property owners as targets"
  -> "Start the campaign"
  -> [Background worker calls each target with retry logic]
  -> "Show me campaign analytics"
```

### Research Deep Dive
```
"Run full agentic research on 456 Oak Ave with extensive environmental"
  -> "Show me the research dossier"
  -> "What's the flood zone status?"
  -> "Find similar properties in the area"
  -> "Search research for environmental hazards in Brooklyn"
```

---

## Deployment

### Fly.io

```bash
# Deploy
fly deploy

# Set secrets
fly secrets set \
  GOOGLE_PLACES_API_KEY="..." \
  ANTHROPIC_API_KEY="..." \
  DOCUSEAL_API_KEY="..." \
  VAPI_API_KEY="..." \
  RESEND_API_KEY="..." \
  OPENAI_API_KEY="..." \
  --app ai-realtor

# View logs
fly logs --app ai-realtor

# SSH into instance
fly ssh console --app ai-realtor

# Database access
fly postgres connect -a ai-realtor-db
```

### Startup Sequence (start.sh)
1. `alembic upgrade head` — Run database migrations
2. Start MCP SSE server on port 8001 (background)
3. Start FastAPI on port 8000 (foreground)

### Docker
- Base: Python 3.11-slim
- Dependencies: gcc, libpq-dev (PostgreSQL)
- Multi-stage build with requirement caching
- Copies: app/, mcp_server/, scripts/, alembic/, alembic.ini

---

## Database Schema

### Core Tables
| Table | Purpose |
|---|---|
| `agents` | Real estate agents with API key auth |
| `properties` | Property listings with deal scoring |
| `contacts` | Buyers, sellers, agents, and 16 other roles |
| `contracts` | Contract documents with DocuSeal integration |
| `contract_templates` | Reusable templates with state/city/price filters |
| `contract_submitters` | Per-contract signer roles and statuses |
| `offers` | Offer lifecycle with negotiation chains |

### Enrichment & Research
| Table | Purpose |
|---|---|
| `zillow_enrichments` | Photos, Zestimate, schools, tax/price history |
| `skip_traces` | Owner contact info from skip trace |
| `property_recaps` | AI-generated summaries (3 formats) |
| `agentic_jobs` | Research job tracking |
| `research_properties` | Normalized research output |
| `comp_sales` | Comparable sale records |
| `comp_rentals` | Comparable rental records |
| `dossiers` | Research markdown with embeddings |
| `evidence_items` | Research claims with source URLs |
| `worker_runs` | Individual AI worker execution logs |
| `underwritings` | ARV/rent/rehab/offer estimates |
| `risk_scores` | Title risk, data confidence, compliance flags |

### Campaigns & Activity
| Table | Purpose |
|---|---|
| `voice_campaigns` | Campaign metadata and configuration |
| `voice_campaign_targets` | Phone numbers with attempt tracking |
| `activity_events` | Event log for all tool executions |
| `notifications` | System notifications with priority |
| `todos` | Property-specific tasks |

### Configuration
| Table | Purpose |
|---|---|
| `agent_preferences` | Per-agent settings |
| `deal_type_configs` | Deal type definitions |
| `compliance_rules` | Compliance rule definitions |
| `research_templates` | Research strategy templates |

---

## License

MIT License — See LICENSE file for details.

---

**Built with [Claude Code](https://claude.ai/code) via [Happy](https://happy.engineering)**
