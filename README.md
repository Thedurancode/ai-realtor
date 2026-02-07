# AI Realtor - Real Estate Management Platform

A comprehensive real estate management platform with AI-powered features, DocuSeal contract integration, TV display dashboard, and Claude Desktop MCP integration.

## Features

- 🏠 **Property Management** - Create, list, and manage properties
- 📝 **Contract Management** - DocuSeal integration for e-signatures
- 👥 **Contact Management** - Track buyers, sellers, agents, and more
- 🔍 **Zillow Enrichment** - Automatic property data enrichment
- 🔎 **Skip Tracing** - Find property owner information
- 📧 **Email Notifications** - Resend API integration
- 📺 **TV Display** - Real-time dashboard with animated notifications
- 🎤 **Voice Optimized** - Natural language queries with voice support
- 🤖 **Claude Desktop MCP** - Control everything with natural language
- 🔔 **Real-time Notifications** - WebSocket-powered updates

## Quick Start

### Local Development

```bash
# Backend
python3 -m uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

Visit:
- Backend API: http://localhost:8000/docs
- Frontend TV Display: http://localhost:3025

### Deploy to Fly.io

```bash
# Quick deploy (5 minutes)
./deploy.sh
```

See `QUICK_DEPLOY.md` for details.

## Documentation

### Deployment
- **[QUICK_DEPLOY.md](QUICK_DEPLOY.md)** - Deploy in 5 minutes
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment guide
- **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** - What's configured

### Features
- **[MCP_CONTRACTS.md](MCP_CONTRACTS.md)** - Contract tools for Claude Desktop
- **[ADDING_CONTACTS_GUIDE.md](ADDING_CONTACTS_GUIDE.md)** - How to add contacts
- **[VOICE_OPTIMIZATION.md](VOICE_OPTIMIZATION.md)** - Voice assistant integration
- **[NOTIFICATIONS_GUIDE.md](NOTIFICATIONS_GUIDE.md)** - Real-time notifications

### Integration
- **[MCP_INTEGRATION_GUIDE.md](MCP_INTEGRATION_GUIDE.md)** - Claude Desktop setup
- **[CLAUDE_DESKTOP_DEMO.md](CLAUDE_DESKTOP_DEMO.md)** - Demo scenarios

## MCP Tools (14 Total)

### Property Tools (7)
1. `list_properties` - List all properties
2. `get_property` - Get property details
3. `create_property` - Create new property
4. `delete_property` - Delete property
5. `enrich_property` - Add Zillow data
6. `skip_trace_property` - Find owner info
7. `add_contact` - Add contact to property

### Notification Tools (2)
8. `send_notification` - Send TV notification
9. `list_notifications` - View notification history

### Contract Tools (5)
10. `send_contract` - Send DocuSeal contract
11. `check_contract_status` - Check signing status
12. `list_contracts` - List all contracts
13. `list_contracts_voice` - 🎤 Voice-optimized list
14. `check_contract_status_voice` - 🎤 Voice-optimized status

## API Endpoints

### Properties
- `GET /properties/` - List properties
- `POST /properties/` - Create property
- `GET /properties/{id}` - Get property
- `PATCH /properties/{id}` - Update property
- `DELETE /properties/{id}` - Delete property

### Contracts
- `GET /contracts/` - List contracts
- `POST /contracts/` - Create contract
- `GET /contracts/{id}/status` - Check status
- `POST /contracts/{id}/send-to-contact` - Send contract

### Contacts
- `GET /contacts/` - List contacts
- `POST /contacts/` - Create contact
- `POST /contacts/voice` - Voice-optimized create

### Notifications
- `GET /notifications/` - List notifications
- `POST /notifications/` - Create notification
- `WS /ws` - WebSocket connection

### Agentic Research
- `POST /agentic/jobs` - Start async evidence-first research
- `GET /agentic/jobs/{job_id}` - Get job status and progress
- `GET /agentic/properties/{property_id}` - Get full structured research JSON
- `GET /agentic/properties/{property_id}/enrichment-status` - Check CRM/skip-trace/Zillow enrichment + freshness
- `GET /agentic/properties/{property_id}/dossier` - Get Markdown dossier
- `POST /agentic/research` - Run synchronous research shortcut

### Exa Research
- `POST /exa/research/property-dossier` - One-click investor-grade property dossier task
- `POST /exa/research` - Create Exa research task
- `GET /exa/research/{task_id}` - Fetch Exa research status/results

### Voice Campaigns
- `POST /voice-campaigns/` - Create outbound voice campaign
- `POST /voice-campaigns/{id}/targets` - Add targets by contact IDs or phone numbers
- `POST /voice-campaigns/{id}/targets/from-filters` - Enroll targets by property/role filters
- `POST /voice-campaigns/{id}/start` - Activate campaign
- `POST /voice-campaigns/{id}/process` - Process campaign queue immediately
- `GET /voice-campaigns/{id}/analytics` - Campaign metrics snapshot
- `POST /webhooks/vapi` - Receive Vapi call lifecycle webhooks

Example request:
```json
{
  "address": "123 Main St",
  "city": "Newark",
  "state": "NJ",
  "zip": "07102",
  "strategy": "wholesale",
  "assumptions": {
    "rehab_tier": "medium",
    "require_enriched_data": true,
    "enriched_max_age_hours": 168
  },
  "limits": {"max_steps": 7, "max_web_calls": 20, "timeout_seconds_per_step": 20}
}
```

Example response shape:
```json
{
  "property_id": 1,
  "latest_job_id": 10,
  "output": {
    "property_profile": {},
    "evidence": [],
    "comps_sales": [],
    "comps_rentals": [],
    "underwrite": {},
    "risk_score": {},
    "dossier": {"markdown": "# Property Dossier"},
    "worker_runs": []
  }
}
```

Exa request example:
```json
{
  "instructions": "Summarize the impact of CRISPR on gene therapy",
  "model": "exa-research-fast"
}
```

One-click property dossier example:
```json
{
  "address": "141 Throop Ave, New Brunswick, NJ 08901",
  "county": "Middlesex County",
  "strategy": "buy&hold",
  "model": "exa-research-fast"
}
```

See full API docs at `/docs` endpoint.

## Environment Variables

```bash
# Google Places API
GOOGLE_PLACES_API_KEY=your_key

