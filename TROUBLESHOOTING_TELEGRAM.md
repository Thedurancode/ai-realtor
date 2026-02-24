# Telegram Bot Not Responding - Complete Troubleshooting Guide

## Quick Diagnosis Checklist

Follow these steps in order to fix your Telegram bot.

---

## Step 1: Start Docker Desktop

**Symptom:** `Cannot connect to Docker daemon`

**Fix:**
1. Open Docker Desktop from Applications
2. Wait 30 seconds for whale icon 🐳 to appear in menu bar
3. Run: `docker ps`

**Expected:** Should see list of running containers

---

## Step 2: Check Container Status

**Command:**
```bash
docker ps --filter "name=nanobot" --format "table {{.Names}}\t{{.Status}}"
```

**Expected Output:**
```
NAMES            STATUS
nanobot-gateway  Up 2 hours
```

**If container is not running:**
```bash
# Start containers
cd /Users/edduran/Documents/GitHub/ai-realtor
docker-compose -f docker-compose-local-nanobot.yml up -d

# Wait 10 seconds
# Check again
docker ps
```

---

## Step 3: Verify Token is Loaded

**Command:**
```bash
docker exec nanobot-gateway printenv TELEGRAM_BOT_TOKEN
```

**Expected:** `8392020900:AAEKlrigz4_B35slxdJpBIApSrotEf3ceiI`

**If empty or wrong token:**
1. Check `.env` file has the token:
   ```bash
   grep TELEGRAM_BOT_TOKEN /Users/edduran/Documents/GitHub/ai-realtor/.env
   ```

2. If missing, add it:
   ```bash
   nano .env
   # Add: TELEGRAM_BOT_TOKEN=8392020900:AAEKlrigz4_B35slxdJpBIApSrotEf3ceiI
   ```

3. Restart container:
   ```bash
   docker restart nanobot-gateway
   ```

---

## Step 4: Test Bot Token Validity

**Command:**
```bash
curl "https://api.telegram.org/bot8392020900:AAEKlrigz4_B35slxdJpBIApSrotEf3ceiI/getMe"
```

**Expected Response:**
```json
{
  "ok": true,
  "result": {
    "id": 8392020900,
    "is_bot": true,
    "first_name": "...",
    "username": "...",
    "can_join_groups": true,
    ...
  }
}
```

**If error:**
- `{"ok": false, "error_code": 401}` → Token is invalid
- `{"ok": false, "error_code": 409}` → Bot was blocked by Telegram
- **Fix:** Create new bot with @BotFather

---

## Step 5: Check Nanobot Configuration

**Command:**
```bash
docker exec nanobot-gateway cat /root/.nanobot/config.json
```

**Expected:**
```json
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
```

**If file doesn't exist or wrong:**
```bash
# Run setup script
cd /Users/edduran/Documents/GitHub/ai-realtor
./scripts/setup-nanobot.sh

# Or create manually
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

## Step 6: Check Nanobot Logs

**Command:**
```bash
docker logs nanobot-gateway --tail 50
```

**Look for:**
- ✓ `Starting nanobot gateway`
- ✓ `Agent loaded`
- ✓ `Skill loaded: ai-realtor`
- ✓ `Telegram connection established`
- ✗ Any ERROR messages

**Common Errors:**

### Error: "No API key configured"
**Meaning:** ZHIPU_API_KEY not set
**Fix:**
```bash
# Check it's in .env
grep ZHIPU_API_KEY .env

# Restart containers
docker-compose -f docker-compose-local-nanobot.yml restart
```

### Error: "Cannot connect to AI Realtor"
**Meaning:** Can't reach http://ai-realtor-sqlite:8000
**Fix:**
```bash
# Check AI Realtor is healthy
curl http://localhost:8000/health

# Check network
docker network inspect ai-platform-network

# Test connection from Nanobot
docker exec nanobot-gateway ping ai-realtor-sqlite
```

### Error: "Telegram connection failed"
**Meaning:** Can't connect to Telegram servers
**Fix:**
- Check internet connection
- Verify bot token is valid
- Check if Telegram is blocked in your network

---

## Step 7: Check AI Realtor API

**Command:**
```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": {
    "type": "SQLite",
    "status": "healthy"
  }
}
```

**If not responding:**
```bash
# Check AI Realtor container
docker ps --filter "name=ai-realtor"

