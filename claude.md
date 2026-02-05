# AI Realtor Platform - Complete Feature Guide

## Overview

AI Realtor is an intelligent real estate management platform that combines property data enrichment, AI-powered analysis, voice-controlled operations, automated contract management, and phone call automation. Built with FastAPI, PostgreSQL, and integrated with Claude AI, Zillow, DocuSeal, and VAPI.

**Live API:** https://ai-realtor.fly.dev
**Documentation:** https://ai-realtor.fly.dev/docs

---

## Core Features

### 1. Property Management

**Create properties with intelligent address lookup**
- Google Places API integration for accurate address autocomplete
- Automatic geocoding and full address details
- Support for all property types: house, condo, townhouse, apartment, land, commercial, multi-family

**Property data structure:**
- Basic info: address, city, state, ZIP, price, bedrooms, bathrooms, square footage
- Status tracking: available, pending, sold, rented, off_market
- Agent assignment and session tracking
- Automatic activity logging

**API Endpoints:**
- `POST /properties/` - Create property with place_id
- `GET /properties/` - List all properties with filtering
- `GET /properties/{id}` - Get property details
- `PUT /properties/{id}` - Update property
- `DELETE /properties/{id}` - Delete property and all related data

**MCP Tools:**
- `create_property` - Voice: "Create a property at 123 Main St, New York for $850,000"
- `list_properties` - Voice: "Show me all available properties"
- `get_property` - Voice: "Get details for property 5"
- `delete_property` - Voice: "Delete property 3"

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
- Automatic TV display animation when enriching
- Background processing for performance

**API Endpoints:**
- `POST /properties/{id}/enrich` - Enrich property with Zillow data
- `GET /properties/{id}` - Includes enrichment data in response

**MCP Tools:**
- `enrich_property` - Voice: "Enrich property 5 with Zillow data"

**Data stored:**
- `zillow_enrichments` table with JSON fields for photos, schools, features
- Zestimate and rent estimates with update timestamps
- Tax and price history for trend analysis

---

### 3. Skip Trace Integration

**Owner contact discovery for lead generation**
- Finds property owner name
- Discovers phone numbers (mobile and landline)
- Email addresses
- Mailing address
- Relatives and associates

**Use cases:**
- Cold calling property owners
- Direct mail campaigns
- Email outreach
- Lead generation for off-market properties

**API Endpoints:**
- `POST /properties/{id}/skip-trace` - Run skip trace on property
- `GET /skip-trace/{property_id}` - Get skip trace results

**MCP Tools:**
- `skip_trace_property` - Voice: "Skip trace property 5"
- `call_property_owner_skip_trace` - Voice: "Call the owner of property 5 and ask if they want to sell"

**Data structure:**
```json
{
  "owner_name": "John Smith",
  "phone_numbers": ["+14155551234", "+19175559876"],
  "email_addresses": ["john@example.com"],
  "mailing_address": "456 Oak St, Brooklyn, NY 11201",
  "relatives": ["Jane Smith", "Robert Smith"]
}
```

---

### 4. Contact Management

**Track all property stakeholders**
- Multiple contacts per property
- Role-based organization: buyer, seller, agent, other
- Contact info: name, email, phone
- Link contacts to specific properties
- Automatic contact creation from skip trace

**API Endpoints:**
- `POST /properties/{property_id}/contacts` - Add contact to property
- `GET /properties/{property_id}/contacts` - List property contacts
- `GET /contacts/{id}` - Get contact details
- `PUT /contacts/{id}` - Update contact
- `DELETE /contacts/{id}` - Delete contact

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

**Contract categories:**
- Purchase agreements
- Disclosures (lead paint, property condition, seller disclosure)
- Inspection reports
- Title and escrow documents
- Closing documents (deed, bill of sale, settlement statement)
- Special contracts (HOA, condo bylaws, well/septic certification)

