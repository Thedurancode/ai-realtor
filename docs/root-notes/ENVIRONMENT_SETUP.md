# Environment Variables Setup Guide

## Quick Start

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and add your API keys**
3. **Restart the server**

---

## Required API Keys (Minimum for Basic Features)

| Feature | API Key | Where to Get It | Priority |
|---------|---------|-----------------|----------|
| **Database** | `DATABASE_URL` | Your PostgreSQL instance | ⭐ Required |
| **AI Features** | `ANTHROPIC_API_KEY` | https://console.anthropic.com/ | ⭐ Required |
| **Address Lookup** | `GOOGLE_PLACES_API_KEY` | https://console.cloud.google.com/ | ⭐ Required |

With these 3 keys, you get:
- Property CRUD operations
- AI contract suggestions
- Address autocomplete/geocoding
- Basic property management

---

## Optional API Keys (Feature-Specific)

### Property Enrichment
- **ZILLOW_API_KEY** - Zillow data (Zestimates, photos, schools)
- Get from: Zillow or third-party provider

### Skip Trace (Owner Discovery)
- **SKIP_TRACE_API_KEY** - Find property owners
- Providers: TLO, BatchSkipTracer, FindTheSeller

### Contract E-Signatures
- **DOCUSEAL_API_KEY** - DocuSeal e-signature platform
- Get from: https://docuseal.co/
- **DOCUSEAL_WEBHOOK_SECRET** - For real-time signature updates

### Phone Calls
- **VAPI_API_KEY** - AI phone calls
- Get from: https://vapi.ai/
- **VAPI_PHONE_NUMBER** - Your VAPI phone number
- **ELEVENLABS_API_KEY** - Better voice synthesis (optional)
- Get from: https://elevenlabs.io/

### Research
- **EXA_API_KEY** - AI-powered web research
- Get from: https://exa.ai/

### Facebook Ads
- **ZUCKERBOT_API_KEY** - AI campaign generation
- Get from: https://zuckerbot.ai/
- **META_ACCESS_TOKEN** - Launch ads to Facebook
- Get from: https://developers.facebook.com/
- **META_AD_ACCOUNT_ID** - Your ad account ID

### Social Media
- **POSTIZ_API_KEY** - Multi-platform posting
- Get from: Postiz dashboard

### Video Generation
- **VIDEOGEN_API_KEY** - AI video from property data
- Get from: https://videogen.com/

---

## Full Feature Breakdown

### 1. Property Management
**Required:** `DATABASE_URL`, `ANTHROPIC_API_KEY`, `GOOGLE_PLACES_API_KEY`

**Features:**
- Create, update, delete properties
- Address autocomplete
- Geocoding
- Property notes
- Contact management

### 2. Property Enrichment
**Add:** `ZILLOW_API_KEY`

**Features:**
- Zestimates (market value)
- Property photos
- School ratings
- Tax history
- Price history
- Property features

### 3. Skip Trace
**Add:** `SKIP_TRACE_API_KEY`

**Features:**
- Find property owners
- Get phone numbers
- Email addresses
- Mailing addresses

### 4. Contract Management
**Add:** `DOCUSEAL_API_KEY`, `DOCUSEAL_WEBHOOK_SECRET`

**Features:**
- 15+ contract templates
- AI contract suggestions
- E-signature integration
- Real-time status updates
- Multi-party signing

### 5. Phone Calls
**Add:** `VAPI_API_KEY`, `VAPI_PHONE_NUMBER`

**Optional:** `ELEVENLABS_API_KEY` (better voice)

**Features:**
- AI-powered phone calls
- Property updates
- Contract reminders
- Skip trace outreach
- Conversation recording

### 6. Research
**Add:** `EXA_API_KEY`

**Features:**
- Deep property research
- Market analysis
- Comparable sales
- Neighborhood insights
- Research dossiers

### 7. Facebook Ads
**Add:** `ZUCKERBOT_API_KEY`, `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID`

**Features:**
- AI campaign generation
- Launch to Facebook/Instagram
- Performance tracking
- A/B testing
- Competitor analysis

### 8. Social Media
**Add:** `POSTIZ_API_KEY`

**Features:**
- Multi-platform posting
- AI content generation
- Campaign scheduling
- Analytics dashboard
- Content calendar

### 9. Video Generation
**Add:** `VIDEOGEN_API_KEY`

**Features:**
- AI video from property data
- Multiple video styles
- Automated rendering
- Video management

---

## Environment-Specific Settings

### Local Development
```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
WEBHOOK_BASE_URL=https://your-ngrok-url.ngrok.io
```

### Production (Fly.io)
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=
WEBHOOK_BASE_URL=https://ai-realtor.fly.dev
```

### Staging
```bash
ENVIRONMENT=staging
LOG_LEVEL=INFO
CORS_ORIGINS=https://staging.yourdomain.com
WEBHOOK_BASE_URL=https://ai-realtor-staging.fly.dev
```

---

## Scheduling & Automation

### Daily Digest
```bash
# Send at 8 AM UTC (adjust for your timezone)
DAILY_DIGEST_HOUR=8
DAILY_DIGEST_MINUTE=0
```

### Pipeline Automation
```bash
# Enable automatic status transitions
PIPELINE_AUTOMATION_ENABLED=true
# Check every 5 minutes
PIPELINE_CHECK_INTERVAL=5
```

### Task Runner
```bash
# Process tasks every 60 seconds
TASK_RUNNER_INTERVAL=60
```

---

## Security Notes

1. **Never commit `.env` to git** (it's already in `.gitignore`)
2. **Use strong, unique secrets** for webhooks
3. **Rotate API keys** regularly
4. **Limit API key permissions** to only what's needed
5. **Use environment variables** instead of hardcoding keys

---

## Testing Your Setup

After configuring your `.env` file, test it:

```bash
# Test database connection
python -c "from app.database import engine; print(engine.url)"

# Test API key loading
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.environ.get('ANTHROPIC_API_KEY'))"

# Start the server
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs to test the API endpoints.

---

## Troubleshooting

### "Invalid API Key" errors
- Check that the API key is correct (no extra spaces)
- Ensure the `.env` file is being loaded (check `load_dotenv()`)
- Verify the key is active in the provider's dashboard

### Database connection errors
- Verify PostgreSQL is running: `pg_isready`
- Check connection string format
- Ensure database exists: `createdb ai_realtor`

### Webhook not working
- Check `WEBHOOK_BASE_URL` is correct
- Ensure webhook secret matches in both places
- Use ngrok for local development: `ngrok http 8000`

---

## Cost Estimates (Monthly)

| Service | Free Tier | Estimated Cost |
|---------|-----------|----------------|
| Anthropic Claude | - | $1-20 (depends on usage) |
| Google Places | $200 free | $0-10 after free tier |
| Zillow | Varies | $50-200 |
| Skip Trace | - | $50-500 |
| DocuSeal | Free tier available | $0-50 |
| VAPI | $10 free | $10-100 |
| ElevenLabs | Free tier available | $0-30 |
| Exa | $1000 free | $0-50 after free tier |
| Zuckerbot | Varies | $29-99 |
| Postiz | Free tier available | $0-30 |
| Videogen | Varies | $20-100 |

**Estimated minimum monthly cost:** $50-200
**Estimated full-featured cost:** $300-1000

---

## Need Help?

Check the documentation:
- API Docs: https://ai-realtor.fly.dev/docs
- GitHub: https://github.com/Thedurancode/ai-realtor
- Issues: https://github.com/Thedurancode/ai-realtor/issues
