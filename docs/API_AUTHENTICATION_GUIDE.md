# RealtorClaw API - Authentication Guide

## 🔐 Authentication Overview

The RealtorClaw API uses API key authentication. Most endpoints require an API key to be passed in the request header.

### Required Header: X-API-Key

**All protected endpoints require:**

```http
X-API-Key: sk_live_abc123def456...
```

### Example Request

```bash
curl -H "X-API-Key: sk_live_abc123..." http://localhost:8000/properties
```

### Getting an API Key

Register a new agent to receive an API key:

```bash
curl -X POST http://localhost:8000/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "email":"your@email.com",
    "name":"Your Name",
    "phone":"+15551234567"
  }'
```

**Response:**
```json
{
  "id": 1,
  "name": "Your Name",
  "email": "your@email.com",
  "api_key": "sk_live_abc123def456...",
  "created_at": "2026-02-27T10:30:00"
}
```

### Using Your API Key

```bash
# Primary method: X-API-Key header
curl -H "X-API-Key: sk_live_abc123..." http://localhost:8000/properties

# Using Authorization Bearer header (for rate limiting only)
curl -H "Authorization: Bearer sk_live_abc123..." http://localhost:8000/properties
```

---

## 🌐 Public Endpoints (No Authentication Required)

These endpoints can be called **without** an API key:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint with API info |
| GET | `/docs` | Interactive API documentation (Swagger UI) |
| GET | `/redoc` | Alternative API documentation (ReDoc) |
| GET | `/openapi.json` | OpenAPI schema |
| GET | `/health` | Health check endpoint |
| GET | `/rate-limit` | Rate limiting configuration |
| POST | `/agents/register` | Register new agent and get API key |
| ANY | `/webhooks/*` | Webhook endpoints (DocuSeal, Lob, etc.) |
| WS | `/ws` | WebSocket connections |
| ANY | `/portal/*` | Customer portal endpoints |
| ANY | `/api/setup/*` | Setup wizard endpoints |
| ANY | `/composio/*` | Composio integration endpoints |

---

## 🔒 Protected Endpoints (API Key Required)

All **other endpoints** require an API key via `X-API-Key` or `Authorization: Bearer` header.

### Quick Reference by Category

#### Property Management (`/properties`)
```
GET    /properties/                # List all properties
POST   /properties/                # Create new property
GET    /properties/{id}            # Get property details
PUT    /properties/{id}            # Update property
DELETE /properties/{id}            # Delete property
POST   /properties/{id}/enrich     # Enrich with Zillow data
POST   /properties/{id}/skip-trace # Skip trace property
GET    /properties/{id}/heartbeat  # Get property heartbeat
POST   /properties/voice          # Create property via voice
```

#### Contracts (`/contracts`)
```
GET    /contracts/                 # List all contracts
POST   /contracts/                 # Create contract
GET    /contracts/{id}             # Get contract details
PUT    /contracts/{id}             # Update contract
DELETE /contracts/{id}             # Delete contract
POST   /contracts/{id}/send        # Send for signature
GET    /contracts/{id}/status      # Check signing status
POST   /properties/{id}/attach-contracts  # Auto-attach templates
```

#### Contacts (`/contacts`)
```
GET    /contacts/                  # List all contacts
POST   /contacts/                  # Create new contact
GET    /contacts/{id}              # Get contact details
PUT    /contacts/{id}              # Update contact
DELETE /contacts/{id}              # Delete contact
```

#### Direct Mail (`/direct-mail`)
```
POST   /direct-mail/postcards      # Send postcard
POST   /direct-mail/letters        # Send letter
POST   /direct-mail/campaigns      # Create campaign
GET    /direct-mail/postcards/{id} # Check mail status
POST   /direct-mail/import-csv     # Import CSV contacts
GET    /direct-mail/templates      # List templates
```

#### Contact Lists (`/contact-lists`)
```
GET    /contact-lists/             # List all lists
POST   /contact-lists/             # Create list
GET    /contact-lists/{id}         # Get list details
PUT    /contact-lists/{id}         # Update list
DELETE /contact-lists/{id}         # Delete list
POST   /contact-lists/{id}/create-campaign  # Create campaign from list
```

