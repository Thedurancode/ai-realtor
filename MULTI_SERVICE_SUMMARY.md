# 🤖 AI Realtor + Nanobot - Complete Multi-Service Setup

## 🎯 What Was Created

### Files Created (4 files)

| File | Purpose |
|------|---------|
| `docker-compose-multi-service.yml` | Multi-service orchestration |
| `.env.multi-service.example` | Environment template |
| `start-multi-service.sh` | One-command setup script |
| `MULTI_SERVICE_GUIDE.md` | Complete documentation |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Docker Network (Bridge)                    │
│                  ai-platform-network                          │
└─────────────────────────────────────────────────────────────┘
         │                                    │
         ▼                                    ▼
┌─────────────────────────────┐  ┌──────────────────────────────┐
│      AI REALTOR            │  │       NANOBOT               │
│  • FastAPI Backend (8000)   │  │  • Chat Gateway (18790)     │
│  • MCP Server (8001)        │  │  • Multi-platform chat      │
│  • SQLite Database         │◄─┤  • Telegram                │
│  • 45+ tables              │  │  • Discord                 │
│  • 223+ API endpoints      │  │  • Slack                   │
│  • 135 MCP tools          │  │  • WhatsApp                │
└─────────────────────────────┘  │  • Email                   │
                                 │  • And more...              │
                                 └──────────────────────────────┘
                                            │
                                            ▼
                              ┌─────────────────────────┐
                              │      YOU (User)         │
                              │  Chat via your favorite │
                              │  platform                │
                              └─────────────────────────┘
```

---

## 🚀 Quick Start

### One Command Start
```bash
chmod +x start-multi-service.sh
./start-multi-service.sh
```

### Manual Start
```bash
# 1. Configure environment
cp .env.multi-service.example .env
nano .env  # Add your API keys

# 2. Start services
docker compose -f docker-compose-multi-service.yml up -d

# 3. View logs
docker compose -f docker-compose-multi-service.yml logs -f
```

---

## 💬 Example Chat Interactions

### Via Telegram Bot

**User:** "Create a property at 123 Main St, New York for $850,000"

**AI:** "✅ Property created successfully! Here are the details:
- Address: 123 Main St, New York, NY
- Price: $850,000
- Status: new_property
- ID: 1
- Next: Would you like me to enrich it with Zillow data?"

---

**User:** "Yes, enrich property 1"

**AI:** "✅ Enriched property 1 with Zillow data:
- Zestimate: $875,000
- 3 bedrooms, 2 bathrooms
- Built in 1920
- 2,100 sq ft
- Schools nearby: PS 123 (8/10), MS 456 (7/10)
Would you like me to skip trace to find the owner?"

---

**User:** "Show me all properties in New York"

**AI:** "Here are your properties in New York:
1. 123 Main St - $850,000
   - 3 bed, 2 bath, 2,100 sq ft
   - Zestimate: $875,000

2. 456 Oak Lane - $625,000
   - 2 bed, 1 bath, 1,200 sq ft
   - Not yet enriched

Total: 2 properties, $1,475,000 total value"

---

## 🎮 Supported Platforms

| Platform | Setup Difficulty | Features |
|----------|-----------------|----------|
| **Telegram** | ⭐ Easy (5 min) | Full support |
| **Discord** | ⭐⭐ Medium | Full support |
| **Slack** | ⭐⭐ Medium | Full support |
| **WhatsApp** | ⭐⭐⭐ Complex | QR code setup |
| **Email** | ⭐⭐ Medium | IMAP/SMTP config |

---

## 🔗 Service Communication

**Nanobot → AI Realtor API:**

```json
// Example: Create property request
POST http://ai-realtor:8000/properties/
Headers: {"x-api-key": "sk_live_xxx"}
Body: {
  "title": "123 Main St",
  "address": "123 Main Street",
  "city": "New York",
  "state": "NY",
  "zip_code": "10001",
  "price": 850000,
  "bedrooms": 3,
  "bathrooms": 2,
  "square_feet": 1800,
  "property_type": "HOUSE",
  "agent_id": 1
}
```

---

## 📊 Service Dependencies

```
nanobot:
  depends_on:
    ai-realtor:
      condition: service_healthy
```

This means:
- Nanobot waits for AI Realtor to be healthy before starting
- If AI Realtor crashes, Nanobot keeps running
- When AI Realtor recovers, Nanobot can use it again

---

## 🌐 Access URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **AI Realtor API** | http://localhost:8000 | REST API |
| **AI Realtor Docs** | http://localhost:8000/docs | Interactive docs |
| **AI Realtor Health** | http://localhost:8000/health | Health check |
| **Nanobot Gateway** | http://localhost:18790 | Chat gateway |

---

## 🛠️ Management Commands

```bash
# Start
docker compose -f docker-compose-multi-service.yml up -d

