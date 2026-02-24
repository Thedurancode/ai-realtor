# AI Realtor API + Nanobot - Production Docker Deployment

Complete Docker stack including the **real AI Realtor FastAPI application**, Nanobot with the AI Realtor skill, PostgreSQL database, and automated migrations.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  Docker Network (ai-realtor-network)        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ PostgreSQL │  │ AI Realtor   │  │   Nanobot    │       │
│  │            │  │ FastAPI      │  │              │       │
│  │   :5432    │◄─│   API        │◄─│ with skill   │       │
│  │            │  │   :8000      │  │              │       │
│  └────────────┘  └──────┬───────┘  └──────┬───────┘       │
│                          │                  │               │
│                          │ AI_REALTOR_URL   │               │
│                          │ = http://api:   │               │
│                          │       8000       │               │
│                          └──────────────────┘               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Components

### 1. AI Realtor FastAPI Application (`api` service)

**What it is:** The real AI Realtor platform built with FastAPI

**Features:**
- Property management with Zillow enrichment
- Contract management with DocuSeal integration
- Skip tracing for owner discovery
- Marketing hub (Facebook Ads + Social Media)
- Analytics and reporting
- Webhook support
- Background task processing

**Exposes:**
- HTTP API on port 8000
- Interactive docs at `/docs`
- Health check at `/docs`

**Environment Variables:**
```bash
DATABASE_URL=postgresql://user:pass@db:5432/ai_realtor
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_PLACES_API_KEY=...
ZILLOW_API_KEY=...
# ... plus 8 more API keys
```

### 2. Nanobot (`nanobot` service)

**What it is:** AI assistant with voice control

**Configuration:**
- Receives `AI_REALTOR_API_URL=http://api:8000`
- Mounts AI Realtor skill from host
- Uses Anthropic Claude for intelligence
- Provides voice-controlled access to all API features

### 3. PostgreSQL (`db` service)

**What it is:** Database for AI Realtor platform

**Stores:**
- Properties, contracts, contacts
- Enrichment data, skip traces
- Analytics, tasks, watchlists
- All platform data

### 4. Migrations (`migrations` service)

**What it is:** Runs Alembic database migrations

**Runs automatically:**
- After API is healthy
- Before nanobot starts
- One-time setup

## Startup Sequence

```
1. User runs: ./start-prod-stack.sh
   ↓
2. Docker Compose reads docker-compose-prod.yml
   ↓
3. Services start in order:

   a) PostgreSQL starts
      Healthcheck: pg_isready
      ↓
   b) AI Realtor API starts
      Waits for PostgreSQL
      Runs migrations
      Healthcheck: /docs endpoint
      ↓
   c) Migrations run (optional, profile-based)
      Alembic upgrade head
      ↓
   d) Nanobot starts
      Waits for API healthcheck
      Receives AI_REALTOR_URL=http://api:8000
      Loads AI Realtor skill
      ✅ Ready!
```

## Quick Start

### 1. Configure Environment

```bash
# Copy example environment
cp .env.example .env

# Edit with your API keys
nano .env
```

**Required API Keys:**
```bash
ANTHROPIC_API_KEY=sk-ant-your-key
GOOGLE_PLACES_API_KEY=your-key
ZILLOW_API_KEY=your-key
```

**Optional API Keys:**
```bash
SKIP_TRACE_API_KEY=
DOCUSEAL_API_KEY=
VAPI_API_KEY=
ELEVENLABS_API_KEY=
EXA_API_KEY=
BRAVE_API_KEY=
```

### 2. Start Stack

```bash
# Automated startup (recommended)
./start-prod-stack.sh

# Or manual
docker-compose -f docker-compose-prod.yml up -d
```

### 3. Run Migrations (First Time Only)

```bash
# Option 1: Automatic (included in start script)
docker-compose -f docker-compose-prod.yml --profile migrations up migrations

# Option 2: Manual migration
docker exec ai-realtor-api alembic upgrade head
```

### 4. Verify Deployment

```bash
# Check API
curl http://localhost:8000/docs

# Check database
docker exec ai-realtor-db psql -U ai_realtor -d ai_realtor -c "SELECT 1"

# Check nanobot
docker logs nanobot-ai-realtor

# Check all services
docker-compose -f docker-compose-prod.yml ps
```

## Environment Variable Flow

```
docker-compose-prod.yml:
  nanobot:
    environment:
      - AI_REALTOR_API_URL=http://api:8000
              ↓
Docker passes to container:
              ↓
Inside nanobot container:
    export AI_REALTOR_API_URL="http://api:8000"
              ↓
Nanobot loads skill:
    /workspace/skills/ai-realtor/SKILL.md
              ↓
Skill instructs AI:
    "Check AI_REALTOR_API_URL env var"
              ↓
User: "Show me all properties"
              ↓
AI: curl "http://api:8000/properties/"
              ↓
Docker DNS: api → container IP
              ↓
FastAPI app receives request
              ↓
Returns JSON response
```

## File Structure

```
ai-realtor/
├── docker-compose-prod.yml     # Main orchestration
├── Dockerfile                    # API container definition
├── requirements-docker.txt       # Python dependencies
├── start-prod-stack.sh          # Automated startup
├── .env                         # Environment variables
├── .env.example                 # Environment template
├── app/                         # FastAPI application
│   ├── main.py                  # FastAPI app entry
│   ├── routers/                 # API endpoints
│   ├── models/                  # Database models
│   └── ...
├── alembic/                     # Database migrations
│   └── versions/
└── nanobot/                     # Nanobot config
    ├── skills/                  # AI Realtor skill
    │   └── ai-realtor/
    │       └── SKILL.md
    ├── workspace/               # Nanobot workspace
    └── memory/                  # Nanobot memory
```