#### B. AI-Suggested Contracts
- Claude AI analyzes property details
- Recommends required vs optional contracts
- Provides reasoning for each suggestion
- Based on:
  - State and local regulations
  - Property characteristics
  - Industry best practices
  - Transaction type

#### C. Manual Control
- Override any automatic or AI suggestion
- Mark contracts as required or optional
- Set deadlines for contract completion
- Add custom notes and reasons

**Contract statuses:**
- `DRAFT` - Contract created but not sent
- `SENT` - Sent to signer via DocuSeal
- `IN_PROGRESS` - Partially signed
- `PENDING_SIGNATURE` - Waiting for signatures
- `COMPLETED` - Fully executed
- `CANCELLED` - Cancelled
- `EXPIRED` - Deadline passed
- `ARCHIVED` - Archived in DocuSeal

**DocuSeal integration:**
- Link templates to DocuSeal template IDs
- Track submission IDs
- Store signing URLs
- Automatic status updates via webhooks

**API Endpoints:**
```
# Contract CRUD
POST   /contracts/                                    Create contract
GET    /contracts/{id}                                Get contract
PUT    /contracts/{id}                                Update contract
DELETE /contracts/{id}                                Delete contract

# Property contracts
GET    /properties/{property_id}/contracts            List property contracts
POST   /properties/{property_id}/attach-required      Auto-attach from templates

# Contract readiness
GET    /contracts/property/{property_id}/readiness    Check closing readiness
POST   /contracts/address/readiness                   Check readiness by address (voice)

# AI features
POST   /contracts/property/{property_id}/ai-suggest              AI suggest contracts
POST   /contracts/property/{property_id}/ai-apply-suggestions    Apply AI suggestions
PATCH  /contracts/{contract_id}/mark-required                    Mark as required/optional

# Template management
GET    /contract-templates/                           List templates
POST   /contract-templates/                           Create template
GET    /contract-templates/{id}                       Get template
PUT    /contract-templates/{id}                       Update template
DELETE /contract-templates/{id}                       Delete template
```

**MCP Tools:**
```
check_property_contract_readiness         - Check if ready to close
check_property_contract_readiness_voice   - Voice version with natural response
attach_required_contracts                 - Auto-attach matching templates
ai_suggest_contracts                      - Get AI contract suggestions
apply_ai_contract_suggestions             - Apply AI suggestions (create contracts)
mark_contract_required                    - Manually mark as required/optional
```

**Voice examples:**
- "Is property 5 ready to close?"
- "What contracts are needed for 123 Main Street?"
- "Suggest contracts for property 5 using AI"
- "Apply AI contract suggestions for property 5"
- "Mark contract 10 as required"

---

### 6. DocuSeal Webhook Integration

**Real-time contract status synchronization**

When someone signs a contract in DocuSeal:
1. DocuSeal sends webhook to `POST /webhooks/docuseal`
2. API verifies HMAC-SHA256 signature for security
3. Finds contract by `docuseal_submission_id`
4. Updates contract status in database
5. Regenerates property recap with new information
6. AI agent instantly knows contract is signed

**Supported events:**
- `submission.created` - New submission created
- `submission.signed` - Individual signer completed
- `submission.completed` - All signers completed (contract done)
- `submission.archived` - Submission archived
- `submission.viewed` - Submission viewed by signer

**Security:**
- Webhook signature verification using shared secret
- Constant-time signature comparison
- Environment variable for secret: `DOCUSEAL_WEBHOOK_SECRET`

**Background processing:**
- FastAPI BackgroundTasks for async processing
- Quick 200 OK response to DocuSeal
- Property recap regeneration happens in background

**API Endpoints:**
```
POST /webhooks/docuseal       - Receive DocuSeal webhook events
GET  /webhooks/docuseal/test  - Test webhook configuration
```

**MCP Tools:**
```
test_webhook_configuration - Check webhook setup and get instructions
```

