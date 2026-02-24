# AI Realtor Nanobot Skill - Flexible URL Handling

## Problem Solved

The skill now supports **any API URL** - production, localhost, Docker, staging, etc. No hardcoded URLs required!

## Three Approaches

### 1. Environment Variable (Recommended) ⭐

**Set before starting nanobot:**

```bash
# Production
export AI_REALTOR_API_URL="https://ai-realtor.fly.dev"

# Local development
export AI_REALTOR_API_URL="http://localhost:8000"

# Docker (Mac/Windows)
export AI_REALTOR_API_URL="http://host.docker.internal:8000"

# Docker (Linux)
export AI_REALTOR_API_URL="http://172.17.0.1:8000"

# Staging/Custom
export AI_REALTOR_API_URL="https://staging.example.com"
```

**Add to shell profile for persistence:**

```bash
# ~/.bashrc or ~/.zshrc
export AI_REALTOR_API_URL="https://ai-realtor.fly.dev"
```

**How AI uses it:**

When you ask the AI to interact with AI Realtor, it will:
1. Check if `AI_REALTOR_API_URL` is set
2. Use that URL in all curl commands
3. Fall back to `https://ai-realtor.fly.dev` if not set

### 2. Wrapper Script

**Use the provided wrapper:**

```bash
~/.local/bin/ai-realtor-api curl "https://ai-realtor.fly.dev/properties/"
```

The wrapper automatically substitutes the URL based on `AI_REALTOR_API_URL`.

### 3. Direct Configuration

**Tell the AI your URL:**

```
User: "My API is at http://localhost:8000"
AI: Got it! I'll use http://localhost:8000 for all commands.

User: "Show me all properties"
AI: [Uses] curl "http://localhost:8000/properties/"
```

## Quick Start

### Automated Setup (Recommended)

```bash
# Run the smart setup script
./docker-setup-skill.sh

# It will:
# - Auto-detect your environment (Docker, local, production)
# - Configure environment variable
# - Install wrapper script
# - Test connection
```

### Manual Setup

```bash
# 1. Set environment variable
export AI_REALTOR_API_URL="http://localhost:8000"

# 2. Add to shell profile
echo 'export AI_REALTOR_API_URL="http://localhost:8000"' >> ~/.bashrc
source ~/.bashrc

# 3. Restart nanobot
nanobot restart
```

## Docker Scenarios

### Docker Compose (Service Discovery)

```yaml
# docker-compose.yml
services:
  ai-realtor-api:
    image: ai-realtor:latest
    ports:
      - "8000:8000"

  nanobot:
    image: nanobot:latest
    environment:
      - AI_REALTOR_API_URL=http://ai-realtor-api:8000
    volumes:
      - ./skills:/workspace/skills
```

### Docker Desktop (Mac/Windows)

```bash
# Use host.docker.internal to access host from container
export AI_REALTOR_API_URL="http://host.docker.internal:8000"
```

### Docker (Linux)

```bash
# Use Docker bridge IP
export AI_REALTOR_API_URL="http://172.17.0.1:8000"
```

### Kubernetes

```yaml
# deployment.yaml
env:
  - name: AI_REALTOR_API_URL
    value: "http://ai-realtor-service:8000"
```

## Environment-Specific Configuration

### Development

```bash
# .env.development
AI_REALTOR_API_URL="http://localhost:8000"
```

### Staging

```bash
# .env.staging
AI_REALTOR_API_URL="https://staging.ai-realtor.com"
```

### Production

```bash
# .env.production
AI_REALTOR_API_URL="https://ai-realtor.fly.dev"
```

## How the AI Handles URLs

### Flow

```
User asks: "Show me all properties"
    ↓
AI checks: echo $AI_REALTOR_API_URL
    ↓
If set → Use that URL
    ↓
If not set → Use https://ai-realtor.fly.dev
    ↓
Executes: curl "<DETECTED_URL>/properties/"
```

### Examples

**Scenario 1: Production (default)**
```
User: "Show me properties"
AI: [No env var set, uses default]
    curl "https://ai-realtor.fly.dev/properties/"
```

**Scenario 2: Local development**
```
$ export AI_REALTOR_API_URL="http://localhost:8000"

User: "Show me properties"
AI: [Env var detected]
    curl "http://localhost:8000/properties/"
```

**Scenario 3: Docker**
```
$ export AI_REALTOR_API_URL="http://host.docker.internal:8000"

User: "Show me properties"
AI: [Env var detected]
    curl "http://host.docker.internal:8000/properties/"
```