## API Endpoints

Once running, the AI Realtor API exposes:

### Core Endpoints
- `POST /properties/` - Create property
- `GET /properties/` - List properties
- `POST /properties/{id}/enrich` - Zillow enrichment
- `POST /properties/{id}/skip-trace` - Owner discovery

### Contract Endpoints
- `GET /properties/{id}/contract-readiness` - Check readiness
- `POST /properties/{id}/attach-contracts` - Attach templates
- `GET /contracts/` - List contracts
- `POST /contracts/{id}/send` - Send for signature

### Marketing Endpoints
- `POST /agent-brand/{id}` - Create brand
- `POST /facebook-ads/campaigns/generate` - Generate ad
- `POST /postiz/posts/create` - Create social post

### Analytics Endpoints
- `GET /analytics/portfolio` - Portfolio summary
- `GET /analytics/pipeline` - Pipeline stats
- `POST /scoring/property/{id}` - Score property

**Plus 100+ more endpoints!**

Interactive docs: `http://localhost:8000/docs`

## Nanobot Voice Commands

Once deployed, interact with the API via voice:

```
"Show me all properties"
"Enrich property 5 with Zillow data"
"Is property 5 ready to close?"
"Attach the required contracts"
"Create a Facebook ad for property 5"
"How's my portfolio doing?"
"What needs attention?"
"Score property 5"
```

## Management Commands

### View Logs

```bash
# All services
docker-compose -f docker-compose-prod.yml logs -f

# API only
docker logs -f ai-realtor-api

# Nanobot only
docker logs -f nanobot-ai-realtor

# Database only
docker logs -f ai-realtor-db
```

### Access Containers

```bash
# API container
docker exec -it ai-realtor-api bash

# Nanobot container
docker exec -it nanobot-ai-realtor bash

# Database
docker exec -it ai-realtor-db psql -U ai_realtor -d ai_realtor
```

### Restart Services

```bash
# Restart all
docker-compose -f docker-compose-prod.yml restart

# Restart specific service
docker-compose -f docker-compose-prod.yml restart api
docker-compose -f docker-compose-prod.yml restart nanobot
```

### Stop Stack

```bash
# Stop all services
docker-compose -f docker-compose-prod.yml down

# Stop and remove volumes
docker-compose -f docker-compose-prod.yml down -v
```

### Rebuild

```bash
# Rebuild API image
docker-compose -f docker-compose-prod.yml build api

# Rebuild and restart
docker-compose -f docker-compose-prod.yml up -d --build
```

## Troubleshooting

### Issue: API not accessible

```bash
# Check container is running
docker ps | grep ai-realtor-api

# Check logs
docker logs ai-realtor-api

# Check health
curl http://localhost:8000/docs
```

### Issue: Nanobot can't reach API

```bash
# Check environment variable
docker exec nanobot-ai-realtor sh -c 'echo $AI_REALTOR_API_URL'
# Should output: http://api:8000

# Test from nanobot container
docker exec nanobot-ai-realtor curl http://api:8000/docs

# Check network
docker network inspect ai-realtor-network
```

### Issue: Database connection errors

```bash
# Check database is ready
docker exec ai-realtor-db pg_isready -U ai_realtor

# Check DATABASE_URL
docker exec ai-realtor-api sh -c 'echo $DATABASE_URL'

# Run migrations manually
docker exec ai-realtor-api alembic upgrade head
```

### Issue: Migration errors

```bash
# Check migration status
docker exec ai-realtor-api alembic current

# Reset migrations (⚠️  DEV ONLY!)
docker exec ai-realtor-api alembic downgrade base
docker exec ai-realtor-api alembic upgrade head
```

## Production Considerations

### Security

1. **Change default passwords**
   ```bash
   # In .env
   POSTGRES_PASSWORD=strong-password-here
   ```

2. **Use secrets management**
   ```bash
   # Docker secrets
   echo "sk-ant-key" | docker secret create anthropic_key -
   ```

3. **Enable HTTPS**
   - Add reverse proxy (Traefik/Nginx)
   - Use SSL certificates

### Monitoring

1. **Health checks**
   ```bash
   # API health
   curl http://localhost:8000/health

   # Service health
   docker-compose ps
   ```

2. **Logs**
   ```bash
   # Centralized logging
   docker-compose logs -f | tee logs.txt
   ```

3. **Metrics**
   - Add Prometheus endpoints
   - Monitor resource usage
   - Track API performance

### Scaling

```bash
# Scale API (with load balancer)
docker-compose -f docker-compose-prod.yml up -d --scale api=3

# Scale nanobot
docker-compose -f docker-compose-prod.yml up -d --scale nanobot=2
```

## Backup & Restore

### Backup Database

```bash
# Backup
docker exec ai-realtor-db pg_dump -U ai_realtor ai_realtor > backup.sql

# Restore
docker exec -i ai-realtor-db psql -U ai_realtor ai_realtor < backup.sql
```

### Backup Volume

```bash
# Backup volumes
docker run --rm -v ai_realtor_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup.tar.gz /data
```

## Summary

This deployment includes:

✅ **AI Realtor FastAPI Application** - The real API with 119+ endpoints
✅ **PostgreSQL Database** - Persistent data storage
✅ **Nanobot Integration** - Voice-controlled access
✅ **Automated Migrations** - Database setup
✅ **Health Checks** - Proper startup sequence
✅ **Environment Variables** - Flexible configuration
✅ **Production Ready** - Security, monitoring, scaling

**One command starts everything:**
```bash
./start-prod-stack.sh
```

The AI Realtor API + Nanobot skill = Voice-controlled real estate platform! 🏠✨

---

Generated with [Claude Code](https://claude.ai/code) via [Happy](https://happy.engineering)