**Setup:**
```bash
# 1. Set secret in Fly.io
fly secrets set DOCUSEAL_WEBHOOK_SECRET=your-secret --app ai-realtor

# 2. Configure in DocuSeal
URL: https://ai-realtor.fly.dev/webhooks/docuseal
Secret: same as DOCUSEAL_WEBHOOK_SECRET
Events: submission.completed, submission.signed, submission.archived
```

---

### 7. AI Property Recaps

**Intelligent property summaries for voice interactions**

Each property gets an AI-generated recap that includes:
- Comprehensive property overview
- Zestimate and market analysis
- Contract status and readiness
- Skip trace information
- Contact details
- Enrichment highlights
- Next steps and recommendations

**Three recap formats:**

1. **Detailed recap** (3-4 paragraphs)
   - For human reading
   - Comprehensive analysis
   - Market insights

2. **Voice summary** (2-3 sentences)
   - For text-to-speech
   - Quick phone call updates
   - Concise key points

3. **Structured context** (JSON)
   - For AI assistants and VAPI
   - All data points organized
   - Easy to parse programmatically

**Automatic regeneration triggers:**
- Contract signed via webhook: `trigger="contract_signed:Purchase Agreement"`
- Property enriched: `trigger="enrichment_updated"`
- Skip trace completed: `trigger="skip_trace_completed"`
- Manual regeneration: `trigger="manual"`

**Versioning:**
- Each recap has version number
- Tracks last trigger
- Timestamps for created/updated

**API Endpoints:**
```
POST /property-recap/property/{property_id}/generate   - Generate/update recap
GET  /property-recap/property/{property_id}            - Get current recap
```

**MCP Tools:**
```
generate_property_recap  - Voice: "Generate recap for property 5"
get_property_recap       - Voice: "Get the recap for property 5"
```

**Example recap:**
```
PROPERTY OVERVIEW:
Beautiful 2-bedroom, 2-bathroom condo at 123 Main St, New York, NY.
Listed at $850,000 with a Zestimate of $875,000 (current market value).

CONTRACTS & READINESS:
Property has 3 required contracts: Purchase Agreement (completed),
Lead Paint Disclosure (pending signature), Property Disclosure (pending).
NOT ready to close - 2 contracts still need signatures.

NEXT STEPS:
1. Follow up on pending disclosures
2. Schedule final walkthrough
3. Coordinate with title company
```

---

### 8. VAPI Phone Call Automation

**AI-powered phone calls with full property context**

Make automated phone calls using VAPI (GPT-4 + 11Labs voice):
- Property updates and information
- Contract signature reminders
- Closing readiness notifications
- Skip trace cold calling
- Custom messages

**Five call types:**

1. **Property Update** (`property_update`)
   - Share comprehensive property details
   - Answer questions about the property
   - Offer to send info via email

2. **Contract Reminder** (`contract_reminder`)
   - Remind about pending contracts
   - Explain what needs attention
   - Offer to resend contract links

3. **Closing Ready** (`closing_ready`)
   - Celebrate all contracts complete
   - Confirm readiness to close
   - Discuss next steps

4. **Specific Contract Reminder** (`specific_contract_reminder`)
   - Call about one specific contract
   - Personalized with contact and contract names
   - Custom message support

5. **Skip Trace Outreach** (`skip_trace_outreach`)
   - Cold call property owner
   - Ask about interest in selling
   - Professional and respectful approach
   - Offer no-obligation market analysis

**VAPI assistant configuration:**
- Voice: Natural, professional female voice (11Labs)
- Model: GPT-4 Turbo for intelligent conversations
- Context: Full property recap included
- First message: Customized based on call type
- Max duration: 10 minutes
- Recording: Enabled for all calls

**Phone number requirements:**
- Must be in E.164 format: `+14155551234`
- Country code required
- Validates format before calling

**API Endpoints:**
```
POST /property-recap/property/{property_id}/call              - Make property call
POST /property-recap/property/{property_id}/call/contact      - Call specific contact
POST /property-recap/contact/{contact_id}/call/contract       - Call about contract
```

