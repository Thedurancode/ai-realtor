# AI Realtor Codebase Structure - TV Display Component Guide

## Executive Summary

This is a **FastAPI-based backend** (Python) for a real estate agent management system. It's primarily a **REST API** with integrated voice commands, contract management via DocuSeal, and email notifications via Resend.

**Key Point:** There is NO frontend/UI currently built. The project is API-only, designed to work with voice AI assistants and will eventually need a UI.

---

## 1. Framework & Technology Stack

### Backend Framework: **FastAPI**
- **Version:** FastAPI >= 0.115.0
- **Server:** Uvicorn >= 0.32.0
- **Location:** `/Users/edduran/Documents/GitHub/ai-realtor/app/`

### Database
- **Type:** SQLite (development)
- **File:** `realtor.db`
- **ORM:** SQLAlchemy >= 2.0.36
- **Async Support:** aiosqlite >= 0.20.0

### Validation & Schemas
- **Pydantic:** >= 2.10.0 (with email validation)
- **Pydantic Settings:** >= 2.7.0 (environment variable management)

### External Services Integration
- **DocuSeal:** Self-hosted e-signature platform (contract signing)
- **Resend:** Email service for notifications
- **Google Places API:** Address autocomplete and validation

### Core Dependencies
```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
sqlalchemy>=2.0.36
pydantic[email]>=2.10.0
pydantic-settings>=2.7.0
aiosqlite>=0.20.0
python-multipart>=0.0.20
httpx>=0.28.0
python-dateutil>=2.9.0
resend>=2.21.0
```

**No frontend framework (Next.js, React, Vue, etc.) is currently set up.**

---

## 2. Voice Agent/AI Agent Code Location

### Voice-First API Design
The system is designed to be consumed by **external voice AI assistants**. It doesn't contain the AI/LLM code itself, but provides voice-optimized endpoints.

### Voice Endpoints Implemented:
1. **`POST /contracts/voice/send`** - Send contracts using natural language
2. **`POST /contracts/voice/send-multi-party`** - Send to multiple signers
3. **`POST /properties/voice`** - Create properties from voice input
4. **`POST /contacts/voice`** - Create contacts from voice input
5. **`POST /address/suggest`** - Address autocomplete (voice-friendly)

### How It Works:
1. External AI assistant (like voice AI) parses user speech
2. Extracts parameters (e.g., address, contact role, contract name)
3. Sends HTTP POST to a voice endpoint
4. API returns `voice_confirmation` string that AI can read back to user

### Example Voice Flow:
```
User: "Send the property agreement to the lawyer for 141 throop"
     ↓
AI Assistant (external):
  - Parses speech
  - Extracts: address="141 throop", contract="property agreement", role="lawyer"
  - Calls: POST /contracts/voice/send {address_query, contract_name, contact_role}
     ↓
API Response:
  voice_confirmation: "Done! I've sent the Property Agreement to John Lawyer 
                      (lawyer) at john@lawfirm.com for 123 Main Street."
     ↓
AI reads response back to user
```

### Voice-Related Code Files:
- `/app/routers/contracts.py` - Line 18: `ContractSendVoiceRequest`, voice endpoint handlers
- `/app/routers/properties.py` - Line 32: Voice property creation
- `/app/routers/contacts.py` - Voice contact creation with role aliases
- `/app/routers/address.py` - Voice-friendly address suggestions

---

## 3. Current UI Structure

### Current State: **NO UI BUILT**

This is important for your TV display project. The system currently:
- ✅ Has a **REST API** (documented in FastAPI /docs)
- ✅ Has **voice endpoints** ready to consume
- ❌ Has **NO web/mobile/desktop UI**
- ❌ Has **NO real-time display component**
- ❌ Has **NO WebSocket/SSE streams**

### API Documentation Available At:
```
http://localhost:8000/docs  (Swagger UI)
```

### For Your TV Display:
You'll need to build this from scratch using any frontend framework. You can use:
- **Next.js + React** (modern choice)
- **React + TypeScript** (lighter)
- **Vue** (alternative)
- **Svelte** (lightweight)
- **Plain HTML/JavaScript** (minimal)

