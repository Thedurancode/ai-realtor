# AI Realtor - Intelligent Real Estate Management Platform

An AI-powered real estate management platform with voice control, agentic research, automated contracts, phone call automation, and semantic search. Built with FastAPI, PostgreSQL, and integrated with Claude AI, Zillow, DocuSeal, VAPI, ElevenLabs, and more.

**Live API:** https://ai-realtor.fly.dev
**Docs:** https://ai-realtor.fly.dev/docs

---

## Features

### Property Management
- Create, list, update, and delete properties with Google Places address autocomplete
- Support for all property types: house, condo, townhouse, apartment, land, commercial, multi-family
- Status tracking: available, pending, sold, rented, off_market
- Voice-optimized creation and lookup

### Zillow Data Enrichment
- High-res photos, Zestimate, rent estimates, tax history, price history
- Nearby schools with ratings, property features (year built, lot size, parking, heating/cooling)
- Market statistics and comparables
- Background processing with TV display animation

### Skip Tracing & Owner Discovery
- Find property owner names, phone numbers, emails, mailing addresses
- Relatives and associates
- Voice-optimized responses with formatted phone numbers
- Direct cold calling integration

### Contact Management
- 15+ contact roles: buyer, seller, lawyer, contractor, inspector, appraiser, lender, mortgage broker, title company, tenant, landlord, property manager, and more
- Role aliases for voice input (e.g., "attorney" maps to lawyer)
- Auto-contract matching by role

### AI Contract Management
- **Three-tier requirement system:**
  1. **Auto-attach** — matches templates by state, city, price, property type (15+ templates for NY, CA, FL, TX)
  2. **AI suggestions** — Claude analyzes the property and recommends contracts
  3. **Manual overrides** — mark contracts required/optional
- DocuSeal e-signature integration with multi-party signing
- Smart sending with role-based signer matching
- Real-time status via DocuSeal webhooks (HMAC-SHA256 verified)
- Contract statuses: draft, sent, in progress, pending signature, completed, cancelled, expired, archived

### Offer & Negotiation Engine
- Create, counter, accept, reject, and withdraw offers
- Full negotiation chain tracking
- MAO calculation (Maximum Allowable Offer) for wholesale deals
- Contingency tracking: inspection, financing, appraisal, sale of buyer's home
- Earnest money deposit and expiration tracking

### AI Property Recaps
- Three formats: detailed (human), voice summary (TTS), structured context (JSON for AI/VAPI)
- Auto-regenerates when contracts are signed, data is enriched, or skip trace completes
- Version tracking with trigger history

### Agentic Property Research
- **12+ parallel research workers:** Zillow, comparable sales/rentals, property history, neighborhood demographics, school ratings, crime stats, flood zones, tax assessment, market trends, environmental hazards, zoning
- Investor-grade dossier generation with evidence tracking
- Exa AI web research integration
- Background processing with progress tracking

### Semantic Vector Search
- pgvector-powered natural language property search
- OpenAI embeddings (text-embedding-3-small)
- Queries like "Modern condo in Brooklyn under $700k with parking"
- Similar property matching
- Cross-search properties, recaps, dossiers, and evidence

### Phone Call Automation
- **VAPI integration:** GPT-4 Turbo + 11Labs voice for automated calls
- **ElevenLabs conversational AI:** Natural conversation flow with voice selection
- 5 call types: property update, contract reminder, closing ready, specific contract reminder, skip trace outreach
- Full property context injected into calls, recording enabled

### Voice Campaign Management
- Bulk outbound calling campaigns
- Target filtering by property, contact role, or manual selection
- Configurable rate limiting, retry logic, max attempts
- Campaign analytics: success rate, total calls, completions
- Background worker with automatic processing

### Deal Type Workflows
- Pre-configured: traditional sale, wholesale, creative finance, subject-to, novation, lease option
- Auto-attach contracts, create todos, set required contacts per deal type
- Deal progress tracking and workflow previews

