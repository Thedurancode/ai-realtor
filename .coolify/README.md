# AI Realtor + Nanobot - Coolify Deployment

Complete deployment package for AI Realtor Platform with Nanobot Gateway on Coolify.

---

## 🚀 Quick Deploy (15 minutes)

See **[QUICKSTART.md](./QUICKSTART.md)** for the fastest deployment path.

**Steps:**
1. Push code to GitHub
2. Build and push Docker images
3. Create service in Coolify
4. Add environment variables
5. Deploy

---

## 📚 Documentation

| File | Description |
|------|-------------|
| **[QUICKSTART.md](./QUICKSTART.md)** | 15-minute fast deployment guide |
| **[deployment-guide.md](./deployment-guide.md)** | Complete deployment documentation |
| **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** | Common issues and solutions |
| **[.env.example.coolify](./.env.example.coolify)** | Environment variables template |
| **[../docker-compose.coolify.yml](../docker-compose.coolify.yml)** | Coolify-optimized compose file |

---

## 🎯 What You're Deploying

### AI Realtor Platform
- **135+ MCP tools** for voice control via Claude Desktop
- **Property management** with Zillow enrichment
- **Contract management** with DocuSeal e-signatures
- **Skip tracing** for owner contact discovery
- **Intelligence features** - Predictive analytics, market scanning, relationship scoring
- **Phone calls** via VAPI integration
- **Telegram bot** @Smartrealtoraibot

### Nanobot Gateway
- **Multi-platform chat** - Telegram, Discord, Slack, WhatsApp
- **AI-powered** - Uses Zhipu AI (GLM-4.7) or Anthropic Claude
- **Universal translator** - Connects any chat app to any AI service

---

## 📋 Prerequisites

### Required
- ✅ Coolify instance (self-hosted or cloud)
- ✅ Server with 2+ CPU cores, 4+ GB RAM
- ✅ Git repository (GitHub, GitLab, etc.)
- ✅ 5 Essential API Keys:
  - Google Places API
  - RapidAPI (Zillow + Skip Trace)
  - DocuSeal
  - Telegram Bot
  - Zhipu AI

### Optional
- ⚪ Domain name (for automatic SSL)
- ⚪ Additional API keys (Anthropic, VAPI, ElevenLabs, Resend, Exa)

---

## 🔑 Get API Keys

