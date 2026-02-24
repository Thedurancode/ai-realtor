# How the AI Realtor Skill API URL Works

## The Problem

Nanobot skills are **static markdown files** that get read into the AI's context. They can't dynamically access environment variables or shell expansions.

### What Doesn't Work ❌

```markdown
# This WON'T work in a skill file:
curl "$AI_REALTOR_API_URL/properties/"
```

**Why?**
When nanobot reads the skill file, it's just text. The `$AI_REALTOR_API_URL` won't be expanded because:
1. The skill file isn't executed as a shell script
2. Environment variables aren't available when the skill is loaded
3. The AI sees the literal string `$AI_REALTOR_API_URL`, not its value

## The Solution ✅

### Hardcoded Production URL

The skill now uses the **hardcoded production URL** directly:

```markdown
curl "https://ai-realtor.fly.dev/properties/"
```

**Why this works:**
- ✅ No setup required
- ✅ Works immediately out of the box
- ✅ Clear and explicit
- ✅ Production API is always available

### How It Works

```
1. Nanobot starts
   ↓
2. Loads skills (reads SKILL.md files)
   ↓
3. AI sees: curl "https://ai-realtor.fly.dev/properties/"
   ↓
4. AI uses exec tool to run the command
   ↓
5. curl makes HTTP request to production API
   ↓
6. Response returned to AI
```

## For Custom Deployments

If you need to use a different API URL (localhost, staging, etc.), the skill documents explains:

```markdown
## Custom URL (Optional)

For local development or custom deployment:

# Use URL replacement in commands
# Replace: https://ai-realtor.fly.dev
# With: http://localhost:8000
```

The AI can understand this instruction and modify commands accordingly.

## Comparison: Approaches

### Approach 1: Environment Variables (What we tried) ❌

```markdown
export AI_REALTOR_API_URL="https://ai-realtor.fly.dev"

# In skill:
curl "$AI_REALTOR_API_URL/properties/"
```

**Problems:**
- Environment variables not expanded in skill files
- Requires manual setup
- Confusing for users
- AI sees literal `$AI_REALTOR_API_URL`

### Approach 2: Hardcoded URL (Current solution) ✅

```markdown
# In skill:
curl "https://ai-realtor.fly.dev/properties/"
```

**Benefits:**
- Works immediately
- No setup required
- Clear and explicit
- Production API is reliable

### Approach 3: Multiple Examples (Also in skill) ✅

The skill shows both production and explains how to adapt:

```markdown
# Production (works immediately)
curl "https://ai-realtor.fly.dev/properties/"

# For localhost (AI can adapt)
curl "http://localhost:8000/properties/"
```

## Real-World Example

### User Experience with Hardcoded URL

```
User: "Show me all my properties"

AI: I'll list all properties from the AI Realtor API.

[Executes]: curl "https://ai-realtor.fly.dev/properties/"

[Returns]: Property list from production API

AI: Here are your properties...
```

### If User Has Local Development Server

```
User: "I'm using a local API at http://localhost:8000, show me properties"

AI: I'll use your local API endpoint.

[Executes]: curl "http://localhost:8000/properties/"

[Returns]: Property list from local API

AI: Here are your properties from localhost...
```

## Skill File Structure

### Frontmatter (Metadata)

```yaml
---
name: ai-realtor
description: "..."
always: true
metadata: {"nanobot":{"emoji":"🏠","requires":{}}}
---
```

**Note:** The `requires: {}` is now empty! No environment variables required.

### Content

The skill content uses hardcoded URLs:

```markdown
## Quick Start

All commands use the production API by default - **no setup required!**

Simply use the curl commands as shown below.

### Custom URL (Optional)

For local development or custom deployment:

# Replace: https://ai-realtor.fly.dev
# With: http://localhost:8000
```

## Testing It Out

### 1. Verify Production API Works

```bash
# Test directly
curl "https://ai-realtor.fly.dev/properties/" | jq '.'

# Should return property list
```

### 2. Check Skill File

```bash
# View the skill
cat ~/.nanobot/workspace/skills/ai-realtor/SKILL.md

# All URLs should be hardcoded
```

### 3. Restart Nanobot

```bash
nanobot restart
```

### 4. Use Voice Commands

```
"Show me all properties"
"Enrich property 5 with Zillow data"
"How's my portfolio doing?"
```

## Summary

| Aspect | Approach | Status |
|--------|----------|--------|
| **Production URL** | Hardcoded `https://ai-realtor.fly.dev` | ✅ Works |
| **Custom URL** | Documented in skill, AI can adapt | ✅ Works |
| **Environment Variables** | Not required | ✅ Simplified |
| **Setup Required** | None | ✅ Zero-config |
| **User Experience** | Works immediately | ✅ Optimal |

## Key Takeaway

**Hardcoded URLs are better for nanobot skills** because:

1. Skills are static text, not executable scripts
2. Environment variables don't expand in skill files
3. Hardcoded URLs work immediately without setup
4. The AI can adapt commands when told about different endpoints
5. Production APIs are typically stable and reliable

The AI Realtor skill now uses **hardcoded production URLs** by default, making it **zero-setup and ready to use** immediately!
