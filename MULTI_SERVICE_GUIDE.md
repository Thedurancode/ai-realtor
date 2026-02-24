# 🤖 AI Realtor + Nanobot - Multi-Service Setup

Run **AI Realtor** and **Nanobot** together in Docker for a complete AI-powered real estate assistant with multi-platform chat integration.

---

## 🎯 What This Does

| Service | Purpose | Port |
|---------|---------|------|
| **AI Realtor** | Real estate management platform | 8000, 8001 |
| **Nanobot** | AI assistant chat gateway | 18790 |

**Together they provide:**
- Chat with your AI Realtor platform via Telegram, Discord, Slack, Email, etc.
- Natural language property management
- Multi-platform accessibility
- Voice control through chat

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network                            │
│                  (ai-platform-network)                       │
└─────────────────────────────────────────────────────────────┘
         │                                    │
         ▼                                    ▼
┌─────────────────────────────┐  ┌──────────────────────────────┐
│      AI REALTOR            │  │       NANOBOT               │
│  ┌───────────────────────┐  │  ┌──────────────────────────┐ │
│  │  FastAPI Backend     │  │  │  Chat Gateway            │ │
│  │  Port 8000          │◄─┼─►│  Port 18790              │ │
│  └───────────────────────┘  │  │  - Telegram              │ │
│  ┌───────────────────────┐  │  │  - Discord               │ │
│  │  MCP Server          │  │  │  - Slack                 │ │
│  │  Port 8001          │  │  │  - WhatsApp              │ │
│  └───────────────────────┘  │  │  - Email                 │ │
│                             │  │  - And more...            │ │
│  SQLite Database            │  └──────────────────────────┘ │
│  (45+ tables)               │            │                    │
└─────────────────────────────┘            │                    │
         │                                  │
         ▼                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      Users                                   │
│  Chat with AI Realtor via:                                │
│  • Telegram Bot                                              │
│  • Discord Bot                                              │
│  • Slack Bot                                                │
│  • WhatsApp                                                 │
│  • Email                                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Option 1: Automated Setup

```bash
# Make script executable
chmod +x start-multi-service.sh

# Run it!
./start-multi-service.sh
```

### Option 2: Manual Setup

```bash
# 1. Copy environment template
cp .env.multi-service.example .env

# 2. Edit .env and add your API keys
nano .env  # or use your favorite editor

# 3. Pull Nanobot image
docker pull ghcr.io/hkuds/nanobot:latest

# 4. Build and start
docker compose -f docker-compose-multi-service.yml up -d

# 5. View logs
docker compose -f docker-compose-multi-service.yml logs -f
```

---

## 🔧 Configuration

### Required API Keys

Create a `.env` file with these keys:

```bash
# AI Provider (for Nanobot)
ANTHROPIC_API_KEY=sk-ant-xxx

# AI Realtor API Keys
GOOGLE_PLACES_API_KEY=xxx
RAPIDAPI_KEY=xxx
```

### Chat Platform (Choose One)

**Telegram (Recommended - Easiest):**
```bash
# 1. Message @BotFather on Telegram
# 2. Send /newbot and follow prompts
# 3. Copy the token
TELEGRAM_BOT_TOKEN=your-bot-token-here
TELEGRAM_ALLOW_FROM=your-user-id
```

**Discord:**
```bash
# 1. Go to https://discord.com/developers/applications
# 2. Create bot and get token
# 3. Enable MESSAGE CONTENT INTENT
DISCORD_BOT_TOKEN=your-bot-token
DISCORD_ALLOW_FROM=your-discord-user-id
```

**Slack:**
```bash
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
```

---

## 💬 How to Use

### Via Telegram (Example)

1. **Setup Telegram Bot** (one time)
   - Open Telegram, search `@BotFather`
   - Send `/newbot`, follow instructions
   - Copy the token to `.env` file

2. **Start the platform**
   ```bash
   ./start-multi-service.sh
   ```

3. **Chat with your AI Realtor**
   - Open Telegram
   - Find your bot and start chatting
   - Try these commands:
     - "Create a property at 123 Main St, New York for $850,000"
     - "Show me all properties in New York"
     - "Enrich property 1"
     - "Add John Smith as a buyer for property 1"

---

## 🌐 Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| AI Realtor API | http://localhost:8000 | Main API |
| AI Realtor Docs | http://localhost:8000/docs | Interactive documentation |
| AI Realtor Health | http://localhost:8000/health | Health check |
| Nanobot Gateway | http://localhost:18790 | Chat gateway |

---

## 🔄 How They Work Together

### Example Flow: "Create a property"

1. **User** sends Telegram message: "Create a property at 123 Main St for $500,000"

2. **Nanobot** receives the message via Telegram

3. **Nanobot** processes with AI and decides to call AI Realtor API

4. **AI Realtor** API receives the request:
   ```http
   POST /properties/
   {
     "address": "123 Main St",
     "city": "New York",
     "price": 500000
   }
   ```