### Compliance Engine
- AI-powered checks against federal (RESPA, TILA, Fair Housing), state, and local regulations
- Violation severity levels: critical, high, medium, low, info
- Cost and time estimates for fixes
- Scheduled auto-checks after property creation
- Voice-optimized compliance summaries

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
- Work hours and communication preferences
- Default property creation values

---

## MCP Voice Control — 55 Tools

All features are accessible through natural language via the MCP server for Claude Desktop.

| Category | Tools | Count |
|---|---|---|
| Property | list, get, create, update, delete | 5 |
| Enrichment | enrich_property, skip_trace_property | 2 |
| Contacts | add_contact | 1 |
| Contracts | send, check status, list, signing status, readiness, attach, AI suggest, apply suggestions, mark required, smart send | 13 |
| Recaps & Calls | generate/get recap, phone call, call about contract, cold call owner | 5 |
| Offers | create, get, list, counter, accept, reject, withdraw, calculate MAO | 8 |
| Research | research (sync/async), status, dossier, search | 5 |
| Search | semantic search, find similar properties | 2 |
| ElevenLabs | call, setup, status | 3 |
| Deal Types | list, get, create, update, delete, preview, set, status | 8 |
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
"Find me properties similar to the Brooklyn condo"
"Run full agentic research on property 8"
```

---

## API Endpoints (216+)

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
```

### Agentic Research
```
POST   /agentic-research/property/{id}/run           Run full pipeline
GET    /agentic-research/property/{id}/status         Get status
POST   /agentic-research/property/{id}/rerun-worker   Rerun worker
GET    /agentic-research/property/{id}/dossier         Get dossier
POST   /agentic-research/voice/run                     Voice research
POST   /exa-research/property/{id}                     Exa research
GET    /exa-research/property/{id}/results             Exa results
```

### Semantic Search
```
POST   /search/properties                    Natural language search
POST   /search/research                      Search dossiers/evidence
GET    /search/similar/{id}                  Find similar properties
POST   /search/backfill                      Backfill embeddings
```

### Phone Calls & Campaigns
```
POST   /property-recap/property/{id}/call              VAPI call
GET    /property-recap/call/{id}/status                Call status
POST   /elevenlabs/call                                ElevenLabs call
POST   /voice-campaigns/                               Create campaign
POST   /voice-campaigns/{id}/targets                   Add targets
POST   /voice-campaigns/{id}/start                     Start campaign
GET    /voice-campaigns/{id}/analytics                 Analytics
```

### Compliance
```
POST   /compliance/properties/{id}/check               Full check
POST   /compliance/properties/{id}/quick-check          Quick check
GET    /compliance/properties/{id}/report               Report
POST   /compliance/voice/check                          Voice check
GET    /compliance/voice/status                          Voice status
```

### Contacts, Notifications, Todos, Webhooks
```
POST   /contacts/                            Create contact
POST   /contacts/voice                       Voice creation
GET    /contacts/property/{id}               Property contacts
POST   /notifications/                       Create notification
WS     /ws                                   WebSocket connection
POST   /display/command                      TV display command
POST   /webhooks/docuseal                    DocuSeal webhook
GET    /todos/                               List todos
POST   /todos/                               Create todo
```

See full interactive docs at `/docs`.

---

## Tech Stack

### Backend
- **FastAPI** — Python web framework
- **SQLAlchemy** — ORM with 35 models
- **PostgreSQL** — Database with pgvector extension
- **Alembic** — Database migrations
- **Pydantic v2** — Data validation

### AI & ML
- **Anthropic Claude Sonnet 4** — Contract analysis, recaps, compliance, research synthesis
- **GPT-4 Turbo** — VAPI phone conversations
- **OpenAI Embeddings** — text-embedding-3-small for vector search

