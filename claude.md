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
- Status tracking: available, pending, sold, rented, off_market
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
- `update_property` - Voice: "Update property 5 status to pending"

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

**15 supported actions:**
- `resolve_property` - Find the target property
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

**Heuristic plan matching:**
- "Set up property 5 as a new lead" → resolve → enrich → skip trace → contracts → recap → summarize
- "Close the deal on property 3" → resolve → check readiness → recap → summarize
- "Note that property 2 has a new fence" → resolve → add note → summarize
- "Enrich property 5" → resolve → enrich → recap → summarize
- "Skip trace property 5" → resolve → skip trace → summarize
- "Call the owner of property 5" → resolve → skip trace → call → summarize

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

## MCP Tools — Complete List (77 tools)

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

**Research & Search Tools (5):**
`research_property`, `research_property_async`, `get_research_status`, `get_research_dossier`, `search_research`, `semantic_search`, `find_similar_properties`

**Conversation & History Tools (4):**
`get_conversation_history`, `what_did_we_discuss`, `clear_conversation_history`, `get_property_history`

**Property Notes Tools (2):**
`add_property_note`, `list_property_notes`

**Workflow Tools (2):**
`list_workflows`, `execute_workflow`

**Campaign Tools (6):**
`create_voice_campaign`, `start_voice_campaign`, `pause_voice_campaign`, `get_campaign_status`, `list_voice_campaigns`, `add_campaign_targets`

**Notification Tools (5):**
`send_notification`, `list_notifications`, `acknowledge_notification`, `get_notification_summary`, `poll_for_updates`

**Webhook Tools (1):**
`test_webhook_configuration`

**Total: 77 MCP tools** for complete voice control of the entire platform.

---

## Voice Examples

```
# Property Management
"Create a property at 123 Main St, New York for $850,000 with 2 bedrooms"
"Show me all condos under 500k in Miami"
"Show me houses with 3+ bedrooms"
"Update property 5 status to pending"

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
- MCP Server (Claude Desktop integration) — 77 tools
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
│              77 Tools for Voice Control                      │
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
│  │   Notes, Workflows, Contacts, Compliance, Offers     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Services: Voice Goal Planner, AI Recap, VAPI,        │   │
│  │   Enrichment, Skip Trace, Compliance, Workflows      │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Auto-Recap: Background regeneration on key events    │   │
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
- `todos` - Tasks
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

## Recent Updates (Feb 2026)

- Voice Goal Planner with 15 autonomous actions and heuristic plan matching
- Property Notes system with NoteSource enum and voice integration
- Workflow Templates (5 pre-built workflows)
- Voice Campaign Management (6 MCP tools)
- Proactive Notifications (5 MCP tools)
- Context Auto-Injection for all MCP responses
- Auto-Recap Regeneration on key events (notes, enrichment, skip trace, contacts, property updates)
- Property-Linked Conversation History with per-property audit trail
- Property filtering by type, city, price range, bedrooms via MCP
- Deal Calculator and Offer Management (18 MCP tools)
- Research and Semantic Search (7 MCP tools)
- ElevenLabs voice integration
- MCP tools expanded from 20 to **77 total**

---

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)
