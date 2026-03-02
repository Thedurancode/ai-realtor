# Key Files Reference - File Paths & Quick Links

## Core Application Files

### Entry Point
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/main.py`
- **Purpose:** FastAPI application initialization and router registration
- **Key Lines:** Registers all routers (agents, properties, contracts, etc.)

### Configuration
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/config.py`
- **Purpose:** Settings management (API keys, external service URLs)
- **Variables:** GOOGLE_PLACES_API_KEY, DOCUSEAL_API_KEY, RESEND_API_KEY, FROM_EMAIL

### Database Setup
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/database.py`
- **Purpose:** SQLAlchemy configuration and database session management
- **Uses:** SQLite (development)

---

## Database Models

### Agent
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/models/agent.py`
- **Table:** `agents`
- **Fields:** id, email, name, phone, license_number, created_at, updated_at

### Property
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/models/property.py`
- **Table:** `properties`
- **Fields:** id, title, address, city, state, zip_code, price, bedrooms, bathrooms, property_type, status, agent_id
- **Enums:** PropertyStatus (available, pending, sold, rented, off_market), PropertyType (house, apartment, condo, townhouse, land, commercial)

### Contact
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/models/contact.py`
- **Table:** `contacts`
- **Fields:** id, property_id, name, email, phone, role
- **Enum:** ContactRole (buyer, seller, lawyer, contractor, inspector, appraiser, lender, tenant, landlord, property_manager, handyman, plumber, electrician)

### Contract
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/models/contract.py`
- **Table:** `contracts`
- **Fields:** id, property_id, contact_id, name, description, docuseal_template_id, docuseal_submission_id, docuseal_url, status, sent_at, completed_at
- **Enum:** ContractStatus (draft, sent, in_progress, completed, cancelled, expired)

### ContractSubmitter
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/models/contract_submitter.py`
- **Table:** `contract_submitters`
- **Fields:** id, contract_id, name, email, role, status, signing_order, docuseal_submitter_id, sent_at, opened_at, completed_at
- **Enum:** SubmitterStatus (pending, opened, completed, declined)
- **Purpose:** Tracks individual signers on contracts

### Todo
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/models/todo.py`
- **Table:** `todos`
- **Fields:** id, property_id, agent_id, title, description, status, due_date, priority

### SkipTrace
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/models/skip_trace.py`
- **Table:** `skip_traces`
- **Purpose:** Stores skip tracing results for property owners

---

## API Routes / Endpoints

### Agents Router
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/routers/agents.py`
- **Prefix:** `/agents`
- **Endpoints:**
  - `POST /` - Create agent
  - `GET /` - List all agents
  - `GET /{agent_id}` - Get agent by ID
  - `PATCH /{agent_id}` - Update agent
  - `DELETE /{agent_id}` - Delete agent

### Properties Router (Voice-Enabled)
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/routers/properties.py`
- **Prefix:** `/properties`
- **Key Endpoints:**
  - `POST /` - Create property
  - `POST /voice` - **Create property from voice input** (Line 32)
  - `GET /` - List properties
  - `GET /{property_id}` - Get property details
  - `PATCH /{property_id}` - Update property

### Contacts Router (Voice-Enabled)
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/routers/contacts.py`
- **Prefix:** `/contacts`
- **Key Endpoints:**
  - `POST /` - Create contact
  - `POST /voice` - **Create contact from voice input** (voice role parsing)
  - `GET /property/{property_id}` - List contacts for property
  - `GET /property/{property_id}/{role}` - Get contacts by role (voice-friendly)

### Contracts Router (Voice-Enabled)
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/routers/contracts.py`
- **Prefix:** `/contracts`
- **Key Voice Endpoints:**
  - `POST /voice/send` - **Send contract using natural language** (Line 18+)
  - `POST /voice/send-multi-party` - **Send to multiple signers** (voice)
- **Status Endpoints:**
  - `GET /property/{property_id}` - List contracts for property
  - `GET /{contract_id}/status` - Get contract with signers (refresh from DocuSeal)
  - `POST /{contract_id}/send-to-contact` - Send single
  - `POST /{contract_id}/send-multi-party` - Send multiple

### Address Router (Voice-Friendly)
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/routers/address.py`
- **Endpoints:**
  - `POST /suggest` - Address autocomplete with voice-friendly responses

### Todos Router
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/routers/todos.py`
- **Endpoints:** Create, read, update, delete tasks

### SkipTrace Router
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/routers/skip_trace.py`
- **Endpoints:** Skip tracing lookups

### Agent Preferences Router
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/routers/agent_preferences.py`
- **Endpoints:** Agent settings management

---

## Request/Response Schemas

All schemas are in `/Users/edduran/Documents/GitHub/ai-realtor/app/schemas/`

