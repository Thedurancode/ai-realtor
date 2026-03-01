# AI Realtor — Repository Overview

> Voice-first AI real estate platform that manages the entire property lifecycle through natural language, controlled via Claude Desktop MCP.

**Live API:** https://ai-realtor.fly.dev
**Docs:** https://ai-realtor.fly.dev/docs

```
61 MCP Tools · 223 API Endpoints · 31+ Models · 31+ Services · 30+ External APIs
```

---

## Architecture

```
Claude Desktop (voice)
        │ MCP Protocol (stdio / SSE)
        v
MCP Server (Python) ── 61 tools across 13 modules
        │ HTTP (localhost:8000)
        v
FastAPI Backend ── 80 routers · 120+ services · 31+ models
   │           │
   v           v
PostgreSQL     30+ External APIs
+ pgvector     (Google, Zillow, DocuSeal, VAPI,
                ElevenLabs, Exa, Resend, Meta, etc.)
   ^
   │ WebSocket
   v
Next.js 15 Frontend ── Dashboard · TV Display · Portal
```

| Layer | Technology | Scale |
|-------|-----------|-------|
| Backend | FastAPI (Python 3.11), SQLAlchemy, Alembic | 223 endpoints, 80 routers, 120+ services |
| MCP Server | Python MCP SDK, stdio + SSE | 61 voice-controlled tools, 13 modules |
| Frontend | Next.js 15, TypeScript, Zustand, TailwindCSS | Dashboard, TV display, customer portal |
| Database | PostgreSQL + pgvector | 31+ tables, 1536-dim vector embeddings |
| AI | Claude Sonnet 4, GPT-4 Turbo, OpenAI Embeddings | Analysis, calls, search |
| Deployment | Fly.io, Docker, Depot | Multi-stage builds, 1GB RAM |

---

## Directory Structure

```
ai-realtor/
├── app/                           # FastAPI backend (core application)
│   ├── main.py                    #   App entrypoint — router registration, middleware, startup
│   ├── models/                    #   SQLAlchemy models (31+ tables)
│   ├── routers/                   #   API route handlers (80 modules, 223 endpoints)
│   ├── services/                  #   Business logic layer (120+ service modules)
│   ├── schemas/                   #   Pydantic v2 request/response schemas
│   └── database.py               #   Database session & engine setup
│
├── mcp_server/                    # MCP server for Claude Desktop
│   ├── property_mcp.py            #   Server entrypoint (stdio + SSE modes)
│   └── tools/                     #   61 MCP tool definitions across 13 files
│       ├── property_tools.py      #     Property CRUD
│       ├── contracts.py           #     Contract management
│       ├── offers.py              #     Offer & negotiation
│       ├── deal_calculator.py     #     Investment analysis
│       ├── research.py            #     Agentic research
│       ├── vector_search.py       #     Semantic search
│       ├── analytics.py           #     Analytics & insights
│       ├── elevenlabs.py          #     Voice calls
│       ├── reports.py             #     PDF reports
│       ├── videogen.py            #     Video generation
│       ├── follow_ups.py          #     Follow-up management
│       └── conversation.py        #     Conversational AI
│
├── frontend/                      # Next.js 15 frontend
│   ├── app/                       #   Pages (dashboard, portal, setup, activity)
│   ├── components/                #   React components (18+ major)
│   │   ├── TVDisplay.tsx          #     Main TV display interface
│   │   ├── BloombergTerminal.tsx  #     Market terminal visualization
│   │   ├── PropertyDetailView.tsx #     Property info display
│   │   └── VoiceCompanion.tsx     #     Voice assistant UI
│   └── lib/                       #   Utilities, API client, stores
│
├── agentic_researcher/            # Multi-agent AI research pipeline (12+ workers)
├── remotion/                      # Remotion video rendering engine
├── nanobot/                       # Telegram bot integration
├── skills/                        # Claude Code skills modules
├── alembic/                       # Database migrations
├── scripts/                       # Deployment & utility scripts
├── tests/                         # Test suite (pytest)
├── docs/                          # Documentation
├── static/                        # Static assets (timeline editor, HTML)
├── landing-page/                  # Landing page assets
│
├── Dockerfile                     # Production Docker image (Python 3.11-slim)
├── docker-compose.yml             # Local development stack
├── fly.toml                       # Fly.io deployment config
├── start.sh                       # Startup script (migrations + MCP + API)
├── requirements.txt               # Python dependencies (43+)
├── alembic.ini                    # Alembic migration config
├── pytest.ini                     # Test configuration
└── claude.md                      # Claude Code project instructions
```

---

## Feature Summary

### Property Management
- Full CRUD with Google Places address autocomplete
- Property types: house, condo, townhouse, apartment, land, commercial, multi-family
- Status tracking: available, pending, sold, rented, off_market
- Auto-enrich pipeline: create → enrich → research → score → attach contracts

### Data Enrichment
- **Zillow**: Photos, Zestimates, rent estimates, tax/price history, schools, comps
- **Skip Trace**: Owner phone, email, mailing address, relatives/associates
- **Agentic Research**: 12+ parallel AI workers (property profile, comp sales/rentals, underwriting, neighborhood, environmental, seismic, wetlands, historic places, HUD opportunity zones)