**MCP Tools:**
```
make_property_phone_call         - Basic property call
call_contact_about_contract      - Call contact about specific contract
call_property_owner_skip_trace   - Cold call owner about selling
```

**Voice examples:**
- "Call John at +14155551234 about property 5"
- "Call contact 3 about the Purchase Agreement that needs signature"
- "Call the owner of property 5 and ask if they want to sell"
- "Make a cold call to the property owner and mention we have buyers interested"

**Setup:**
```bash
# Set VAPI API key
fly secrets set VAPI_API_KEY=your-vapi-key --app ai-realtor
```

---

### 9. Real-time Activity Feed

**Live event tracking and notifications**

Track all important events in real-time:
- Property created/updated/deleted
- Enrichment completed
- Skip trace completed
- Contracts created/signed/completed
- Phone calls made
- MCP tool executions
- AI agent interactions

**WebSocket integration:**
- Real-time updates to frontend
- Connection manager for multiple clients
- Broadcast events to all connected clients

**Activity event structure:**
```json
{
  "id": 123,
  "event_type": "property_created",
  "tool_name": "create_property",
  "user_source": "Claude Desktop MCP",
  "description": "Created property at 123 Main St",
  "status": "success",
  "duration_ms": 1234,
  "metadata": {
    "property_id": 5,
    "address": "123 Main St"
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Event types:**
- `property_created`, `property_enriched`, `property_deleted`
- `skip_trace_completed`
- `contract_created`, `contract_signed`, `contract_completed`
- `contact_added`
- `phone_call_initiated`
- `tool_call` (MCP tool execution)

**API Endpoints:**
```
GET /activities/                - List activity events (paginated)
GET /activities/{id}            - Get specific event
POST /activities/log            - Log new activity
PATCH /activities/{id}          - Update activity status
```

**WebSocket endpoint:**
```
ws://localhost:8000/ws          - WebSocket connection for real-time updates
```

**Display command endpoint:**
```
POST /display/command           - Send commands to TV display
```

**Commands:**
- `{"action": "show_property", "property_id": 3}`
- `{"action": "agent_speak", "message": "Welcome!"}`
- `{"action": "close_detail"}`

---

### 10. Compliance Engine

**AI-powered real estate compliance checking**

Ensures all transactions comply with:
- Federal regulations (RESPA, TILA, Fair Housing Act)
- State-specific laws
- Local ordinances
- Industry best practices

**Compliance checks:**
- Property disclosures required by state
- Contract completeness
- Deadline compliance
- Document retention requirements
- Anti-discrimination compliance
- Data privacy (GDPR, CCPA)

**Knowledge base:**
- Federal regulations in markdown
- State-specific requirements
- Real estate best practices
- Regular updates for law changes

**API Endpoints:**
```
POST /compliance/check          - Run compliance check on property
GET /compliance/requirements    - Get requirements for state/type
```

**Compliance categories:**
- Disclosures
- Contracts
- Deadlines
- Documentation
- Fair Housing
- Data Privacy

---

### 11. Agent Preferences

**Personalized settings per agent**

Customize behavior for each agent:
- Auto-enrich properties on creation
- Preferred contract templates
- Default notification settings
- Communication preferences

**API Endpoints:**
```
GET /agent-preferences/{agent_id}     - Get preferences
PUT /agent-preferences/{agent_id}     - Update preferences
```

---

### 12. ToDo Management

**Task tracking for properties**

Create and manage tasks:
- Property-specific todos
- Deadlines and priorities
- Status tracking (pending, completed)
- Agent assignment

**API Endpoints:**
```
POST /properties/{property_id}/todos  - Create todo
GET /properties/{property_id}/todos   - List todos
PUT /todos/{id}                        - Update todo
DELETE /todos/{id}                     - Delete todo
```

---

## MCP (Model Context Protocol) Integration

**Full voice control via Claude Desktop**

All features accessible through natural language via MCP server:

**Property Tools:** (6)
- `list_properties`, `get_property`, `create_property`
- `delete_property`, `enrich_property`, `skip_trace_property`

**Contact Tools:** (1)
- `add_contact`

**Contract Tools:** (6)
- `check_property_contract_readiness`
- `check_property_contract_readiness_voice`
- `attach_required_contracts`
- `ai_suggest_contracts`
- `apply_ai_contract_suggestions`
- `mark_contract_required`

**Recap & Call Tools:** (5)
- `generate_property_recap`
- `get_property_recap`
- `make_property_phone_call`
- `call_contact_about_contract`
- `call_property_owner_skip_trace`

**Webhook Tools:** (1)
- `test_webhook_configuration`

**Utility Tools:** (1)
- `send_notification`

**Total: 20 MCP tools** for complete voice control

**Natural language examples:**
- "Create a property at 123 Main St, New York for $850,000 with 2 bedrooms"
- "Enrich property 5 with Zillow data and generate a recap"
- "Is the property at 123 Main Street ready to close?"
- "Call John about the Purchase Agreement that needs his signature"
- "Skip trace property 5 and call the owner to ask if they want to sell"
- "What contracts are required for this property based on AI analysis?"

---

## Technology Stack

**Backend:**
- FastAPI (Python 3.11)
- PostgreSQL (via Fly.io)
- SQLAlchemy ORM
- Alembic migrations
- Pydantic validation

**AI & ML:**
- Anthropic Claude Sonnet 4 (contract analysis, recaps)
- GPT-4 Turbo (VAPI phone calls)

**External APIs:**
- Google Places API (address lookup)
- Zillow API (property enrichment)
- Skip Trace API (owner discovery)
- DocuSeal API (e-signatures)
- VAPI API (phone calls)

**Voice & Communication:**
- MCP Server (Claude Desktop integration)
- VAPI (voice AI platform)
- 11Labs (text-to-speech)
- WebSocket (real-time updates)

**Deployment:**
- Fly.io (cloud hosting)
- Docker containers
- Depot (fast builds)
- PostgreSQL on Fly.io

**Security:**
- HMAC-SHA256 webhook signatures
- Environment variable secrets
- CORS middleware
- Input validation

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
│            20 Tools for Voice Control                        │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP API
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Routers: Properties, Contracts, Webhooks, Recaps     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Services: AI, VAPI, Enrichment, Skip Trace          │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Models: Property, Contract, Contact, Recap, etc.    │   │
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
│  • contacts        │    │  • VAPI                         │
│  • recaps          │    │  • Anthropic Claude             │
│  • templates       │    └─────────────────────────────────┘
│  • activities      │
│  • enrichments     │
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
- `contacts` - Buyers, sellers, agents
- `contracts` - Contract documents
- `contract_templates` - Reusable templates
- `skip_traces` - Owner contact info
- `zillow_enrichments` - Zillow data
- `property_recaps` - AI-generated summaries
- `activity_events` - Event log
- `todos` - Tasks
- `agent_preferences` - Agent settings

**Relationships:**
- Property → many Contracts
- Property → many Contacts
- Property → one ZillowEnrichment
- Property → one SkipTrace
- Property → one PropertyRecap
- Property → many ActivityEvents
- Contract → one Property
- Contract → one Contact (signer)
- ContractTemplate → many Contracts

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Google Places
GOOGLE_PLACES_API_KEY=your-key

# Zillow
ZILLOW_API_KEY=your-key

# Skip Trace
SKIP_TRACE_API_KEY=your-key

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-your-key

# DocuSeal
DOCUSEAL_API_KEY=your-key
DOCUSEAL_WEBHOOK_SECRET=your-webhook-secret

# VAPI
VAPI_API_KEY=your-vapi-key
VAPI_PHONE_NUMBER=+14155551234
```

