# 🐳 AI Realtor Docker Quick Start

Easy one-command startup with automatic environment variable loading!

## Quick Start

```bash
./scripts/start-docker.sh
```

That's it! The script will:
1. ✅ Check if `.env.docker` exists (creates it if needed)
2. ✅ Validate required API keys
3. ✅ Build Docker images
4. ✅ Start all services (PostgreSQL, Redis, AI Realtor app)

## Required Environment Variables

You **must** configure these in `.env.docker`:

```bash
# Primary AI (REQUIRED)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Address lookup (REQUIRED)
GOOGLE_PLACES_API_KEY=AIzaSy...

# Zillow enrichment (REQUIRED)
RAPIDAPI_KEY=7f97645717msh...
```

## Optional Environment Variables

Telegram bot (already configured!):
```bash
TELEGRAM_BOT_TOKEN=8392020900:AAEKlrigz4_B35slxdJpBIApSrotEf3cei
```

Other optional services:
- `ELEVENLABS_API_KEY` - Voice features
- `VAPI_API_KEY`, `VAPI_PHONE_NUMBER_ID`, `VAPI_WEBHOOK_SECRET` - Voice campaigns
- `DOCUSEAL_API_KEY` - Contract sending
- `RESEND_API_KEY` - Email notifications
- `LOB_API_KEY` - Direct mail
- `POSTIZ_API_KEY` - Social media
- `REPLICATE_API_KEY` - Video generation
- `HEYGEN_API_KEY`, `DID_API_KEY` - Avatar videos
- `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID` - Facebook ads
- `COMPOSIO_API_KEY` - Compos.io integration
- `PORTAL_JWT_SECRET`, `PORTAL_URL` - Customer portal

## Configuration Steps

1. **Copy environment file template:**
   ```bash
   cp .env.docker .env.docker
   ```

2. **Edit `.env.docker` with your API keys:**
   ```bash
   vim .env.docker
   # or
   nano .env.docker
   # or
   code .env.docker
   ```

3. **Start Docker:**
   ```bash
   ./scripts/start-docker.sh
   ```

## Docker Commands

```bash
# Start all services
./scripts/start-docker.sh

# Or use docker compose directly
docker compose up -d --build

# View logs
docker compose logs -f app

# Stop all services
docker compose down

# Stop and rebuild
docker compose down
docker compose up -d --build --force-recreate

# Restart just the app (keeps database running)
docker compose restart app
```

## Access the Application

Once started, access at:
- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3025 (if running)

## Telegram Bot Testing

Send a message to your bot in Telegram to test the integration!

## Troubleshooting

**Can't connect to database?**
```bash
docker compose down
docker compose up -d --build
```

**Need to update environment variables?**
```bash
# Edit .env.docker
vim .env.docker

# Then restart app container
docker compose restart app
```

**View logs?**
```bash
docker compose logs -f app --tail=100
```

## Production Deployment

For production, consider:
1. Use a real database (not in-memory)
2. Set `PORTAL_JWT_SECRET` to a strong random value
3. Configure proper CORS origins
4. Use HTTPS/reverse proxy (Traefik, Nginx)
5. Set up proper backups for PostgreSQL data volume
