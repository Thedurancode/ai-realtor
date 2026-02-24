# AI Realtor + Nanobot Docker Deployment

Complete Docker stack with proper service startup sequence and environment variable passing.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Network                          │
│                 (ai-realtor-network)                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │ PostgreSQL   │         │ AI Realtor   │                 │
│  │   :5432      │◄────────┤   API        │                 │
│  │              │         │   :8000      │                 │
│  └──────────────┘         └──────┬───────┘                 │
│                                   │                          │
│                                   │ AI_REALTOR_API_URL      │
│                                   │ = http://ai-realtor-api │
│                                   │       :8000              │
│                                   │                          │
│                            ┌──────▼───────┐                 │
│                            │   Nanobot    │                 │
│                            │  (with skill) │                 │
│                            └──────────────┘                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Startup Sequence

```
1. docker-compose up
   ↓
2. PostgreSQL starts (port 5432)
   ↓
3. AI Realtor API starts (port 8000)
   - Waits for PostgreSQL
   - Runs migrations
   - Healthcheck: /docs endpoint
   ↓
4. Nanobot starts (after API is healthy)
   - Receives AI_REALTOR_API_URL env var
   - Loads AI Realtor skill
   - Ready for voice commands!
```

## Quick Start

### 1. Create Environment File

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-your-key
GOOGLE_PLACES_API_KEY=your-key
ZILLOW_API_KEY=your-key
# ... other API keys
```

### 2. Start the Stack

```bash
# Automated startup
./start-stack.sh

# Or manual
docker-compose -f docker-compose-ai-realtor.yml up -d
```

### 3. Verify Services

```bash
# Check all services running
docker-compose -f docker-compose-ai-realtor.yml ps

# Check API is accessible
curl http://localhost:8000/docs

# View nanobot logs
docker logs -f nanobot-ai-realtor
```

### 4. Interact with Nanobot

```bash
# Attach to nanobot container
docker exec -it nanobot-ai-realtor bash

# Inside container, check environment
echo $AI_REALTOR_API_URL
# Output: http://ai-realtor-api:8000

# Test skill is loaded
ls /workspace/skills/
# Should see: ai-realtor/

# Try voice command (via nanobot CLI)
"Show me all properties"
```

## Environment Variable Flow

### Docker Compose → Container

```yaml
# docker-compose-ai-realtor.yml
services:
  nanobot:
    environment:
      - AI_REALTOR_API_URL=http://ai-realtor-api:8000
                              ^^^^^^^^^^^^^^^^^^^^
                              Docker service name
```

### Inside Nanobot Container

```bash
# Container startup
export AI_REALTOR_API_URL="http://ai-realtor-api:8000"

# Nanobot loads skill
# Skill tells AI: "Check AI_REALTOR_API_URL environment variable"

# User asks: "Show me all properties"
# AI checks: echo $AI_REALTOR_API_URL
# AI uses: curl "http://ai-realtor-api:8000/properties/"
#                  ^^^^^^^^^^^^^^^^^^^^^^^^^
#                  Docker internal DNS
```

## Service Discovery

### How Nanobot Finds the API

**Inside Docker network:**
- Uses service name: `ai-realtor-api`
- Full URL: `http://ai-realtor-api:8000`
- Docker's internal DNS resolves this

**From host machine:**
- Uses localhost: `http://localhost:8000`
- Port mapping: `8000:8000`

**Why different URLs?**
- **Internal** (container-to-container): Service names
- **External** (host-to-container): Localhost + port

## Docker Compose Configuration

### Key Sections

```yaml
services:
  ai-realtor-api:
    # Healthcheck ensures API is ready before nanobot starts
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/docs"]
      interval: 30s
      retries: 3
      start_period: 40s

  nanobot:
    # Depends on API being healthy
    depends_on:
      ai-realtor-api:
        condition: service_healthy

    # Environment variable passed here
    environment:
      - AI_REALTOR_API_URL=http://ai-realtor-api:8000
```

### Volume Mounts

```yaml
nanobot:
  volumes:
    # Mount skill into container
    - ./nanobot/skills:/workspace/skills:ro

    # Workspace for persistence
    - ./nanobot/workspace:/workspace:rw

    # Memory for conversations
    - ./nanobot/memory:/workspace/memory:rw
```