# Logs
docker compose -f docker-compose-multi-service.yml logs -f

# Restart
docker compose -f docker-compose-multi-service.yml restart

# Stop
docker compose -f docker-compose-multi-service.yml down

# Rebuild
docker compose -f docker-compose-multi-service.yml up -d --build

# Status
docker compose -f docker-compose-multi-service.yml ps
```

---

## 💾 Data Persistence

Two Docker volumes keep your data safe:

| Volume | Purpose |
|--------|---------|
| `ai_realtor_sqlite_data` | AI Realtor database + backups |
| `nanobot_config_data` | Nanobot config + workspace |

**List volumes:**
```bash
docker volume ls | grep -E "ai_realtor|nanobot"
```

---

## 🧪 Testing Integration

### Test 1: Health Checks
```bash
curl http://localhost:8000/health
curl http://localhost:18790/health
```

### Test 2: Create Property via API
```bash
curl -X POST http://localhost:8000/properties/ \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk_live_xxx" \
  -d @/tmp/test_property_fixed.json
```

### Test 3: Via Chat Platform
Send a message to your bot:
- "Show me all properties"
- "Create a property at 123 Main St, New York, $500,000"
- "Enrich property 1"

---

## 🔧 Configuration Options

### AI Provider
Choose which LLM provider Nanobot uses:
- **Anthropic** (Claude) - Recommended
- **OpenRouter** (Access to all models)
- **OpenAI** (GPT-4)
- **DeepSeek**, **Groq**, **Gemini**, etc.

### Chat Platform
Configure one or more:
- Telegram (easiest, 5 minutes)
- Discord (medium, 15 minutes)
- Slack (medium, 15 minutes)
- WhatsApp (complex, 30 minutes)
- Email (medium, 10 minutes)

---

## 📈 Resource Usage

| Service | Memory | CPU | Disk |
|---------|--------|-----|------|
| AI Realtor | ~300 MB | <5% idle | ~50 MB |
| Nanobot | ~200 MB | <3% idle | ~100 MB |
| **Total** | ~500 MB | ~8% idle | ~150 MB |

---

## 🎓 Next Steps

1. **Configure API Keys** in `.env`
   - ANTHROPIC_API_KEY (required)
   - GOOGLE_PLACES_API_KEY (addresses)
   - RAPIDAPI_KEY (Zillow/Skip Trace)

2. **Setup Chat Platform**
   - Telegram recommended (easiest)
   - Get bot token from @BotFather

3. **Test Integration**
   - Send test message to your bot
   - Try voice commands

4. **Explore**
   - Read [MULTI_SERVICE_GUIDE.md](./MULTI_SERVICE_GUIDE.md)
   - Check http://localhost:8000/docs

---

## 🆚 Troubleshooting

### Problem: Nanobot can't reach AI Realtor

**Solution:** Check network
```bash
docker network inspect ai-platform-network
docker exec nanobot-gateway curl http://ai-realtor:8000/health
```

### Problem: Chat bot not responding

**Solution:** Check chat platform config
```bash
# Verify token in .env
grep TELEGRAM_BOT_TOKEN .env

# Check Nanobot logs
docker compose -f docker-compose-multi-service.yml logs -f nanobot
```

### Problem: Port already in use

**Solution:** Stop existing containers
```bash
docker compose -f docker-compose.sqlite.yml down
docker compose -f docker-compose-multi-service.yml up -d
```

---

## 📚 Documentation

- [MULTI_SERVICE_GUIDE.md](./MULTI_SERVICE_GUIDE.md) - Complete guide
- [DOCKER_SQLITE_GUIDE.md](./DOCKER_SQLITE_GUIDE.md) - AI Realtor Docker guide
- [CLAUDE.md](./CLAUDE.md) - Full platform docs
- http://localhost:8000/docs - API documentation

---

## 🤝 Integration Diagram

```
User (Telegram/Discord/Slack/WhatsApp/Email)
                    ↓
              Nanobot Gateway
              (Chat Platform Handler)
                    ↓
              AI Processing (Claude/GPT-4)
                    ↓
              API Call to AI Realtor
                    ↓
              ┌──────────────────┐
              │  AI Realtor API   │
              │  - Properties    │
              │  - Contacts      │
              │  - Contracts     │
              │  - Enrichment    │
              │  - Skip Trace    │
              └──────────────────┘
                    ↓
              Database (SQLite)
                    ↓
              Response → Nanobot
                    ↓
              User receives reply
```

---

**Made with ❤️ by the AI Realtor Team**

*Last Updated: February 2026*
