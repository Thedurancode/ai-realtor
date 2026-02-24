# AI Realtor Nanobot Integration - Flexible URL Edition

Complete integration with **dynamic URL support** for Docker, local development, staging, and production.

## 🎯 What Changed?

### Before (Hardcoded) ❌
- URLs hardcoded in skill file
- Only worked with production API
- Required manual file edits for different environments

### After (Flexible) ✅
- Environment variable-based
- Works with ANY API URL
- Zero configuration changes needed
- Docker-friendly
- Smart AI that adapts automatically

## 🚀 Quick Start

### For Docker Builds

```bash
# Set your API URL
export AI_REALTOR_API_URL="http://localhost:8000"

# Or use Docker service discovery
export AI_REALTOR_API_URL="http://ai-realtor-api:8000"

# Or Docker host (Mac/Windows)
export AI_REALTOR_API_URL="http://host.docker.internal:8000"
```

### Automated Setup

```bash
./docker-setup-skill.sh
```

This script will:
- Auto-detect your environment
- Configure `AI_REALTOR_API_URL`
- Test the connection
- Install wrapper script

### Manual Setup

```bash
# 1. Set environment variable
export AI_REALTOR_API_URL="http://your-api-url"

# 2. Add to shell profile
echo 'export AI_REALTOR_API_URL="http://your-api-url"' >> ~/.bashrc
source ~/.bashrc

# 3. Restart nanobot
nanobot restart
```

## 📖 How It Works

### The Flow

```
1. Set environment variable
   export AI_REALTOR_API_URL="http://localhost:8000"

2. User asks: "Show me all properties"

3. AI checks: echo $AI_REALTOR_API_URL

4. AI uses detected URL in all commands
   curl "http://localhost:8000/properties/"
```

### Key Innovation

The skill file now **instructs the AI** to check the environment variable:

```markdown
## How AI Should Handle URLs

1. First, check if AI_REALTOR_API_URL environment variable is set
2. If set, use that URL in all curl commands
3. If not set, use default production URL
4. User can also tell you their URL explicitly
```

The AI understands these instructions and adapts accordingly!

## 🐳 Docker Deployment

### Docker Compose (Service Discovery)

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

### Dockerfile (Build Arg)

```dockerfile
FROM nanobot:latest

ARG AI_REALTOR_API_URL=https://ai-realtor.fly.dev
ENV AI_REALTOR_API_URL=${AI_REALTOR_API_URL}

COPY skills/ai-realtor /workspace/skills/ai-realtor
```

Build with:
```bash
docker build --build-arg AI_REALTOR_API_URL=http://localhost:8000 -t nanobot-ai-realtor .
```

### Kubernetes

```yaml
apiVersion: v1
kind: Deployment
metadata:
  name: nanobot
spec:
  template:
    spec:
      containers:
      - name: nanobot
        env:
        - name: AI_REALTOR_API_URL
          value: "http://ai-realtor-service:8000"
```

## 📁 Files

### Core Files

1. **`~/.nanobot/workspace/skills/ai-realtor/SKILL.md`**
   - Smart skill with environment variable instructions
   - Tells AI how to handle different URLs
   - Works with any API endpoint

2. **`docker-setup-skill.sh`**
   - Automated setup script
   - Auto-detects environment
   - Configures everything

3. **`~/.local/bin/ai-realtor-api`**
   - Wrapper script for URL substitution
   - Useful for command-line usage

### Documentation

1. **`DOCKER_URL_HANDLING.md`**
   - Complete Docker deployment guide
   - All scenarios (production, local, Docker)
   - Troubleshooting

2. **`README_FLEXIBLE_URL.md`** (this file)
   - Overview and quick reference

3. **`config.md`**
   - Configuration reference
   - Environment variable setup

## ✨ Supported Scenarios

| Scenario | URL | Command |
|----------|-----|---------|
| Production | `https://ai-realtor.fly.dev` | `export AI_REALTOR_API_URL="https://ai-realtor.fly.dev"` |
| Local Dev | `http://localhost:8000` | `export AI_REALTOR_API_URL="http://localhost:8000"` |
| Docker (Mac/Win) | `http://host.docker.internal:8000` | `export AI_REALTOR_API_URL="http://host.docker.internal:8000"` |
| Docker (Linux) | `http://172.17.0.1:8000` | `export AI_REALTOR_API_URL="http://172.17.0.1:8000"` |
| Docker Service | `http://ai-realtor-api:8000` | `export AI_REALTOR_API_URL="http://ai-realtor-api:8000"` |
| Staging | `https://staging.example.com` | `export AI_REALTOR_API_URL="https://staging.example.com"` |