**Scenario 4: User override**
```
User: "Use http://192.168.1.100:8000 and show properties"
AI: [User-specified URL]
    curl "http://192.168.1.100:8000/properties/"
```

## Verification

### Check Configuration

```bash
# Check environment variable
echo $AI_REALTOR_API_URL

# Test API connection
curl "$AI_REALTOR_API_URL/properties/" | jq '.'

# View skill instructions
cat ~/.nanobot/workspace/skills/ai-realtor/SKILL.md | head -30
```

### Test with Nanobot

```bash
# Restart nanobot to pick up changes
nanobot restart

# In nanobot, ask:
"What's my AI Realtor API URL?"
"Show me all properties"
```

## Migration from Hardcoded URLs

If you used the previous version with hardcoded URLs:

1. **Set environment variable:**
   ```bash
   export AI_REALTOR_API_URL="https://ai-realtor.fly.dev"
   ```

2. **Update shell profile:**
   ```bash
   echo 'export AI_REALTOR_API_URL="https://ai-realtor.fly.dev"' >> ~/.bashrc
   source ~/.bashrc
   ```

3. **Restart nanobot:**
   ```bash
   nanobot restart
   ```

Everything continues to work exactly the same!

## Wrapper Script Usage

The wrapper script at `~/.local/bin/ai-realtor-api` provides URL substitution:

```bash
# Direct usage
~/.local/bin/ai-realtor-api curl "/properties/"

# With full command
~/.local/bin/ai-realtor-api curl "https://ai-realtor.fly.dev/properties/"

# The wrapper replaces https://ai-realtor.fly.dev with $AI_REALTOR_API_URL
```

## Docker Deployment Example

### Complete Dockerfile

```dockerfile
FROM nanobot:latest

# Install AI Realtor skill
COPY skills/ai-realtor /workspace/skills/ai-realtor

# Set API URL (build arg)
ARG AI_REALTOR_API_URL=https://ai-realtor.fly.dev
ENV AI_REALTOR_API_URL=${AI_REALTOR_API_URL}

# Or use docker-compose override
# ENV AI_REALTOR_API_URL=http://ai-realtor-api:8000
```

### Docker Compose

```yaml
version: '3.8'
services:
  ai-realtor:
    image: ai-realtor:latest
    ports:
      - "8000:8000"

  nanobot:
    image: nanobot:latest
    environment:
      - AI_REALTOR_API_URL=http://ai-realtor:8000
    volumes:
      - ./skills:/workspace/skills:ro
    depends_on:
      - ai-realtor
```

## Troubleshooting

### Issue: AI not using custom URL

**Solution:**
```bash
# Verify env var is set
echo $AI_REALTOR_API_URL

# Restart nanobot to pick up changes
nanobot restart

# Tell AI explicitly
"Use http://localhost:8000 for the API"
```

### Issue: Docker container can't reach localhost

**Solution:**
```bash
# Mac/Windows: Use host.docker.internal
export AI_REALTOR_API_URL="http://host.docker.internal:8000"

# Linux: Use Docker bridge IP
export AI_REALTOR_API_URL="http://172.17.0.1:8000"
```

### Issue: URL changes between restarts

**Solution:**
```bash
# Add to shell profile permanently
echo 'export AI_REALTOR_API_URL="http://localhost:8000"' >> ~/.bashrc
source ~/.bashrc
```

## Best Practices

1. **Always set AI_REALTOR_API_URL** - Even for production (explicit > implicit)

2. **Use environment-specific configs:**
   ```bash
   # .env files
   AI_REALTOR_API_URL="http://localhost:8000"  # dev
   AI_REALTOR_API_URL="https://staging..."    # staging
   AI_REALTOR_API_URL="https://ai-realtor..." # prod
   ```

3. **Docker deployments:** Use service names, not localhost:
   ```yaml
   AI_REALTOR_API_URL="http://ai-realtor-api:8000"
   ```

4. **Test connection after setup:**
   ```bash
   curl "$AI_REALTOR_API_URL/properties/" | jq '.'
   ```

5. **Document in team wiki:**
   ```markdown
   ## Development Setup
   export AI_REALTOR_API_URL="http://localhost:8000"

   ## Production
   export AI_REALTOR_API_URL="https://ai-realtor.fly.dev"
   ```

## Summary

✅ **Flexible** - Works with any API URL
✅ **Zero-config default** - Uses production if not set
✅ **Docker-friendly** - Supports all Docker networking modes
✅ **Smart detection** - Auto-detects common scenarios
✅ **Backward compatible** - Works with existing setups

**One environment variable, unlimited deployments!**
