# AI Realtor Nanobot Skill - Complete Guide

## Overview

The AI Realtor skill integrates the AI Realtor platform into nanobot, giving you voice-controlled access to 135+ real estate management commands through a conversational AI assistant.

**What it enables:**
- Property management with Zillow enrichment
- Contract management and e-signatures
- Skip tracing for owner discovery
- Marketing hub (Facebook Ads + Social Media)
- Analytics and reporting
- Voice goal execution

## Quick Start

### Method 1: Automated Setup (Recommended)

```bash
# Run the setup script
cd /path/to/ai-realtor
./setup-ai-realtor-skill.sh

# Restart nanobot
nanobot restart
```

### Method 2: Manual Setup

```bash
# 1. Create skill directory
mkdir -p ~/.nanobot/workspace/skills/ai-realtor

# 2. Copy the skill file
cp ai-realtor/SKILL.md ~/.nanobot/workspace/skills/ai-realtor/

# 3. Set environment variables
export AI_REALTOR_API_URL="https://ai-realtor.fly.dev"
export AI_REALTOR_API_KEY="your-key"  # Optional

# 4. Add to shell profile (~/.bashrc or ~/.zshrc)
echo 'export AI_REALTOR_API_URL="https://ai-realtor.fly.dev"' >> ~/.bashrc
source ~/.bashrc

# 5. Restart nanobot
nanobot restart
```

### Method 3: As Builtin Skill

For distribution with nanobot, add to builtin skills:

```bash
# Copy to nanobot builtin skills directory
cp -r ai-realtor /path/to/nanobot/nanobot/skills/
```

## Verification

Test that the skill is loaded:

```bash
# In nanobot conversation, say:
"List all available skills"

# Or test the API directly:
curl $AI_REALTOR_API_URL/properties/ | jq '.'
```

## Usage Examples

### Property Management

```
User: "Create a property at 123 Main St, New York for $850,000"
Nanobot: [Calls API to create property with Google Places lookup]

User: "Show me all condos under 500k in Miami"
Nanobot: [Lists properties with filters]

User: "Enrich property 5 with Zillow data"
Nanobot: [Calls enrichment endpoint, shows Zestimate, photos, schools]
```

### Contract Workflow

```
User: "Is property 5 ready to close?"
Nanobot: [Checks contract readiness, reports status]

User: "Attach the required contracts for property 5"
Nanobot: [Auto-attaches templates based on state/type/price]

User: "Send the Purchase Agreement for signing"
Nanobot: [Sends contract via DocuSeal]
```

### Skip Tracing

```
User: "Skip trace property 5"
Nanobot: [Finds owner contact info]

User: "Call the owner of property 5"
Nanobot: [Initiates VAPI phone call with property context]
```

### Analytics

```
User: "How's my portfolio doing?"
Nanobot: [Pulls analytics summary - pipeline, value, contracts]

User: "What needs attention?"
Nanobot: [Gets insights - stale properties, missing enrichment, deadlines]
```

### Marketing

```
User: "Create a Facebook ad for property 5"
Nanobot: [Generates ad campaign with AI copy]

User: "Schedule social posts for next week"
Nanobot: [Creates multi-platform posts]

User: "Apply the Luxury Gold brand colors"
Nanobot: [Updates brand configuration]
```

### Bulk Operations

```
User: "Enrich all Miami properties"
Nanobot: [Executes bulk enrichment across filtered properties]

User: "Score all my properties"
Nanobot: [Runs scoring engine on portfolio]
```

## Skill Features

### Always Loaded
The skill is marked with `always: true`, so it's:
- ✅ Fully loaded into nanobot's context on startup
- ✅ Immediately available without extra steps
- ✅ No need for `read_file` tool calls

### Smart Requirements
The skill checks for:
- `AI_REALTOR_API_URL` environment variable (required)
- `AI_REALTOR_API_KEY` (optional, if authentication needed)

### Comprehensive Coverage
Covers all 40+ API endpoints across:
- Properties (7 endpoints)
- Contracts (13 endpoints)
- Contacts (2 endpoints)
- Analytics (3 endpoints)
- Marketing Hub (39 endpoints)
- Web Scraper (8 endpoints)
- And more!

## Architecture

```
┌─────────────────┐
│   Nanobot       │
│  (AI Assistant) │
└────────┬────────┘
         │ Reads SKILL.md
         ▼
┌─────────────────┐
│ AI Realtor      │
│ Skill           │
│ (Instructions)  │
└────────┬────────┘
         │ Uses curl/exec
         ▼
┌─────────────────┐
│ AI Realtor API  │
│ (Backend)       │
└─────────────────┘
```

## Environment Variables

### Required

```bash
export AI_REALTOR_API_URL="https://ai-realtor.fly.dev"
```

### Optional

```bash
export AI_REALTOR_API_KEY="your-api-key-here"
```

### Test Configuration

```bash
# Check if variables are set
echo $AI_REALTOR_API_URL
echo $AI_REALTOR_API_KEY

# Test API connection
curl $AI_REALTOR_API_URL/docs
```

## API Endpoint Reference

### Properties
- `POST /properties/` - Create property
- `GET /properties/` - List with filters
- `GET /properties/{id}` - Get details
- `PUT /properties/{id}` - Update
- `DELETE /properties/{id}` - Delete
- `POST /properties/{id}/enrich` - Zillow enrichment
- `POST /properties/{id}/skip-trace` - Find owner

