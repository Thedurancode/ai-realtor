# AI Realtor - Fly.io Deployment Guide

## Overview

This guide will help you deploy the AI Realtor backend to Fly.io. The app is already configured with `fly.toml` and `Dockerfile`.

---

## Prerequisites

1. **Fly.io Account**
   - Sign up at https://fly.io/
   - Install Fly CLI: `brew install flyctl` (macOS) or see https://fly.io/docs/hands-on/install-flyctl/

2. **API Keys Required**
   - Google Places API key
   - DocuSeal API key
   - Resend API key
   - RapidAPI key (for Zillow & Skip Trace)

3. **Domain (Optional)**
   - If you want a custom domain

---

## Step 1: Install Fly CLI

### macOS
```bash
brew install flyctl
```

### Linux
```bash
curl -L https://fly.io/install.sh | sh
```

### Windows
```powershell
pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

---

## Step 2: Authenticate with Fly.io

```bash
fly auth login
```

This will open your browser for authentication.

---

## Step 3: Review Configuration

Your app is already configured in `fly.toml`:

```toml
app = "ai-realtor"
primary_region = "ewr"  # Newark (East Coast)

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  memory = "1gb"
  cpu_kind = "shared"
  cpus = 1
```

**Key Features:**
- ✅ Auto-start/stop (saves money when not in use)
- ✅ HTTPS enforced
- ✅ 1GB RAM, 1 CPU
- ✅ East Coast region (low latency)

---

## Step 4: Launch the App

```bash
fly launch --no-deploy
```

This will:
1. Detect your Dockerfile
2. Use existing `fly.toml`
3. Create the app on Fly.io
4. **NOT** deploy yet (we need to set secrets first)

If asked:
- **"Would you like to copy its configuration to the new app?"** → Yes
- **"Would you like to set up a Postgres database?"** → No (we use SQLite)
- **"Would you like to deploy now?"** → No (we need secrets first)

---

## Step 5: Set Environment Variables (Secrets)

Fly.io uses secrets for sensitive data. Set all your API keys:

```bash
# Google Places API
fly secrets set GOOGLE_PLACES_API_KEY="your_google_places_api_key_here"

# DocuSeal API
fly secrets set DOCUSEAL_API_KEY="your_docuseal_api_key_here"
fly secrets set DOCUSEAL_API_URL="https://api.docuseal.com"

# Resend API (Email)
fly secrets set RESEND_API_KEY="your_resend_api_key_here"
fly secrets set FROM_EMAIL="noreply@yourdomain.com"
fly secrets set FROM_NAME="Real Estate Contracts"

# RapidAPI (Zillow & Skip Trace)
fly secrets set RAPIDAPI_KEY="your_rapidapi_key_here"
fly secrets set SKIP_TRACE_API_HOST="skip-tracing-working-api.p.rapidapi.com"
fly secrets set ZILLOW_API_HOST="private-zillow.p.rapidapi.com"
```

**All in one command:**
```bash
fly secrets set \
  GOOGLE_PLACES_API_KEY="your_key" \
  DOCUSEAL_API_KEY="your_key" \
  DOCUSEAL_API_URL="https://api.docuseal.com" \
  RESEND_API_KEY="your_key" \
  FROM_EMAIL="noreply@yourdomain.com" \
  FROM_NAME="Real Estate Contracts" \
  RAPIDAPI_KEY="your_key" \
  SKIP_TRACE_API_HOST="skip-tracing-working-api.p.rapidapi.com" \
  ZILLOW_API_HOST="private-zillow.p.rapidapi.com"
```

**Verify secrets:**
```bash
fly secrets list
```

---

## Step 6: Add Volume for SQLite Database (Optional but Recommended)

If you want persistent storage for your SQLite database:

```bash
# Create a 1GB volume
fly volumes create data --size 1 --region ewr

# Update fly.toml to mount the volume
```

Add to `fly.toml`:
```toml
[[mounts]]
  source = "data"
  destination = "/data"
