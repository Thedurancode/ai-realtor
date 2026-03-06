# AI Realtor — The AI-Powered Real Estate Operating System

An autonomous AI platform that manages the entire real estate lifecycle — from property discovery to closing — through natural language. Built on FastAPI + Next.js with 500+ AI tools, 30+ API integrations, and a Claude-powered brain that can research, negotiate, market, call, email, design, and close deals.

**Live API:** http://ai-realtor.emprezario.com
**Docs:** http://ai-realtor.emprezario.com/docs

```
500+ MCP Tools  ·  223 API Endpoints  ·  31 Models  ·  31 Services  ·  30+ External APIs
21 Social Platforms  ·  269 CRM Tools  ·  22 Ad Management Tools  ·  21 E-commerce Tools
```

---

## Table of Contents

- [Real Estate API](#real-estate-api)
  - [Property Management](#property-management)
  - [Deal Calculator & Scoring](#deal-calculator--scoring)
  - [Offer & Negotiation Engine](#offer--negotiation-engine)
  - [AI Contract Management](#ai-contract-management)
  - [Agentic Property Research](#agentic-property-research)
  - [Phone Call Automation](#phone-call-automation)
  - [Skip Tracing & Owner Discovery](#skip-tracing--owner-discovery)
  - [Compliance Engine](#compliance-engine)
  - [CMA Reports & Listing Presentations](#cma-reports--listing-presentations)
- [MCP Tool Ecosystem](#mcp-tool-ecosystem)
  - [RealtorClaw (200+ Tools)](#realtorclaw-200-tools)
  - [Social Media MCP (21 Platforms)](#social-media-mcp-21-platforms)
  - [Google Ads MCP (22 Tools)](#google-ads-mcp-22-tools)
  - [GoHighLevel CRM (269 Tools)](#gohighlevel-crm-269-tools)
  - [E-commerce (WooCommerce + Shopify)](#e-commerce-woocommerce--shopify)
  - [Google Workspace (Drive, Docs, Sheets, Slides)](#google-workspace)
  - [WordPress Management](#wordpress-management)
  - [Design (Figma + Canva)](#design-figma--canva)
  - [Finance (QuickBooks + Stripe)](#finance-quickbooks--stripe)
  - [Zillow Market Data](#zillow-market-data)
  - [Voice & Media (ElevenLabs)](#voice--media-elevenlabs)
  - [Additional Integrations](#additional-integrations)
- [AI Brain](#ai-brain)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [API Endpoints (223)](#api-endpoints-223)
- [Database Schema](#database-schema)
- [Environment Variables](#environment-variables)
- [Deployment](#deployment)

---

# Real Estate API

The core of the platform — a full-stack real estate backend with AI at every layer.

## Property Management

Create, enrich, research, score, and manage properties through voice or API.

```
"Create a property at 123 Main St, Brooklyn for $650,000 with 3 beds"
"Enrich it with Zillow data"
"Run full agentic research"
"Score the deal"
```

- **Property types:** house, condo, townhouse, apartment, land, commercial, multi-family
- **Status tracking:** available, pending, sold, rented, off_market
- **Auto-enrich pipeline:** create → enrich → research → score → attach contracts
- **Google Places** address autocomplete and geocoding
- **Zillow enrichment:** high-res photos, Zestimate, rent estimates, tax history, schools, comps
- **Semantic vector search** via pgvector + OpenAI embeddings (1536 dims)

### API Endpoints
```
POST   /properties/                    Create property
GET    /properties/                    List with filtering
GET    /properties/{id}                Get details
PATCH  /properties/{id}                Update
DELETE /properties/{id}                Delete
POST   /properties/{id}/set-deal-type  Set deal type
GET    /properties/{id}/deal-status    Deal progress
```

---

## Deal Calculator & Scoring

Investor-grade underwriting across four strategies with AI-powered scoring.

```
"Calculate the deal for property 5"
"Compare wholesale vs flip vs rental for 123 Main St"
"What if ARV is $400K and rent is $2,800/month?"
```

### Four Investment Strategies

| Strategy | Key Metrics |
|----------|------------|
| **Wholesale** | Offer price, assignment fee, profit, ROI |
| **Fix & Flip** | Purchase + rehab costs, ARV, profit, ROI, hold time |
| **Rental** | Monthly cash flow, cap rate, expense breakdown, debt service |
| **BRRRR** | Initial cash in, refi amount, cash back, infinite return flag, post-refi cash flow |

### Scoring
- **Deal grades A–F** based on weighted market conditions and profitability
- **Data fallback chain:** user override → agentic underwriting → Zestimate → comp average → list price
- **Rehab cost tiers:** light ($15/sqft), medium ($35/sqft), heavy ($60/sqft)
- Side-by-side strategy comparison
- What-if scenario analysis with custom assumptions

### BRRRR-Specific
- Initial cash in (down payment + closing costs + rehab)
- Refi at 75% ARV after stabilization
- Cash back at refinance, cash left in deal
- Infinite return detection (all cash recovered)
- Post-refi monthly cash flow

---

## Offer & Negotiation Engine

Full offer lifecycle with AI-drafted letters and negotiation tracking.

```
"Submit an offer of $600K on property 3 with inspection contingency"
"Counter at $575K"
"Draft the offer letter"
```

- Create, counter, accept, reject, and withdraw offers
- Full negotiation chain tracking (parent/child offer history)
- **MAO calculation** (Maximum Allowable Offer) for wholesale deals
- **AI-drafted offer letters** with negotiation strategy and talking points
- DocuSeal pre-fill for instant buyer signature
- **Contingencies:** inspection, financing, appraisal, sale of buyer's home
- **Financing types:** cash, conventional, FHA, VA, hard_money, seller_financing

### API Endpoints
```
POST   /offers/                         Create offer
GET    /offers/                         List offers
POST   /offers/{id}/counter             Counter offer
POST   /offers/{id}/accept              Accept
POST   /offers/{id}/reject              Reject
POST   /offers/{id}/withdraw            Withdraw
GET    /offers/{id}/chain               Negotiation chain
POST   /offers/property/{id}/mao        Calculate MAO
POST   /offers/{id}/draft-letter        AI offer letter
```

---

## AI Contract Management

Three-tier requirement system with e-signatures and multi-party signing.

| Tier | How It Works |
|------|-------------|
| **Auto-attach** | Template matching by state, city, price range, property type (15+ templates) |
| **AI Suggestions** | Claude analyzes property and recommends required vs optional contracts |
| **Manual Override** | Mark any contract required/optional with deadline and reason |

- **DocuSeal e-signature** integration with multi-party signing
- **Smart sending** with role-based signer detection
- Real-time status via DocuSeal webhooks (HMAC-SHA256 verified)
- Contract statuses: draft → sent → in_progress → pending_signature → completed

### API Endpoints
```
POST   /contracts/{id}/send              Send via DocuSeal
POST   /contracts/{id}/send-multi-party  Multi-party signing
POST   /contracts/voice/smart-send       Auto-determine signers
POST   /contracts/property/{id}/ai-suggest   AI suggestions
GET    /contracts/property/{id}/signing-status  Who signed what
```

---

## Agentic Property Research

12+ parallel AI research workers that produce investor-grade dossiers.

```
"Run full agentic research on property 8"
"Research 123 Main St with extensive environmental analysis"
```

| Worker | Output |
|--------|--------|
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

All findings stored as searchable **Dossiers** and **Evidence Items** with vector embeddings.

---

## Phone Call Automation

### VAPI Calls
```
"Call the owner of property 5 and ask if they want to sell"
"Call John about the Purchase Agreement"
```

| Call Type | What It Does |
|-----------|-------------|
| `property_update` | Shares property details, answers questions |
| `contract_reminder` | Reminds about pending contracts |
| `skip_trace_outreach` | Cold calls owner about selling |
| `closing_ready` | Celebrates all contracts complete |

### ElevenLabs Conversational Agent
- Voice agent with **live access to all 200+ tools** during calls
- Can look up properties, check contracts, calculate deals mid-conversation
- Claude Sonnet as the brain + natural ElevenLabs voice
- Embeddable website widget + Twilio phone number

### Voice Campaigns
```
"Create a campaign to call all property owners"
"Start campaign 3"
"Show me campaign analytics"
```
- Bulk outbound calling with retry logic and rate limiting
- Campaign lifecycle: draft → active → paused → completed
- Background worker with automatic processing

---

## Skip Tracing & Owner Discovery

```
"Skip trace property 5"
"Find the owner of 123 Main St and call them"
```

- Owner names, phone numbers, emails, mailing addresses
- Relatives and associates
- Direct cold calling integration with VAPI
- Voice-optimized responses with formatted phone numbers

---

## Compliance Engine

```
"Run a compliance check on property 5"
```

- AI-powered checks against federal (RESPA, TILA, Fair Housing), state, and local regulations
- Rule types: disclosure, contract, deadline, documentation, fair_housing, data_privacy
- Violation severity: critical, high, medium, low, info
- Claude-generated compliance summary with remediation steps

---

## CMA Reports & Listing Presentations

### CMA Report Generator
- Claude AI analysis → branded PDF (navy/gold)
- Comparable sales analysis with adjustments
- Email delivery via Resend

### Listing Presentation Builder
Address → 8-component marketing package:
1. CMA Report
2. Marketing Plan
3. Video Script
4. Social Media Posts
5. MLS Description
6. Email Blast
7. Talking Points
8. Timeline

---

## Follow-Up Sequences

Multi-channel drip campaigns with 5 built-in templates:
- Email, SMS, phone calls, postcards
- Configurable timing and touch sequence
- Engagement tracking

## Deal Journal

Auto-logs all deal interactions → Knowledge Base for RAG search. Every call, email, note, and status change is captured and searchable.

## Direct Mail

- Postcards and letters via Lob.com USPS integration
- Address verification before sending
- Campaign tracking

---

# MCP Tool Ecosystem

Beyond the core real estate API, the platform connects to 500+ tools across 20+ MCP servers.

## RealtorClaw (200+ Tools)

The primary MCP server — the full real estate platform exposed as Claude tools.

| Category | Tools | Examples |
|----------|-------|---------|
| Properties | 20+ | list, create, update, enrich, research, score |
| Deals | 15+ | calculate, compare strategies, what-if, MAO |
| Contracts | 15+ | send, check status, AI suggest, smart send |
| Offers | 10+ | create, counter, accept, reject, draft letter |
| Research | 10+ | async research, dossier, evidence search |
| Calls | 10+ | VAPI calls, ElevenLabs, voice campaigns |
| Contacts | 5+ | add, list, score relationship |
| Calendar | 10+ | events, conflicts, optimize schedule |
| Mail | 5+ | postcards, letters, address verification |
| Social | 5+ | preview, publish, schedule posts |
| Search | 5+ | semantic search, similar properties |
| Reports | 5+ | CMA, listing presentations, property reports |
| Knowledge | 5+ | ingest docs, search knowledge base |
| Notifications | 5+ | send, list, acknowledge |
| Webhooks | 5+ | register, test, list |

---

## Social Media MCP (21 Platforms)

Custom-built MCP server — direct API calls, no third-party dependency.

**File:** `mcp_server/social_mcp.py`

| # | Platform | Tool | Content Type |
|---|----------|------|-------------|
| 1 | Twitter/X | `post_tweet` | Tweets (280 char) |
| 2 | LinkedIn | `post_linkedin` | Personal posts |
| 3 | LinkedIn Page | `post_linkedin_page` | Company page posts |
| 4 | Facebook | `post_facebook` | Page posts + links |
| 5 | Instagram | `post_instagram` | Photos + captions |
| 6 | Threads | `post_threads` | Text posts |
| 7 | TikTok | `post_tiktok` | Videos |
| 8 | YouTube | `post_youtube` | Community posts |
| 9 | Reddit | `post_reddit` | Subreddit posts |
| 10 | Pinterest | `post_pinterest` | Pins |
| 11 | Discord | `post_discord` | Webhook messages |
| 12 | Slack | `post_slack` | Webhook messages |
| 13 | Telegram | `post_telegram` | Bot messages |
| 14 | Bluesky | `post_bluesky` | Posts |
| 15 | Mastodon | `post_mastodon` | Toots |
| 16 | Medium | `post_medium` | Articles (draft) |
| 17 | Dev.to | `post_devto` | Articles |
| 18 | Hashnode | `post_hashnode` | Blog posts |
| 19 | WordPress | `post_wordpress` | Blog posts |
| 20 | Google My Business | `post_gmb` | Business updates |
| 21 | Dribbble | `post_dribbble` | Design shots |

Plus `crosspost` (hit multiple at once) and `check_social_connections` (see what's ready).

---

## Google Ads MCP (22 Tools)

Custom-built full CRUD Google Ads management.

**File:** `mcp_server/google_ads_mcp.py`

| Category | Tools | Actions |
|----------|-------|---------|
| Account | 3 | List accounts, get info, check connection |
| Campaigns | 4 | List, create, update (enable/pause), delete |
| Ad Groups | 3 | List, create, update (bid/status) |
| Ads | 3 | List, create responsive search ads, enable/pause |
| Keywords | 3 | List with quality scores, add keywords, add negatives |
| Targeting | 2 | Search locations by name, set geo targeting |
| Budget | 1 | Update daily budget |
| Reporting | 2 | Performance reports (4 levels), daily spend |
| GAQL | 1 | Run any custom query |

**Safety:** New campaigns and ads start PAUSED. Budget changes are explicit.

```
"Create a Search campaign for NJ real estate, $50/day, maximize clicks"
"Add keywords: homes for sale bergen county, NJ realtor, sell my house NJ"
"Set targeting to New Jersey only"
"Show me top campaigns by cost this month"
"What search terms are wasting budget?"
```

---

## GoHighLevel CRM (269 Tools)

Full CRM management via the GoHighLevel MCP server.

| Category | Tools | Highlights |
|----------|-------|-----------|
| Contacts | 31 | CRUD, tags, tasks, notes, workflow automation |
| Conversations | 20 | SMS, email, call recordings, live chat |
| Opportunities | 10 | Pipeline management, deal tracking |
| Calendars | 14 | Appointments, free slots, time blocking |
| Invoices & Billing | 39 | Invoices, estimates, recurring, text2pay |
| Payments | 20 | Orders, subscriptions, coupons, transactions |
| Social Media | 17 | Post management, account integration |
| Location Mgmt | 24 | Sub-accounts, custom fields, templates |
| Products | 10 | CRUD, pricing, inventory, collections |
| Store/E-commerce | 18 | Shipping, carriers, store settings |
| Email Marketing | 5 | Campaigns, templates |
| Blogs | 7 | Posts, authors, categories, SEO |
| Custom Objects | 9 | Schema + record management |
| Associations | 10 | Relationship mapping between objects |
| Custom Fields | 8 | Field management |
| Surveys | 2 | Survey management and responses |

---

## E-commerce (WooCommerce + Shopify)

### WooCommerce
Official Automattic MCP adapter — full store management through WordPress REST API.
- Products, orders, customers, coupons, shipping, inventory, refunds

### Shopify (70+ Tools)
`@ajackus/shopify-mcp-server` — comprehensive Shopify Admin API access.

| Category | Capabilities |
|----------|-------------|
| Products | CRUD, variants, images, collections |
| Orders | List, filter, fulfill, refund |
| Customers | Search, manage, tags |
| Inventory | Track stock levels, adjust |
| Discounts | Create/manage discount codes |
| Shipping | Fulfillment, tracking |

---

## Google Workspace

### Google Drive MCP
`@piotr-agier/google-drive-mcp` — authenticated and connected.

- **Google Drive** — files, folders, sharing
- **Google Docs** — read/write documents
- **Google Sheets** — read/write spreadsheets
- **Google Slides** — read/write presentations
- **Google Calendar** — events, scheduling

### Gmail MCP
- Read, search, draft emails
- Auto-triage with AI classification

---

## WordPress Management

Official WordPress MCP adapter (`@automattic/mcp-wordpress-remote`).
- Posts, pages, custom post types
- Media uploads
- Users, plugins, themes
- Full site administration

---

## Design (Figma + Canva)

### Figma MCP
- Read design data, inspect properties
- List components, extract styles
- Export assets (PNG, SVG)
- Code to Canvas (push UI back to Figma)

### Canva MCP
`@canva/cli@latest mcp`
- Create designs from templates
- Manage folders and assets
- Autofill templates
- Export as PDF/image

---

## Finance (QuickBooks + Stripe)

### QuickBooks MCP
`quickbooks-mcp` — full accounting management.
- P&L reports, balance sheets, trial balance
- Create invoices and journal entries
- SQL-like queries across all QuickBooks entities
- Draft/preview mode by default (safe)

### Stripe
Payment processing (configured, needs API key).
- Payments, invoices, subscriptions

---

## Zillow Market Data

Zillow MCP server for supplementary market intelligence.
- Property search by location, price, beds, baths
- Zestimates (Zillow's proprietary valuations)
- Market trends by location
- Mortgage calculator with PMI, taxes, insurance

---

## Voice & Media (ElevenLabs)

ElevenLabs MCP — text-to-speech, voice cloning, AI agents, phone calls.
- Generate speech in any voice
- Clone voices
- Make outbound AI phone calls
- Conversational agents with tool access

---

## Additional Integrations

| MCP Server | Purpose | Status |
|-----------|---------|--------|
| **Playwright** | Browser automation, screenshots, UI testing | Active |
| **Context7** | Live documentation lookup for any library | Active |
| **Z.AI Vision** | Image/video analysis, UI diffs, screenshots | Active |
| **Web Search** | Live internet search | Active |
| **Sequential Thinking** | Structured reasoning for complex problems | Active |
| **Claude-mem** | Cross-session searchable memory | Active |
| **Fetch** | HTTP requests to any URL | Active |
| **Docker** | Container management | Configured |
| **Meta Ads** | Facebook/Instagram ad campaigns | Needs API key |
| **Resend** | Transactional email | Needs API key |

---

# AI Brain

### Memory System
- **Persistent memory** across sessions (projects, bugs, decisions, preferences)
- **Heartbeat system** — auto-checks for tasks at session start
- **Claude-mem plugin** — cross-session searchable memory database
- **End-of-session learning** — auto-saves discoveries before signing off

### Skills System
12 installable skill packs that teach Claude new domain expertise:
- Luxury Negotiation, Short-Sale Expert, FSBO Converter
- Find Skills, and 8+ nanobot skills

### Autonomy
- Full YOLO mode — autonomous task execution
- Subagent delegation for parallel work
- Automated video pipeline (ElevenLabs TTS → HeyGen → Pexels → Shotstack)

---

# Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Claude Code (AI Brain)                      │
│    Persistent Memory · 12 Skills · YOLO Mode · Subagents        │
└────────────────────────────┬────────────────────────────────────┘
                             │ MCP Protocol
           ┌─────────────────┼─────────────────────┐
           v                 v                     v
┌──────────────────┐ ┌──────────────┐ ┌────────────────────────┐
│  RealtorClaw     │ │ Social Media │ │   Google Ads MCP       │
│  200+ RE Tools   │ │ 21 Platforms │ │   22 Campaign Tools    │
└────────┬─────────┘ └──────────────┘ └────────────────────────┘
         │
         │ HTTP API                    ┌────────────────────────┐
         v                            │   External MCPs         │
┌──────────────────────────────┐      │  GoHighLevel (269)     │
│      FastAPI Backend          │      │  Shopify (70+)         │
│  27 Routers · 223 Endpoints  │      │  WooCommerce           │
│  31 Services · 31 Models     │      │  Google Drive/Docs     │
│  Rate Limiting · CORS        │      │  WordPress             │
└──────┬──────────────┬────────┘      │  Figma · Canva         │
       │              │               │  QuickBooks · Stripe   │
       v              v               │  Zillow · ElevenLabs   │
┌────────────┐ ┌─────────────────┐    │  Gmail · Calendar      │
│ PostgreSQL │ │ External APIs   │    │  Playwright · Vision   │
│ + pgvector │ │ (30+ services)  │    └────────────────────────┘
│ 31 tables  │ │ Google · Zillow │
│ Embeddings │ │ DocuSeal · VAPI │
└────────────┘ │ ElevenLabs      │
               │ Resend · Lob    │
               └─────────────────┘
```

---

# Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/Thedurancode/ai-realtor.git
cd ai-realtor
./scripts/start-docker.sh
```

### Local Development

```bash
git clone https://github.com/Thedurancode/ai-realtor.git
cd ai-realtor
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your API keys
alembic upgrade head
python3 -m uvicorn app.main:app --reload --port 8000
```

### MCP Server Setup

Copy `.mcp.json.example` to `.mcp.json` and fill in your API keys:

```bash
cp .mcp.json.example .mcp.json
# Edit .mcp.json with your credentials
```

Then restart Claude Code. All configured MCP servers will be available.

---

# API Endpoints (223)

### Properties
```
POST   /properties/                    Create property
GET    /properties/                    List with filtering
GET    /properties/{id}                Get details
PATCH  /properties/{id}                Update
DELETE /properties/{id}                Delete
```

### Contracts
```
POST   /contracts/{id}/send            Send via DocuSeal
POST   /contracts/voice/smart-send     Auto-determine signers
POST   /contracts/property/{id}/ai-suggest   AI suggestions
GET    /contracts/property/{id}/signing-status  Who signed
```

### Offers
```
POST   /offers/                         Create offer
POST   /offers/{id}/counter             Counter offer
POST   /offers/{id}/accept              Accept
POST   /offers/property/{id}/mao        Calculate MAO
POST   /offers/{id}/draft-letter        AI offer letter
```

### Deal Calculator
```
POST   /deal-calculator/calculate       Full calculation
POST   /deal-calculator/compare         Compare strategies
POST   /deal-calculator/voice           Voice-optimized
```

### Research
```
POST   /agentic-research/property/{id}/run    Run pipeline
GET    /agentic-research/property/{id}/dossier  Get dossier
```

### Calls & Campaigns
```
POST   /elevenlabs/call                  ElevenLabs outbound call
POST   /voice-campaigns/                 Create campaign
POST   /voice-campaigns/{id}/start       Start campaign
```

Full interactive docs at http://ai-realtor.emprezario.com/docs

---

# Database Schema

### Core Tables
| Table | Purpose |
|-------|---------|
| `properties` | Property listings with deal scoring |
| `contracts` | Contract documents with DocuSeal integration |
| `contacts` | 19 roles: buyer, seller, lawyer, contractor, etc. |
| `offers` | Offer lifecycle with negotiation chains |
| `agents` | Real estate agents with API key auth |

### Enrichment & Research
| Table | Purpose |
|-------|---------|
| `zillow_enrichments` | Photos, Zestimate, schools, tax history |
| `skip_traces` | Owner contact info |
| `dossiers` | Research markdown with embeddings |
| `evidence_items` | Research claims with source URLs |
| `comp_sales` / `comp_rentals` | Comparable records |
| `underwritings` | ARV/rent/rehab/offer estimates |

### Campaigns & Activity
| Table | Purpose |
|-------|---------|
| `voice_campaigns` | Campaign metadata |
| `voice_campaign_targets` | Phone numbers with attempt tracking |
| `activity_events` | Event log for all tool executions |
| `notifications` | System notifications |

---

# Environment Variables

### Minimum Required
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/ai_realtor
ANTHROPIC_API_KEY=sk-ant-your-key
GOOGLE_PLACES_API_KEY=your-key
```

### MCP Servers
All MCP server credentials are in `.mcp.json` (gitignored). See `.mcp.json.example` for the full template with all 20+ servers.

### Feature-Specific
| Feature | Required APIs |
|---------|--------------|
| Property Management | Google Places, Anthropic Claude |
| Property Enrichment | Zillow (RapidAPI) |
| Skip Tracing | Skip Trace (RapidAPI) |
| E-Signatures | DocuSeal |
| Phone Calls | VAPI or ElevenLabs |
| Direct Mail | Lob.com |
| Video Generation | ElevenLabs, Shotstack, HeyGen |
| Social Media | Platform-specific API keys |
| Google Ads | Google Ads Developer Token + OAuth |
| CRM | GoHighLevel Private Integration key |
| E-commerce | WooCommerce keys or Shopify Admin token |

All APIs are optional — the platform functions with only the services you configure.

---

# Deployment

### Fly.io
```bash
fly deploy
fly secrets set ANTHROPIC_API_KEY="..." GOOGLE_PLACES_API_KEY="..." --app ai-realtor
```

### Docker
```bash
docker build -t ai-realtor .
docker run -p 8000:8000 --env-file .env ai-realtor
```

---

# Example Workflows

### Full Property Pipeline
```
"Create property at 123 Main St, Brooklyn for $650,000"
→ "Enrich with Zillow data"
→ "Run full agentic research"
→ "Calculate the deal"
→ "Skip trace the owner"
→ "Call them and ask if they want to sell"
→ "Submit an offer of $500K with inspection contingency"
→ "Send the purchase agreement for e-signature"
```

### Marketing Blitz
```
"Generate a listing presentation for 456 Oak Ave"
→ "Create a property video"
→ "Crosspost to Twitter, LinkedIn, Facebook, and Instagram"
→ "Create a Google Ads search campaign targeting Bergen County"
→ "Send a postcard to nearby homeowners"
→ "Schedule a blog post on WordPress"
```

### Business Operations
```
"Show me my QuickBooks P&L for last quarter"
→ "Check my Google Ads spend this month"
→ "List all pending GHL opportunities"
→ "Send an invoice for $5,000 to the buyer"
→ "Create a follow-up sequence for cold leads"
```

---

**Built by [Ed Duran](https://www.emprezario.com) at Emprezario Inc**
**Powered by [Claude Code](https://claude.ai/code)**

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