# If not running
docker-compose -f docker-compose-local-nanobot.yml up -d ai-realtor
```

---

## Step 8: Test Bot in Telegram

Once everything is running:

1. **Open Telegram app**
2. **Find your bot** (search by username or create with @BotFather)
3. **Send:** `/start`
4. **Send:** `"Show me all properties"`

**Expected:** Bot responds with your 2 properties

---

## Common Issues & Solutions

### Issue: Bot doesn't respond at all

**Possible causes:**
1. Nanobot container not running
2. Bot token invalid
3. Nanobot not configured
4. AI Realtor API down

**Solution:**
```bash
# Check all services
docker ps

# Restart Nanobot
docker restart nanobot-gateway

# Check logs
docker logs nanobot-gateway --tail 50 -f
```

---

### Issue: Bot responds but says "API error"

**Meaning:** Nanobot can't reach AI Realtor API

**Solution:**
```bash
# Check AI Realtor is running
curl http://localhost:8000/health

# Check network connection
docker exec nanobot-gateway ping ai-realtor-sqlite

# Check AI Realtor logs
docker logs ai-realtor-sqlite --tail 20
```

---

### Issue: Bot says "No such command"

**Meaning:** Nanobot doesn't understand the command

**Solution:**
- Make sure you're using natural language
- Try simpler commands first: "Show me all properties"
- Check Nanobot config has AI Realtor skill

---

### Issue: Bot responds but shows no data

**Meaning:** API works but database empty

**Solution:**
```bash
# Check database has properties
docker exec ai-realtor-sqlite sqlite3 /app/data/ai_realtor.db "SELECT COUNT(*) FROM properties;"

# Should return: 2
```

---

## Complete Reset Procedure

If nothing works, do a complete reset:

```bash
# 1. Stop everything
cd /Users/edduran/Documents/GitHub/ai-realtor
docker-compose -f docker-compose-local-nanobot.yml down

# 2. Start fresh
docker-compose -f docker-compose-local-nanobot.yml up -d

# 3. Wait 10 seconds

# 4. Run Nanobot setup
./scripts/setup-nanobot.sh

# 5. Check status
docker ps
curl http://localhost:8000/health
docker logs nanobot-gateway --tail 20

# 6. Test in Telegram
```

---

## Manual Test Sequence

Do these in order:

```bash
# 1. Docker running?
docker ps

# 2. Containers up?
docker ps --filter "name=nanobot"
docker ps --filter "name=ai-realtor"

# 3. Token loaded?
docker exec nanobot-gateway printenv TELEGRAM_BOT_TOKEN

# 4. Token valid?
curl "https://api.telegram.org/bot8392020900:AAEKlrigz4_B35slxdJpBIApSrotEf3ceiI/getMe"

# 5. Nanobot configured?
docker exec nanobot-gateway cat /root/.nanobot/config.json

# 6. AI Realtor healthy?
curl http://localhost:8000/health

# 7. Nanobot logs OK?
docker logs nanobot-gateway --tail 20

# 8. Test in Telegram
# Open app → Find bot → Send: /start → Send: "Show me all properties"
```

---

## Still Not Working?

Collect this information:

```bash
# Save diagnostics
docker ps > /tmp/docker_status.txt
docker logs nanobot-gateway --tail 100 > /tmp/nanobot_logs.txt
docker logs ai-realtor-sqlite --tail 100 > /tmp/ai_realtor_logs.txt
docker exec nanobot-gateway printenv TELEGRAM_BOT_TOKEN > /tmp/token.txt
docker exec nanobot-gateway cat /root/.nanobot/config.json > /tmp/nanobot_config.json
```

Then check each file for errors.

---

## Summary

Most common issue is **Docker Desktop not running**.

**Quick fix:**
1. Start Docker Desktop
2. Wait 30 seconds
3. Run: `docker ps`
4. Restart Nanobot: `docker restart nanobot-gateway`
5. Test bot in Telegram

**If still not working, check logs:**
```bash
docker logs nanobot-gateway --tail 50 -f
```

This will show you exactly what's wrong!