### Agent Schema
- **File:** `/app/schemas/agent.py`
- **Classes:** AgentBase, AgentCreate, AgentUpdate, AgentResponse

### Property Schema
- **File:** `/app/schemas/property.py`
- **Classes:** PropertyCreate, PropertyCreateFromVoice, PropertyResponse, PropertyCreateFromVoiceResponse

### Contact Schema
- **File:** `/app/schemas/contact.py`
- **Classes:** ContactCreate, ContactCreateFromVoiceResponse

### Contract Schema
- **File:** `/app/schemas/contract.py`
- **Classes:** ContractCreate, ContractResponse, ContractSendRequest, **ContractSendVoiceRequest** (Line 18)
- **Important:** ContractStatusResponse includes submitters array

### ContractSubmitter Schema
- **File:** `/app/schemas/contract_submitter.py`
- **Classes:** MultiPartyContractRequest, **MultiPartyVoiceRequest**, MultiPartyContractResponse
- **Purpose:** Multi-signer contract data structures

### Address Schema
- **File:** `/app/schemas/address.py`
- **Classes:** AddressSuggestion, AddressSuggestionResponse

---

## External Service Integrations

### DocuSeal Service
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/services/docuseal.py`
- **Purpose:** Contract signing via DocuSeal platform
- **Key Functions:**
  - `create_submission()` - Send contract to signers
  - `get_submission_status()` - Fetch signer status
  - `list_templates()` - Get available templates
- **Uses:** Self-hosted DocuSeal instance

### Resend Service
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/services/resend_service.py`
- **Purpose:** Email notifications for contracts
- **Key Functions:**
  - `send_multi_party_notification()` - Email notification
  - `send_contract_notification()` - Single signer email
- **Uses:** Resend API for reliable email delivery

### Google Places Service
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/services/google_places.py`
- **Purpose:** Address autocomplete and validation
- **Key Functions:**
  - `get_place_suggestions()` - Address search
  - `get_place_details()` - Full address details

### Skip Trace Service
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/app/services/skip_trace.py`
- **Purpose:** Skip tracing for property lookups
- **Uses:** External skip tracing API

---

## Documentation Files

### Voice Commands Guide
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/VOICE_COMMANDS.md`
- **Content:** Complete examples of voice endpoints and usage

### Integration Complete Status
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/INTEGRATION_COMPLETE.md`
- **Content:** Current system status, configuration, test results

### DocuSeal Integration
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/DOCUSEAL_INTEGRATION.md`
- **Content:** Contract signing system setup and details

### Multi-Party Contracts
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/MULTI_PARTY_CONTRACTS.md`
- **Content:** Multiple signer workflow and examples

### Webhook Setup
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/WEBHOOK_SETUP.md`
- **Content:** Real-time contract status updates via webhooks

### Test Results
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/TEST_RESULTS.md`
- **Content:** System testing summary

---

## Configuration & Environment

### Environment Variables
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/.env`
- **Variables:**
  - GOOGLE_PLACES_API_KEY
  - DOCUSEAL_API_KEY
  - DOCUSEAL_API_URL
  - RESEND_API_KEY
  - FROM_EMAIL
  - FROM_NAME

### Python Dependencies
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/requirements.txt`
- **Key Packages:**
  - fastapi >= 0.115.0
  - uvicorn >= 0.32.0
  - sqlalchemy >= 2.0.36
  - pydantic >= 2.10.0
  - aiosqlite >= 0.20.0
  - httpx >= 0.28.0
  - resend >= 2.21.0

---

## Database

### SQLite Database File
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/realtor.db`
- **Type:** SQLite 3
- **Tables:** agents, properties, contracts, contract_submitters, contacts, todos, skip_traces, agent_preferences

### Database Backups
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/realtor.db.backup`
- **File:** `/Users/edduran/Documents/GitHub/ai-realtor/realtor.db.backup-multi-party`

---

## Test Scripts

These are Python scripts for testing the system:

- **`scripts/manual/send_test_contract.py`** - Test contract sending via DocuSeal
- **`tests/manual/test_docuseal_api.py`** - Test DocuSeal API connection
- **`tests/manual/test_resend_email.py`** - Test email sending
- **`tests/manual/test_webhook.py`** - Test webhook integration
- **`tests/manual/test_complete_multiparty.py`** - Test multi-signer workflow
- **`tests/manual/simple_multi_party_test.py`** - Simple multi-party test
- **`scripts/manual/diagnose_docuseal.py`** - Diagnostic tool for DocuSeal issues
- **`scripts/manual/get_docuseal_templates.py`** - Fetch available DocuSeal templates

---

## Project Structure Summary