```

Update your app to use `/data/ai_realtor.db` instead of `./ai_realtor.db`.

**Or** use a managed database (see Advanced Options below).

---

## Step 7: Deploy!

```bash
fly deploy
```

This will:
1. Build your Docker image
2. Push to Fly.io registry
3. Deploy to your machine
4. Start the app

**Watch logs during deployment:**
```bash
fly logs
```

---

## Step 8: Verify Deployment

### Check Status
```bash
fly status
```

### Check Logs
```bash
fly logs
```

### Test API
```bash
# Get your app URL
fly info

# Test health endpoint
curl https://ai-realtor.fly.dev/
```

### Open in Browser
```bash
fly open
```

This opens your app's URL. You should see:
```json
{
  "message": "AI Realtor API",
  "version": "1.0",
  "status": "running"
}
```

### Test API Docs
```bash
fly open /docs
```

---

## Step 9: Monitor Your App

### View Logs
```bash
# Stream live logs
fly logs

# Show last 200 lines
fly logs --lines 200
```

### Check Metrics
```bash
fly dashboard
```

Opens Fly.io dashboard in browser with:
- CPU usage
- Memory usage
- Request rate
- Response times

### SSH into Machine
```bash
fly ssh console
```

---

## Step 10: Update Environment Variables

If you need to change API keys or settings:

```bash
# Update a secret
fly secrets set DOCUSEAL_API_KEY="new_key"

# This will trigger a redeploy
```

---

## Common Commands

### Deploy Updates
```bash
# After making code changes
git add .
git commit -m "Update"
fly deploy
```

### Restart App
```bash
fly machine restart
```

### Scale Resources
```bash
# Increase memory to 2GB
fly scale memory 2048

# Add more CPUs
fly scale count 2
```

### View App Info
```bash
fly info
```

### Check App URL
```bash
fly info | grep Hostname
```

---

## Custom Domain Setup

### Add Your Domain

```bash
# Add your domain
fly certs add yourdomain.com

# Check certificate status
fly certs show yourdomain.com
```

### Update DNS

Add these records to your DNS provider:

**For root domain (yourdomain.com):**
```
A     @    <fly-ip-address>
AAAA  @    <fly-ipv6-address>
```

**For subdomain (api.yourdomain.com):**
```
CNAME  api  ai-realtor.fly.dev
```

Get your IPs:
```bash
fly ips list
```

### Verify Certificate
```bash
fly certs check yourdomain.com
```

---

## Frontend Integration

Once backend is deployed, update your frontend to use the production URL:

### Update Frontend .env

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=https://ai-realtor.fly.dev
NEXT_PUBLIC_WS_URL=wss://ai-realtor.fly.dev
```

### WebSocket Configuration

Fly.io supports WebSockets automatically. Your existing WebSocket code will work:

```typescript
const ws = new WebSocket('wss://ai-realtor.fly.dev/ws')
```

---

## Database Options

### Option 1: SQLite with Volume (Current Setup)

**Pros:**
- Simple
- No extra cost
- Fast for single-region

**Cons:**
- Single machine only
- No automatic backups

**Setup:**
```bash
fly volumes create data --size 1
```

Update `fly.toml`:
```toml
[[mounts]]
  source = "data"
  destination = "/data"
```

Update database path in your app to `/data/ai_realtor.db`.

---

### Option 2: PostgreSQL (Recommended for Production)

**Pros:**
- Scalable
- Automatic backups
- Multi-region support

**Cons:**
- Additional cost ($1/month minimum)

**Setup:**
```bash
# Create Postgres database
fly postgres create

# Attach to your app
fly postgres attach <postgres-app-name>

# This sets DATABASE_URL automatically
```

Update your app to use PostgreSQL instead of SQLite:

```python
# app/database.py
import os
from sqlalchemy import create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_realtor.db")

# For Postgres on Fly.io
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
```

---

### Option 3: LiteFS (Distributed SQLite)

**Pros:**
- Keep SQLite
- Distributed across regions
- Automatic replication

**Cons:**
- More complex setup

See: https://fly.io/docs/litefs/

---

## Cost Estimates

### Free Tier
- **Included:**
  - 3 shared-cpu-1x machines with 256MB RAM
  - 3GB storage
  - 160GB bandwidth

