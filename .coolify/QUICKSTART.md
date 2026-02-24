# Deploy AI Realtor to Coolify - Quick Start

Fastest way to get AI Realtor + Nanobot running on Coolify.

## Prerequisites Check

Before you start, make sure you have:

- [ ] A Coolify instance running (https://coolify.io)
- [ ] A server with at least 2 CPU cores and 4GB RAM
- [ ] Domain name configured (optional but recommended for SSL)
- [ ] Git repository with your code (GitHub, GitLab, etc.)
- [ ] At least these 5 API keys:
  - Google Places API Key
  - RapidAPI Key
  - DocuSeal API Key
  - Telegram Bot Token
  - Zhipu AI API Key

**Don't have API keys yet?** See `.env.example.coolify` for quick links to get them.

---

## 5-Minute Deployment

### Step 1: Push Code to GitHub (2 minutes)

```bash
# If not already in Git
git init
git add .
git commit -m "Add Coolify deployment files"

# Create repo on GitHub first, then:
git remote add origin https://github.com/your-username/ai-realtor.git
git push -u origin main
```

### Step 2: Build and Push Docker Images (3 minutes)

**Option A: Use the build script (recommended)**

```bash
# For Docker Hub
./scripts/coolify-build.sh docker.io your-dockerhub-username

# For GitHub Container Registry
./scripts/coolify-build.sh ghcr.io your-github-username
```

**Option B: Build manually**

```bash
# Build AI Realtor
docker build -f Dockerfile.sqlite -t your-username/ai-realtor-sqlite:latest .

# Build Nanobot
cd nanobot
docker build -t your-username/nanobot-gateway:latest .
cd ..

# Push to registry
docker push your-username/ai-realtor-sqlite:latest
docker push your-username/nanobot-gateway:latest
```

### Step 3: Create Coolify Application (2 minutes)

1. **Open Coolify Dashboard**
   - Go to your Coolify URL

2. **Create New Project**
   - Click "New Project" → Name: "AI Realtor"

3. **Create Docker Compose Service**
   - Click "New Service" → "Docker Compose"
   - Select your GitHub repository
   - Branch: `main`
   - Compose file path: `docker-compose.coolify.yml`

4. **Update Image References**
   - In Coolify editor, update image names:
     ```yaml
     services:
       ai-realtor:
         image: your-username/ai-realtor-sqlite:latest  # Change this
       nanobot:
         image: your-username/nanobot-gateway:latest    # Change this
     ```

### Step 4: Add Environment Variables (3 minutes)

In Coolify, click "Add Variable" and add these:

```bash
# Required - Replace with your actual keys
GOOGLE_PLACES_API_KEY=your_actual_key_here
RAPIDAPI_KEY=your_actual_rapidapi_key
DOCUSEAL_API_KEY=your_actual_docuseal_key
DOCUSEAL_API_URL=https://api.docuseal.com
TELEGRAM_BOT_TOKEN=your_actual_telegram_token
ZHIPU_API_KEY=your_actual_zhipu_key

# Optional
ANTHROPIC_API_KEY=sk-ant-your-key-here
RESEND_API_KEY=re_your_key_here
EXA_API_KEY=your_exa_key_here
```

### Step 5: Deploy (1 minute)

1. Click "Deploy" in Coolify
2. Wait for containers to start (check logs)
3. Verify health checks pass (green status)

---

## Post-Deployment Setup

### Configure Nanobot (5 minutes)

After containers are running:

```bash
# SSH into your Coolify server
ssh root@your-coolify-server

# Access Nanobot container
docker exec -it nanobot-gateway bash

# Create config file
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

# Exit and restart
exit
docker restart nanobot-gateway
```

### Test Your Deployment

**1. Test AI Realtor API**
```bash
curl https://ai-realtor.your-domain.com/health
# Should return: {"status":"healthy"}
```

**2. Test Telegram Bot**
- Open Telegram
- Find your bot: `@Smartrealtoraibot`
- Send: "Show me all properties"
- Should respond with property list or "No properties found"

**3. Test Property Creation**
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

---

## Optional: Configure Custom Domain & SSL

1. **Add Domain in Coolify**
   - Go to your service → Domains
   - Add: `ai-realtor.your-domain.com`
   - Enable "Force HTTPS"
   - Enable "Automatic HTTPS"

2. **Configure DNS**
   - Go to your domain registrar
   - Add A record:
     ```
     ai-realtor    A    your-coolify-server-ip
     ```

3. **Wait for SSL**
   - Coolify will automatically provision Let's Encrypt certificate
   - Takes 1-2 minutes

---

## Troubleshooting

### Container won't start

**Check logs:**
```bash
docker logs ai-realtor-sqlite
docker logs nanobot-gateway
```

**Common issues:**
- Missing environment variable → Check all required vars are set
- Invalid API key → Verify keys are correct
- Port already in use → Stop conflicting containers

### Nanobot can't connect to AI Realtor

**Verify network:**
```bash
docker network inspect ai-platform-network
```

**Test DNS from Nanobot:**
```bash
docker exec nanobot-gateway ping ai-realtor-sqlite
```

### Database errors

**Check database file exists:**
```bash
docker exec ai-realtor-sqlite ls -la /app/data/
```

**Reset database (last resort):**
```bash
docker exec ai-realtor-sqlite rm /app/data/ai_realtor.db
docker restart ai-realtor-sqlite
```

---

## What's Next?

Your AI Realtor platform is now running! Here's what you can do:

1. **Connect Telegram Bot**
   - Start chatting with @Smartrealtoraibot
   - Try commands: "Show me all properties", "Create property at 123 Main St"

2. **Set Up Claude Desktop MCP**
   - Install Claude Desktop
   - Configure MCP server (see CLAUDE.md)
   - Use 135+ voice commands

3. **Enable Phone Calls** (optional)
   - Add VAPI_API_KEY
   - Add ELEVENLABS_API_KEY
   - Restart containers

4. **Configure Backups**
   - Set up automated database backups
   - Test restore procedure

5. **Monitor Performance**
   - Check Coolify dashboard
   - Set up alerts
   - Scale resources if needed

---

## Full Documentation

- **Complete Deployment Guide**: `.coolify/deployment-guide.md`
- **Environment Variables**: `.coolify/.env.example.coolify`
- **Platform Features**: `CLAUDE.md`
- **MCP Voice Commands**: 135+ tools available

---

## Support

- **Coolify Docs**: https://coolify.io/docs
- **AI Realtor GitHub**: https://github.com/Thedurancode/ai-realtor
- **Issues**: Open issue on GitHub

---

**Deployment Time: ~15 minutes**
**Total Cost: $5-50/month depending on features**

You're live! 🎉