---

## API Documentation

**Interactive docs:** https://ai-realtor.fly.dev/docs

**Swagger UI:** Full API documentation with try-it-out functionality

**ReDoc:** https://ai-realtor.fly.dev/redoc

---

## Deployment

**Platform:** Fly.io

**Commands:**
```bash
# Deploy
fly deploy

# Set secrets
fly secrets set KEY=value --app ai-realtor

# View logs
fly logs --app ai-realtor

# SSH into instance
fly ssh console --app ai-realtor

# Scale
fly scale count 2 --app ai-realtor

# Database
fly postgres connect -a ai-realtor-db
```

**Configuration:** `fly.toml`

**Docker:** Multi-stage build for optimization

---

## Getting Started

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/ai-realtor.git
cd ai-realtor
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Run Database Migrations
```bash
alembic upgrade head
```

### 5. Seed Contract Templates
```bash
python seed_contract_templates.py
```

### 6. Start Server
```bash
uvicorn app.main:app --reload
```

### 7. Start MCP Server (for voice)
```bash
python mcp_server/property_mcp.py
```

### 8. Configure Claude Desktop
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

---

## Use Cases

### 1. New Property Workflow
```
Voice: "Create property at 123 Main St, Brooklyn, NY for $650,000 with 2 bedrooms"
      ↓
Voice: "Enrich it with Zillow data"
      ↓
Voice: "Skip trace to find the owner"
      ↓
Voice: "Attach required contracts based on AI analysis"
      ↓
Voice: "Generate a recap"
      ↓
Voice: "Call the owner and ask if they're interested in selling"
```

