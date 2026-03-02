# RealtorClaw API - Complete Platform Documentation

**Version:** 1.0.0
**Last Updated:** February 27, 2026
**Base URL:** `https://ai-realtor.fly.dev`
**Documentation:** https://ai-realtor.fly.dev/docs

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Authentication](#authentication)
4. [Core Features](#core-features)
5. [Property Management](#property-management)
6. [Direct Mail System](#direct-mail-system)
7. [Contact Lists](#contact-lists)
8. [Voice Control (MCP)](#voice-control-mcp)
9. [AI Features](#ai-features)
10. [Marketing Hub](#marketing-hub)
11. [Calendar Integration](#calendar-integration)
12. [API Reference](#api-reference)

---

## Overview

RealtorClaw is an **AI-powered real estate platform** that combines:
- Property data management with Zillow enrichment
- Direct mail automation via Lob.com
- Voice-controlled operations (262 MCP tools)
- Intelligent contract management
- AI-driven analytics and insights
- Social media and Facebook ad integration

### Technology Stack

- **Backend:** FastAPI (Python 3.11)
- **Database:** PostgreSQL with SQLAlchemy ORM
- **AI Models:** Anthropic Claude, GPT-4
- **External APIs:** Google Places, Zillow, Lob.com, DocuSeal, VAPI, ElevenLabs, Facebook Ads

### Platform Statistics

- **API Endpoints:** 591 total
- **MCP Voice Tools:** 262 tools
- **Database Tables:** 70+
- **External Integrations:** 15+ services

---

## Quick Start

### 1. Get API Access

```bash
# Get your API key from the platform
export API_KEY="your_api_key_here"
```

### 2. Make Your First Request

```bash
# Check platform health
curl https://ai-realtor.fly.dev/health

# List properties
curl -H "x-api-key: $API_KEY" \
  https://ai-realtor.fly.dev/properties/
```

### 3. Create a Property

```bash
curl -X POST \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "place_id": "ChIJY7N0yElw1ZYRJGs6wzX3kedYY",
    "property_type": "house",
    "price": 850000,
    "bedrooms": 3,
    "bathrooms": 2
  }' \
  https://ai-realtor.fly.dev/properties/voice
```

### 4. Enrich with Zillow Data

```bash
curl -X POST \
  -H "x-api-key: $API_KEY" \
  https://ai-realtor.fly.dev/properties/1/enrich
```

---

## Authentication

### API Key Authentication

All API requests require an API key in the header:

```bash
curl -H "x-api-key: YOUR_API_KEY" \
  https://ai-realtor.fly.dev/properties/
```

### Getting an API Key

1. Register at https://ai-realtor.fly.dev
2. Navigate to API Keys section
3. Generate a new API key
4. Include it in all requests via `x-api-key` header

### Rate Limiting

- **Default:** 100 requests per minute
- **Rate Limit Header:** `X-RateLimit-Remaining`
- **Rate Limit Exceeded:** Returns 429 status with error details

---

## Core Features

### Feature Overview

| Feature | Description | API Endpoints | MCP Tools |
|---------|-------------|---------------|-----------|
| **Property Management** | Create, list, update, enrich, score properties | 10 | 7 |
| **Direct Mail** | Send postcards/letters via Lob.com | 16 | 9 |
| **Contact Lists** | Smart auto-populating contact lists | 13 | 10 |
| **Contracts** | AI-powered contract management | 26 | 9 |
| **Skip Trace** | Owner contact discovery | 5 | 3 |
| **Voice Control** | 262 MCP voice commands | - | 262 |
| **Calendar** | Google Calendar integration | 15+ | 15 |
| **Marketing Hub** | Facebook Ads, Social Media, Branding | 39 | 23 |
| **AI Analytics** | Predictive intelligence, scoring | 30+ | 30+ |

---

## Property Management

### Property CRUD Operations

#### Create Property with Google Places

```http
POST /properties/voice
Content-Type: application/json

{
  "place_id": "ChIJY7N0yElw1ZYRJGs6wzX3kedYY",
  "property_type": "house",
  "price": 850000,
  "bedrooms": 3,
  "bathroom": 2,
  "square_footage": 2000,
  "year_built": 2020,
  "description": "Beautiful family home"
}
```

**Response:**
```json
{
  "id": 1,
  "address": "123 Main St",
  "city": "Anytown",
  "state": "CA",
  "zip_code": "90210",
  "price": 850000,
  "property_type": "house",
  "status": "new_property",
  "created_at": "2026-02-27T10:00:00Z"
}
```

#### List Properties with Filters

```http
GET /properties/?property_type=condo&city=Miami&min_price=100000&max_price=500000&bedrooms=2
```

#### Get Property Details

```http
GET /properties/{id}
```

#### Update Property

```http
PUT /properties/{id}
Content-Type: application/json

{
  "status": "enriched",
  "price": 900000
}
```

#### Delete Property

```http
DELETE /properties/{id}
```

### Zillow Data Enrichment

#### Enrich Property

```http
POST /properties/{id}/enrich
```

**Enrichment Data Includes:**
- High-resolution property photos (up to 10)
- Zestimate (current market value)
- Rent Zestimate
- Tax assessment history
- Price history (past sales)
- Nearby schools with ratings
- Property features
- Year built, lot size, parking

**Example Response:**

```json
{
  "property_id": 1,
  "zillow_id": "zillow_12345",
  "zestimate": 875000,
  "rent_zestimate": 3500,
  "photos": ["https://photos.zillow.com/..."],
  "schools": [
    {
      "name": "Lincoln Elementary",
      "rating": 8,
      "distance": "0.3 mi"
    }
  ]
}
```

### Property Scoring

#### Score a Property

```http
POST /scoring/property/{id}
```

**Scoring Dimensions:**
- **Market (30%):** Zestimate spread, days on market, price trends
- **Financial (25%):** ROI, rental yield, price per sqft
- **Readiness (25%):** Contract completion, contact coverage
- **Engagement (20%):** Recent activity, notes, tasks

**Response:**

```json
{
  "property_id": 1,
  "deal_score": 85,
  "score_grade": "A",
  "score_breakdown": {
    "market_score": 88,
    "financial_score": 82,
    "readiness_score": 80,
    "engagement_score": 90
  }
}
```

#### Voice Commands

```
"Score property 5"
"Rate this deal"
"Grade this property"
"Score all my properties"
"What are my best deals?"
```

---

## Direct Mail System

### Overview

Automated physical mail via Lob.com integration:
- **Postcards:** 4x6, 6x9, 6x11 sizes
- **Letters:** Legal/letter size with PDFs
- **USPS Address Verification:** CASS-certified
- **Real-time Tracking:** Webhook integration

### Send Postcard

```http
POST /direct-mail/postcards
Content-Type: application/json

{
  "to_address": {
    "name": "John Doe",
    "address_line1": "123 Main St",
    "city": "Miami",
    "state": "FL",
    "zip_code": "33101"
  },
  "template": "just_sold",
  "property_id": 1,
  "size": "4x6",
  "color": true,
  "double_sided": true
}
```

### Pre-Built Templates

1. **Just Sold** - Neighborhood announcements
2. **Open House** - Event invitations
3. **Market Update** - Quarterly statistics
4. **New Listing** - New property announcements
5. **Price Reduction** - Price drop notifications
6. **Hello/Farming** - Agent introduction
7. **Interested in Selling?** - Lead generation

### Template Variables

Templates use Jinja2 syntax for variable substitution:

```jinja2
<h1>JUST SOLD!</h1>

<p>{{property_address}}</p>
<p>Sold for {{sold_price}}</p>

<p>Agent: {{agent_name}}</p>
<p>Phone: {{agent_phone}}</p>

{% if property_photo %}
<img src="{{property_photo}}" />
{% endif %}
```

### Create Campaign

```http
POST /direct-mail/campaigns
Content-Type: application/json

{
  "name": "Miami Condo Campaign",
  "campaign_type": "just_sold",
  "mail_type": "postcard",
  "target_property_ids": [1, 2, 3],
  "send_immediately": false
}
```

### CSV Import

```http
POST /direct-mail/import-csv?template=interested_in_selling&create_campaign=true
Content-Type: multipart/form-data

file: contacts.csv
```

**CSV Format:**
```csv
name,address,city,state,zip_code,phone,email
"John Doe","123 Main St","Miami","FL","33101","(555) 123-4567","john@example.com"
"Jane Smith","456 Oak Ave","Miami","FL","33102","(555) 987-6543","jane@example.com"
```

### Check Mail Status

```http
GET /direct-mail/postcards/{mailpiece_id}
```

**Status Flow:**
- `draft` → `scheduled` → `processing` → `mailed` → `in_transit` → `delivered`

### Voice Commands

```
"Send a just sold postcard to 123 Main St"
"Create an open house campaign for all properties in Miami"
"Check the status of mailpiece 5"
"Verify the address 456 Oak Avenue, Austin, TX"
```

---

## Contact Lists

### Smart Contact Lists

Automatically organized contact lists based on:
- **Time-based:** Last 2 days, This week, This month
- **Property-based:** Has property, No property
- **Contact info:** Has email, No phone
- **Status:** Uncontacted leads

### Create Smart List

```http
POST /contact-lists/quick
Content-Type: application/json

{
  "preset": "interested_this_week",
  "custom_name": "Miami Leads This Week",
  "filters": {
    "city": "Miami"
  }
}
```

**Available Presets:**

| Preset | Description | Auto-Generated Name |
|--------|-------------|-------------------|
| `interested_this_week` | Contacts added this week | "Interested This Week" |
| `new_leads_2days` | Last 48 hours | "New Leads - Last 2 Days" |
| `new_leads_7days` | Last 7 days | "New Leads - Last 7 Days" |
| `this_month` | This month | "New Contacts - February 2026" |
| `uncontacted` | Never contacted | "Uncontacted Leads" |
| `no_phone` | Missing phone | "Missing Phone Numbers" |
| `has_email` | Has email | "Contacts With Email" |
| `no_property` | Not linked to property | "No Property Linked" |

### List Contact Lists

```http
GET /contact-lists?list_type=smart
```

**Response:**

```json
[
  {
    "id": 1,
    "name": "Interested This Week",
    "list_type": "smart",
    "smart_rule": "this_week",
    "total_contacts": 50,
    "auto_refresh": true
  }
]
```

### Get List Contacts

```http
GET /contact-lists/{id}?include_contacts=true&limit=20
```

### Create Campaign from List

```http
POST /contact-lists/{id}/create-campaign?template=interested_in_selling
```

### Voice Commands

```
"Show me all my contact lists"
"Create a list for contacts interested this week"
"Make a new leads list for last 2 days"
"Create uncontacted leads list"
"Show me list 5"
"Create a campaign from list 5"
"Refresh smart list 5"
```

### Auto-Refresh

Smart lists automatically refresh every 24 hours (configurable):

```python
# Auto-refresh interval
refresh_interval_hours: 24  # Default

# Refresh triggers:
# - Manual: POST /contact-lists/{id}/refresh
# - Automatic: Every 24 hours
```

---

## Voice Control (MCP)

### Overview

**262 MCP voice commands** for hands-free platform control via Claude Desktop.

### Setup MCP Server

**1. Install Dependencies**

```bash
pip install mcp
```

**2. Configure Claude Desktop**

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

**3. Restart Claude Desktop**

### Voice Command Examples

#### Properties

```
"Create a property at 123 Main St, New York for $850,000"
"Show me all condos under 500k in Miami"
"Enrich property 5 with Zillow data"
"Score property 5"
"Delete property 3"
```

#### Direct Mail

```
"Send a just sold postcard to 123 Main St"
"Create an open house campaign for all properties in Miami"
"Check the status of mailpiece 5"
"Verify the address 456 Oak Avenue, Austin, TX"
```

#### Contact Lists

```
"Show me all my contact lists"
"Create a list for contacts interested this week"
"Show me list 5"
"Create a campaign from list 5"
```

#### Contracts

```
"Is property 5 ready to close?"
"Suggest contracts for property 5"
"Send the Purchase Agreement"
```

#### Calendar

```
"Connect my Google Calendar"
"Schedule a showing for 123 Main St tomorrow at 2pm"
"Check if Saturday at 2pm works"
"Show me this week's events"
"Optimize my schedule with AI"
```

#### Marketing

```
"Set up my brand with Emprezario Inc"
"Apply the Luxury Gold color scheme"
"Create a Facebook ad for property 5"
"Generate Instagram content with AI"
```

#### Skills

```
"Show me all available skills"
"Enable the voice commands skill"
"Turn off property scoring"
```

### All 262 MCP Tools

See `CLAUDE.md` for complete list of 262 voice commands organized by feature.

---

## AI Features

### Predictive Intelligence

#### Predict Closing Probability

```http
POST /intelligence/predict-outcome
Content-Type: application/json

{
  "property_id": 5
}
```

**Response:**

```json
{
  "property_id": 5,
  "closing_probability": 85,
  "confidence": "high",
  "risk_factors": ["Price above market", "Days on market > 90"],
  "strengths": ["Great location", "Recent price reduction"],
  "time_to_close": "45-60 days"
}
```

#### Recommend Next Action

```http
POST /intelligence/recommend-action
Content-Type: application/json

{
  "property_id": 5
}
```

**Response:**

```json
{
  "property_id": 5,
  "recommended_action": "Schedule follow-up call",
  "reasoning": "Property has high score but no activity in 14 days",
  "priority": "high"
}
```

### Market Opportunity Scanner

```http
POST /intelligence/scan-opportunities
Content-Type: application/json

{
  "agent_id": 1
}
```

**Finds deals matching agent's success patterns.**

### Relationship Intelligence

```http
POST /intelligence/score-relationship
Content-Type: application/json

{
  "contact_id": 5
}
```

**Scores relationship health (0-100) with trend analysis.**

---

## Marketing Hub

### Agent Branding

#### Create Brand

```http
POST /agent-brand/{agent_id}
Content-Type: application/json

{
  "company_name": "Emprezario Inc",
  "tagline": "Your Dream Home Awaits",
  "primary_color": "#B45309",
  "secondary_color": "#D97706",
  "logo_url": "https://example.com/logo.png"
}
```

#### Apply Color Preset

```http
POST /agent-brand/{id}/apply-preset
Content-Type: application/json

{
  "preset": "luxury_gold"
}
```

**Presets:** `professional_blue`, `modern_green`, `luxury_gold`, `bold_red`, `minimalist_black`, `ocean_teal`

### Facebook Ads

#### Generate Campaign

```http
POST /facebook-ads/campaigns/generate
Content-Type: application/json

{
  "url": "https://example.com/properties/123",
  "campaign_objective": "leads",
  "daily_budget": 100
}
```

#### Launch to Meta

```http
POST /facebook-ads/campaigns/{id}/launch
Content-Type: application/json

{
  "meta_access_token": "your_token",
  "ad_account_id": "act_1234567890"
}
```

#### Market Research

```http
POST /facebook-ads/research/generate
Content-Type: application/json

{
  "location": "Miami, FL",
  "target_audience": "luxury_condos",
  "business_type": "real_estate"
}
```

### Postiz Social Media

#### Create Post

```http
POST /social/posts/create
Content-Type: application/json

{
  "content_type": "property_promo",
  "caption": "🏠 Stunning luxury condo in NYC!",
  "platforms": ["facebook", "instagram"],
  "use_branding": true
}
```

#### Create Campaign

```http
POST /social/campaigns/create
Content-Type: application/json

{
  "campaign_name": "Property Launch Campaign",
  "campaign_type": "property_launch",
  "platforms": ["facebook", "instagram"],
  "post_count": 10,
  "auto_generate": true
}
```

---

## Calendar Integration

### Connect Google Calendar

```http
GET /calendar/connect
```

**Returns OAuth URL for authorization.**

### Create Calendar Event

```http
POST /calendar/events/create
Content-Type: application/json

{
  "title": "Property Showing - 123 Main St",
  "description": "Showing luxury condo",
  "start_time": "2026-02-28T14:00:00Z",
  "duration_minutes": 60,
  "location": "123 Main St, New York, NY",
  "add_attendees": ["buyer@email.com"],
  "create_google_meet": true
}
```

### Smart Calendar Analysis

#### Check Conflicts

```http
POST /calendar/check-conflicts
Content-Type: application/json

{
  "start_time": "2026-02-28T14:00:00Z",
  "duration_minutes": 60
}
```

#### Suggest Optimal Time

```http
POST /calendar/find-optimal-time
Content-Type: application/json

{
  "event_type": "showing",
  "duration_minutes": 60,
  "preferred_days": ["monday", "tuesday", "wednesday"]
}
```

#### Optimize Schedule

```http
POST /calendar/optimize
Content-Type: application/json

{
  "days": 7
}
```

**AI-powered schedule optimization with meeting success predictions.**

---

## API Reference

### Response Format

All API responses follow this format:

**Success (200-299):**
```json
{
  "data": {...},
  "message": "Success"
}
```

**Error (400-599):**
```json
{
  "detail": "Error message description",
  "status_code": 400
}
```

### Common Errors

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid input data |
| 401 | Unauthorized - Missing or invalid API key |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 422 | Validation Error - Data validation failed |
| 429 | Rate Limit Exceeded - Too many requests |
| 500 | Internal Server Error - Server error |

### Pagination

List endpoints support pagination:

```http
GET /properties/?limit=10&offset=0
```

**Response:**

```json
{
  "total": 150,
  "limit": 10,
  "offset": 0,
  "data": [...]
}
```

---

## Webhooks

### Lob Webhook

**Endpoint:** `POST /webhooks/lob`

**Signature Verification:** HMAC-SHA256

```python
# Example webhook payload
{
  "id": "evt_test123",
  "event_type": "postcard.delivered",
  "resource": {
    "type": "postcard",
    "id": "postcard_test123"
  },
  "data": {
    "id": "lob_abc123",
    "tracking_events": [
      {"event": "delivered", "time": "2026-02-27T14:30:00Z"}
    ]
  }
}
```

### DocuSeal Webhook

**Endpoint:** `POST /webhooks/docuseal`

**Signature Verification:** HMAC-SHA256

Auto-updates contract status when documents are signed.

---

## Database Schema

### Core Tables

```sql
-- Properties
CREATE TABLE properties (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    property_type VARCHAR(50),
    price DECIMAL(12,2),
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Contacts
CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    property_id INTEGER REFERENCES properties(id),
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    role VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Contracts
CREATE TABLE contracts (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    property_id INTEGER REFERENCES properties(id),
    template_id INTEGER REFERENCES contract_templates(id),
    status VARCHAR(50),
    docuseal_document_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Direct Mail
CREATE TABLE direct_mail (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    mail_type VARCHAR(50),
    mail_status VARCHAR(50),
    lob_mailpiece_id VARCHAR(100),
    to_address JSONB,
    from_address JSONB,
    front_html TEXT,
    back_html TEXT,
    tracking_events JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Contact Lists
CREATE TABLE contact_lists (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    name VARCHAR(200),
    list_type VARCHAR(20),
    smart_rule VARCHAR(50),
    contact_ids JSONB,
    total_contacts INTEGER DEFAULT 0,
    auto_refresh BOOLEAN DEFAULT TRUE,
    last_refreshed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Environment Variables

### Required

```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
GOOGLE_PLACES_API_KEY=your_key
RAPIDAPI_KEY=your_key
DOCUSEAL_API_KEY=your_key
```

### Optional

```bash
ANTHROPIC_API_KEY=sk-ant-your-key
VAPI_API_KEY=your_vapi_key
ELEVENLABS_API_KEY=your_elevenlabs_key
LOB_API_KEY=your_lob_api_key
LOB_WEBHOOK_SECRET=your_webhook_secret
```

---

## Support & Resources

- **Documentation:** https://ai-realtor.fly.dev/docs
- **GitHub:** https://github.com/Thedurancode/ai-realtor
- **Status Page:** https://ai-realtor.fly.dev/health
- **MCP Tools:** 262 voice commands (see CLAUDE.md)

---

## Changelog

### February 2026

- **Contact Lists System** - Smart auto-populating contact lists (10 MCP tools)
- **Skills System** - Agent skill management (6 MCP tools)
- **Zuckerbot Integration** - AI Facebook ad generation (9 MCP tools)
- **Direct Mail Enhancement** - CSV import, address-based voice commands

### January 2026

- **Property Videos** - AI-generated property videos with voiceover
- **Calendar Optimization** - AI-powered schedule optimization
- **Q&A Phone Calls** - Automated information gathering calls

### December 2025

- **Marketing Hub** - Complete branding, Facebook Ads, Postiz integration
- **Property Scoring Engine** - 4-dimension deal analysis
- **Smart Follow-Up Queue** - AI-prioritized lead management

---

**© 2026 RealtorClaw Platform. All rights reserved.**

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)