#### Facebook Ads (`/facebook-ads`)
```
POST   /facebook-ads/campaigns/generate      # Generate ad campaign
POST   /facebook-ads/campaigns/{id}/launch   # Launch to Meta
GET    /facebook-ads/campaigns               # List campaigns
POST   /facebook-ads/audiences/recommend     # Get audience recommendations
```

#### Social Media (`/social`)
```
POST   /social/posts/create          # Create social post
POST   /social/posts/{id}/schedule   # Schedule post
GET    /social/posts                  # List posts
POST   /social/ai/generate            # AI content generation
GET    /social/analytics/overview     # Get analytics
```

#### Calendar (`/calendar`)
```
POST   /calendar/connect        # Connect Google Calendar
POST   /calendar/events         # Create event
GET    /calendar/events         # List events
POST   /calendar/sync           # Sync to calendar
GET    /calendar/calendars      # List connected calendars
```

#### Analytics (`/analytics`)
```
GET    /analytics/portfolio      # Portfolio summary
GET    /analytics/pipeline       # Pipeline breakdown
GET    /analytics/contracts      # Contract stats
```

#### Web Scraper (`/scrape`)
```
POST   /scrape/url               # Scrape URL for property data
POST   /scrape/scrape-and-create # Scrape and create property
POST   /scrape/zillow-search     # Scrape Zillow search
```

#### Pipeline (`/pipeline`)
```
GET    /pipeline/status          # Get pipeline status
POST   /pipeline/check           # Trigger pipeline check
```

#### Insights (`/insights`)
```
GET    /insights/                # Get all insights
GET    /insights/property/{id}   # Property-specific insights
```

---

## 📊 Summary

| Metric | Count |
|--------|-------|
| **Total Endpoints** | ~585 |
| **Public (No Auth)** | ~41 |
| **Protected (API Key)** | ~544 |
| **Authentication Method** | `X-API-Key` or `Authorization: Bearer` |
| **Rate Limiting** | 20 requests/hour per agent (default) |

---

## 💡 Quick Test

```bash
# Register and get API key
API_KEY=$(curl -s -X POST http://localhost:8000/agents/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test"}' \
  | jq -r '.api_key')

# Use API key with X-API-Key header
curl -H "X-API-Key: $API_KEY" http://localhost:8000/properties

# Or with Authorization Bearer header
curl -H "Authorization: Bearer $API_KEY" http://localhost:8000/properties
```

---

## 🔒 Rate Limiting

### Default Limits
- **20 requests per hour** per agent (API key)
- **30 requests per minute** burst limit

### Checking Rate Limit Status
```bash
curl http://localhost:8000/rate-limit
```

### Response
```json
{
  "rate_limiting": {
    "enabled": true,
    "message": "Rate limiting is ENABLED"
  },
  "limits": {
    "default": "20/hour",
    "burst": "30/minute"
  },
  "tiers": {
    "free": "20/hour",
    "pro": "100/hour",
    "enterprise": "1000/hour"
  }
}
```

### When Rate Limited

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 3600

{
  "detail": "Rate limit exceeded: 20 per 1 hour"
}
```

### Disabling Rate Limiting

```bash
# .env file
RATE_LIMIT_ENABLED=false

# Or environment variable
export RATE_LIMIT_ENABLED=false
```

See [docs/RATE_LIMITING.md](./RATE_LIMITING.md) for complete rate limiting documentation.

---

## 📚 Full API Documentation

- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## 🚨 Error Responses

### Missing API Key
```http
HTTP/1.1 401 Unauthorized

{
  "detail": "Missing API key"
}
```

### Invalid API Key
```http
HTTP/1.1 401 Unauthorized

{
  "detail": "Invalid API key"
}
```

### Rate Limit Exceeded
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 3600

{
  "detail": "Rate limit exceeded: 20 per 1 hour"
}
```