### 2. Contract Management
```
Voice: "What contracts are required for property 5?"
      ↓
Voice: "AI suggest contracts for this property"
      ↓
Voice: "Apply the AI suggestions"
      ↓
Voice: "Is the property ready to close?"
      ↓
[DocuSeal webhook fires when contract signed]
      ↓
AI agent: "Great news! The Purchase Agreement was just signed!"
```

### 3. Lead Generation
```
Voice: "Skip trace property 8"
      ↓
Voice: "Generate a recap with market analysis"
      ↓
Voice: "Call the owner and mention we have buyers interested in the area"
      ↓
[VAPI makes intelligent cold call with full context]
```

---

## Recent Updates

**Latest features:**
- ✅ DocuSeal webhook integration for real-time contract updates
- ✅ AI property recaps with three output formats
- ✅ VAPI phone call automation with 5 call types
- ✅ Context-aware contract templates with AI suggestions
- ✅ Three-tier contract requirement system
- ✅ WebSocket real-time activity feed
- ✅ MCP tools expanded to 20 total
- ✅ Background task processing for webhooks
- ✅ Comprehensive documentation

---

## Future Roadmap

**Planned features:**
- [ ] SMS notifications via Twilio
- [ ] Email campaign automation
- [ ] AI-powered property valuation models
- [ ] Market trend analysis and predictions
- [ ] CRM integration (Salesforce, HubSpot)
- [ ] Mobile app (React Native)
- [ ] Scheduled phone call campaigns
- [ ] Multi-language support
- [ ] Advanced reporting and analytics
- [ ] Video property tours with AI narration
- [ ] Blockchain-based contract verification
- [ ] AI negotiation assistant

---

## Documentation Files

- `README.md` - Project overview and setup
- `CONTEXT_AWARE_CONTRACTS.md` - Contract system documentation
- `AI_RECAP_PHONE_CALLS.md` - Recap and VAPI documentation
- `DOCUSEAL_WEBHOOK.md` - Webhook integration guide
- `claude.md` - This complete feature guide

---

## Support

**Issues:** https://github.com/yourusername/ai-realtor/issues
**Documentation:** https://ai-realtor.fly.dev/docs
**API Status:** https://ai-realtor.fly.dev/

---

## License

MIT License - See LICENSE file for details

---

**Built with ❤️ using Claude Code**

Generated with [Claude Code](https://claude.com/claude-code)
via [Happy](https://happy.engineering)