```
/Users/edduran/Documents/GitHub/ai-realtor/
├── app/
│   ├── main.py                          # App entry point
│   ├── config.py                        # Settings
│   ├── database.py                      # DB setup
│   │
│   ├── models/
│   │   ├── agent.py
│   │   ├── property.py
│   │   ├── contact.py
│   │   ├── contract.py
│   │   ├── contract_submitter.py
│   │   ├── todo.py
│   │   └── skip_trace.py
│   │
│   ├── schemas/
│   │   ├── agent.py
│   │   ├── property.py
│   │   ├── contact.py
│   │   ├── contract.py
│   │   ├── contract_submitter.py
│   │   ├── address.py
│   │   ├── skip_trace.py
│   │   ├── todo.py
│   │   └── agent_preference.py
│   │
│   ├── routers/
│   │   ├── agents.py
│   │   ├── properties.py           (includes /voice endpoint)
│   │   ├── contacts.py             (includes /voice endpoint)
│   │   ├── contracts.py            (includes /voice endpoints)
│   │   ├── address.py              (voice-friendly)
│   │   ├── todos.py
│   │   ├── skip_trace.py
│   │   └── agent_preferences.py
│   │
│   └── services/
│       ├── docuseal.py             # Contract signing
│       ├── resend_service.py       # Email notifications
│       ├── google_places.py        # Address autocomplete
│       └── skip_trace.py           # Skip tracing
│
├── realtor.db                       # SQLite database
├── requirements.txt                 # Dependencies
│
├── Documentation/
│   ├── CODEBASE_STRUCTURE.md       # This document
│   ├── TV_DISPLAY_GUIDE.md         # TV display implementation guide
│   ├── VOICE_COMMANDS.md           # Voice endpoint examples
│   ├── INTEGRATION_COMPLETE.md     # System status
│   ├── DOCUSEAL_INTEGRATION.md     # Contract system
│   ├── MULTI_PARTY_CONTRACTS.md    # Multi-signer workflow
│   └── WEBHOOK_SETUP.md            # Real-time updates
│
├── scripts/
│   ├── manual/                     # One-off utilities and admin scripts
│   ├── migrations/                 # Manual migration helpers
│   ├── seeds/                      # Seed data scripts
│   └── setup/                      # Environment/bootstrap setup scripts
│
├── examples/
│   ├── data/                       # Sample CSV fixtures
│   ├── output/                     # Generated example outputs
│   └── web/                        # Standalone HTML prototypes
│
└── tests/
    ├── manual/                     # Ad hoc/manual test scripts
    └── ...
```

---

## How to Navigate

### To Understand Voice Commands
1. Start: `/VOICE_COMMANDS.md`
2. Implementation: `/app/routers/contracts.py` (voice endpoints)
3. Request/Response: `/app/schemas/contract.py` (ContractSendVoiceRequest)

### To Understand Data Models
1. Database schemas: `/app/models/`
2. Request/response format: `/app/schemas/`
3. API routes: `/app/routers/`

### To Build TV Display
1. Read: `/TV_DISPLAY_GUIDE.md`
2. API endpoints: `/app/routers/contracts.py`, `/properties.py`, `/contacts.py`
3. Data available: `/app/models/contract.py` (ContractSubmitter array)

### To Setup Development Environment
1. Install dependencies: `pip install -r requirements.txt`
2. Configure `.env` file with API keys
3. Run: `python -m uvicorn app.main:app --reload`
4. Visit: `http://localhost:8000/docs`

### To Add New Features
1. Create model in `/app/models/`
2. Create schema in `/app/schemas/`
3. Create router in `/app/routers/`
4. Register router in `/app/main.py`

---

## Key Lines of Code Reference

### Voice Endpoints for Contracts
- **File:** `/app/routers/contracts.py`
- **Line:** ~18+ - Voice request schemas definition
- **Search:** Look for `ContractSendVoiceRequest` and `@router.post("/voice/send")`

### Voice Endpoint for Properties
- **File:** `/app/routers/properties.py`
- **Line:** 32 - `@router.post("/voice")` endpoint

### Voice Endpoint for Contacts
- **File:** `/app/routers/contacts.py`
- **Search:** `@router.post("/voice")` - Create contact from voice

### Contract with Multiple Signers
- **File:** `/app/models/contract_submitter.py`
- **Key Field:** `contract.submitters` - Array of individual signers

### Status Tracking for TV Display
- **File:** `/app/models/contract_submitter.py`
- **Fields:** `sent_at`, `opened_at`, `completed_at`, `status`

---

## Next Steps for TV Display Development

1. **Read**: `TV_DISPLAY_GUIDE.md` for complete implementation steps
2. **Create**: New frontend folder (e.g., `/frontend`) with Next.js
3. **Connect**: To API endpoints in `/app/routers/`
4. **Display**: Contract status from `/contracts/{id}/status` endpoint
5. **Refresh**: Every 30 seconds using polling pattern
6. **Optimize**: For large TV screens (fonts, colors, spacing)