# DocuSeal
DOCUSEAL_API_KEY=your_key
DOCUSEAL_API_URL=https://api.docuseal.com

# Resend (Email)
RESEND_API_KEY=your_key
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=Real Estate Contracts

# RapidAPI (Zillow & Skip Trace)
RAPIDAPI_KEY=your_key
SKIP_TRACE_API_HOST=skip-tracing-working-api.p.rapidapi.com
ZILLOW_API_HOST=private-zillow.p.rapidapi.com

# Exa web search (used by /agentic workers)
EXA_API_KEY=your_key
EXA_BASE_URL=https://api.exa.ai
EXA_SEARCH_TYPE=auto
EXA_TIMEOUT_SECONDS=20

# Vapi voice calling / campaign webhooks
VAPI_API_KEY=your_key
VAPI_PHONE_NUMBER_ID=optional_vapi_phone_number_id
VAPI_WEBHOOK_SECRET=your_webhook_secret

# Outbound campaign worker
CAMPAIGN_WORKER_ENABLED=true
CAMPAIGN_WORKER_INTERVAL_SECONDS=15
CAMPAIGN_WORKER_MAX_CALLS_PER_TICK=5

# Database
DATABASE_URL=postgresql://localhost:5432/ai_realtor

# LLM (optional for dossier expansion hooks)
ANTHROPIC_API_KEY=your_key
```

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database
- **Pydantic** - Data validation
- **WebSockets** - Real-time communication

### Frontend
- **Next.js 15** - React framework
- **TypeScript** - Type safety
- **Zustand** - State management
- **Framer Motion** - Animations
- **Remotion** - Video/animation rendering

### Integrations
- **DocuSeal** - E-signature platform
- **Google Places API** - Address validation
- **Zillow API** - Property enrichment
- **Skip Trace API** - Owner lookup
- **Resend** - Email delivery
- **Claude MCP** - AI assistant integration

## Architecture

```
┌─────────────────┐
│  Claude Desktop │
│   (MCP Client)  │
└────────┬────────┘
         │ Natural Language
         ↓