### Contract Management
- Three-tier system: auto-attach templates, AI suggestions, manual override
- DocuSeal e-signature integration with multi-party signing
- 15+ templates for NY, CA, FL, TX (state/city/price filters)
- Webhook-driven status sync (HMAC-SHA256 verified)

### Offer & Negotiation
- Full lifecycle: create, counter, accept, reject, withdraw
- Negotiation chain tracking (parent/child offers)
- MAO calculation for wholesale deals
- AI-drafted offer letters with negotiation strategy

### Deal Calculator
- Four investment strategies: Wholesale, Fix & Flip, Rental, BRRRR
- Deal scoring (A-F grades) with weighted factors
- What-if scenario analysis with custom assumptions
- Data fallback chain: user override → agentic underwriting → Zestimate → comp average → list price

### Voice & Phone
- **VAPI**: AI phone calls with full property context (GPT-4 Turbo + 11Labs voice)
- **ElevenLabs**: Conversational AI agent with live MCP tool access during calls
- **Voice Campaigns**: Bulk outbound calling with rate limiting, retry logic, analytics

### Search & Intelligence
- **Semantic Search**: pgvector + OpenAI embeddings (text-embedding-3-small, 1536 dims)
- **Compliance Engine**: Federal (RESPA, TILA, Fair Housing), state, local regulations
- **PDF Reports**: Property overview reports generated with fpdf2 and emailed via Resend

### Frontend
- Real-time dashboard via WebSocket
- TV display with animated notifications
- Customer portal (register, login, properties, contracts)
- Bloomberg Terminal-style market visualization

### Marketing & Video
- Facebook Ads / Meta integration
- Postiz multi-platform social posting
- Video generation (HeyGen, D-ID, Replicate/PixVerse, Remotion)

---

## Tech Stack

### Backend
- **FastAPI** (Python 3.11) — Web framework with OpenAPI docs
- **SQLAlchemy 2.0** — ORM with 31+ models
- **PostgreSQL + pgvector** — Database with vector search
- **Alembic** — Schema migrations (auto-run on deploy)
- **Pydantic v2** — Data validation
- **slowapi** — Rate limiting
- **Redis** — Caching (optional)

### Frontend
- **Next.js 15** — React framework
- **TypeScript** — Type safety
- **Zustand** — State management
- **TailwindCSS** — Styling
- **Framer Motion** — Animations
- **Remotion** — Video/animation rendering
- **Socket.io** — Real-time updates

### AI & ML
- **Anthropic Claude Sonnet 4** — Contract analysis, recaps, compliance, research synthesis
- **GPT-4 Turbo** — VAPI phone conversations
- **OpenAI text-embedding-3-small** — 1536-dim embeddings for vector search
- **fpdf2** — PDF report generation

### Infrastructure
- **Fly.io** — Production hosting (EWR region)
- **Docker** — Multi-stage builds (Python 3.11-slim + Node.js 20)
- **Depot** — Fast container builds
- **supervisord** — Process management

---

## External API Integrations (30+)

| Category | Services |
|----------|----------|
| Property & Address | Google Places, Zillow (RapidAPI), Skip Trace (RapidAPI), Web Scraping |
| AI / LLM | Anthropic Claude, OpenAI, OpenRouter |
| Voice & Phone | VAPI, ElevenLabs, Telnyx |
| Contracts | DocuSeal (e-signatures) |
| Email | Resend |
| Research | Exa AI, RentCast |
| Direct Mail | Lob.com |
| Calendar | Google Calendar (OAuth) |
| Marketing | Meta / Facebook Ads, Postiz, Zuckerbot AI |
| Video | HeyGen, D-ID, Replicate (PixVerse), Remotion |
| Storage | AWS S3 |
| Infrastructure | Redis, PostgreSQL / SQLite |

All APIs are optional except PostgreSQL, Anthropic Claude, and Google Places.

---

## Database Schema (31+ tables)

**Core:** agents, properties, contacts, contracts, contract_templates, contract_submitters, offers

**Enrichment & Research:** zillow_enrichments, skip_traces, property_recaps, agentic_jobs, research_properties, comp_sales, comp_rentals, dossiers, evidence_items, worker_runs, underwritings, risk_scores

**Communication:** voice_campaigns, voice_campaign_targets, activity_events, notifications, todos

**Configuration:** agent_preferences, deal_type_configs, compliance_rules, research_templates

**Advanced:** property_websites, property_videos, render_jobs, agent_brands, agent_conversations, analytics_events, analytics_alerts

---

## Quick Start

```bash
# Clone and setup
git clone https://github.com/Thedurancode/ai-realtor.git
cd ai-realtor
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edit with your API keys

# Database
createdb ai_realtor
alembic upgrade head

# Run
python3 -m uvicorn app.main:app --reload --port 8000   # backend
cd frontend && npm install && npm run dev                # frontend (separate terminal)
```

- Backend API: http://localhost:8000/docs
- Frontend: http://localhost:3025

---

## Testing

```bash
pytest                    # run test suite
pytest tests/ -v          # verbose output
```

- Framework: pytest + pytest-asyncio
- Test files in `tests/` and project root
- Covers: compliance engine, conversations, DocuSeal, enrichment, memory, multi-party, notifications

---

*Generated 2026-03-01*