**Your Current Config:**
- 1GB RAM, 1 CPU, auto-stop = **~$2-5/month**
- Most of the time your app will be stopped (free)
- Only runs when receiving requests

### Cost Optimization

**Use auto-stop (already configured):**
```toml
auto_stop_machines = "stop"
auto_start_machines = true
min_machines_running = 0
```

Your app will:
- Stop after 5 minutes of inactivity
- Start automatically on first request
- **Cost:** $0 when stopped, ~$0.01/hour when running

---

## Monitoring & Debugging

### Health Checks

Add health check endpoint (already exists):

```python
@app.get("/health")
async def health():
    return {"status": "healthy"}
```

Configure in `fly.toml`:
```toml
[http_service.checks]
  [http_service.checks.health]
    interval = "30s"
    timeout = "5s"
    path = "/health"
```

### Error Tracking

View errors in logs:
```bash
fly logs | grep ERROR
```

### Performance Monitoring

```bash
# View metrics
fly dashboard

# Check resource usage
fly machine status
```

---

## Security Best Practices

### 1. Use Secrets for All Sensitive Data

```bash
# Never commit secrets to git
fly secrets set KEY="value"
```

### 2. Enable HTTPS Only (Already Configured)

```toml
force_https = true
```

### 3. Set CORS Properly

Update `app/main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.vercel.app",
        "http://localhost:3000",  # Development only
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Rate Limiting

Consider adding rate limiting middleware.

---

## Rollback

If deployment fails:

```bash
# List deployments
fly releases

# Rollback to previous version
fly rollback
```

---

## CI/CD with GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Fly.io

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: superfly/flyctl-actions/setup-flyctl@master

      - run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

Get your API token:
```bash
fly auth token
```

Add to GitHub secrets: `FLY_API_TOKEN`

---

## Troubleshooting

### Issue: App not starting

**Check logs:**
```bash
fly logs
```

**Common issues:**
- Missing environment variables
- Database connection errors
- Port mismatch (must use 8000)

---

### Issue: Can't connect to database

**If using SQLite:**
- Ensure volume is mounted
- Check file permissions

**If using Postgres:**
```bash
fly postgres connect -a <postgres-app-name>
```

---

### Issue: App timing out

**Increase timeout in `fly.toml`:**
```toml
[http_service]
  grace_period = "30s"
```

---

### Issue: High costs

**Enable auto-stop:**
```toml
auto_stop_machines = "stop"
min_machines_running = 0
```

**Or scale down:**
```bash
fly scale memory 256
```

---

## Complete Deployment Checklist

- [ ] Install Fly CLI
- [ ] Authenticate: `fly auth login`
- [ ] Launch app: `fly launch --no-deploy`
- [ ] Set all secrets: `fly secrets set ...`
- [ ] (Optional) Create volume: `fly volumes create data`
- [ ] Deploy: `fly deploy`
- [ ] Verify: `fly open /docs`
- [ ] Check logs: `fly logs`
- [ ] Test API endpoints
- [ ] Update frontend with production URL
- [ ] (Optional) Add custom domain
- [ ] Set up monitoring
- [ ] Configure backups

---

## Quick Reference

```bash
# Deploy
fly deploy

# Logs
fly logs

# Status
fly status

# Open app
fly open

# SSH
fly ssh console

# Secrets
fly secrets list
fly secrets set KEY="value"

# Scale
fly scale memory 2048
fly scale count 2

# Restart
fly machine restart

# Rollback
fly rollback
```

---

## Support

- **Fly.io Docs:** https://fly.io/docs/
- **Community:** https://community.fly.io/
- **Status:** https://status.fly.io/

---

## Next Steps

Once deployed:

1. **Test all endpoints** via `/docs`
2. **Update frontend** with production URL
3. **Set up monitoring** in Fly.io dashboard
4. **Configure custom domain** (optional)
5. **Set up CI/CD** with GitHub Actions
6. **Add health checks** for reliability
7. **Configure backups** for database

---

**Ready to deploy? Run:**

```bash
fly launch --no-deploy
fly secrets set GOOGLE_PLACES_API_KEY="..." # ... all secrets
fly deploy
fly open /docs
```

🚀 Your AI Realtor API is now live!