┌─────────────────┐      ┌──────────────┐
│   MCP Server    │←────→│   Backend    │
│ (14 AI Tools)   │      │   FastAPI    │
└─────────────────┘      └──────┬───────┘
                                │
                         ┌──────┴───────┐
                         │              │
                    ┌────▼────┐    ┌───▼────┐
                    │ Postgres│    │  APIs  │
                    │Database │    │External│
                    └─────────┘    └────────┘
                                        │
                         ┌──────────────┼──────────┐
                         ↓              ↓          ↓
                    DocuSeal      Google Places  Zillow
                   (Contracts)    (Addresses)    (Data)
```

## Example Usage

### Via Claude Desktop

```
"Create a property at 789 Main St for $600K,
add John Smith as the buyer (john@email.com),
and send him a purchase agreement"
```

Claude will:
1. Create the property
2. Validate address via Google Places
3. Add contact (triggers new lead notification)
4. Create contract
5. Send to John via DocuSeal
6. Show confirmation on TV display

### Via Voice Assistant

```
"Show me contracts for one forty one throop"
```

System will:
1. Normalize voice input ("one forty one" → "141", "throop" → phonetic variations)
2. Find property via fuzzy matching
3. Return contracts with natural language response
4. Perfect for text-to-speech output

### Via API

```bash
# Create property
curl -X POST http://localhost:8000/properties/ \
  -H "Content-Type: application/json" \
  -d '{
    "address": "789 Main St",
    "city": "Brooklyn",
    "state": "NY",
    "price": 600000,
    "bedrooms": 3,
    "bathrooms": 2
  }'
```

## Development

### Backend Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys

# Run server
python3 -m uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

### MCP Server Setup

See `MCP_INTEGRATION_GUIDE.md` for Claude Desktop integration.

## Deployment

### Option 1: Quick Deploy Script

```bash
./deploy.sh
```

### Option 2: Manual Deploy

```bash
fly launch
fly secrets set GOOGLE_PLACES_API_KEY="..." # etc
fly deploy
```

### Option 3: GitHub Actions

Push to `main` branch = automatic deployment

See `.github/workflows/deploy.yml`

## Testing

### Test API Endpoints

```bash
# View docs
open http://localhost:8000/docs

# Test health endpoint
curl http://localhost:8000/health
```

### Test MCP Tools

Open Claude Desktop and try:
```
"List all properties"
"Create a property at 123 Test St for $500K"
"Show me contracts for property 1"
```

### Test Voice Optimization

```
"um show me contracts for like one forty one troop avenue"
```

Should normalize to "141 throop avenue" and find matching properties.

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

## License

MIT License - See LICENSE file for details

## Support

- **Documentation:** See `/docs` in this repo
- **API Docs:** Visit `/docs` endpoint
- **Issues:** Open an issue on GitHub
- **Fly.io:** https://fly.io/docs/

## Roadmap

- [ ] Multi-tenant support
- [ ] Mobile app
- [ ] Advanced analytics
- [ ] CRM integration
- [ ] Automated marketing
- [ ] Multi-language support
- [ ] AI-powered insights

## Acknowledgments

- **Anthropic** - Claude AI & MCP
- **DocuSeal** - E-signature platform
- **Fly.io** - Hosting platform
- **Next.js** - Frontend framework
- **FastAPI** - Backend framework

---

**Ready to deploy?** Run `./deploy.sh` and follow the prompts!

For detailed instructions, see [QUICK_DEPLOY.md](QUICK_DEPLOY.md).