## 🎤 Voice Commands

Once configured, use natural language:

```
"Show me all properties"
"Enrich property 5 with Zillow data"
"Is property 5 ready to close?"
"Create a Facebook ad for property 5"
"How's my portfolio doing?"
```

The AI will use your configured API URL automatically.

## 🔧 Configuration

### Environment Variables

```bash
# Required (if not using default production)
AI_REALTOR_API_URL=http://localhost:8000

# Optional (if API requires authentication)
AI_REALTOR_API_KEY=your-api-key
```

### Shell Profiles

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# AI Realtor Configuration
export AI_REALTOR_API_URL="http://localhost:8000"
```

## 🧪 Testing

```bash
# 1. Verify environment variable
echo $AI_REALTOR_API_URL

# 2. Test API connection
curl "$AI_REALTOR_API_URL/properties/" | jq '.'

# 3. Restart nanobot
nanobot restart

# 4. Try voice commands
"Show me all properties"
```

## 🎯 Best Practices

1. **Always set AI_REALTOR_API_URL explicitly**
   ```bash
   export AI_REALTOR_API_URL="http://localhost:8000"
   ```

2. **Use environment-specific configs**
   ```bash
   # .env.development
   AI_REALTOR_API_URL="http://localhost:8000"

   # .env.production
   AI_REALTOR_API_URL="https://ai-realtor.fly.dev"
   ```

3. **For Docker, use service names (not localhost)**
   ```yaml
   AI_REALTOR_API_URL=http://ai-realtor-api:8000
   ```

4. **Test connection after setup**
   ```bash
   curl "$AI_REALTOR_API_URL/properties/" | jq '.'
   ```

5. **Document in team wiki**
   ```markdown
   ## Development
   export AI_REALTOR_API_URL="http://localhost:8000"

   ## Production
   export AI_REALTOR_API_URL="https://ai-realtor.fly.dev"
   ```

## 🔄 Migration from Hardcoded URLs

If you used the previous hardcoded version:

1. **No breaking changes** - Production URL still works as default
2. **Set environment variable** for your environment
3. **Restart nanobot** - That's it!

Everything continues to work.

## 💡 Key Benefits

✅ **Flexible** - Works with any URL
✅ **Zero-config default** - Production works out of the box
✅ **Docker-friendly** - All networking modes supported
✅ **Smart AI** - Adapts to user's URL automatically
✅ **One variable** - Set once, works everywhere
✅ **Backward compatible** - Existing setups still work
✅ **Environment-aware** - Development, staging, production

## 📞 Troubleshooting

### Issue: AI not using my custom URL

**Solution:**
```bash
# Verify env var is set
echo $AI_REALTOR_API_URL

# Restart nanobot
nanobot restart

# Or tell AI explicitly
"Use http://localhost:8000 for the API"
```

### Issue: Docker container can't reach localhost

**Solution:**
```bash
# Mac/Windows: Use host.docker.internal
export AI_REALTOR_API_URL="http://host.docker.internal:8000"

# Linux: Use Docker bridge IP
export AI_REALTOR_API_URL="http://172.17.0.1:8000"

# Or use service discovery
export AI_REALTOR_API_URL="http://ai-realtor-api:8000"
```

## 📚 Additional Documentation

- **`DOCKER_URL_HANDLING.md`** - Complete Docker guide
- **`NANOBOT_SKILL_GUIDE.md`** - Complete usage guide
- **`NANOBOT_QUICK_REF.md`** - Quick reference
- **`NANOBOT_SKILL_PRELOADING.md`** - Technical details

## 🎉 Summary

**One environment variable = Unlimited deployment flexibility**

```bash
export AI_REALTOR_API_URL="your-url-here"
```

That's it! The AI handles the rest.

---

**Generated with [Claude Code](https://claude.ai/code) via [Happy](https://happy.engineering)**
