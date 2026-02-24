# Coolify Deployment Troubleshooting Guide

Common issues and solutions when deploying AI Realtor + Nanobot to Coolify.

---

## Table of Contents

1. [Deployment Issues](#deployment-issues)
2. [Container Issues](#container-issues)
3. [Networking Issues](#networking-issues)
4. [Database Issues](#database-issues)
5. [API Integration Issues](#api-integration-issues)
6. [Performance Issues](#performance-issues)
7. [SSL/HTTPS Issues](#sslhttps-issues)
8. [Monitoring & Logging](#monitoring--logging)

---

## Deployment Issues

### Issue: "Docker Compose file not found"

**Error:**
```
Error: docker-compose.coolify.yml not found in repository
```

**Solution:**
1. Verify file exists in your Git repository
2. Check the file path in Coolify matches exactly
3. Commit and push the file:
   ```bash
   git add docker-compose.coolify.yml
   git commit -m "Add Coolify compose file"
   git push
   ```
4. In Coolify, click "Refresh Repository"

---

### Issue: "Image pull error"

**Error:**
```
Error: pull access denied for your-username/ai-realtor-sqlite
```

**Solutions:**

**Option A: Check image name**
- Verify image name in compose file matches what you pushed
- Check for typos in username or image name

**Option B: Check image is pushed**
```bash
# Verify image exists in registry
docker search your-username/ai-realtor-sqlite

# Or pull it to test
docker pull your-username/ai-realtor-sqlite:latest
```

**Option C: Check registry access**
- Verify you're logged in:
  ```bash
  docker login docker.io -u your-username
  ```
- If using private registry, check credentials in Coolify

---

### Issue: "Environment variable not set"

**Error:**
```
Error: GOOGLE_PLACES_API_KEY is not set
```

**Solution:**
1. Go to Coolify → Your Service → Environment Variables
2. Add missing variable:
   ```bash
   GOOGLE_PLACES_API_KEY=your_actual_key_here
   ```
3. Click "Save" and "Redeploy"

**Check all required variables:**
- GOOGLE_PLACES_API_KEY
- RAPIDAPI_KEY
- DOCUSEAL_API_KEY
- TELEGRAM_BOT_TOKEN
- ZHIPU_API_KEY

---

## Container Issues

### Issue: Container stuck in "Restarting" loop

**Check logs first:**
```bash
docker logs ai-realtor-sqlite
docker logs nanobot-gateway
```

**Common causes:**

**1. Missing dependency**
```
Error: Module 'fastapi' not found
```
**Solution:** Rebuild image with correct requirements.txt

**2. Invalid environment variable**
```
Error: Invalid DATABASE_URL format
```
**Solution:** Check environment variables in Coolify UI

**3. Port already in use**
```
Error: Port 8000 already allocated
```
**Solution:**
- Stop conflicting containers
- Or change port mapping in compose file

---

### Issue: Container starts but health check fails

**Symptoms:**
- Container is running
- Health check shows "unhealthy"
- Logs show no errors

**Solution:**

**1. Manual health check:**
```bash
docker exec ai-realtor-sqlite curl -f http://localhost:8000/health
```

**2. Check if FastAPI is actually running:**
```bash
docker exec ai-realtor-sqlite ps aux | grep uvicorn
```

**3. Common fix - increase start_period:**
In `docker-compose.coolify.yml`:
```yaml
healthcheck:
  start_period: 60s  # Increase from 40s
```

---

### Issue: Nanobot container exits immediately

**Check logs:**
```bash
docker logs nanobot-gateway
```

**Common error:**
```
Error: No such command 'status'
```

**Solution:**
Verify compose file has correct command:
```yaml
nanobot:
  command: ["gateway"]  # Not "status"
```

**Or check for missing config:**
```bash
docker exec nanobot-gateway ls -la /root/.nanobot/
```

If config missing, see "Post-Deployment Setup" in QUICKSTART.md

---

## Networking Issues

### Issue: Nanobot can't reach AI Realtor API

**Symptoms:**
- Nanobot logs show "Connection refused"
- API calls fail from Nanobot

**Diagnose:**
```bash
# Check both containers on same network
docker network inspect ai-platform-network

# Test DNS from Nanobot
docker exec nanobot-gateway ping ai-realtor-sqlite

# Test HTTP connection
docker exec nanobot-gateway curl http://ai-realtor-sqlite:8000/health
```

**Solutions:**

**1. Verify network configuration:**
Both services must have:
```yaml
networks:
  default:
    name: ai-platform-network
```

**2. Check service name matches:**
- In compose file: `container_name: ai-realtor-sqlite`
- In Nanobot config: `http://ai-realtor-sqlite:8000`

**3. Restart both containers:**
```bash
docker restart ai-realtor-sqlite nanobot-gateway
```

---

### Issue: Can't access API from external IP

**Symptoms:**
- Works inside container
- Doesn't work from browser
- curl fails from external machine

**Solutions:**

**1. Check port mapping:**
```yaml
ports:
  - "8000:8000"  # Correct
  # Not: - "8000"  # Wrong - no external port
```

**2. Check Coolify firewall:**
- In Coolify dashboard → Server → Firewall
- Ensure ports 8000, 8001, 18790 are allowed

**3. Check server firewall:**
```bash
# On Coolify server
sudo ufw allow 8000/tcp
sudo ufw allow 8001/tcp
sudo ufw allow 18790/tcp
```

---

### Issue: Custom domain not working

**Symptoms:**
- IP address works
- Domain name doesn't

**Solutions:**

**1. Check DNS propagation:**
```bash
dig ai-realtor.your-domain.com
# Should resolve to your Coolify server IP
```

**2. Verify A record:**
- Go to your domain registrar
- Check A record points to correct IP
- Wait 5-10 minutes for DNS propagation

**3. Check Coolify domain configuration:**
- Coolify → Your Service → Domains
- Verify domain name is correct
- Check "Force HTTPS" is enabled

---

## Database Issues

### Issue: "Database is locked" (SQLite)

**Error:**
```
Error: database is locked
```

**Cause:** SQLite doesn't handle high write concurrency well

**Solutions:**

**1. Quick fix - restart container:**
```bash
docker restart ai-realtor-sqlite
```

**2. Check for long-running transactions:**
```bash
docker exec ai-realtor-sqlite sqlite3 /app/data/ai_realtor.db "PRAGMA busy_timeout;"
```

**3. Enable WAL mode (if not already):**
```bash
docker exec ai-realtor-sqlite sqlite3 /app/data/ai_realtor.db "PRAGMA journal_mode=WAL;"
```

**4. Last resort - reset database:**
```bash
# Backup first
docker cp ai-realtor-sqlite:/app/data/ai_realtor.db ./backup.db

# Remove and restart
docker exec ai-realtor-sqlite rm /app/data/ai_realtor.db
docker restart ai-realtor-sqlite
```

---

### Issue: "Table doesn't exist"

**Error:**
```
Error: no such table: properties
```

**Cause:** Database not initialized

**Solution:**
```bash
# Run migrations
docker exec ai-realtor-sqlite alembic upgrade head

# Or restart (auto-runs migrations on start)
docker restart ai-realtor-sqlite
```

---

### Issue: Database lost after container restart

**Cause:** Volume not mounted correctly

**Check:**
```bash
docker inspect ai-realtor-sqlite | grep -A 10 Mounts
```

**Should show:**
```json
{
  "Source": "ai_realtor_sqlite_data",
  "Destination": "/app/data"
}
```

**Fix:**
Verify compose file has:
```yaml
volumes:
  - ai_realtor_data:/app/data
```

And volume is defined:
```yaml
volumes:
  ai_realtor_data:
    driver: local
```

---

## API Integration Issues

### Issue: Google Places API returns "API key invalid"

**Error:**
```json
{"error_message":"API key invalid"}
```

**Solutions:**

**1. Verify API key is correct:**
```bash
# Test key manually
curl "https://maps.googleapis.com/maps/api/place/autocomplete/json?input=123+Main+St&key=YOUR_KEY"
```

**2. Check API key restrictions:**
- Go to Google Cloud Console
- APIs & Services → Credentials
- Edit your API key
- Under "Application restrictions", ensure it allows:
  - None (for testing) or
  - Your Coolify server IP
- Under "API restrictions", ensure "Places API" is enabled

**3. Enable Places API:**
- Google Cloud Console → APIs & Services → Library
- Search "Places API"
- Click "Enable"

---

### Issue: Zillow API returns 401/403

**Error:**
```json
{"message":"401: Unauthorized"}
```

**Cause:** Invalid RapidAPI key or subscription expired

**Solutions:**

**1. Verify RapidAPI key:**
```bash
# Test key
curl -X GET "https://private-zillow.p.rapidapi.com/listings?address=123+Main+St" \
  -H "X-RapidAPI-Key: YOUR_KEY" \
  -H "X-RapidAPI-Host: private-zillow.p.rapidapi.com"
```

**2. Check RapidAPI subscription:**
- Go to https://rapidapi.com
- My Apps → Zillow API (Private)
- Verify subscription is active
- Check pricing tier

**3. Check environment variable:**
- In Coolify, verify `RAPIDAPI_KEY` has no extra spaces
- Ensure it's not wrapped in quotes

---

### Issue: DocuSeal returns "Not authenticated"

**Error:**
```json
{"error":"Not authenticated"}
```

**Cause:** Wrong API key or URL

**Solutions:**

**1. Verify DocuSeal is accessible:**
```bash
curl https://api.docuseal.com/templates
```

**2. Test API key:**
```bash
curl -X GET https://api.docuseal.com/templates \
  -H "X-Auth-Token: YOUR_KEY"
```

**3. Check if self-hosted:**
If using self-hosted DocuSeal, verify URL:
```bash
DOCUSEAL_API_URL=http://docuseal-p8oc4sw8scksocoo80occw8c.44.203.101.160.sslip.io/api
```

---

### Issue: Telegram bot doesn't respond

**Symptoms:**
- Bot sends no messages
- Bot shows "bot can't initiate conversation"

**Solutions:**

**1. Verify bot token:**
```bash
curl "https://api.telegram.org/botYOUR_TOKEN/getMe"
# Should return bot info
```

**2. Check Nanobot logs:**
```bash
docker logs nanobot-gateway | grep telegram
```

**3. Verify Nanobot config:**
```bash
docker exec nanobot-gateway cat /root/.nanobot/config.json
# Should have TELEGRAM_BOT_TOKEN
```

**4. Test bot manually:**
- Open Telegram
- Find your bot
- Send /start
- Should get welcome message

---

## Performance Issues

### Issue: Slow API response times

**Diagnose:**
```bash
# Check response time
time curl https://ai-realtor.your-domain.com/health

# Check container resources
docker stats ai-realtor-sqlite
```

**Solutions:**

**1. Increase resources in Coolify:**
- Go to Your Service → Resources
- Increase CPU limit (2-4 cores)
- Increase RAM limit (4-8GB)

**2. Enable caching:**
```bash
# In environment variables
CACHE_ENABLED=true
CACHE_TTL=3600
```

**3. Check for N+1 queries:**
```bash
docker exec ai-realtor-sqlite sqlite3 /app/data/ai_realtor.db ".tables"
```

**4. Use connection pooling:**
Already enabled by default, but verify:
```python
# In app/database.py
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
```

---

### Issue: High memory usage

**Check current usage:**
```bash
docker stats --no-stream
```

**Solutions:**

**1. Restart container:**
```bash
docker restart ai-realtor-sqlite
```

**2. Clean up old data:**
```bash
docker exec ai-realtor-sqlite sqlite3 /app/data/ai_realtor.db "VACUUM;"
```

**3. Increase memory limit in Coolify:**
- Go to Your Service → Resources
- Set memory limit to 8GB or higher

---

## SSL/HTTPS Issues

### Issue: "SSL certificate error"

**Symptoms:**
- Browser shows "Not secure" warning
- API calls fail with SSL error

**Solutions:**

**1. Check Let's Encrypt is enabled:**
- Coolify → Your Service → Domains
- Verify "Automatic HTTPS" is enabled

**2. Check DNS propagation:**
```bash
dig ai-realtor.your-domain.com
# Must resolve to correct IP
```

**3. Force certificate renewal:**
- In Coolify, disable "Automatic HTTPS"
- Wait 30 seconds
- Re-enable "Automatic HTTPS"

**4. Check Coolify logs:**
```bash
docker logs coolify-traefik | grep letsencrypt
```

---

### Issue: "Too many redirects" error

**Cause:** Incorrect HTTPS configuration

**Solution:**
- In Coolify → Your Service → Domains
- Enable "Force HTTPS"
- Disable "Redirect HTTP to HTTPS" if both enabled

---

## Monitoring & Logging

### View Container Logs

**Real-time logs:**
```bash
docker logs -f ai-realtor-sqlite
docker logs -f nanobot-gateway
```

**Last 100 lines:**
```bash
docker logs --tail 100 ai-realtor-sqlite
```

**Logs with timestamps:**
```bash
docker logs -t ai-realtor-sqlite
```

---

### Check Container Health

**Detailed health info:**
```bash
docker inspect ai-realtor-sqlite | grep -A 10 Health
```

**Health check log:**
```bash
docker inspect ai-realtor-sqlite --format='{{json .State.Health}}' | jq
```

---

### Monitor Resource Usage

**Live stats:**
```bash
docker stats
```

**One-time snapshot:**
```bash
docker stats --no-stream
```

---

### Export Logs for Analysis

```bash
# Save to file
docker logs ai-realtor-sqlite > ai-realtor-logs.txt

# Last 1000 lines
docker logs --tail 1000 ai-realtor-sqlite > ai-realtor-recent.txt

# With timestamps
docker logs -t ai-realtor-sqlite > ai-realtor-timestamped.txt
```

---

## Still Having Issues?

### Collect Debug Info

```bash
# System info
docker version
docker-compose version

# Container status
docker ps -a

# Network info
docker network ls
docker network inspect ai-platform-network

# Volume info
docker volume ls

# Resource usage
docker stats --no-stream

# Recent logs
docker logs --tail 50 ai-realtor-sqlite > ai-realtor.log
docker logs --tail 50 nanobot-gateway > nanobot.log
```

### Get Help

1. **Check logs first** - Most issues show up in logs
2. **Search GitHub issues** - https://github.com/Thedurancode/ai-realtor/issues
3. **Create new issue** - Include:
   - Error messages
   - Container logs
   - System info
   - Steps to reproduce

---

**Most common fixes:**
1. Restart container (fixes 50% of issues)
2. Check environment variables (fixes 30% of issues)
3. Rebuild image (fixes 15% of issues)
4. Check networking (fixes 5% of issues)
