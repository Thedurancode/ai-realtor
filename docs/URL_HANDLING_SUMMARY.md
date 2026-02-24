# AI Realtor Nanobot Skill - API URL Handling Summary

## Question: "Does the skill get running url of the api how does that work?"

### Short Answer
**No**, the skill does not use environment variables or dynamic URL resolution. Instead, it **hardcodes the production API URL** directly in all commands.

## Why This Approach?

### The Problem with Environment Variables

Nanobot skills are **static markdown files** that get loaded into the AI's context. They cannot:
- ❌ Access environment variables dynamically
- ❌ Expand shell variables like `$AI_REALTOR_API_URL`
- ❌ Execute code to read configuration
- ❌ Make HTTP requests themselves

When nanobot loads a skill file, it reads it as plain text. The AI sees literally what's written, including the unexpanded variable name.

### The Solution: Hardcoded URLs

The skill uses the **hardcoded production URL** in all commands:

```bash
curl "https://ai-realtor.fly.dev/properties/"
```

**Benefits:**
- ✅ Zero setup required
- ✅ Works immediately out of the box
- ✅ Production API is reliable and always available
- ✅ Clear and explicit
- ✅ No environment variables to configure

## How It Works

### Flow Diagram

```
1. Nanobot starts
   ↓
2. Reads ~/.nanobot/workspace/skills/ai-realtor/SKILL.md
   (Loads as plain text)
   ↓
3. AI sees in its context:
   curl "https://ai-realtor.fly.dev/properties/"
   ↓
4. User asks: "Show me all my properties"
   ↓
5. AI uses exec tool to run:
   curl "https://ai-realtor.fly.dev/properties/"
   ↓
6. curl makes HTTP request to production API
   ↓
7. JSON response returned to AI
   ↓
8. AI formats and presents to user
```

### Skill File Structure

**Before (didn't work):**
```yaml
---
metadata: {"nanobot":{"requires":{"env":["AI_REALTOR_API_URL"]}}}
---
```
```bash
curl "$AI_REALTOR_API_URL/properties/"  # ❌ Variable not expanded
```

**After (works perfectly):**
```yaml
---
metadata: {"nanobot":{"requires":{}}}  # ✅ No requirements
---
```
```bash
curl "https://ai-realtor.fly.dev/properties/"  # ✅ Hardcoded URL
```

## Custom URL Support

### For Local Development

If a user needs to use a different API endpoint (localhost, staging, etc.), they can:

**Option 1: Tell the AI**
```
User: "I'm using a local API at http://localhost:8000, show me properties"
AI: [Understands and adapts] curl "http://localhost:8000/properties/"
```

**Option 2: Manual Replacement**
The skill documents the pattern:
```markdown
# Replace: https://ai-realtor.fly.dev
# With: http://localhost:8000
```

The AI understands this pattern and can modify commands accordingly.

## Statistics

### Current Skill File

- **Total commands:** 63
- **Hardcoded URLs:** 63 (100%)
- **Environment variables:** 0
- **Setup required:** None

### Coverage

All major endpoint groups covered:
- Properties (7 endpoints)
- Contracts (13 endpoints)
- Analytics (3 endpoints)
- Marketing Hub (39 endpoints)
- And more...

## Verification

### Test Production API

```bash
# Should work immediately
curl "https://ai-realtor.fly.dev/properties/" | jq '.'
```

### Check Skill File

```bash
# View the skill
cat ~/.nanobot/workspace/skills/ai-realtor/SKILL.md

# Verify no environment variables
grep AI_REALTOR_API_URL ~/.nanobot/workspace/skills/ai-realtor/SKILL.md
# Should only appear in comments/docs, not in commands
```

### Restart Nanobot

```bash
nanobot restart
```

### Use Voice Commands

```
"Show me all properties"
"Enrich property 5 with Zillow data"
"How's my portfolio doing?"
```

All commands will work immediately with **no setup required**.

## Key Takeaway

**For nanobot skills: Hardcoded URLs > Environment Variables**

**Why?**
1. Skills are static text, not executable scripts
2. Shell variables don't expand in skill files
3. Hardcoded URLs work immediately without setup
4. The AI can adapt commands when told about different endpoints
5. Production APIs are typically stable and reliable
6. Zero configuration = better user experience

## Best Practices for Nanobot Skills

### ✅ DO:

- **Hardcode production URLs** for public APIs
- **Document alternatives** for custom deployments
- **Keep it simple** - zero setup is best
- **Trust the AI** to adapt when needed

### ❌ DON'T:

- **Rely on environment variables** in skill files (they won't expand)
- **Require manual setup** unless absolutely necessary
- **Make users configure** things that could have defaults
- **Over-complicate** with configuration files

## Conclusion

The AI Realtor skill uses **hardcoded production URLs** to ensure it works **immediately without any setup**. This provides the best user experience while still allowing flexibility for custom deployments through AI adaptation.

**Status:** ✅ Zero-config, ready to use!

---

For more details, see: `HOW_URL_WORKS.md`