### Contracts
- `GET /properties/{id}/contract-readiness` - Check readiness
- `POST /properties/{id}/attach-contracts` - Auto-attach templates
- `POST /properties/{id}/ai-suggest-contracts` - AI suggestions
- `GET /contracts/` - List contracts
- `POST /contracts/{id}/send` - Send for signature
- `GET /contracts/{id}/signing-status` - Check status

### Analytics
- `GET /analytics/portfolio` - Full dashboard
- `GET /analytics/pipeline` - Pipeline breakdown
- `GET /analytics/contracts` - Contract stats

### Marketing
- `POST /agent-brand/{id}` - Create brand
- `POST /facebook-ads/campaigns/generate` - Generate ad
- `POST /postiz/posts/create` - Create social post

## Common Workflows

### New Lead Setup

```bash
# Nanobot understands this as:
"Set up property 5 as a new lead"

# Which executes:
1. resolve_property(5)
2. enrich_property()
3. skip_trace_property()
4. attach_required_contracts()
5. generate_recap()
6. summarize_next_actions()
```

### Deal Closing

```bash
"Close the deal on property 3"

# Executes:
1. resolve_property(3)
2. check_contract_readiness()
3. generate_recap()
4. summarize()
```

### Market Analysis

```bash
"Show me comps for property 5"

# Executes:
1. resolve_property(5)
2. get_comps_dashboard()
3. summarize()
```

## Troubleshooting

### Skill Not Loading

```bash
# Check skill file exists
ls -la ~/.nanobot/workspace/skills/ai-realtor/SKILL.md

# Check environment variables
echo $AI_REALTOR_API_URL

# Restart nanobot
nanobot restart
```

### API Connection Issues

```bash
# Test API directly
curl $AI_REALTOR_API_URL/properties/ | jq '.'

# Check network connectivity
ping ai-realtor.fly.dev

# Verify API URL
curl $AI_REALTOR_API_URL/docs
```

### Permission Errors

```bash
# Check file permissions
ls -la ~/.nanobot/workspace/skills/ai-realtor/

# Fix permissions
chmod 644 ~/.nanobot/workspace/skills/ai-realtor/SKILL.md
```

## Advanced Configuration

### Custom API Endpoint

For development or self-hosted:

```bash
export AI_REALTOR_API_URL="http://localhost:8000"
```

### Preload Configuration

To ensure skill is always loaded, add to nanobot config:

```yaml
# ~/.nanobot/config.yaml
skills:
  preload:
    - ai-realtor
    - memory
    - github
```

### Alias for Quick Access

Add to shell profile:

```bash
# AI Realtor aliases
alias ai-realtor='curl $AI_REALTOR_API_URL'
alias ai-props='curl $AI_REALTOR_API_URL/properties/ | jq .'
alias ai-analytics='curl $AI_REALTOR_API_URL/analytics/portfolio | jq .'
```

## Integration with Other Skills

### With GitHub Skill

```
User: "Create a GitHub issue for property 5 needing repairs"
Nanobot: [Uses both ai-realtor and github skills]
```

### With Memory Skill

```
User: "Remember that property 5 has a new fence"
Nanobot: [Adds note to property + saves to memory]
```

### With Cron Skill

```
User: "Remind me to follow up on property 5 in 3 days"
Nanobot: [Creates scheduled task via cron]
```

## Examples by Use Case

### Real Estate Agent

```
"Create a property for 123 Main St"
"Enrich it with Zillow data"
"Skip trace the owner"
"Create a follow-up task for 3 days"
"Generate a Facebook ad campaign"
```

### Property Manager

```
"Show me all properties needing repairs"
"Create a task for the contractor"
"Schedule inspection for property 5"
"Check contract status for all leases"
```

### Investor

```
"Score all my properties"
"Show me the top 5 deals"
"Get comparable sales for property 5"
"Calculate MAO for property 3"
"What's my portfolio value?"
```

### Marketing Coordinator

```
"Set up our brand with Luxury Gold colors"
"Create social posts for our 3 new listings"
"Schedule them for next week"
"Get analytics on our last campaign"
```

## Performance Tips

1. **Use filters** - When listing properties, use filters to reduce payload
2. **Cache recaps** - Property recaps are expensive; don't regenerate unnecessarily
3. **Bulk operations** - Use bulk endpoints instead of loops
4. **Pagination** - Use `offset` and `limit` for large datasets
5. **Webhooks** - Use DocuSeal webhooks instead of polling

## Security Best Practices

1. **Never commit API keys** to git
2. **Use environment variables** for secrets
3. **Rotate keys regularly**
4. **Use read-only keys** for analytics
5. **Audit access logs**

## Updates & Maintenance

### Update Skill

```bash
# Pull latest version
cp ai-realtor/SKILL.md ~/.nanobot/workspace/skills/ai-realtor/

# Restart nanobot
nanobot restart
```

### Check Version

```bash
# View skill metadata
head -5 ~/.nanobot/workspace/skills/ai-realtor/SKILL.md
```

## Support

- **API Docs**: https://ai-realtor.fly.dev/docs
- **GitHub**: https://github.com/Thedurancode/ai-realtor
- **Issues**: https://github.com/Thedurancode/ai-realtor/issues

## Contributing

To improve the skill:

1. Edit `SKILL.md` with new endpoints
2. Test with nanobot
3. Submit PR to ai-realtor repo

## License

Same as AI Realtor platform (MIT).
