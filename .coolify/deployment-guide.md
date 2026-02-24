# AI Realtor + Nanobot - Coolify Deployment Guide

Complete guide to deploying the AI Realtor platform with Nanobot gateway to Coolify.

## Prerequisites

### 1. Coolify Server Setup

You need a Coolify instance running. Options:
- **Self-hosted**: Deploy Coolify to your own server (recommended for production)
- **Coolify Cloud**: Use managed Coolify service (https://coolify.io)

**Minimum Server Requirements:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB SSD
- OS: Ubuntu 20.04+ or Debian 11+

### 2. Required API Keys

**Essential Keys (Platform won't work without these):**
- ✅ `GOOGLE_PLACES_API_KEY` - Address lookup and property validation
- ✅ `RAPIDAPI_KEY` - Zillow enrichment and Skip Trace
- ✅ `DOCUSEAL_API_KEY` - E-signature integration
- ✅ `TELEGRAM_BOT_TOKEN` - Telegram bot integration
- ✅ `ZHIPU_API_KEY` - AI provider for Nanobot (recommended)

**Optional Keys (Add more features):**
- ⚪ `ANTHROPIC_API_KEY` - AI recaps and contract analysis
- ⚪ `VAPI_API_KEY` - Phone call automation
- ⚪ `ELEVENLABS_API_KEY` - Voice synthesis
- ⚪ `RESEND_API_KEY` - Email notifications
- ⚪ `EXA_API_KEY` - Property research

### 3. Domain Names (Optional but Recommended)

For automatic SSL certificates, configure these DNS records:
```
ai-realtor.your-domain.com    → A record → Coolify server IP
nanobot.your-domain.com       → A record → Coolify server IP
```

---

## Deployment Steps

### Step 1: Prepare Docker Images

Since Nanobot needs to be built from source, you need to build and push images to a registry.

**Option A: Build locally and push to Docker Hub**

```bash
# 1. Build AI Realtor SQLite image
docker build -f Dockerfile.sqlite -t your-username/ai-realtor-sqlite:latest .

# 2. Build Nanobot image
cd nanobot
docker build -t your-username/nanobot-gateway:latest .
cd ..

# 3. Push to Docker Hub
docker push your-username/ai-realtor-sqlite:latest
docker push your-username/nanobot-gateway:latest
```

**Option B: Use GitHub Container Registry (GHCR)**

```bash
# 1. Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u your-username --password-stdin

# 2. Build and tag
docker build -f Dockerfile.sqlite -t ghcr.io/your-username/ai-realtor-sqlite:latest .
cd nanobot
docker build -t ghcr.io/your-username/nanobot-gateway:latest .
cd ..

# 3. Push to GHCR
docker push ghcr.io/your-username/ai-realtor-sqlite:latest
docker push ghcr.io/your-username/nanobot-gateway:latest
```

**Option C: Let Coolify build from your Git repository**

1. Push your code to GitHub
2. In Coolify, select "From GitHub"
3. Choose your repository
4. Set Dockerfile path for each service:
   - AI Realtor: `Dockerfile.sqlite`
   - Nanobot: `nanobot/Dockerfile`

---

### Step 2: Create Application in Coolify

1. **Log in to Coolify Dashboard**
   - Go to your Coolify URL (e.g., `https://coolify.your-domain.com`)

2. **Create New Project**
   - Click "New Project"
   - Name: `AI Realtor Platform`

3. **Create Docker Compose Service**
   - Click "New Service"
   - Select "Docker Compose"
   - Name: `ai-realtor-stack`

---

### Step 3: Configure Docker Compose in Coolify

1. **Select Source**
   - Choose "From Git Repository"
   - Select your `ai-realtor` repository
   - Branch: `main`

2. **Set Compose File Path**
   - Path: `docker-compose.coolify.yml`

3. **Configure Environment Variables**

   Coolify will read environment variables from your compose file. Click "Add Variable" for each:

   ```bash
   # Essential - Replace with your actual keys
   GOOGLE_PLACES_API_KEY=AIzaSyYourActualKeyHere
   RAPIDAPI_KEY=your_rapidapi_key_here
   DOCUSEAL_API_KEY=your_docuseal_key
   DOCUSEAL_API_URL=https://api.docuseal.com
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   ZHIPU_API_KEY=your_zhipu_api_key

   # Optional
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   VAPI_API_KEY=your_vapi_key
   ELEVENLABS_API_KEY=your_elevenlabs_key
   RESEND_API_KEY=re_your_resend_key
   EXA_API_KEY=your_exa_key

   # Configuration (keep defaults)
   CAMPAIGN_WORKER_ENABLED=true
   DAILY_DIGEST_ENABLED=true
   DAILY_DIGEST_HOUR=8
   ```

---

### Step 4: Configure Persistent Volumes

Coolify automatically creates volumes from your compose file:

1. **AI Realtor Data Volume**
   - Name: `ai_realtor_sqlite_data`
   - Mount path: `/app/data`
   - Contains: SQLite database and uploaded files

2. **Nanobot Config Volume**
   - Name: `nanobot_config_data`
   - Mount path: `/root/.nanobot`
   - Contains: Nanobot configuration and skill data

3. **Nanobot Skills Volume**
   - Name: `nanobot_skills_data`
   - Mount path: `/root/.nanobot/workspace/skills`
   - Contains: AI Realtor skill for Nanobot

---

### Step 5: Configure Domain & SSL

1. **Add Custom Domain**
   - Go to your service in Coolify
   - Click "Domains"
   - Add: `ai-realtor.your-domain.com`
   - Enable "Force HTTPS"
   - Enable "Automatic HTTPS (Let's Encrypt)"

2. **Repeat for Nanobot** (if exposing publicly)
   - Add: `nanobot.your-domain.com`
   - Enable HTTPS

3. **Configure DNS**
   - Go to your domain registrar
   - Add A records:
     ```
     ai-realtor    A    your-coolify-server-ip
     nanobot       A    your-coolify-server-ip
     ```

---

### Step 6: Deploy

1. **Click "Deploy"**
   - Coolify will pull images, create containers, and start services

2. **Monitor Deployment**
   - Click "Logs" to watch deployment progress
   - Wait for health checks to pass (green status)

3. **Verify Services**

   **AI Realtor API:**
   ```bash
   curl https://ai-realtor.your-domain.com/health
   # Expected: {"status":"healthy","timestamp":"..."}
   ```

   **Nanobot Gateway:**
   ```bash
   curl https://nanobot.your-domain.com/health
   # Expected: {"status":"ok"}
   ```

---

### Step 7: Initial Nanobot Configuration

After deployment, configure Nanobot to use Zhipu AI:

1. **SSH into Coolify server**
   ```bash
   ssh root@your-coolify-server
   ```

2. **Access Nanobot container**
   ```bash
   docker exec -it nanobot-gateway bash
   ```

3. **Create configuration file**
   ```bash
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
   ```

4. **Restart Nanobot**
   ```bash
   exit
   docker restart nanobot-gateway
   ```

---

### Step 8: Test Integration

1. **Test Telegram Bot**
   - Open Telegram
   - Find your bot: `@Smartrealtoraibot`
   - Send: "Show me all properties"
   - Should respond with property list

2. **Test AI Realtor API**
   ```bash
   # List properties
   curl https://ai-realtor.your-domain.com/properties/

   # Create property
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

3. **Check Logs**
   ```bash
   # AI Realtor logs
   docker logs -f ai-realtor-sqlite

   # Nanobot logs
   docker logs -f nanobot-gateway
   ```

---

## Updating Your Deployment

### Automatic Updates (Git-Based)

When you push to your Git repository:

1. Coolify detects new commits
2. Click "Deploy" in Coolify dashboard
3. Images rebuild and redeploy automatically

### Manual Updates

1. **Rebuild and push images**
   ```bash
   docker build -f Dockerfile.sqlite -t your-username/ai-realtor-sqlite:latest .
   docker push your-username/ai-realtor-sqlite:latest
   ```

2. **Pull and restart in Coolify**
   - Go to your service
   - Click "Update"
   - Or click "Redeploy" to restart without rebuilding

---

## Monitoring and Maintenance

### Health Checks

Coolify automatically monitors health checks:
- AI Realtor: `http://localhost:8000/health` (every 30s)
- Nanobot: `http://localhost:18790/health` (every 30s)

### View Logs

In Coolify dashboard:
1. Go to your service
2. Click "Logs"
3. Select container (ai-realtor or nanobot)
4. View real-time logs

### Database Backups

**Automated Backups:**

```bash
# Add to Coolify cron jobs
0 2 * * * docker exec ai-realtor-sqlite sqlite3 /app/data/ai_realtor.db ".backup /app/data/backup_$(date +\%Y\%m\%d).db"
```

**Manual Backup:**

```bash
# Copy database from container
docker cp ai-realtor-sqlite:/app/data/ai_realtor.db ./backup_$(date +%Y%m%d).db

# Or backup to Coolify volume
docker exec ai-realtor-sqlite sqlite3 /app/data/ai_realtor.db ".backup /app/data/backup.db"
```

### Resource Monitoring

In Coolify dashboard:
- Go to "Resources"
- View CPU, RAM, and disk usage for each container

---

## Troubleshooting

### Issue: Container won't start

**Check logs:**
```bash
docker logs ai-realtor-sqlite
docker logs nanobot-gateway
```

**Common causes:**
- Missing environment variables
- Invalid API keys
- Port conflicts
- Volume permission issues

### Issue: Nanobot can't reach AI Realtor

**Check network:**
```bash
docker network inspect ai-platform-network
```

**Verify DNS:**
```bash
docker exec nanobot-gateway ping ai-realtor-sqlite
```

### Issue: Database is locked

SQLite doesn't handle high write concurrency. If you see locking errors:

1. Restart container
   ```bash
   docker restart ai-realtor-sqlite
   ```

2. Check for long-running transactions
   ```bash
   docker exec ai-realtor-sqlite sqlite3 /app/data/ai_realtor.db "PRAGMA busy_timeout;"
   ```

### Issue: SSL certificate not renewing

**Check Let's Encrypt logs:**
```bash
docker logs coolify-traefik | grep letsencrypt
```

**Force renewal:**
- In Coolify, disable "Automatic HTTPS"
- Wait 30 seconds
- Re-enable "Automatic HTTPS"

---

## Scaling

### Vertical Scaling (More Power)

In Coolify:
1. Go to "Resources"
2. Adjust CPU and RAM limits
3. Click "Update"

**Recommended for production:**
- CPU: 2-4 cores
- RAM: 4-8GB
- Storage: 50GB+

### Horizontal Scaling (Multiple Instances)

**AI Realtor** (Stateful - SQLite):
- ❌ Cannot scale horizontally (single instance required)

**Nanobot** (Stateless):
- ✅ Can scale horizontally
- Add replicas in Coolify: Settings → Replicas → 2+

---

## Security Best Practices

1. **Use Secret Management**
   - Store API keys in Coolify's secret manager
   - Never commit keys to Git

2. **Enable HTTPS**
   - Force HTTPS for all domains
   - Use Let's Encrypt for automatic certificates

3. **Restrict Access**
   - Use firewall rules to limit access
   - Only expose necessary ports (80, 443)
   - Keep Nanobot internal if not needed externally

4. **Regular Updates**
   - Keep Docker images updated
   - Update Coolify regularly
   - Monitor security advisories

5. **Backup Strategy**
   - Daily automated backups
   - Offsite backup storage
   - Test restore procedure

---

## Cost Estimation

### Coolify Cloud (Managed)
- Starting at $5/month for basic plan
- Plus compute costs (~$10-30/month depending on resources)

### Self-Hosted (Your Server)
- Server rental: $5-20/month (Hetzner, DigitalOcean, Linode)
- Domain: $10-15/year
- SSL: Free (Let's Encrypt)

**Total: ~$10-40/month for production deployment**

---

## Next Steps

After successful deployment:

1. **Set up monitoring** - Configure alerts in Coolify
2. **Configure backups** - Set automated backup schedule
3. **Test all features** - Verify API, MCP, Telegram bot
4. **Add custom domain** - Point your domain to Coolify
5. **Scale resources** - Adjust based on usage
6. **Monitor costs** - Keep track of API usage

---

## Support

- **Coolify Docs**: https://coolify.io/docs
- **AI Realtor Docs**: https://github.com/Thedurancode/ai-realtor
- **Nanobot Docs**: https://github.com/nanobot/nanobot

---

**Deployment Checklist:**

- [ ] Coolify server running
- [ ] Domain configured with A records
- [ ] API keys obtained and added to Coolify
- [ ] Docker images built and pushed
- [ ] Application created in Coolify
- [ ] Environment variables configured
- [ ] Persistent volumes created
- [ ] Domain names added and SSL enabled
- [ ] Services deployed and healthy
- [ ] Nanobot configured with Zhipu AI
- [ ] Telegram bot tested
- [ ] API tested successfully
- [ ] Backup strategy configured
- [ ] Monitoring and alerts set up

---

**You're ready to deploy! 🚀**
