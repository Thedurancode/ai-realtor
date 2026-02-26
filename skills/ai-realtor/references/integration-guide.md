# Integration Guide

Complete guide for integrating AI Realtor API with Clawbot/OpenClaw and other systems.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Environment Setup](#environment-setup)
3. [Clawbot/OpenClaw Integration](#clawbotopenclaw-integration)
4. [REST API Integration](#rest-api-integration)
5. [Webhook Configuration](#webhook-configuration)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [Production Deployment](#production-deployment)

---

## Quick Start

### 5-Minute Setup

```bash
# 1. Clone the repository
git clone https://github.com/Thedurancode/ai-realtor.git
cd ai-realtor

# 2. Set environment variables
cp .env.example .env
# Edit .env with your API keys

# 3. Run migrations
alembic upgrade head

# 4. Start server
uvicorn app.main:app --reload

# 5. Test health endpoint
curl http://localhost:8000/health
```

### What You Need

**Required API Keys:**
- Google Places API Key - For address lookup
- Anthropic API Key - For AI analysis (Claude Sonnet 4)
- DocuSeal API Key - For contract e-signatures
- ElevenLabs API Key - For voice synthesis (optional)
- VAPI API Key - For phone calls (optional)
- Skip Trace API Key - For owner discovery (optional)
- Zillow API access - For property enrichment (optional)

**Optional Integrations:**
- Facebook Ads API - For paid advertising
- Postiz API - For social media scheduling
- Exa API - For property research
- RentCast API - For rental comparables

---

## Environment Setup

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env file
nano .env
```

### Required .env Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ai_realtor

# API Keys
GOOGLE_PLACES_API_KEY=your-google-places-key
ANTHROPIC_API_KEY=sk-ant-your-key
DOCUSEAL_API_KEY=your-docuseal-key
DOCUSEAL_API_URL=https://api.docuseal.com
DOCUSEAL_WEBHOOK_SECRET=your-webhook-secret

# Optional (but recommended)
VAPI_API_KEY=your-vapi-key
ELEVENLABS_API_KEY=your-elevenlabs-key
RAPIDAPI_KEY=your-rapidapi-key
RENTCAST_API_KEY=your-rentcast-key
EXA_API_KEY=your-exa-key

# Marketing (optional)
FACEBOOK_ACCESS_TOKEN=your-facebook-token
FACEBOOK_AD_ACCOUNT_ID=act_your_account_id
POSTIZ_API_KEY=your-postiz-key

# Remotion (for video generation)
REDIS_HOST=localhost
REDIS_PORT=6379
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_S3_BUCKET=ai-realtor-renders
```

### Cloud Deployment (Fly.io)

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Deploy
fly deploy

# Set secrets
fly secrets set DATABASE_URL=your-db-url --app ai-realtor
fly secrets set ANTHROPIC_API_KEY=your-key --app ai-realtor
fly secrets set GOOGLE_PLACES_API_KEY=your-key --app ai-realtor
# ... set all other secrets

# View logs
fly logs --app ai-realtor
```

---

## Clawbot/OpenClaw Integration

### What is MCP?

MCP (Model Context Protocol) is the standard for AI agent communication. The AI Realtor platform includes a complete MCP server with 135 tools for voice control.

### Installation

**Option 1: Global Installation**

```bash
# Create global skills directory
mkdir -p ~/.openclaw/skills/

# Copy AI Realtor skill
cp -r /path/to/ai-realtor/skills/ai-realtor ~/.openclaw/skills/
```

**Option 2: Workspace Installation**

```bash
# In your workspace directory
mkdir -p skills/
cp -r /path/to/ai-realtor/skills/ai-realtor skills/
```

### Configuration

Edit your OpenClaw configuration file:

**Location:** `~/.config/openclaw/config.json` or `~/.openclaw/config.json`

```json
{
  "mcpServers": {
    "ai-realtor": {
      "command": "python",
      "args": [
        "/path/to/ai-realtor/mcp_server/property_mcp.py"
      ],
      "env": {
        "API_URL": "http://localhost:8000",
        "API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**For production deployment:**

```json
{
  "mcpServers": {
    "ai-realtor": {
      "command": "python",
      "args": [
        "/path/to/ai-realtor/mcp_server/property_mcp.py"
      ],
      "env": {
        "API_URL": "https://ai-realtor.fly.dev",
        "API_KEY": "your-production-api-key"
      }
    }
  }
}
```

### Testing the Integration

1. **Restart OpenClaw**
   ```bash
   # Restart your OpenClaw/Clawbot instance
   ```

2. **Verify MCP Server Loaded**
   - OpenClaw should discover 135 available tools
   - Check logs for successful connection

3. **Test Voice Commands**
   ```
   "Create a property at 123 Main St in Miami for $750,000"
   "Score property 1"
   "Show me all properties"
   ```

### MCP Tool Categories

OpenClaw will have access to these tool categories:

- **Property Tools (7)** - Create, list, get, update, delete, enrich, skip trace
- **Contract Tools (13)** - Manage contracts, signatures, readiness
- **Scoring Tools (4)** - Score properties, get breakdowns, top deals
- **Analytics Tools (3)** - Portfolio, pipeline, contract summaries
- **Marketing Tools (12)** - Branding, Facebook ads, social media
- **Phone Call Tools (6)** - VAPI integration, ElevenLabs voice
- **Research Tools (7)** - Deep research, semantic search, comps
- **Campaign Tools (6)** - Voice campaign management
- **Notification Tools (5)** - Alerts and notifications
- **Insights Tools (2)** - Proactive intelligence
- **Task Tools (3)** - Scheduled tasks
- **Follow-Up Tools (3)** - Priority queue
- **Bulk Operations (2)** - Bulk property operations
- **Timeline Tools (3)** - Activity timeline
- **Watchlist Tools (5)** - Market watchlists
- **Heartbeat Tool (1)** - Property health
- **Web Scraper Tools (6)** - Property data extraction
- **Intelligence Tools (23)** - Predictive AI, negotiation, etc.

**Total: 135 MCP tools**

---

## REST API Integration

### Authentication

All API endpoints (except /health and /docs) require authentication.

**Method 1: Header-based (Recommended)**

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  https://ai-realtor.fly.dev/properties/
```

**Method 2: Query parameter**

```bash
curl "https://ai-realtor.fly.dev/properties/?api_key=YOUR_API_KEY"
```

### Making API Calls

### Python Example

```python
import requests

API_URL = "https://ai-realtor.fly.dev"
API_KEY = "your-api-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# List properties
response = requests.get(f"{API_URL}/properties/", headers=headers)
properties = response.json()
print(f"Found {len(properties)} properties")

# Create property
property_data = {
    "address": "123 Main St",
    "city": "Miami",
    "state": "FL",
    "zip_code": "33101",
    "price": 750000,
    "bedrooms": 3,
    "bathrooms": 2,
    "square_footage": 1800,
    "property_type": "house"
}

response = requests.post(
    f"{API_URL}/properties/",
    headers=headers,
    json=property_data
)
property = response.json()
print(f"Created property {property['id']}")

# Enrich property
response = requests.post(
    f"{API_URL}/properties/{property['id']}/enrich",
    headers=headers
)
enrichment = response.json()
print(f"Enriched with {len(enrichment['photos'])} photos")
```

### JavaScript/Node.js Example

```javascript
const fetch = require('node-fetch');

const API_URL = 'https://ai-realtor.fly.dev';
const API_KEY = 'your-api-key';

const headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
};

// List properties
async function getProperties() {
    const response = await fetch(`${API_URL}/properties/`, { headers });
    const properties = await response.json();
    console.log(`Found ${properties.length} properties`);
    return properties;
}

// Create property
async function createProperty(propertyData) {
    const response = await fetch(`${API_URL}/properties/`, {
        method: 'POST',
        headers,
        body: JSON.stringify(propertyData)
    });
    const property = await response.json();
    console.log(`Created property ${property.id}`);
    return property;
}

// Enrich property
async function enrichProperty(propertyId) {
    const response = await fetch(`${API_URL}/properties/${propertyId}/enrich`, {
        method: 'POST',
        headers
    });
    const enrichment = await response.json();
    console.log(`Enriched with ${enrichment.photos.length} photos`);
    return enrichment;
}

// Usage
(async () => {
    await getProperties();

    const property = await createProperty({
        address: '123 Main St',
        city: 'Miami',
        state: 'FL',
        zip_code: '33101',
        price: 750000,
        bedrooms: 3,
        bathrooms: 2,
        square_footage: 1800,
        property_type: 'house'
    });

    await enrichProperty(property.id);
})();
```

### cURL Examples

```bash
# Health check
curl https://ai-realtor.fly.dev/health

# List properties
curl -H "X-API-Key: YOUR_KEY" https://ai-realtor.fly.dev/properties/

# Create property
curl -X POST https://ai-realtor.fly.dev/properties/ \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "address": "123 Main St",
    "city": "Miami",
    "state": "FL",
    "zip_code": "33101",
    "price": 750000,
    "bedrooms": 3,
    "bathrooms": 2,
    "square_footage": 1800,
    "property_type": "house"
  }'

# Enrich property
curl -X POST https://ai-realtor.fly.dev/properties/1/enrich \
  -H "X-API-Key: YOUR_KEY"

# Score property
curl -X POST https://ai-realtor.fly.dev/scoring/property/1 \
  -H "X-API-Key: YOUR_KEY"

# Get property heartbeat
curl https://ai-realtor.fly.dev/properties/1/heartbeat?api_key=YOUR_KEY

# Send contract
curl -X POST https://ai-realtor.fly.dev/contracts/1/send \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "signer_roles": ["buyer", "seller"],
    "subject": "Purchase Agreement",
    "message": "Please sign"
  }'
```

---

## Webhook Configuration

### DocuSeal Webhooks

**Purpose:** Real-time contract signature updates

**Configuration:**

1. **In DocuSeal Dashboard:**
   - Go to Settings → Webhooks
   - Add webhook URL: `https://your-domain.com/webhooks/docuseal`
   - Select events: document.completed, document.signed
   - Copy webhook secret

2. **Set Environment Variable:**
   ```bash
   DOCUSEAL_WEBHOOK_SECRET=your-webhook-secret-from-docuseal
   ```

3. **Test Webhook:**
   ```bash
   curl -X POST https://ai-realtor.fly.dev/webhooks/test \
     -H "X-API-Key: YOUR_KEY"
   ```

**Webhook Events:**
- `document.completed` - All parties signed
- `document.viewed` - Document opened
- `document.sent` - Document sent for signature
- `document.signed` - One party signed

**Security:** HMAC-SHA256 signature verification with constant-time comparison

### Custom Webhooks

You can configure custom webhooks for notifications:

**Add to your application:**

```python
import requests

def send_webhook_notification(webhook_url, data):
    response = requests.post(webhook_url, json=data)
    return response.status_code == 200

# Example: Send notification when contract signed
webhook_url = "https://your-app.com/webhooks/ai-realtor"
data = {
    "event": "contract_signed",
    "property_id": 5,
    "contract_id": 3,
    "timestamp": "2026-02-26T10:00:00Z"
}
send_webhook_notification(webhook_url, data)
```

---

## Best Practices

### 1. API Key Management

**Do:**
- Store API keys in environment variables
- Use different keys for dev/staging/production
- Rotate keys periodically
- Never commit keys to git

**Don't:**
- Hardcode keys in source code
- Share keys via email/chat
- Use production keys in development

### 2. Error Handling

**Always handle errors gracefully:**

```python
import requests
from requests.exceptions import RequestException

try:
    response = requests.post(
        f"{API_URL}/properties/{id}/enrich",
        headers=headers,
        timeout=30
    )
    response.raise_for_status()
    data = response.json()

except RequestException as e:
    print(f"API error: {e}")
    # Handle error appropriately
except ValueError as e:
    print(f"JSON decode error: {e}")
```

### 3. Rate Limiting

**Respect rate limits:**

- Implement exponential backoff for retries
- Cache responses where appropriate
- Use bulk operations for multiple properties

```python
import time

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except RequestException as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            time.sleep(wait_time)
```

### 4. Webhook Verification

**Always verify webhook signatures:**

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison
    return hmac.compare_digest(expected_signature, signature)
```

### 5. Property Heartbeat

**Use heartbeat for deal visibility:**

```python
# Check if property needs attention
response = requests.get(
    f"{API_URL}/properties/{id}/heartbeat",
    headers=headers
)
heartbeat = response.json()

if heartbeat['health_status'] == 'stale':
    # Property needs attention
    print(f"Action needed: {heartbeat['next_action']}")
```

### 6. Pipeline Automation

**Let automation work for you:**

- Properties auto-advance every 5 minutes
- Manual changes have 24-hour grace period
- Check pipeline status for recent transitions

```python
# Get recent auto-transitions
response = requests.get(
    f"{API_URL}/pipeline/status",
    headers=headers
)
transitions = response.json()
```

### 7. Daily Digest

**Leverage automated daily briefing:**

- Generated daily at 8 AM (configurable)
- Combines insights + analytics + notifications
- Full briefing + voice summary

```python
# Get latest digest
response = requests.get(
    f"{API_URL}/digest/latest",
    headers=headers
)
digest = response.json()
print(digest['voice_summary'])
```

---

## Troubleshooting

### Common Issues

#### 1. Property Not Auto-Advancing

**Check heartbeat:**
```bash
curl "https://ai-realtor.fly.dev/properties/5/heartbeat?api_key=YOUR_KEY"
```

**Manual pipeline check:**
```bash
curl -X POST "https://ai-realtor.fly.dev/pipeline/check?api_key=YOUR_KEY"
```

**Common causes:**
- Missing enrichment (run `/properties/{id}/enrich`)
- Missing skip trace (run `/properties/{id}/skip-trace`)
- No contracts attached (run `/contracts/attach-required`)
- Contracts not completed (check signing status)

#### 2. Contracts Not Sending

**Check signing status:**
```bash
curl "https://ai-realtor.fly.dev/contracts/signing-status/5?api_key=YOUR_KEY"
```

**Test DocuSeal webhook:**
```bash
curl -X POST "https://ai-realtor.fly.dev/webhooks/test?api_key=YOUR_KEY"
```

**Common causes:**
- Invalid DocuSeal API key
- Template not found
- Webhook not configured
- Signer email not set

#### 3. Missing Enrichment Data

**Re-enrich property:**
```bash
curl -X POST "https://ai-realtor.fly.dev/properties/5/enrich?api_key=YOUR_KEY"
```

**Common causes:**
- Zillow API key invalid
- Property not found on Zillow
- Rate limit exceeded

#### 4. MCP Server Not Loading

**Check OpenClaw config:**
```bash
cat ~/.openclaw/config.json
```

**Test MCP server directly:**
```bash
python /path/to/mcp_server/property_mcp.py
```

**Common causes:**
- Incorrect path to MCP server
- API_URL or API_KEY not set
- Python dependencies not installed

### Debug Mode

Enable debug logging:

```bash
# In .env
LOG_LEVEL=debug

# Restart server
uvicorn app.main:app --reload --log-level debug
```

### Health Check

Always start with health check:

```bash
curl https://ai-realtor.fly.dev/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-02-26T10:00:00Z"
}
```

---

## Production Deployment

### Fly.io Deployment

**1. Create app:**
```bash
fly launch --no-deploy
```

**2. Configure:**
```bash
# Set region
fly regions set iad --app ai-realtor

# Set secrets
fly secrets set DATABASE_URL=... --app ai-realtor
fly secrets set ANTHROPIC_API_KEY=... --app ai-realtor
fly secrets set GOOGLE_PLACES_API_KEY=... --app ai-realtor
# ... set all secrets
```

**3. Deploy:**
```bash
fly deploy --app ai-realtor
```

**4. Scale:**
```bash
fly scale count 2 --app ai-realtor
```

**5. Monitor:**
```bash
fly logs --app ai-realtor
fly status --app ai-realtor
```

### Database Setup

**1. Create database:**
```bash
fly postgres create --name ai-realtor-db
```

**2. Get connection string:**
```bash
fly postgres connect -a ai-realtor-db
```

**3. Set DATABASE_URL:**
```bash
fly secrets set DATABASE_URL=... --app ai-realtor
```

**4. Run migrations:**
```bash
fly ssh console --app ai-realtor
alembic upgrade head
```

### SSL Certificates

Fly.io provides automatic SSL certificates for custom domains:

```bash
# Add custom domain
fly certs add yourdomain.com --app ai-realtor
```

### Monitoring

**1. Metrics:**
```bash
fly metrics --app ai-realtor
```

**2. Logs:**
```bash
# Real-time logs
fly logs --app ai-realtor

# Last 100 lines
fly logs --app ai-realtor --lines 100
```

**3. Status:**
```bash
fly status --app ai-realtor
```

### Backup Strategy

**Database backups:**
```bash
# Fly.io automatic backups
fly postgres backups list --app ai-realtor-db

# Manual backup
fly postgres backups create --app ai-realtor-db
```

**Environment backup:**
```bash
# List all secrets
fly secrets list --app ai-realtor

# Save to secure file
fly secrets list --app ai-realtor > .env.backup
```

---

## API Versioning

The AI Realtor API uses semantic versioning:

- **Major version** - Breaking changes
- **Minor version** - New features
- **Patch version** - Bug fixes

**Current version:** v1.0.0

**Specify version in requests:**
```bash
curl -H "X-API-Version: 1.0" \
  -H "X-API-Key: YOUR_KEY" \
  https://ai-realtor.fly.dev/properties/
```

---

## Support

### Documentation

- **Interactive API Docs:** https://ai-realtor.fly.dev/docs
- **OpenAPI Spec:** https://ai-realtor.fly.dev/openapi.json
- **GitHub:** https://github.com/Thedurancode/ai-realtor

### Getting Help

1. **Check this guide first** - Most issues are covered here
2. **Check API docs** - Interactive docs show all endpoints
3. **Check GitHub issues** - Search for similar problems
4. **Create GitHub issue** - If bug or feature request

### Community

- **GitHub Discussions** - Ask questions, share integrations
- **Contributions welcome** - Pull requests accepted

---

## Advanced Topics

### Custom Contract Templates

Add your own contract templates:

```python
# Via API
POST /contract-templates/
{
  "name": "Custom Purchase Agreement",
  "state": "CA",
  "property_types": ["house", "condo"],
  "content": "Contract text...",
  "required_signer_roles": ["buyer", "seller"]
}
```

### Custom Deal Types

Configure deal calculation logic:

```python
POST /deals/types/create
{
  "name": "Fix and Flip",
  "holding_period_months": 6,
  "rehab_budget_percentage": 0.15,
  "target_roi_percentage": 0.20
}
```

### Brand Customization

Create custom brand identity:

```python
POST /agent-brand/{agent_id}
{
  "company_name": "Your Brand",
  "primary_color": "#YOUR_COLOR",
  "logo_url": "https://...",
  "tagline": "Your Tagline"
}
```

---

**Ready to integrate!** 🚀

For specific integration help, create an issue on GitHub or refer to the interactive API documentation.