---

## 4. Voice/Audio Integration Status

### Audio Input: ❌ **NOT IMPLEMENTED**
- No speech-to-text
- No microphone access
- No audio codec support

### Audio Output: ❌ **NOT IMPLEMENTED**
- No text-to-speech
- No audio streaming
- No WebSocket audio support

### How to Add Audio:
The system is designed to work with **external audio services**:
1. External service handles speech-to-text (e.g., OpenAI Whisper, Google Speech-to-Text)
2. Sends text parameters to API endpoints
3. Receives `voice_confirmation` text back
4. External service converts text-to-speech

### Related Documentation:
- `/VOICE_COMMANDS.md` - Complete voice command guide
- `/INTEGRATION_COMPLETE.md` - Current system capabilities

---

## 5. Project Structure & Key Files

### Directory Layout:
```
/Users/edduran/Documents/GitHub/ai-realtor/
├── app/
│   ├── main.py                 # FastAPI app initialization
│   ├── config.py              # Settings (API keys, URLs)
│   ├── database.py            # SQLAlchemy setup
│   │
│   ├── models/                # Database models
│   │   ├── agent.py           # Real estate agent
│   │   ├── property.py        # Property listing
│   │   ├── contact.py         # Contact (buyer, seller, lawyer, etc.)
│   │   ├── contract.py        # Contract document
│   │   ├── contract_submitter.py  # Individual signer
│   │   ├── todo.py            # Task management
│   │   └── skip_trace.py      # Skip tracing service
│   │
│   ├── schemas/               # Pydantic request/response schemas
│   │   ├── agent.py
│   │   ├── property.py
│   │   ├── contact.py
│   │   ├── contract.py
│   │   ├── contract_submitter.py
│   │   └── address.py
│   │
│   ├── routers/               # API endpoints (grouped by domain)
│   │   ├── agents.py          # POST/GET /agents/*
│   │   ├── properties.py      # POST/GET /properties/* (includes voice)
│   │   ├── contacts.py        # POST/GET /contacts/* (includes voice)
│   │   ├── contracts.py       # POST/GET /contracts/* (includes voice)
│   │   ├── address.py         # POST /address/suggest
│   │   ├── todos.py           # Task management
│   │   ├── skip_trace.py      # Skip tracing
│   │   └── agent_preferences.py  # Agent settings
│   │
│   └── services/              # External service integrations
│       ├── docuseal.py        # Contract signing integration
│       ├── resend_service.py  # Email notifications
│       ├── google_places.py   # Address autocomplete
│       └── skip_trace.py      # Skip tracing service
│
├── requirements.txt           # Python dependencies
├── realtor.db                # SQLite database (development)
│
└── Documentation/
    ├── VOICE_COMMANDS.md      # Voice API examples
    ├── INTEGRATION_COMPLETE.md # Current system status
    ├── DOCUSEAL_INTEGRATION.md # Contract system
    ├── MULTI_PARTY_CONTRACTS.md # Multi-signer workflow
    └── WEBHOOK_SETUP.md       # Real-time updates
```

---

## 6. Core Data Models (For TV Display)

### Agent
```python
- id: int (primary key)
- email: str (unique)
- name: str
- phone: str (optional)
- license_number: str (optional)
- created_at: datetime
- updated_at: datetime
- properties: list[Property]  # Relationships
- preferences: list[AgentPreference]
```

### Property
```python
- id: int
- title: str
- description: str (optional)
- address: str
- city, state, zip_code: str
- price: float
- bedrooms, bathrooms: int/float
- square_feet, lot_size: int/float
- year_built: int
- property_type: enum (house, apartment, condo, townhouse, land, commercial)
- status: enum (available, pending, sold, rented, off_market)
- agent_id: int (foreign key)
- created_at, updated_at: datetime
- agent: Agent  # Relationship
- contacts: list[Contact]
- contracts: list[Contract]
- todos: list[Todo]
```

