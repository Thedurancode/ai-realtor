# AI Realtor Nanobot Integration

Complete integration of the AI Realtor platform with [nanobot](https://github.com/HKD0/nanobot) - a voice-controlled AI assistant.

## 📚 Documentation

- **[Quick Reference](NANOBOT_QUICK_REF.md)** - Essential commands and voice examples
- **[Complete Guide](NANOBOT_SKILL_GUIDE.md)** - Full documentation with use cases
- **[Preloading Implementation](NANOBOT_SKILL_PRELOADING.md)** - Technical implementation details

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Run the setup script
./setup-ai-realtor-skill.sh

# Restart nanobot
nanobot restart
```

### Option 2: Manual Setup

```bash
# 1. Create skill directory
mkdir -p ~/.nanobot/workspace/skills/ai-realtor

# 2. Copy skill file (already created at)
#    ~/.nanobot/workspace/skills/ai-realtor/SKILL.md

# 3. Set environment variables
export AI_REALTOR_API_URL="https://ai-realtor.fly.dev"

# 4. Add to shell profile
echo 'export AI_REALTOR_API_URL="https://ai-realtor.fly.dev"' >> ~/.bashrc
source ~/.bashrc

# 5. Restart nanobot
nanobot restart
```

## ✨ What It Does

The AI Realtor skill gives nanobot voice-controlled access to:

### Core Features
- 🏠 **Property Management** - Create, list, update, delete properties
- 📊 **Zillow Enrichment** - Photos, Zestimate, tax history, schools
- 🔍 **Skip Tracing** - Find property owner contacts
- 📄 **Contract Management** - Templates, e-signatures, status tracking
- 📈 **Analytics** - Portfolio stats, pipeline, deal scoring

### Marketing Hub
- 🎨 **Agent Branding** - Colors, logo, identity
- 📱 **Facebook Ads** - AI-powered campaign generation
- 📲 **Social Media** - Multi-platform posting (Facebook, Instagram, LinkedIn, etc.)

### Intelligence
- 🧠 **AI Recaps** - Auto-generated property summaries
- ⚡ **Insights** - Proactive alerts for issues
- 📊 **Scoring** - 4-dimensional deal analysis
- 🔔 **Tasks** - Scheduled reminders and follow-ups

## 🎤 Voice Examples

Once installed, you can control the AI Realtor platform with natural language:

```
"Create a property at 123 Main St, New York for $850,000"

"Show me all condos under 500k in Miami"

"Enrich property 5 with Zillow data"

"Skip trace property 5 to find the owner"

"Is property 5 ready to close?"

"Attach the required contracts for property 5"

"Send the Purchase Agreement for signing"

"How's my portfolio doing?"

"What needs attention?"

"Score property 5"

"Create a Facebook ad for property 5"

"Schedule social posts for next week"

"Apply the Luxury Gold brand colors"
```

## 📁 Files Created

1. **`~/.nanobot/workspace/skills/ai-realtor/SKILL.md`**
   - Main skill file (12KB)
   - Loaded automatically on nanobot startup
   - Contains all API endpoints and usage examples

2. **`setup-ai-realtor-skill.sh`**
   - Automated setup script
   - Configures environment variables
   - Creates skill directory

3. **`NANOBOT_QUICK_REF.md`**
   - Quick reference card
   - Essential commands
   - Voice examples

4. **`NANOBOT_SKILL_GUIDE.md`**
   - Complete documentation
   - Use cases by role (agent, investor, marketing)
   - Troubleshooting guide

5. **`NANOBOT_SKILL_PRELOADING.md`**
   - Technical implementation
   - How to add preloading to nanobot
   - Architecture decisions

## 🔧 Configuration

### Environment Variables

```bash
# Required
export AI_REALTOR_API_URL="https://ai-realtor.fly.dev"

# Optional (if authentication enabled)
export AI_REALTOR_API_KEY="your-api-key"
```

### Skill Features

- ✅ **Always Loaded** - Marked with `always: true` for instant access
- ✅ **Smart Requirements** - Checks for API_URL environment variable
- ✅ **Comprehensive** - Covers 40+ API endpoints
- ✅ **Voice-Native** - Optimized for voice commands

## 🎯 Use Cases

### Real Estate Agent
```
"Create a property listing"
"Enrich it with market data"
"Find the owner's contact info"
"Set up contracts for closing"
"Create marketing campaigns"
```

### Property Manager
```
"Show properties needing repairs"
"Schedule contractor inspections"
"Check contract expiration dates"
"Generate maintenance reports"
```

### Investor
```
"Score all my properties"
"Show me the best deals"
"Get comparable sales data"
"Calculate maximum allowable offer"
"What's my portfolio value?"
```

### Marketing Coordinator
```
"Set up our brand identity"
"Create social media posts"
"Schedule posts for next week"
"Generate Facebook ads"
"Get campaign analytics"
```

## 🔍 Verification

Test that everything is working:

```bash
# Check environment variables
echo $AI_REALTOR_API_URL

# Test API connection
curl $AI_REALTOR_API_URL/properties/ | jq '.'

# Check skill file exists
ls -la ~/.nanobot/workspace/skills/ai-realtor/SKILL.md

# In nanobot, ask:
"List all available skills"
```

## 📊 API Coverage

The skill covers all major AI Realtor endpoints:

### Properties (7 endpoints)
- Create, list, get, update, delete
- Zillow enrichment
- Skip tracing

### Contracts (13 endpoints)
- Readiness checks
- Template attachment
- AI suggestions
- E-signatures via DocuSeal

### Analytics (3 endpoints)
- Portfolio summary
- Pipeline breakdown
- Contract statistics

### Marketing Hub (39 endpoints)
- Agent branding (12 endpoints)
- Facebook Ads (13 endpoints)
- Social Media (14 endpoints)

### Plus...
- Contacts (2 endpoints)
- Property notes (2 endpoints)
- Insights (2 endpoints)
- Scoring (4 endpoints)
- Bulk operations (2 endpoints)
- Activity timeline (3 endpoints)
- Watchlists (5 endpoints)
- Scheduled tasks (4 endpoints)
- Daily digest (2 endpoints)
- Follow-ups (3 endpoints)
- Comparable sales (3 endpoints)
- Pipeline automation (2 endpoints)
- Web scraper (6 endpoints)
- Webhooks (1 endpoint)

**Total: 119+ endpoints covered**

## 🛠️ Troubleshooting

### Skill Not Loading

```bash
# Check file exists
ls -la ~/.nanobot/workspace/skills/ai-realtor/SKILL.md

# Check environment
echo $AI_REALTOR_API_URL

# Restart nanobot
nanobot restart
```

### API Connection Issues

```bash
# Test API
curl $AI_REALTOR_API_URL/docs

# Check connectivity
ping ai-realtor.fly.dev

# View error details
curl "$AI_REALTOR_API_URL/properties/999" | jq '.detail'
```

### Permission Errors

```bash
# Fix permissions
chmod 644 ~/.nanobot/workspace/skills/ai-realtor/SKILL.md
```

## 📖 Additional Resources

### AI Realtor Platform
- **Live API**: https://ai-realtor.fly.dev
- **Documentation**: https://ai-realtor.fly.dev/docs
- **GitHub**: https://github.com/Thedurancode/ai-realtor
- **Features**: See [CLAUDE.md](CLAUDE.md) for complete feature list

### Nanobot
- **Repository**: https://github.com/HKD0/nanobot
- **Documentation**: https://github.com/HKD0/nanobot/blob/main/README.md

## 🤝 Contributing

To improve the skill:

1. Edit `~/.nanobot/workspace/skills/ai-realtor/SKILL.md`
2. Test with nanobot
3. Submit PR to ai-realtor repository

## 📝 License

Same as AI Realtor platform (MIT License).

## 🎉 Summary

You now have:
- ✅ AI Realtor skill installed in nanobot
- ✅ Voice-controlled access to 135+ commands
- ✅ Complete API integration
- ✅ Marketing hub capabilities
- ✅ Analytics and reporting
- ✅ Automated setup script
- ✅ Comprehensive documentation

**Start using it now:**

```
"Show me all my properties"
"What needs attention today?"
"Create a Facebook ad for my latest listing"
```

---

**Generated with [Claude Code](https://claude.ai/code) via [Happy](https://happy.engineering)**