**Quick links:**
- [Google Places API](https://console.cloud.google.com/apis/library/places-backend.googleapis.com) - Free tier: 200/day
- [RapidAPI](https://rapidapi.com) - Zillow + Skip Trace (free tier available)
- [DocuSeal](https://docuseal.com) - Self-hosted free, cloud from $9/month
- [Telegram Bot](https://telegram.me/BotFather) - Free
- [Zhipu AI](https://open.bigmodel.cn/) - ~$0.50/1M tokens
- [Anthropic Claude](https://console.anthropic.com/) - ~$3/1M input tokens
- [VAPI](https://vapi.ai) - ~$0.10/minute
- [ElevenLabs](https://elevenlabs.io) - ~$5-22/10k characters
- [Resend](https://resend.com) - Free tier: 3,000 emails/month
- [Exa AI](https://exa.ai) - Free tier available

**Estimated monthly cost:** $5-50 depending on features

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Coolify PaaS                        │
│  ┌───────────────────────────────────────────────────┐  │
│  │         AI Realtor Container                       │  │
│  │  • FastAPI Backend (port 8000)                    │  │
│  │  • MCP Server (port 8001)                         │  │
│  │  • SQLite Database (persistent volume)            │  │
│  │  • Background workers (campaigns, daily digest)    │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │         Nanobot Container                         │  │
│  │  • Gateway Server (port 18790)                    │  │
│  │  • Multi-platform chat bridges                    │  │
│  │  • AI Agent (Zhipu/Claude)                        │  │
│  │  • AI Realtor Skill integration                   │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  Persistent Volumes:                                    │
│  • ai_realtor_sqlite_data (database)                   │
│  • nanobot_config_data (config)                        │
│  • nanobot_skills_data (skills)                        │
│                                                          │
│  Automatic SSL (Let's Encrypt):                         │
│  • ai-realtor.your-domain.com                          │
│  • nanobot.your-domain.com                             │
└─────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────┐         ┌────────────────────┐
│ Claude Desktop  │         │  Telegram Bot      │
│  (MCP Protocol) │         │ @Smartrealtoraibot │
└─────────────────┘         └────────────────────┘
```

---

## 🛠️ Deployment Methods

### Method 1: Use Pre-built Images (Fastest)

If images are already pushed to a registry:

1. Create Docker Compose service in Coolify
2. Use `docker-compose.coolify.yml`
3. Add environment variables
4. Deploy

**Time:** 5 minutes

---

### Method 2: Build with Script (Recommended)

Build and push images using the provided script:

```bash
./scripts/coolify-build.sh docker.io your-username
```

Then deploy in Coolify.

**Time:** 10 minutes

---

### Method 3: Let Coolify Build from Git

Coolify will build images directly from your GitHub repository:

1. Push code to GitHub
2. In Coolify, select "From GitHub"
3. Choose repository
4. Set Dockerfile paths:
   - AI Realtor: `Dockerfile.sqlite`
   - Nanobot: `nanobot/Dockerfile`

**Time:** 20 minutes (first build)

---

## 🔧 Configuration

### Environment Variables

Copy `.env.example.coolify` and add to Coolify:

**Essential:**
```bash
GOOGLE_PLACES_API_KEY=your_key
RAPIDAPI_KEY=your_key
DOCUSEAL_API_KEY=your_key
TELEGRAM_BOT_TOKEN=your_token
ZHIPU_API_KEY=your_key
```

**Optional:**
```bash
ANTHROPIC_API_KEY=sk-ant-your-key
VAPI_API_KEY=your_key
ELEVENLABS_API_KEY=your_key
RESEND_API_KEY=re_your_key
EXA_API_KEY=your_key
```

See **[.env.example.coolify](./.env.example.coolify)** for complete list.

---

### Post-Deployment: Nanobot Config

After containers start, configure Nanobot:

```bash
docker exec -it nanobot-gateway bash

cat > /root/.nanobot/config.json << 'EOF'
{
  "agents": {
    "defaults": {
      "model": "glm-4.7",
      "provider": "openai"
    }
  },
  "providers": {
    "openai": {
      "api_key": "${ZHIPU_API_KEY}",
      "api_base": "https://open.bigmodel.cn/api/paas/v4"
    }
  },
  "skills": {
    "ai-realtor": {
      "type": "api",
      "endpoint": "http://ai-realtor-sqlite:8000"
    }
  }
}
EOF

exit
docker restart nanobot-gateway
```

---

## ✅ Testing Your Deployment

### 1. Health Checks

```bash
# AI Realtor
curl https://ai-realtor.your-domain.com/health

# Nanobot
curl https://nanobot.your-domain.com/health
```

### 2. API Test

```bash
curl -X POST https://ai-realtor.your-domain.com/properties/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Property",
    "address": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip_code": "10001",
    "price": 850000,
    "property_type": "HOUSE"
  }'
```

### 3. Telegram Bot Test

1. Open Telegram
2. Find @Smartrealtoraibot
3. Send: "Show me all properties"

---

## 📊 Features After Deployment

### ✅ Working Immediately
- Property CRUD operations
- Zillow data enrichment
- Skip tracing
- Contract management
- DocuSeal e-signatures
- Telegram bot interface
- MCP voice commands (135+ tools)
- Property recaps (if Anthropic key provided)

### 🚧 Require Additional Configuration
- Phone calls (VAPI + ElevenLabs keys)
- Email notifications (Resend key)
- Advanced research (Exa AI key)

---

## 🔄 Updates

### Automatic Updates (Git-Based)

1. Push changes to GitHub
2. In Coolify, click "Deploy"
3. Images rebuild and redeploy

### Manual Updates

```bash
# Rebuild images
docker build -f Dockerfile.sqlite -t your-username/ai-realtor-sqlite:latest .
docker push your-username/ai-realtor-sqlite:latest

# Redeploy in Coolify
```

---

## 💾 Backups

### Automated Backups

Add to Coolify cron jobs:

```bash
# Daily database backup at 2 AM
0 2 * * * docker exec ai-realtor-sqlite sqlite3 /app/data/ai_realtor.db ".backup /app/data/backup_$(date +\%Y\%m\%d).db"
```

### Manual Backup

```bash
# Copy database from container
docker cp ai-realtor-sqlite:/app/data/ai_realtor.db ./backup_$(date +%Y%m%d).db
```

---

## 📈 Scaling

### Vertical Scaling (More Power)

In Coolify → Your Service → Resources:
- CPU: 2-4 cores recommended
- RAM: 4-8GB recommended
- Storage: 50GB+ recommended

### Horizontal Scaling

- **AI Realtor:** ❌ Cannot scale (SQLite single instance)
- **Nanobot:** ✅ Can scale (stateless)

Set replicas in Coolify → Settings → Replicas

---

## 🔒 Security

### Best Practices

1. ✅ Use HTTPS (automatic with Coolify)
2. ✅ Store API keys in Coolify secrets (not in Git)
3. ✅ Use firewall rules to limit access
4. ✅ Regular updates (Coolify, Docker images, dependencies)
5. ✅ Automated backups
6. ✅ Monitor logs and resource usage

### Firewall Rules

```bash
# Allow only necessary ports
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 22/tcp    # SSH
sudo ufw enable
```

---

## 🐛 Troubleshooting

### Quick Fixes

**Most issues are fixed by:**
1. Restarting containers (50%)
2. Checking environment variables (30%)
3. Rebuilding images (15%)
4. Checking networking (5%)

```bash
# Restart everything
docker restart ai-realtor-sqlite nanobot-gateway

# View logs
docker logs -f ai-realtor-sqlite
docker logs -f nanobot-gateway
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Container won't start | Check logs, verify env vars |
| Nanobot can't reach API | Check network, verify service name |
| Database locked | Restart container |
| SSL certificate error | Check DNS, force renewal |
| Telegram bot not responding | Verify token, check Nanobot config |

See **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** for complete guide.

---

## 📞 Support

### Documentation
- **[AI Realtor Docs](../CLAUDE.md)** - Complete platform features
- **[Coolify Docs](https://coolify.io/docs)** - Coolify PaaS documentation
- **[Nanobot Docs](https://github.com/nanobot/nanobot)** - Nanobot gateway

### Community
- **GitHub Issues:** https://github.com/Thedurancode/ai-realtor/issues
- **Telegram:** @Smartrealtoraibot (after deployment)

### Debug Info Collection

```bash
# System info
docker version
docker ps -a
docker network ls
docker volume ls
docker stats --no-stream

# Logs
docker logs --tail 100 ai-realtor-sqlite > ai-realtor.log
docker logs --tail 100 nanobot-gateway > nanobot.log
```

---

## 📝 Deployment Checklist

- [ ] Coolify server running
- [ ] Domain configured (optional but recommended)
- [ ] Code pushed to GitHub
- [ ] Docker images built and pushed
- [ ] Application created in Coolify
- [ ] Environment variables configured (5 required)
- [ ] Persistent volumes created
- [ ] Services deployed and healthy
- [ ] Nanobot configured with Zhipu AI
- [ ] Telegram bot tested
- [ ] API tested successfully
- [ ] Custom domain configured (if applicable)
- [ ] SSL certificates issued
- [ ] Backup strategy configured
- [ ] Monitoring and alerts set up

---

## 💰 Cost Estimation

### Coolify Cloud (Managed)
- **Plan:** $5-20/month
- **Compute:** $10-50/month (depending on resources)
- **Total:** ~$15-70/month

### Self-Hosted (Your Server)
- **Server:** $5-20/month (Hetzner, DigitalOcean, Linode)
- **Domain:** $10-15/year
- **SSL:** Free (Let's Encrypt)
- **APIs:** $5-50/month (depending on usage)
- **Total:** ~$10-70/month

### API Costs Breakdown

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| Google Places | 200 requests/day | $0 (generous free tier) |
| RapidAPI | Limited | $0-50/month |
| DocuSeal | Self-hosted free | $9/month cloud |
| Zhipu AI | None | ~$5-20/month |
| Anthropic | None | ~$20-50/month |
| Telegram | Free | Free |
| **Total** | **$0-5/month** | **$20-150/month** |

---

## 🎉 You're Ready!

Follow **[QUICKSTART.md](./QUICKSTART.md)** to deploy in 15 minutes.

**Questions?** Check **[TROUBLESHOOTING.md](./TROUBLESHOOTING.md)** or open a GitHub issue.

---

**Deployment Time:** ~15 minutes
**Total Cost:** $10-70/month
**Status:** ✅ Production Ready

Good luck! 🚀