5. **AI Realtor** creates property and returns response

6. **Nanobot** formats response and sends back to Telegram

7. **User** sees: "✅ Property created successfully at 123 Main St, New York, $500,000"

---

## 🛠️ Common Commands

### View Logs
```bash
docker compose -f docker-compose-multi-service.yml logs -f
```

### Follow Specific Service
```bash
docker compose -f docker-compose-multi-service.yml logs -f ai-realtor
docker compose -f docker-compose-multi-service.yml logs -f nanobot
```

### Restart Services
```bash
docker compose -f docker-compose-multi-service.yml restart
```

### Stop Everything
```bash
docker compose -f docker-compose-multi-service.yml down
```

### Rebuild After Changes
```bash
docker compose -f docker-compose-multi-service.yml up -d --build
```

### Check Container Status
```bash
docker compose -f docker-compose-multi-service.yml ps
```

---

## 📊 Container Status

```bash
$ docker compose -f docker-compose-multi-service.yml ps

NAME                STATUS    PORTS
ai-realtor-sqlite    Up        0.0.0.0:8000->8000/tcp, 0.0.0.0:8001->8001/tcp
nanobot-gateway     Up        0.0.0.0:18790->18790/tcp
```

---

## 🔗 Network Communication

Both services run on the same Docker network (`ai-platform-network`), so they can communicate:

**Nanobot → AI Realtor:**
```bash
# From inside Nanobot container
curl http://ai-realtor:8000/properties/
```

**Environment variable set:**
```bash
NANOBOT_AI_REALTOR_API_BASE_URL=http://ai-realtor:8000
```

---

## 📁 Persistent Data

| Service | Volume | Contents |
|---------|--------|----------|
| AI Realtor | `ai_realtor_sqlite_data` | SQLite database, backups |
| Nanobot | `nanobot_config_data` | Config, workspace |

**List volumes:**
```bash
docker volume ls | grep ai
```

**Backup volume:**
```bash
docker run --rm -v ai_realtor_sqlite_data:/data -v $(pwd):/backup ubuntu \
  tar czf /backup/ai-realtor-backup.tar.gz /data
```

---

## 🧪 Testing the Integration

### 1. Test AI Realtor API
```bash
curl http://localhost:8000/health
```

### 2. Test Nanobot Gateway
```bash
curl http://localhost:18790/health
```

### 3. Test Integration
```bash
# Via your chat platform (Telegram/Discord/Slack):
"Show me all properties"
"Create a property at 123 Main St, New York, $500,000"
"Enrich property 1"
```

---

## 🎓 Voice Commands

Through Nanobot's chat interface, you can use natural language:

| Command | Description |
|---------|-------------|
| "Create a property at [address] for [price]" | Create new property |
| "Show me all [city] properties" | List properties |
| "Enrich property [id]" | Add Zillow data |
| "Skip trace property [id]" | Find owner info |
| "Add [name] as a buyer for property [id]" | Add contact |
| "What's the status of property [id]?" | Check status |
| "Score property [id]" | Deal analysis |

---

## 🔒 Security

### AI Realtor API Key
The Nanobot container has access to the AI Realtor API via environment variable. You can also pass an API key:

```bash
NANOBOT_AI_REALTOR_KEY=sk_live_xxx
```

### Restrict Chat Access
Configure `allowFrom` in your chat platform to restrict who can use your bot:

```bash
# Telegram
TELEGRAM_ALLOW_FROM=["123456789", "987654321"]

# Discord
DISCORD_ALLOW_FROM=["123456789012345678"]
```

---

## 📈 Scaling

### Resource Limits
Add to `docker-compose-multi-service.yml`:

```yaml
services:
  ai-realtor:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G

  nanobot:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

---

## 🐛 Troubleshooting

### Containers Not Starting
```bash
# Check logs
docker compose -f docker-compose-multi-service.yml logs

# Check health
curl http://localhost:8000/health
curl http://localhost:18790/health
```

### Nanobot Can't Reach AI Realtor
```bash
# Check network
docker network inspect ai-platform-network

# Test connection from Nanobot container
docker exec nanobot-gateway curl http://ai-realtor:8000/health
```

### Port Already in Use
```bash
# Check what's using the port
lsof -i :8000
lsof -i :18790

# Stop conflicting services
docker compose -f docker-compose-multi-service.yml down
```

---

## 🚀 Next Steps

1. **Configure API Keys** - Add your keys to `.env`
2. **Setup Chat Platform** - Configure Telegram/Discord/Slack
3. **Test Integration** - Send a test message
4. **Customize** - Add more channels or configure Nanobot skills

---

## 📚 Documentation

- **AI Realtor:** [CLAUDE.md](./CLAUDE.md) - Full platform documentation
- **AI Realtor:** http://localhost:8000/docs - API documentation
- **Nanobot:** https://github.com/HKUDS/nanobot - Nanobot repository

---

**Made with ❤️ by the AI Realtor Team**