## Managing the Stack

### Start

```bash
# Start all services
docker-compose -f docker-compose-ai-realtor.yml up -d

# Or use automated script
./start-stack.sh
```

### Stop

```bash
# Stop all services
docker-compose -f docker-compose-ai-realtor.yml down

# Stop and remove volumes
docker-compose -f docker-compose-ai-realtor.yml down -v
```

### View Logs

```bash
# All services
docker-compose -f docker-compose-ai-realtor.yml logs -f

# Specific service
docker logs -f nanobot-ai-realtor
docker logs -f ai-realtor-api
```

### Restart

```bash
# Restart all
docker-compose -f docker-compose-ai-realtor.yml restart

# Restart specific service
docker-compose -f docker-compose-ai-realtor.yml restart nanobot
```

## Troubleshooting

### Issue: Nanobot can't reach API

**Check:**
```bash
# From host
curl http://localhost:8000/docs

# From nanobot container
docker exec nanobot-ai-realtor curl http://ai-realtor-api:8000/docs

# Check environment variable
docker exec nanobot-ai-realtor env | grep AI_REALTOR
```

**Solution:**
- Verify services are on same network
- Check service name matches
- Ensure API is healthy before nanobot starts

### Issue: Services start in wrong order

**Check:**
```bash
# View dependency status
docker-compose -f docker-compose-ai-realtor.yml ps -a
```

**Solution:**
- Verify `depends_on` with healthcheck
- Ensure healthcheck endpoint exists
- Check healthcheck configuration

### Issue: Environment variable not set

**Check:**
```bash
# Inside nanobot container
docker exec nanobot-ai-realtor bash
echo $AI_REALTOR_API_URL
```

**Solution:**
- Verify `.env` file exists
- Check docker-compose.yml environment section
- Restart stack after changes

## Production Deployment

### Use Docker Secrets

```yaml
version: '3.8'

services:
  nanobot:
    environment:
      - AI_REALTOR_API_URL=http://ai-realtor-api:8000
    secrets:
      - anthropic_api_key
      - google_places_key

secrets:
  anthropic_api_key:
    external: true
  google_places_key:
    external: true
```

### Set Secrets

```bash
# Create secrets
echo "sk-ant-your-key" | docker secret create anthropic_api_key -
echo "your-key" | docker secret create google_places_key -
```

## Multi-Stage Deployment

### Development

```bash
# Use local build
export COMPOSE_FILE=docker-compose-ai-realtor.yml
docker-compose up -d
```

### Staging

```bash
# Use staging API
export AI_REALTOR_API_URL=https://staging.ai-realtor.com
docker-compose -f docker-compose-ai-realtor.yml up -d
```

### Production

```bash
# Use production API
export AI_REALTOR_API_URL=https://ai-realtor.fly.dev
docker-compose -f docker-compose-ai-realtor.yml up -d
```

## Verification Checklist

- [ ] `.env` file configured with API keys
- [ ] Docker network created: `ai-realtor-network`
- [ ] PostgreSQL is healthy
- [ ] API is accessible: `curl http://localhost:8000/docs`
- [ ] Nanobot container has `AI_REALTOR_API_URL` set
- [ ] Skill is mounted: `ls /workspace/skills/ai-realtor/`
- [ ] Nanobot can reach API internally
- [ ] Voice commands work: "Show me all properties"

## Architecture Benefits

✅ **Isolation** - Each service in its own container
✅ **Startup Order** - Healthchecks ensure proper sequence
✅ **Service Discovery** - Docker DNS for internal communication
✅ **Environment** - Variables passed securely
✅ **Persistence** - Volumes for data and workspace
✅ **Scalability** - Easy to scale individual services
✅ **Maintainability** - Easy to update/restart services

## Summary

**The flow:**

1. Docker Compose starts services in dependency order
2. API gets healthy (healthcheck passes)
3. Nanobot starts with `AI_REALTOR_API_URL` env var
4. Nanobot loads AI Realtor skill
5. Skill tells AI to check environment variable
6. AI uses detected URL for all commands

**One environment variable, seamless integration!**

---

Generated with [Claude Code](https://claude.ai/code) via [Happy](https://happy.engineering)