### Contact
```python
- id: int
- property_id: int (foreign key)
- name: str
- email: str
- phone: str (optional)
- role: enum (buyer, seller, lawyer, contractor, inspector, appraiser, lender, tenant, landlord, property_manager, handyman, plumber, electrician)
- created_at, updated_at: datetime
- property: Property  # Relationship
- contracts: list[Contract]
```

### Contract
```python
- id: int
- property_id: int (foreign key)
- contact_id: int (optional, foreign key)
- name: str
- description: str (optional)
- docuseal_template_id: str
- docuseal_submission_id: str
- docuseal_url: str
- status: enum (draft, sent, in_progress, completed, cancelled, expired)
- sent_at, completed_at: datetime
- created_at, updated_at: datetime
- property: Property  # Relationship
- contact: Contact  # Relationship
- submitters: list[ContractSubmitter]  # Multiple signers
```

### ContractSubmitter (Individual Signer)
```python
- id: int
- contract_id: int (foreign key)
- name: str
- email: str
- role: str (First Party, Second Party, etc.)
- status: enum (pending, opened, completed, declined)
- signing_order: int
- docuseal_submitter_id: str
- docuseal_submitter_slug: str
- sent_at, opened_at, completed_at: datetime
- created_at, updated_at: datetime
- contract: Contract  # Relationship
```

### Todo (Task)
```python
- id: int
- property_id: int (foreign key)
- agent_id: int (foreign key)
- title: str
- description: str
- status: enum (pending, in_progress, completed)
- due_date: datetime
- priority: enum (low, medium, high)
- created_at, updated_at: datetime
```

---

## 7. API Endpoints Summary (For TV Display Integration)

### Agents
```
GET /agents/                    # List all agents
GET /agents/{agent_id}          # Get agent details
POST /agents/                   # Create agent
PATCH /agents/{agent_id}        # Update agent
DELETE /agents/{agent_id}       # Delete agent
```

### Properties
```
GET /properties/                # List all properties
GET /properties/{property_id}   # Get property details
POST /properties/               # Create property
POST /properties/voice          # Create from voice input
PATCH /properties/{property_id} # Update property
DELETE /properties/{property_id}# Delete property
```

### Contacts
```
GET /contacts/                  # List all contacts
POST /contacts/                 # Create contact
POST /contacts/voice            # Create from voice
GET /contacts/property/{id}     # Get contacts for property
GET /contacts/property/{id}/{role} # Get contacts by role
```

### Contracts
```
GET /contracts/property/{id}    # List contracts for property
POST /contracts/                # Create contract
POST /contracts/voice/send      # Voice: send single contract
POST /contracts/voice/send-multi-party # Voice: send to multiple
GET /contracts/{id}/status      # Get contract status
POST /contracts/{id}/send-to-contact # Send to single contact
POST /contracts/{id}/send-multi-party # Send to multiple contacts
```

### Address (For Autocomplete)
```
POST /address/suggest           # Get address suggestions
GET /address/                   # Validate/search addresses
```

### Additional
```
GET /todos/                     # List tasks
GET /address/suggest            # Voice-friendly address suggestions
```

---

## 8. Key Information for TV Display Component

### What You'll Need to Display:

#### Dashboard View
- [ ] Agent information (name, email, license)
- [ ] List of properties with status
- [ ] Active contracts and their status
- [ ] Recent activities/tasks
- [ ] Signing progress (% complete)

#### Real-Time Updates Needed
- [ ] Contract status changes (sent → opened → completed)
- [ ] Signer status updates (pending → completed/declined)
- [ ] New contracts sent
- [ ] Task updates

#### Current Status Tracking
- Database has: `sent_at`, `opened_at`, `completed_at` timestamps
- Status fields: `draft`, `sent`, `in_progress`, `completed`, `cancelled`, `expired`
- Individual signer tracking with timestamps

#### Missing for Real-Time Display
- ❌ WebSocket support (for live updates)
- ❌ Server-Sent Events (SSE) streaming
- Need to implement polling or WebSocket layer

### Recommended TV Display Features

1. **Contract Status Board**
   - Show contracts by status (Sent, Pending, Completed)
   - Display signer names and current status
   - Show signing order (sequential/parallel)

