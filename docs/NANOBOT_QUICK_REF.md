# AI Realtor Nanobot Skill - Quick Reference

## Setup

```bash
# Quick setup
export AI_REALTOR_API_URL="https://ai-realtor.fly.dev"
mkdir -p ~/.nanobot/workspace/skills/ai-realtor
# Copy SKILL.md to this location
nanobot restart
```

## Essential Commands

### Properties
```bash
# List all
curl "$AI_REALTOR_API_URL/properties/"

# Create
curl -X POST "$AI_REALTOR_API_URL/properties/" \
  -H "Content-Type: application/json" \
  -d '{"place_id": "...", "property_type": "house", "agent_id": 1}'

# Get details
curl "$AI_REALTOR_API_URL/properties/5"

# Enrich with Zillow
curl -X POST "$AI_REALTOR_API_URL/properties/5/enrich"

# Skip trace
curl -X POST "$AI_REALTOR_API_URL/properties/5/skip-trace"
```

### Contracts
```bash
# Check readiness
curl "$AI_REALTOR_API_URL/properties/5/contract-readiness"

# Attach templates
curl -X POST "$AI_REALTOR_API_URL/properties/5/attach-contracts"

# List contracts
curl "$AI_REALTOR_API_URL/contracts/?property_id=5"

# Send for signature
curl -X POST "$AI_REALTOR_API_URL/contracts/3/send"
```

### Analytics
```bash
# Portfolio summary
curl "$AI_REALTOR_API_URL/analytics/portfolio"

# Pipeline status
curl "$AI_REALTOR_API_URL/analytics/pipeline"

# Property score
curl -X POST "$AI_REALTOR_API_URL/scoring/property/5"
```

### Marketing
```bash
# Create brand
curl -X POST "$AI_REALTOR_API_URL/agent-brand/1" \
  -d '{"company_name": "Acme Realty", "primary_color": "#B45309"}'

# Generate Facebook ad
curl -X POST "$AI_REALTOR_API_URL/facebook-ads/campaigns/generate?agent_id=1" \
  -d '{"url": "...", "campaign_objective": "leads"}'

# Create social post
curl -X POST "$AI_REALTOR_API_URL/postiz/posts/create?agent_id=1" \
  -d '{"content_type": "property_promo", "caption": "..."}'
```

## Voice Examples (Nanobot)

```
"Create a property at 123 Main St for $850,000"
"Show me all condos under 500k in Miami"
"Enrich property 5 with Zillow data"
"Skip trace property 5"
"Is property 5 ready to close?"
"Attach the required contracts"
"Send the Purchase Agreement for signing"
"How's my portfolio doing?"
"What needs attention?"
"Score property 5"
"Create a Facebook ad for property 5"
"Schedule social posts for next week"
```

## Common Filters

### Properties
```
?status=new_property
?property_type=condo
?city=Miami
?min_price=100000
?max_price=500000
?bedrooms=3
```

### Insights
```
?priority=urgent
?priority=high
```

### Scoring
```
?limit=10
?min_score=80
```

## Status Values

### Property Pipeline
- `new_property` → Just created
- `enriched` → Zillow data added
- `researched` → Skip trace completed
- `waiting_for_contracts` → Contracts attached
- `complete` → All contracts signed

### Contract Status
- `DRAFT` → Created but not sent
- `SENT` → Sent to signers
- `PENDING_SIGNATURE` → Waiting for signatures
- `COMPLETED` → Fully signed

## Property Types
`house` | `condo` | `townhouse` | `apartment` | `land` | `commercial` | `multi-family`

## Contact Roles
`buyer` | `seller` | `lawyer` | `contractor` | `inspector` | `lender` | `title_company`

## Quick Workflows

### New Lead
```bash
curl -X POST "$AI_REALTOR_API_URL/properties/" -d '{...}'          # 1. Create
curl -X POST "$AI_REALTOR_API_URL/properties/1/enrich"             # 2. Enrich
curl -X POST "$AI_REALTOR_API_URL/properties/1/skip-trace"         # 3. Skip trace
curl -X POST "$AI_REALTOR_API_URL/properties/1/attach-contracts"   # 4. Contracts
curl -X POST "$AI_REALTOR_API_URL/properties/1/generate-recap"     # 5. Recap
```

### Check Deal Health
```bash
curl "$AI_REALTOR_API_URL/properties/5/contract-readiness"        # Readiness
curl "$AI_REALTOR_API_URL/scoring/property/5"                      # Score
curl "$AI_REALTOR_API_URL/comps/5"                                 # Comps
curl "$AI_REALTOR_API_URL/insights/property/5"                     # Issues
```

## Tips

1. **Use jq** for JSON parsing: `curl ... | jq '.'`
2. **Check heartbeat** in property responses for pipeline status
3. **Use bulk operations** for multiple properties
4. **Webhooks auto-update** contract status when documents are signed
5. **AI recaps auto-regenerate** on key events

## Troubleshooting

```bash
# Test connection
curl $AI_REALTOR_API_URL/docs

# Check env var
echo $AI_REALTOR_API_URL

# View error details
curl "$AI_REALTOR_API_URL/properties/999" | jq '.detail'
```

## Full Docs
- **API**: https://ai-realtor.fly.dev/docs
- **GitHub**: https://github.com/Thedurancode/ai-realtor
- **Setup Guide**: See NANOBOT_SKILL_GUIDE.md