### External APIs
- **Google Places** — Address autocomplete and geocoding
- **Zillow (RapidAPI)** — Property enrichment
- **Skip Trace (RapidAPI)** — Owner discovery
- **DocuSeal** — E-signatures with webhook sync
- **VAPI** — AI phone calls
- **ElevenLabs** — Conversational AI and TTS
- **Exa** — AI web research
- **Resend** — Email delivery

### Frontend
- **Next.js 15** — React framework
- **TypeScript** — Type safety
- **Zustand** — State management
- **Framer Motion** — Animations
- **Remotion** — Video/animation rendering

### Infrastructure
- **Fly.io** — Cloud hosting
- **Docker** — Multi-stage builds
- **Depot** — Fast container builds
- **WebSocket** — Real-time updates

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Claude Desktop                            │
│                   (Voice Interface)                           │
└───────────────────────┬──────────────────────────────────────┘
                        │ MCP Protocol
                        ▼
┌──────────────────────────────────────────────────────────────┐
│                  MCP Server (Python)                          │
│               55 Voice-Controlled Tools                      │
└───────────────────────┬──────────────────────────────────────┘
                        │ HTTP API
                        ▼
┌──────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                             │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  26 Routers · 216+ Endpoints · Rate Limiting · CORS   │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  34 Services: AI, VAPI, ElevenLabs, Enrichment,       │  │
│  │  Skip Trace, Compliance, Offers, Research, Campaigns   │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  35 Models: Property, Contract, Contact, Offer,       │  │
│  │  Recap, Dossier, Evidence, Campaign, Compliance...     │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────┬──────────────────────────┬────────────────────────┘
           │                          │
           ▼                          ▼
┌─────────────────────┐   ┌──────────────────────────────────┐
│  PostgreSQL + pgvec │   │       External APIs              │
│                     │   │  Google Places · Zillow · Exa    │
│  35 tables          │   │  Skip Trace · DocuSeal · VAPI   │
│  Vector embeddings  │   │  ElevenLabs · Resend · RapidAPI │
└─────────────────────┘   └──────────────────────────────────┘
           ▲
           │ WebSocket
           ▼
┌──────────────────────────────────────────────────────────────┐
│               Frontend (Next.js 15)                          │
│         Real-time Dashboard · TV Display · Activity Feed     │
└──────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Local Development

```bash
# Clone
git clone https://github.com/Thedurancode/ai-realtor.git
cd ai-realtor

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

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
      "command": "python3",
      "args": ["/path/to/ai-realtor/mcp_server/property_mcp.py"]
    }
  }
}
```

### Deploy to Fly.io

```bash
fly deploy
fly secrets set GOOGLE_PLACES_API_KEY="..." ANTHROPIC_API_KEY="..." # etc
```

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

# Resend (email)
RESEND_API_KEY=your_key

# OpenAI (embeddings)
OPENAI_API_KEY=your_key

# Voice campaigns
CAMPAIGN_WORKER_ENABLED=true
CAMPAIGN_WORKER_INTERVAL_SECONDS=15
```

---

## Example Workflows

### New Property — Full Pipeline
```
"Create property at 123 Main St, Brooklyn, NY for $650,000 with 2 bedrooms"
→ "Enrich it with Zillow data"
→ "Run full agentic research"
→ "Skip trace to find the owner"
→ "Attach required contracts based on AI analysis"
→ "Generate a recap"
→ "Call the owner and ask if they're interested in selling"
```

### Contract to Close
```
"What contracts are required for property 5?"
→ "AI suggest contracts for this property"
→ "Apply the AI suggestions"
→ "Send the purchase agreement to John Smith"
→ [DocuSeal webhook fires when signed]
→ "Is the property ready to close?"
```

### Wholesale Deal
```
"Set property 3 to wholesale deal type"
→ "Calculate MAO for property 3"
→ "Submit an offer of $180K with inspection contingency"
→ "Run comparable sales research"
→ "Find me similar properties in the area"
```

---

## License

MIT License — See LICENSE file for details.

---

**Built with Claude Code via [Happy](https://happy.engineering)**