2. **Property Dashboard**
   - Properties by agent
   - Filter by status (available, pending, sold)
   - Quick metrics (total price, avg days on market)

3. **Real-Time Notifications**
   - New contracts sent
   - Signers opening documents
   - Documents completed/declined
   - Timestamps of each action

4. **Agent Activity**
   - Recent actions
   - Contracts sent today
   - Task completion rate

---

## 9. Running the API Server

### Start Development Server:
```bash
cd /Users/edduran/Documents/GitHub/ai-realtor
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation:
```
http://localhost:8000/docs          # Swagger UI
http://localhost:8000/redoc         # ReDoc documentation
```

### Test Voice Command:
```bash
curl -X POST http://localhost:8000/contracts/voice/send \
  -H "Content-Type: application/json" \
  -d '{
    "address_query": "141 throop",
    "contract_name": "property agreement",
    "contact_role": "lawyer"
  }'
```

---

## 10. Environment Configuration

### Required Environment Variables (.env file)
```
GOOGLE_PLACES_API_KEY=your_key
DOCUSEAL_API_KEY=jnTC1bKhVToZZFekCcr8BZjbZznC7KGjD14qhujcUMj
DOCUSEAL_API_URL=http://docuseal-p8oc4sw8scksocoo80occw8c.44.203.101.160.sslip.io/api
RESEND_API_KEY=re_Vx7YxwHT_KQgyS8zPHhR1WRzuydZfgQBA
FROM_EMAIL=onboarding@resend.dev
FROM_NAME=Emprezario Inc
```

### Configuration Location:
`/Users/edduran/Documents/GitHub/ai-realtor/app/config.py`

---

## 11. Next Steps for TV Display Implementation

### Phase 1: Frontend Setup
- [ ] Choose framework (Next.js recommended)
- [ ] Set up TypeScript
- [ ] Create folder structure (`/frontend` or `/web`)
- [ ] Install dependencies (React, Tailwind CSS, SWR/React Query)

### Phase 2: Core Screens
- [ ] Dashboard/Home
- [ ] Contracts board (Kanban-style)
- [ ] Properties list
- [ ] Agent profile
- [ ] Task/Todo list

### Phase 3: Real-Time Updates
- [ ] Implement polling (fetch every 5-10 seconds)
- [ ] OR add WebSocket support to API
- [ ] Set up automatic status refresh

### Phase 4: Display-Specific Features
- [ ] Full-screen mode
- [ ] Large, readable fonts
- [ ] Bright colors/high contrast
- [ ] Auto-refresh every 30 seconds
- [ ] Minimal UI clutter
- [ ] Touch-friendly for TV remotes (if applicable)

### Phase 5: Integration
- [ ] Connect to FastAPI backend
- [ ] Add authentication (if needed)
- [ ] Test all endpoints
- [ ] Deploy

---

## 12. Database Schema (SQLite)

Current tables:
- `agents` - Real estate agents
- `properties` - Property listings
- `contacts` - Property contacts
- `contracts` - Contract documents
- `contract_submitters` - Individual signers
- `todos` - Task management
- `skip_traces` - Skip tracing results
- `agent_preferences` - Agent settings

All tables have `created_at` and `updated_at` timestamps.

---

## Summary for TV Display Component

Your **AI Realtor** project is a **FastAPI backend** designed for voice-first operations. The good news:

✅ **Strengths:**
- Well-structured API with clear routes
- Voice-friendly endpoints ready to consume
- Real-time data available (contracts, status, timestamps)
- Multiple data sources (agents, properties, contacts, contracts)
- Email integration working
- Contract signing fully integrated

❌ **Gaps for TV Display:**
- No frontend exists yet
- No WebSocket/real-time streaming
- No display components
- No authentication UI

**Your task:** Build a **React/Next.js TV display** that:
1. Fetches data from FastAPI endpoints
2. Shows contract status, signers, and progress
3. Refreshes regularly (polling)
4. Displays agent activity and property info
5. Optimized for large-screen viewing

Would you like me to help you set up a Next.js frontend for this?
