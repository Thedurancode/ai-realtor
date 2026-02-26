# AI Realtor Platform - Complete Feature Documentation

**Version:** 1.0.0
**Last Updated:** February 26, 2026
**Documentation:** https://ai-realtor.fly.dev/docs
**GitHub:** https://github.com/Thedurancode/ai-realtor

---

## Table of Contents

1. [Property Management](#1-property-management)
2. [Data Enrichment](#2-data-enrichment)
3. [Skip Trace & Lead Generation](#3-skip-trace--lead-generation)
4. [Contract Management](#4-contract-management)
5. [Phone Call Automation](#5-phone-call-automation)
6. [AI-Powered Video Generation](#6-ai-powered-video-generation)
7. [Voiceover Generation](#7-voiceover-generation)
8. [Google Calendar Integration](#8-google-calendar-integration)
9. [Marketing Hub](#9-marketing-hub)
10. [Voice Control (MCP)](#10-voice-control-mcp)
11. [Predictive Intelligence](#11-predictive-intelligence)
12. [Market Analytics](#12-market-analytics)
13. [Relationship Intelligence](#13-relationship-intelligence)
14. [Negotiation Agent](#14-negotiation-agent)
15. [Document Analysis](#15-document-analysis)
16. [Competitive Intelligence](#16-competitive-intelligence)
17. [Deal Sequencing](#17-deal-sequencing)
18. [Analytics Dashboard](#18-analytics-dashboard)
19. [Scheduled Tasks](#19-scheduled-tasks)
20. [Follow-Up Queue](#20-follow-up-queue)
21. [Pipeline Automation](#21-pipeline-automation)
22. [Daily Digest](#22-daily-digest)
23. [Property Scoring](#23-property-scoring)
24. [Market Watchlists](#24-market-watchlists)
25. [Bulk Operations](#25-bulk-operations)
26. [Activity Timeline](#26-activity-timeline)
27. [Property Heartbeat](#27-property-heartbeat)
28. [Web Scraper](#28-web-scraper)
29. [Deal Calculator](#29-deal-calculator)
30. [Offer Management](#30-offer-management)
31. [Research & Semantic Search](#31-research--semantic-search)
32. [Property Notes](#32-property-notes)
33. [Conversation History](#33-conversation-history)
34. [Workflow Templates](#34-workflow-templates)
35. [Voice Campaigns](#35-voice-campaigns)
36. [Proactive Notifications](#36-proactive-notifications)
37. [Real-Time Activity Feed](#37-real-time-activity-feed)
38. [Customer Portal](#38-customer-portal)
39. [Compliance Engine](#39-compliance-engine)
40. [Security Features](#40-security-features)

---

## 1. Property Management

### Overview
Complete property lifecycle management with intelligent address lookup, status tracking, and automatic activity logging.

### Features

#### Property Creation
- **Google Places Integration**: Autocomplete for accurate addresses
- **Automatic Geocoding**: Lat/long coordinates
- **Property Types**: house, condo, townhouse, apartment, land, commercial, multi-family
- **Price & Details**: Beds, baths, square footage, year built, lot size
- **Deal Scoring**: Automatic grade assignment (A-F)
- **Agent Assignment**: Link properties to specific agents

#### Property Status Pipeline
5-stage automated pipeline:
1. **NEW_PROPERTY** - Newly created
2. **ENRICHED** - Zillow data added
3. **RESEARCHED** - Skip trace completed
4. **WAITING_FOR_CONTRACTS** - Contracts attached
5. **COMPLETE** - All contracts signed

#### Advanced Filtering
- By status, property type, city, state
- Price range (min/max)
- Bedroom/bathroom counts
- Square footage ranges
- Agent assignment
- Date ranges

### API Endpoints
```
POST   /properties/                    - Create property
GET    /properties/                    - List all properties (with filters)
GET    /properties/{id}                - Get property details
PUT    /properties/{id}                - Update property
DELETE /properties/{id}                - Delete property
GET    /properties/{id}/heartbeat      - Get property heartbeat
```

### Voice Commands (MCP)
- "Create a property at 123 Main St, New York for $850,000"
- "Show me all condos under 500k in Miami"
- "Show me houses with 3+ bedrooms in Austin"
- "Update property 5 status to complete"
- "Delete property 3"

### Database Tables
- `properties` - Main property records
- `property_enrichments` - External data sources

---

## 2. Data Enrichment

### Overview
Automated property data enrichment from Zillow, web scraping, and external APIs.

### Zillow Integration
Automatically fetches comprehensive property data:
- **High-resolution photos** (up to 10 images)
- **Zestimate** - Current market value estimate
- **Rent Zestimate** - Monthly rental value
- **Tax assessment** - Property tax history
- **Price history** - Past sales data
- **Schools nearby** - Ratings and test scores
- **Property features** - Year built, lot size, parking, HVAC
- **Market statistics** - Comparable sales

### Web Scraping
Import properties from any URL:
- **Specialized scrapers**: Zillow, Redfin, Realtor.com
- **Generic AI scraper**: Any website with Claude AI
- **Concurrent scraping**: Multiple URLs at once
- **Duplicate detection**: Prevents duplicate properties
- **Auto-enrichment**: Enrich after scraping

### API Endpoints
```
POST   /properties/{id}/enrich        - Enrich property with Zillow data
POST   /scrape/url                    - Scrape URL and preview
POST   /scrape/scrape-and-create      - Scrape and create property
POST   /scrape/zillow-listing         - Scrape Zillow listing
POST   /scrape/redfin-listing         - Scrape Redfin listing
POST   /scrape/realtor-listing        - Scrape Realtor.com listing
POST   /scrape/zillow-search          - Scrape Zillow search results
POST   /scrape/scrape-and-enrich-batch - Bulk import with enrichment
```

### Voice Commands
- "Enrich property 5 with Zillow data"
- "Scrape this Zillow listing URL"
- "Add this property from the URL"
- "Import these 10 Zillow listings and enrich them all"
- "Scrape this Redfin property and auto-enrich it"

### Database Tables
- `zillow_enrichments` - Zillow data cache
- `property_enrichments` - Multi-source enrichment data

---

## 3. Skip Trace & Lead Generation

### Overview
Owner contact discovery for lead generation and off-market opportunities.

### Features
- **Owner Name Discovery**
- **Phone Numbers** - Mobile and landline
- **Email Addresses**
- **Mailing Addresses**
- **Property History**
- **Auto-Contact Creation** - Adds to contacts automatically

### Skip Trace Providers
Supports multiple providers:
- BatchSkipTracer
- TLO
- FindTheSeller
- Custom providers via API

### API Endpoints
```
POST   /properties/{id}/skip-trace   - Skip trace a property
GET    /skip-traces/{id}             - Get skip trace results
```

### Voice Commands
- "Skip trace property 5"
- "Find the owner of 123 Main St"
- "Get contact info for property 3"

### Database Tables
- `skip_traces` - Skip trace results
- `contacts` - Auto-created contacts from skip trace

---

## 4. Contract Management

### Overview
AI-powered contract management with automatic template matching, e-signatures, and compliance checking.

### Three-Tier Contract System

#### A. Automatic Template Matching
- **15+ pre-configured templates** for NY, CA, FL, TX
- **State-specific requirements** (disclosure laws, purchase agreements)
- **Property type filtering** (residential vs commercial)
- **Price range filtering** (high-value = additional contracts)
- **City-specific contracts** (NYC seller disclosure, etc.)
- **Signer role mapping** - Contracts → Contact roles

#### B. AI-Suggested Contracts
- **Claude AI analysis** of property details
- **Required vs optional** recommendations
- **Reasoning** for each suggestion
- **Compliance checking**

#### C. Manual Control
- Override automatic suggestions
- Mark contracts as required/optional
- Set deadlines
- Custom contract creation

### Contract Statuses
- DRAFT - Created but not sent
- SENT - Sent for signature
- IN_PROGRESS - Being signed
- PENDING_SIGNATURE - Awaiting signatures
- COMPLETED - Fully signed
- CANCELLED - Cancelled
- EXPIRED - Expired
- ARCHIVED - Archived

### DocuSeal Integration
- **E-signature platform** integration
- **Real-time webhook sync** when signed
- **Automatic status updates**
- **HMAC signature verification** for security

### Compliance Engine
- **Federal regulations**: RESPA, TILA, Fair Housing
- **State requirements**: Per-state compliance checks
- **Local ordinances**: City-specific requirements
- **AI-powered analysis**: Claude identifies issues

### API Endpoints
```
POST   /contracts/                     - Create contract
GET    /contracts/                     - List contracts
GET    /contracts/{id}                 - Get contract details
PUT    /contracts/{id}                 - Update contract
DELETE /contracts/{id}                 - Delete contract
POST   /contracts/{id}/send            - Send for signature
POST   /contracts/smart-send           - Multi-party send
GET    /contracts/{id}/status          - Check signing status
POST   /contracts/check-readiness      - Check property readiness
POST   /contracts/attach-required      - Auto-attach templates
POST   /contracts/ai-suggest           - AI contract suggestions
POST   /contracts/apply-suggestions    - Apply AI suggestions
POST   /contracts/{id}/mark-required   - Mark as required/optional
POST   /compliance/check               - Run compliance check
GET    /compliance/requirements        - Get requirements for state/type
```

### Voice Commands
- "Is property 5 ready to close?"
- "Suggest contracts for property 5 using AI"
- "Apply AI contract suggestions for property 5"
- "Send the Purchase Agreement for signing"
- "Check contract status for property 3"
- "Mark the Disclosure as required"

### Database Tables
- `contracts` - Contract records
- `contract_templates` - Reusable templates
- `contract_signers` - Contract signers
- `contract_documents` - Document storage
- `compliance_checks` - Compliance check results

---

## 5. Phone Call Automation

### Overview
AI-powered phone calls with full property context, recording, and transcription.

### Phone Providers

#### VAPI Integration
- **AI-powered conversations**
- **Property context injection**
- **Custom scripts**
- **Call recording**
- **Transcription**
- **Intent detection**
- **Sentiment analysis**

#### Telnyx Integration
- **Direct telephony API**
- **Answering machine detection**
- **Call recording**
- **DTMF gathering**
- **Text-to-speech**
- **Call control** (hangup, speak, gather)

#### ElevenLabs
- **Text-to-speech** for call scripts
- **Voice selection**
- **Custom voice profiles**

### Call Types
1. **Property Update** - Share property details
2. **Contract Reminder** - Contract deadline reminders
3. **Closing Ready** - Celebrate completed deals
4. **Specific Contract Reminder** - Call about one contract
5. **Skip Trace Outreach** - Cold call property owners

### Call Features
- **Automatic recording**
- **Full transcription**
- **AI summary generation**
- **Intent detection** (property_inquiry, schedule_viewing, offer, speak_agent, general)
- **Outcome tracking** (information_provided, viewing_scheduled, offer_created, message_taken, transferred)
- **Caller information capture**
- **Follow-up task creation**

### Webhook Security
- **HMAC-SHA256 signature verification**
- **Constant-time comparison** (timing attack prevention)
- **Telnyx webhook signature validation**

### API Endpoints
```
# VAPI
POST   /vapi/calls                    - Make VAPI call
GET    /vapi/calls/{call_id}          - Get call status
POST   /vapi/calls/{call_id}/hangup   - Hangup call

# Telnyx
POST   /telnyx/calls                  - Make Telnyx call
GET    /telnyx/calls/{call_control_id} - Get call status
POST   /telnyx/calls/{call_control_id}/hangup - Hangup call
POST   /telnyx/calls/{call_control_id}/speak - Speak text
POST   /telnyx/calls/{call_control_id}/gather - Gather DTMF/audio
GET    /telnyx/recordings/{recording_id} - Get recording
GET    /telnyx/phone-numbers          - List phone numbers
POST   /telnyx/webhook                - Telnyx webhook handler

# Phone Calls
GET    /phone-calls/                  - List all calls
GET    /phone-calls/{id}              - Get call details
```

### Voice Commands
- "Call John about property 5"
- "Call the owner of property 5"
- "Call contact 3 about the Purchase Agreement"
- "Make a call to +14155551234"

### Database Tables
- `phone_calls` - Call records with transcription
- Indexes for performance:
  - `idx_phonecall_property_created` - Property call history
  - `idx_phonecall_agent_created` - Agent's calls
  - `idx_phonecall_provider_status` - Provider filtering

---

## 6. AI-Powered Video Generation

### Overview
Generate professional property showcase videos with Remotion and AI.

### Video Features
- **Company logo intro** (3 seconds)
- **Property photo slideshow** (4 seconds per photo)
- **Property details overlay** (price, address, beds, baths, sqft)
- **Smooth transitions** between photos
- **Agent branding** (logo, colors, contact info)
- **Background music** (optional)
- **HD output** (1080p)

### Remotion Integration
- **React-based video engine**
- **Programmatic video generation**
- **Customizable templates**
- **Interactive video editor**
- **Async rendering** with Redis queue
- **S3 storage** for rendered videos

### Video Generation Process
1. Fetch property data
2. Gather photos from Zillow enrichment
3. Generate AI script
4. Render video with Remotion
5. Store in S3
6. Return video URL

### API Endpoints
```
POST   /videos/property/{id}/generate - Generate property video
GET    /videos/renders/{render_id}    - Get render status
POST   /videos/renders/{render_id}/cancel - Cancel render
GET    /videos/renders                - List all renders
```

### Database Tables
- `video_renders` - Render job tracking
- `render_assets` - Asset management

---

## 7. Voiceover Generation

### Overview
Generate professional AI voiceovers using ElevenLabs text-to-speech.

### Voiceover Features
- **AI-generated scripts** from property data
- **Multiple voice options** from ElevenLabs
- **Natural-sounding speech**
- **Synchronized timing** with video
- **Standalone audio** or video-integrated

### ElevenLabs Integration
- **80+ voice options**
- **Multiple languages**
- **Voice cloning** (custom voices)
- **Adjustable speed** and pitch
- **Commercial-quality audio**

### Voiceover Options

#### 1. Full Video with Voiceover
Generate complete video with synchronized voiceover.

#### 2. Standalone Voiceover (Audio Only)
Generate just the audio file for:
- Preview before video generation
- Use in other video editors
- Test different voices

#### 3. Script Preview
Review the generated script before production:
- Text preview
- Word count
- Estimated duration
- Photo count

#### 4. List Available Voices
Browse all ElevenLabs voices with IDs and names.

### API Endpoints
```
POST   /v1/property-videos/generate       - Generate video with voiceover
POST   /v1/property-videos/voiceover      - Generate voiceover only
POST   /v1/property-videos/script-preview - Preview script
GET    /v1/property-videos/voices         - List available voices
```

### Example Usage
```json
// Generate voiceover
POST /v1/property-videos/voiceover
{
  "property_id": 3,
  "agent_id": 5,
  "voice_id": "21m00Tcm4TlvDq8ikWAM"  // Rachel's voice
}

// Response
{
  "audio_path": "/tmp/property_3_voiceover.mp3",
  "script": "Welcome to 123 Main Street...",
  "duration_seconds": 45.2,
  "word_count": 113,
  "property_id": 3,
  "voice_id": "21m00Tcm4TlvDq8ikWAM",
  "audio_size_bytes": 524288
}
```

### Voice Commands
- "Generate a video for property 5"
- "Create a voiceover for property 3"
- "Preview the script for property 7"

---

## 8. Google Calendar Integration

### Overview
Two-way sync with Google Calendar for appointments, tasks, and events.

### Features

#### Calendar Connections
- **OAuth authentication** with Google
- **Multiple calendar support**
- **Access token management**
- **Automatic token refresh** (5-minute buffer)
- **Calendar list management**

#### Sync Types
1. **Scheduled Tasks** - Auto-sync to calendar
2. **Manual Events** - Create appointments
3. **Google Meet Integration** - Auto-create meeting links
4. **Reminders** - Custom reminder times
5. **Recurring Events** - Repeat patterns

#### Calendar Sync Features
- **Automatic event creation** from tasks
- **Event updates** synced back
- **Google Meet conference** creation
- **Attendee management**
- **Location support**
- **Multi-calendar support**

### Token Management
- **Automatic refresh** before expiry
- **5-minute buffer** for safety
- **Refresh token rotation**
- **Error handling** and re-auth prompts

### API Endpoints
```
# Calendar Connections
POST   /calendar/auth/url              - Get OAuth URL
POST   /calendar/callback              - OAuth callback
GET    /calendar/connections           - List connections
POST   /calendar/connections           - Create connection
GET    /calendar/connections/{id}      - Get connection
DELETE /calendar/connections/{id}      - Delete connection

# Calendars
GET    /calendar/calendars             - List user's calendars
POST   /calendar/events                - Create event
PUT    /calendar/events/{id}           - Update event
DELETE /calendar/events/{id}           - Delete event

# Sync
POST   /calendar/sync/task             - Sync scheduled task
POST   /calendar/sync/event            - Sync manual event
POST   /calendar/sync/all              - Sync all pending items
```

### Database Tables
- `calendar_connections` - OAuth connections
- `calendar_events` - Manual events
- `synced_calendar_events` - Sync tracking

---

## 9. Marketing Hub

### Overview
Complete marketing platform with brand management, Facebook Ads, and social media posting.

### A. Agent Branding System

#### Brand Identity Management
- **Company name** and logo
- **5-color palette**:
  - Primary color - Main brand color
  - Secondary color - Supporting color
  - Accent color - Highlight color
  - Background color - Page backgrounds
  - Text color - Main text
- **Tagline/slogan**
- **Website URL**
- **Bio/about text**
- **Social media links**

#### Pre-defined Color Presets
1. **Professional Blue** - Corporate, trustworthy
2. **Modern Green** - Growth, eco-friendly
3. **Luxury Gold** - Premium, high-end
4. **Bold Red** - Urgent, attention-grabbing
5. **Minimalist Black** - Sleek, modern
6. **Ocean Teal** - Calm, coastal

#### Brand Features
- **One-time setup** - Apply everywhere automatically
- **Consistent branding** across all channels
- **Brand guidelines generation**
- **Export brand kit**
- **Preview generation**

### B. Facebook Ads Integration

#### Campaign Generation
- **AI-powered ad creation** from property URLs
- **Automatic target audience** recommendations
- **Ad copy generation** with brand voice
- **Direct Meta Ads Manager** launch
- **Performance tracking** and ROI

#### Campaign Types
- Property promotion
- Open house
- Brand awareness
- Lead generation
- Just listed
- Price reduction

#### AI Features
- **Market research** generation
- **Competitor analysis**
- **Review intelligence** (Google/Yelp reviews)
- **Target audience recommendations**
- **Creative optimization**

### C. Postiz Social Media Integration

#### Supported Platforms
- Facebook (63,206 characters)
- Instagram (2,200 characters)
- Twitter (280 characters)
- LinkedIn (3,000 characters)
- TikTok (2,200 characters)

#### Social Media Features
- **Multi-platform posting** - Schedule to multiple platforms
- **AI content generation** - Generate posts with AI
- **Multi-post campaigns** - 10-post campaigns
- **Reusable templates** - Save post templates
- **Content calendar** - Visual calendar view
- **Analytics dashboard** - Performance metrics

#### Content Types
- Property promotion
- Open house announcement
- Market update
- Brand awareness
- Educational content
- Community highlight
- Client testimonial

### API Endpoints

#### Agent Branding (12 endpoints)
```
POST   /agent-brand/{id}                  - Create brand
GET    /agent-brand/{id}                  - Get brand
PUT    /agent-brand/{id}                  - Update brand
DELETE /agent-brand/{id}                  - Delete brand
GET    /agent-brand/colors/presets        - Get color presets
POST   /agent-brand/{id}/apply-preset     - Apply preset
POST   /agent-brand/{id}/generate-preview - Generate preview
GET    /agent-brand/{id}/preview          - Get preview
POST   /agent-brand/{id}/validate         - Validate brand data
GET    /agent-brand/{id}/guidelines       - Get brand guidelines
POST   /agent-brand/{id}/export           - Export brand kit
```

#### Facebook Ads (13 endpoints)
```
POST   /facebook-ads/campaigns/generate          - Generate campaign
POST   /facebook-ads/campaigns/{id}/launch       - Launch to Meta
POST   /facebook-ads/campaigns/{id}/track        - Track performance
GET    /facebook-ads/campaigns                   - List campaigns
GET    /facebook-ads/campaigns/{id}              - Get campaign
PUT    /facebook-ads/campaigns/{id}              - Update campaign
POST   /facebook-ads/research/generate           - Market research
POST   /facebook-ads/competitors/analyze         - Competitor analysis
POST   /facebook-ads/reviews/extract             - Review intelligence
POST   /facebook-ads/audiences/recommend         - Audience recommendations
POST   /facebook-ads/audiences/{id}/create       - Create audience
GET    /facebook-ads/analytics/campaign/{id}     - Campaign analytics
GET    /facebook-ads/analytics/account           - Account analytics
```

#### Postiz Social Media (14 endpoints)
```
POST   /social/accounts/connect              - Connect social account
GET    /social/accounts                      - List connected accounts
POST   /social/posts/create                  - Create post
POST   /social/posts/{id}/schedule           - Schedule post
GET    /social/posts                         - List posts
GET    /social/posts/{id}                    - Get post
PUT    /social/posts/{id}                    - Update post
POST   /social/ai/generate                   - AI content generation
POST   /social/campaigns/create              - Create campaign
GET    /social/campaigns                     - List campaigns
POST   /social/templates/create              - Create template
GET    /social/templates                     - List templates
GET    /social/analytics/overview            - Get analytics
GET    /social/calendar                      - Content calendar
```

### Voice Commands
- "Set up my brand with Emprezario Inc"
- "Apply the Luxury Gold color scheme"
- "Create a Facebook ad for property 5"
- "Generate market research for Miami condos"
- "Create a social media post for this property"
- "Schedule posts for next week"
- "Generate Instagram content with AI"

### Database Tables
- `agent_brands` - Brand identity
- `facebook_ad_campaigns` - Campaigns
- `facebook_ad_sets` - Ad sets
- `facebook_ads` - Individual ads
- `facebook_ad_creatives` - Creative assets
- `facebook_audiences` - Target audiences
- `facebook_ad_metrics` - Performance metrics
- `postiz_accounts` - Connected accounts
- `postiz_posts` - Social media posts
- `postiz_campaigns` - Multi-post campaigns
- `postiz_templates` - Reusable templates
- `postiz_analytics` - Aggregated analytics

---

## 10. Voice Control (MCP)

### Overview
Complete platform control via voice commands through Claude Desktop integration.

### MCP Server
- **135 voice commands** for full platform control
- **Claude Desktop integration** via MCP protocol
- **Context auto-injection** - AI knows related data
- **Activity logging** - All commands logged to property history
- **Natural language processing** - No rigid syntax required

### Voice Goal Planner
Autonomous multi-step goal execution with 26 actions:
1. **resolve_property** - Find target property
2. **inspect_property** - Load property context
3. **enrich_property** - Pull Zillow data
4. **skip_trace_property** - Find owner contacts
5. **attach_required_contracts** - Auto-attach templates
6. **ai_suggest_contracts** - Get AI suggestions
7. **apply_ai_suggestions** - Create suggested contracts
8. **check_compliance** - Run compliance check
9. **generate_recap** - Generate AI recap
10. **make_phone_call** - Call via VAPI
11. **send_notification** - Send alert
12. **update_property_status** - Change status
13. **add_note** - Save note to property
14. **summarize_next_actions** - Summary and next steps
15. **check_contract_readiness** - Check closing readiness
16. **create_property** - Create new property
17. **check_insights** - Scan for alerts
18. **schedule_task** - Create reminders
19. **get_analytics** - Pull analytics
20. **check_follow_ups** - Get follow-up queue
21. **get_comps** - Pull comparables
22. **bulk_operation** - Execute bulk operations
23. **get_activity_timeline** - Fetch activity feed
24. **score_property** - Run scoring engine
25. **check_watchlists** - Manage watchlists

### Heuristic Plan Matching
Natural language goals automatically mapped to action sequences:

| Command | Plan |
|---------|------|
| "Set up property 5 as a new lead" | enrich → skip trace → contracts → recap |
| "Close the deal on property 3" | check readiness → recap → summarize |
| "Enrich property 5" | enrich → recap → summarize |
| "Skip trace property 5" | skip trace → summarize |
| "Call the owner of property 5" | skip trace → call → summarize |
| "Show me comps for property 5" | get comps → summarize |
| "Enrich all Miami properties" | bulk operation → summarize |
| "What should I work on next?" | check follow-ups → summarize |
| "What happened today?" | get activity timeline → summarize |
| "What needs attention?" | check insights → summarize |
| "Remind me to follow up on property 5 in 3 days" | schedule task → summarize |
| "How's my portfolio doing?" | get analytics → summarize |
| "Score property 5" | score property → summarize |
| "Watch for Miami condos under 500k" | check watchlists → summarize |

### Safety Features
- **Checkpoint/rollback** after each step
- **Failure isolation** - One step failing doesn't crash plan
- **Memory graph** persistence of relationships
- **Human confirmation** for destructive actions

### MCP Tool Categories
- **Property Tools** (7)
- **Contract Tools** (13)
- **Recap & Call Tools** (9)
- **Deal & Offer Tools** (18)
- **Research & Search Tools** (7)
- **Intelligence Tools** (23)
- **Campaign Tools** (6)
- **Notification Tools** (5)
- **Insights Tools** (2)
- **Scheduled Task Tools** (3)
- **Analytics Tools** (3)
- **Pipeline Tools** (2)
- **Daily Digest Tools** (2)
- **Follow-Up Tools** (3)
- **Comps Tools** (3)
- **Bulk Operations** (2)
- **Activity Timeline** (3)
- **Property Scoring** (4)
- **Watchlist Tools** (5)
- **Heartbeat Tools** (1)
- **Web Scraper Tools** (6)

### Configuration
```json
{
  "mcpServers": {
    "property-management": {
      "command": "python3",
      "args": ["/path/to/ai-realtor/mcp_server/property_mcp.py"]
    }
  }
}
```

---

## 11. Predictive Intelligence

### Overview
AI-powered predictions and recommendations for deal outcomes and next actions.

### Features

#### Predictive Intelligence Engine
- **Closing probability prediction** (0-100%)
- **Confidence levels** for predictions
- **Risk factor identification**
- **Strength analysis**
- **Time-to-close estimates**
- **Batch predictions** across multiple properties

#### Next Action Recommendations
- **AI-recommended actions** with reasoning
- **Priority scoring**
- **Context-aware suggestions**
- **Historical success patterns**

#### Learning System
- **Outcome recording** - Track actual results
- **Pattern discovery** - Agent success patterns
- **Accuracy tracking** - MAE, directional accuracy
- **Performance metrics** - Agent statistics

### API Endpoints
```
POST   /intelligence/predict/{property_id}    - Predict outcome
POST   /intelligence/predict/batch            - Batch predict
POST   /intelligence/recommend/{property_id}  - Recommend next action
POST   /intelligence/outcome                  - Record actual outcome
GET    /intelligence/patterns/{agent_id}      - Get agent patterns
GET    /intelligence/accuracy                 - Get prediction accuracy
```

### Voice Commands
- "Predict the outcome for property 5"
- "What's the closing probability for property 3?"
- "What should I do next with property 5?"
- "Predict outcomes for all my active deals"
- "Record that property 5 closed successfully"
- "What are my success patterns?"

### Database Tables
- `deal_outcomes` - Actual outcome tracking
- `agent_performance_metrics` - Pattern learning
- `prediction_logs` - Prediction history

---

## 12. Market Analytics

### Overview
Market opportunity scanning and shift detection.

### Features

#### Market Opportunity Scanner
- **Pattern matching** - Find deals like your winners
- **Success pattern analysis** - Type/city/price patterns
- **ROI estimation** - Upside calculations
- **Deal recommendations**

#### Market Shift Detection
- **Price drop detection** (>10% changes)
- **Price surge detection** (>10% increases)
- **Market trend analysis**
- **Supply/demand monitoring**

#### Similar Properties
- **Semantic search** - Find similar properties
- **Feature matching** - Beds, baths, price, location
- **Market comparison**

### API Endpoints
```
POST   /intelligence/market/scan                - Scan for opportunities
POST   /intelligence/market/shifts              - Detect market shifts
POST   /intelligence/similar/{property_id}      - Find similar properties
```

### Voice Commands
- "Scan for opportunities matching my patterns"
- "Find deals like my winners in Miami"
- "Any market shifts in Austin?"
- "Show me properties similar to 123 Main St"

---

## 13. Relationship Intelligence

### Overview
AI-powered relationship scoring and contact strategy optimization.

### Features

#### Relationship Health Scoring
- **Health score** (0-100) per contact
- **Trend analysis** - Improving vs declining
- **Engagement metrics**
- **Responsiveness tracking**

#### Best Contact Method Prediction
- **Phone vs email vs text** recommendations
- **Optimal timing** suggestions
- **Response probability**

#### Sentiment Analysis
- **Sentiment trend** over time
- **Interaction quality** scoring
- **Relationship strength** assessment

### API Endpoints
```
GET    /intelligence/relationship/{contact_id}/score  - Score relationship
GET    /intelligence/relationship/{contact_id}/method  - Best contact method
GET    /intelligence/relationship/{contact_id}/sentiment - Sentiment analysis
```

### Voice Commands
- "How's my relationship with John Smith?"
- "Score relationship health for contact 3"
- "Predict the best way to reach Sarah"
- "Should I call or email the buyer?"
- "Analyze sentiment for contact 5"

---

## 14. Negotiation Agent

### Overview
AI-powered offer analysis and counter-offer generation.

### Features

#### Offer Analysis
- **Acceptance probability** (0-100%)
- **Deal metrics comparison**
- **Market data validation**
- **Terms extraction**

#### Counter-Offer Generation
- **AI-generated letters** with justification
- **Price recommendations**:
  - Conservative
  - Moderate
  - Aggressive
- **Supporting arguments** based on data

#### Walkaway Price
- **Maximum allowable offer** calculation
- **Deal metrics analysis**
- **ROI thresholds**

### API Endpoints
```
POST   /intelligence/negotiation/analyze        - Analyze offer
POST   /intelligence/negotiation/counter        - Generate counter-offer
POST   /intelligence/negotiation/offer-price    - Suggest offer price
POST   /intelligence/negotiation/walkaway       - Calculate walkaway
```

### Voice Commands
- "Analyze this $400,000 offer on property 5"
- "What's the acceptance probability?"
- "Generate a counter-offer for $425,000"
- "Suggest an offer price for property 3"
- "What should I offer? Be aggressive"
- "Calculate walkaway price for property 5"

---

## 15. Document Analysis

### Overview
AI-powered document analysis for inspections, appraisals, and contracts.

### Features

#### Inspection Report Analysis
- **Issue extraction** with NLP
- **Severity classification** (critical/major/minor)
- **Repair cost estimation**
- **Summary generation**

#### Appraisal Comparison
- **Appraisal comparison** - Multiple appraisals
- **Discrepancy flagging**
- **Valuation analysis**

#### Contract Term Extraction
- **Automatic term extraction**
- **Key clause identification**
- **Summary generation**

### API Endpoints
```
POST   /intelligence/documents/inspection       - Analyze inspection
POST   /intelligence/documents/appraisal        - Compare appraisals
POST   /intelligence/documents/contract         - Extract contract terms
```

### Voice Commands
- "Analyze this inspection report for property 5"
- "Extract issues from this inspection text"
- "Do these appraisals match?"
- "Extract terms from this contract"
- "What are the key issues in this report?"

---

## 16. Competitive Intelligence

### Overview
Market competition analysis and activity tracking.

### Features

#### Competitor Analysis
- **Top agents** in market
- **Market share** analysis
- **Active competitor** count
- **Performance comparison**

#### Competitive Activity Detection
- **Competition interested** in property
- **Multiple buyers** alerts
- **Bidding war** likelihood

#### Market Saturation
- **Inventory levels**
- **Price trends**
- **Supply/demand ratio**
- **Buyer's vs seller's market** indicator

### API Endpoints
```
POST   /intelligence/competition/analyze        - Analyze competition
POST   /intelligence/competition/detect         - Detect competitive activity
POST   /intelligence/competition/saturation     - Market saturation
```

### Voice Commands
- "Who are the top agents in Miami?"
- "Analyze competition in Austin, Texas"
- "Is there competition for property 5?"
- "Detect competitive activity on 123 Main St"
- "What's the market saturation in Denver?"
- "Is it a buyer's or seller's market?"

---

## 17. Deal Sequencing

### Overview
Multi-property deal orchestration with deadline management.

### Features

#### 1031 Exchange Sequencing
- **45/180-day deadline** tracking
- **Replacement property** identification
- **Timeline management**
- **Compliance monitoring**

#### Portfolio Acquisition
- **Parallel vs sequential** execution
- **Contingency management**
- **Closing coordination**

#### Sell-and-Buy Transactions
- **Contingency tracking**
- **Timeline optimization**
- **Risk assessment**

### API Endpoints
```
POST   /intelligence/sequence/1031              - Sequence 1031 exchange
POST   /intelligence/sequence/portfolio         - Portfolio acquisition
POST   /intelligence/sequence/sell-buy          - Sell-and-buy with contingencies
```

### Voice Commands
- "Set up a 1031 exchange for property 5"
- "Find replacement properties for my 1031 exchange"
- "Sequence buying properties 1, 2, and 3"
- "I need to sell 5 and buy 10 with contingencies"
- "Orchestrate a portfolio acquisition parallel"

---

## 18. Analytics Dashboard

### Overview
Cross-property analytics and portfolio intelligence.

### Metric Categories

#### Pipeline Statistics
- Properties by status
- Properties by type
- Stage distribution
- Conversion rates

#### Portfolio Value
- Total price
- Average price
- Total Zestimate
- Equity calculation

#### Contract Statistics
- Contracts by status
- Unsigned required contracts
- Completion rates
- Average time to sign

#### Activity Statistics
- Actions in last 24h/7d/30d
- Most active properties
- Agent activity rankings

#### Deal Scores
- Average deal score
- Grade distribution (A-F)
- Top 5 deals
- Score trends

#### Enrichment Coverage
- Zillow enrichment percentage
- Skip trace percentage
- Data completeness score

### API Endpoints
```
GET    /analytics/portfolio              - Full portfolio dashboard
GET    /analytics/pipeline               - Pipeline breakdown
GET    /analytics/contracts              - Contract statistics
```

### Voice Commands
- "How's my portfolio doing?"
- "Give me the numbers"
- "How many properties in each status?"
- "How are my contracts looking?"

---

## 19. Scheduled Tasks

### Overview
Persistent reminders, follow-ups, and recurring tasks with background processing.

### Task Types

#### Task Types
- **REMINDER** - One-time reminders
- **RECURRING** - Repeating tasks
- **FOLLOW_UP** - Property follow-ups
- **CONTRACT_CHECK** - Contract deadline checks

#### Features
- **Background task runner** (60-second loop)
- **Auto-notification** when tasks are due
- **Recurring task** auto-creation
- **Property-linked tasks** for context
- **Priority levels**
- **Due date tracking**

#### Task Automation
- **Notification creation** on due date
- **Recurring tasks** spawn next occurrence
- **Task completion** tracking
- **Overdue detection**

### API Endpoints
```
POST   /scheduled-tasks/              - Create task
GET    /scheduled-tasks/              - List tasks (filter by status)
GET    /scheduled-tasks/{id}          - Get specific task
DELETE /scheduled-tasks/{id}/cancel   - Cancel task
GET    /scheduled-tasks/due           - List due tasks
```

### Voice Commands
- "Remind me to follow up on property 5 in 3 days"
- "What tasks are scheduled?"
- "Cancel task 3"
- "Create a recurring task to check property 10"

### Database Tables
- `scheduled_tasks` - Task records
- Task fields: title, description, task_type, status, scheduled_at, repeat_interval_hours

---

## 20. Follow-Up Queue

### Overview
AI-prioritized queue of properties needing attention.

### Scoring Algorithm

#### Weighted Signals
- **Days since last activity** (base score, capped at 300)
- **Deal grade multiplier** (A=2x through F=0.5x)
- **Contract deadline approaching** (+40)
- **Overdue tasks** (+35)
- **Unsigned required contracts** (+30)
- **Skip trace with no outreach** (+25)
- **Missing contacts** (+15)

#### Priority Mapping
- **300+** = Urgent
- **200+** = High
- **100+** = Medium
- **<100** = Low

#### Features
- **Batch signal queries** (no N+1 issues)
- **Snooze** via ScheduledTask (default 72h)
- **Complete action** logging to ConversationHistory
- **Best contact finder** (buyer → seller → owner)

### API Endpoints
```
GET    /follow-ups/queue               - Get ranked queue
POST   /follow-ups/{property_id}/complete - Mark follow-up done
POST   /follow-ups/{property_id}/snooze   - Snooze property
```

### Voice Commands
- "What should I work on next?"
- "Show me my follow-up queue"
- "Mark follow-up done for property 5"
- "Snooze property 5 for 48 hours"

---

## 21. Pipeline Automation

### Overview
Auto-advance properties through pipeline based on activity.

### Auto-Transitions

| From | To | Condition |
|------|-----|-----------|
| NEW_PROPERTY | ENRICHED | Zillow enrichment data available |
| ENRICHED | RESEARCHED | Skip trace completed |
| RESEARCHED | WAITING_FOR_CONTRACTS | At least 1 contract attached |
| WAITING_FOR_CONTRACTS | COMPLETE | All required contracts COMPLETED |

### Safety Features
- **24-hour grace period** after manual status changes
- **Notifications** created for every transition
- **Conversation history** logged for audit
- **Recap auto-regenerated** after status change
- **5-minute interval** background checks

### API Endpoints
```
GET    /pipeline/status               - Recent auto-transitions
POST   /pipeline/check                - Manual trigger for testing
```

### Voice Commands
- "What's the pipeline status?"
- "Show recent auto-transitions"
- "Run pipeline automation now"

---

## 22. Daily Digest

### Overview
AI-generated morning briefing combining insights, analytics, and notifications.

### Digest Contents
- **Portfolio snapshot** (total properties, value, changes)
- **Urgent alerts** from insights
- **Contract status** summary
- **Activity summary** (last 24h)
- **Top recommendations**

### Digest Outputs
1. **Full briefing** (3-5 paragraphs) - For reading
2. **Voice summary** (2-3 sentences) - For text-to-speech

### Scheduling
- **Auto-scheduled** on server startup
- **Runs at 8 AM** (configurable via DAILY_DIGEST_HOUR)
- **Stored as DAILY_DIGEST** notification

### API Endpoints
```
GET    /digest/latest                  - Most recent digest
POST   /digest/generate                - Manual trigger
GET    /digest/history?days=7          - Past digests
```

### Voice Commands
- "What's my daily digest?"
- "Morning summary"
- "Generate a fresh digest now"

---

## 23. Property Scoring

### Overview
Multi-dimensional deal quality scoring across 4 dimensions.

### Scoring Dimensions

#### 1. Market Score (30%)
- Zestimate spread
- Days on market
- Price trend
- School quality
- Tax gap

#### 2. Financial Score (25%)
- Zestimate upside
- Rental yield
- Price per square foot

#### 3. Readiness Score (25%)
- Contract completion %
- Contact coverage
- Skip trace reachability

#### 4. Engagement Score (20%)
- Recent activity (7d)
- Notes count
- Active tasks
- Recent notifications

### Grade Scale
- **A** (80+) - Excellent deal
- **B** (60+) - Good deal
- **C** (40+) - Fair deal
- **D** (20+) - Poor deal
- **F** (<20) - Avoid

### Features
- **Weight re-normalization** when data missing
- **Bulk scoring** for all properties
- **Top properties** ranking
- **Score breakdown** per dimension

### API Endpoints
```
POST   /scoring/property/{property_id}    - Score single property
POST   /scoring/bulk                      - Score multiple properties
GET    /scoring/property/{property_id}    - Get stored score
GET    /scoring/top?limit=10              - Get top properties
```

### Voice Commands
- "Score property 5"
- "Rate this deal"
- "How good is property 3?"
- "Grade this property"
- "Score all my properties"
- "What are my best deals?"
- "Show me A-grade deals"
- "Show me the score breakdown for property 5"

---

## 24. Market Watchlists

### Overview
Saved-search alerts that fire when new matching properties are added.

### Watchlist Criteria (AND Logic)
- `city` - Case-insensitive partial match
- `state` - Case-insensitive exact match
- `property_type` - Exact match
- `min_price` / `max_price` - Price range
- `min_bedrooms` / `min_bathrooms` - Minimum rooms
- `min_sqft` - Minimum square footage

### Features
- **Auto-firing** on property creation
- **HIGH priority** notifications
- **Watchlist metadata** included in alert
- **Toggle pause/resume**
- **Multiple watchlists** per agent

### API Endpoints
```
POST   /watchlists/                     - Create watchlist
GET    /watchlists/                     - List watchlists
GET    /watchlists/{id}                 - Get specific watchlist
PUT    /watchlists/{id}                 - Update watchlist
DELETE /watchlists/{id}                 - Delete watchlist
POST   /watchlists/{id}/toggle          - Pause/resume watchlist
POST   /watchlists/check/{property_id}  - Manual check
```

### Voice Commands
- "Watch for Miami condos under 500k"
- "Set up alerts for Brooklyn 3-bedrooms"
- "Alert me when houses under 300k in Austin come up"
- "Show me my watchlists"
- "What am I watching?"
- "Pause watchlist 1"
- "Delete watchlist 3"
- "Does property 5 match any watchlists?"

### Database Tables
- `market_watchlists` - Watchlist definitions
- `watchlist_matches` - Match history

---

## 25. Bulk Operations

### Overview
Execute operations across multiple properties at once.

### Supported Operations

| Operation | Description | Skip Logic |
|-----------|-------------|------------|
| `enrich` | Zillow enrichment | Skip if already enriched (unless force=true) |
| `skip_trace` | Owner discovery | Skip if already traced (unless force=true) |
| `attach_contracts` | Auto-attach templates | Always run |
| `generate_recaps` | AI recaps | Always run |
| `update_status` | Change status | Skip if already target status |
| `check_compliance` | Compliance check | Always run |

### Features
- **Property selection** via explicit IDs
- **Dynamic filtering** (city, status, type, price, rooms)
- **Union** of both methods (max 50 properties)
- **Per-property error** isolation
- **Individual commits** per property
- **Voice summary** of results

### API Endpoints
```
POST   /bulk/execute                   - Execute bulk operation
GET    /bulk/operations                - List available operations
```

### Voice Commands
- "Enrich all Miami properties"
- "Skip trace properties 1 through 5"
- "Generate recaps for all available properties"
- "What bulk operations are available?"
- "Update status to complete for all enriched properties"

---

## 26. Activity Timeline

### Overview
Unified chronological event feed from 7 data sources.

### Data Sources
1. **ConversationHistory** - MCP tool calls
2. **Notification** - System alerts
3. **PropertyNote** - Freeform notes
4. **ScheduledTask** - Reminders, follow-ups
5. **Contract** - Lifecycle events
6. **ZillowEnrichment** - Enrichment completions
7. **SkipTrace** - Skip trace completions

### Features
- **Per-property** AND portfolio-wide views
- **Filter** by event types, date range, text search
- **Multiple events** per contract (created, sent, completed)
- **Pagination** with offset/limit
- **Voice summaries** with type counts

### API Endpoints
```
GET    /activity-timeline/                        - Full timeline
GET    /activity-timeline/property/{property_id}  - Property timeline
GET    /activity-timeline/recent?hours=24         - Last N hours
```

### Voice Commands
- "Show me the timeline"
- "What happened today?"
- "What's the activity on property 5?"
- "Show me everything on property 3"
- "What's new?"

---

## 27. Property Heartbeat

### Overview
At-a-glance pipeline stage, checklist, and health status.

### Heartbeat Components

#### Pipeline Stage
Which of 5 stages property is in (with progress index 0-4)

#### Checklist
- [ ] Property enriched
- [ ] Owner discovered (skip trace)
- [ ] Contracts attached
- [ ] Contracts completed

#### Health Status
- **healthy** - Progressing normally
- **stale** - Stuck too long
- **blocked** - Can't advance

#### Next Action
What to do next to advance the pipeline

#### Voice Summary
1-2 sentence summary for text-to-speech

### Per-Stage Stale Thresholds
| Stage | Threshold |
|-------|-----------|
| New Property | 3 days |
| Enriched | 5 days |
| Researched | 7 days |
| Waiting for Contracts | 10 days |
| Complete | never |

### Auto-Inclusion
- Included in all property responses by default
- Opt-out with `?include_heartbeat=false`
- Batch-optimized for list endpoints

### API Endpoints
```
GET    /properties/{id}/heartbeat      - Dedicated heartbeat endpoint
GET    /properties/{id}                - Includes heartbeat by default
GET    /properties/                    - Includes heartbeat for all
```

### Voice Commands
- "What's the heartbeat on property 5?"
- "How is property 3 doing?"
- "Is property 5 stuck?"
- "Check the pulse on the Hillsborough property"

---

## 28. Web Scraper

### Overview
Automated property data extraction from any website.

### Scraper Types

#### Specialized Scrapers
- **Zillow** - Optimized selectors
- **Redfin** - Redfin-specific fields
- **Realtor.com** - Realtor.com format

#### Generic AI Scraper
- **Claude Sonnet 4** powered
- **Any website** support
- **Smart field extraction**

### Scraped Data
- Address, city, state, ZIP
- Price, bedrooms, bathrooms, square footage
- Year built, lot size, property type
- Property description
- Photo URLs

### Features
- **Concurrent scraping** with rate limiting
- **Duplicate detection** before creation
- **Auto-enrichment** option after scraping
- **Batch import** from search results
- **Error handling** and retries

### API Endpoints
```
POST   /scrape/url                    - Scrape URL and preview
POST   /scrape/multiple               - Scrape multiple URLs
POST   /scrape/scrape-and-create      - Scrape and create property
POST   /scrape/zillow-listing         - Zillow URL convenience
POST   /scrape/redfin-listing         - Redfin URL convenience
POST   /scrape/realtor-listing        - Realtor.com URL convenience
POST   /scrape/zillow-search          - Scrape Zillow search results
POST   /scrape/scrape-and-enrich-batch - Bulk import with enrichment
```

### Voice Commands
- "Scrape this Zillow listing URL"
- "What data can we extract from this URL?"
- "Add this property from the URL"
- "Create property from this Redfin link"
- "Import these 10 Zillow listings and enrich them all"
- "Show me properties from this Zillow search page"
- "Batch import these URLs into my portfolio"

---

## 29. Deal Calculator

### Overview
Investment analysis and ROI calculations.

### Calculations

#### Deal Metrics
- **ROI** (Return on Investment)
- **Cash Flow** (monthly/annual)
- **Cap Rate** (Capitalization Rate)
- **Cash on Cash Return**
- **Total Investment**
- **Net Operating Income**
- **Break-Even Ratio**

#### What-If Scenarios
- Different purchase prices
- Varying renovation costs
- Rental income changes
- Expense adjustments

#### Deal Types
- Fix and flip
- Rental property
- Multi-family
- Commercial

### Features
- **Scenario modeling**
- **Strategy comparison**
- **Deal type configuration**
- **Custom parameters**

### API Endpoints
```
POST   /deals/calculate                - Calculate deal metrics
POST   /deals/mao                      - Maximum allowable offer
POST   /deals/what-if                  - Scenario modeling
POST   /deals/compare                  - Strategy comparison
POST   /deals/types/preview            - Preview deal type
POST   /deals/types                    - Set deal type
GET    /deals/status/{property_id}     - Get deal status
```

### Voice Commands
- "Calculate the deal on property 5"
- "What's the MAO for property 5?"
- "What if I buy it for $400k?"
- "Compare flip vs rental strategy"
- "Preview the fix-and-flip configuration"

---

## 30. Offer Management

### Overview
Complete offer tracking and negotiation workflow.

### Offer Features

#### Offer Creation
- **Property linking**
- **Buyer information**
- **Offer amount**
- **Contingencies**
- **Expiration date**
- **Terms and conditions**

#### Offer Actions
- **Create** - New offer
- **Accept** - Accept offer
- **Reject** - Reject offer
- **Counter** - Make counter-offer
- **Withdraw** - Withdraw offer

#### Offer Letters
- **AI-generated** offer letters
- **Professional formatting**
- **Customizable templates**
- **PDF export**

### Offer Statuses
- PENDING
- ACCEPTED
- REJECTED
- COUNTERED
- WITHDRAWN
- EXPIRED

### API Endpoints
```
POST   /offers/                       - Create offer
GET    /offers/                       - List all offers
GET    /offers/{id}                   - Get offer details
POST   /offers/{id}/accept            - Accept offer
POST   /offers/{id}/reject            - Reject offer
POST   /offers/{id}/counter           - Counter offer
POST   /offers/{id}/withdraw          - Withdraw offer
POST   /offers/{id}/letter            - Generate offer letter
```

### Voice Commands
- "Create an offer for $800,000 on property 5"
- "Accept the offer on property 3"
- "Reject offer 7"
- "Counter with $750,000"
- "Generate an offer letter"
- "Withdraw my offer"

### Database Tables
- `offers` - Offer records
- `offer_contingencies` - Contingency tracking

---

## 31. Research & Semantic Search

### Overview
AI-powered property research and semantic search.

### Research Features

#### Deep Property Research
- **Agentic research** - Autonomous investigation
- **Compiling data** from multiple sources
- **Background processing**
- **Research dossiers**

#### Semantic Search
- **Vector embeddings** - Semantic understanding
- **Natural language** queries
- **Similar property** finding
- **Concept matching**

#### Research Database
- **Past research** storage
- **Searchable** research history
- **Compiling comps** and sales data

### API Endpoints
```
POST   /research/property/{id}         - Research property
POST   /research/property/{id}/async   - Background research
GET    /research/status/{request_id}   - Check research status
GET    /research/dossier/{property_id} - Get research dossier
POST   /research/search                - Search past research
POST   /search/semantic                - Semantic search
POST   /search/similar/{property_id}   - Find similar properties
```

### Voice Commands
- "Research property 5 in depth"
- "Find properties similar to property 5"
- "Search for properties with pools in Miami"
- "What did we find about property 3?"

### Database Tables
- `property_research` - Research results
- `comp_sales` - Comparable sales
- `comp_rentals` - Rental comps

---

## 32. Property Notes

### Overview
Freeform notes attached to properties with source tracking.

### Note Sources
- **voice** - Voice commands
- **manual** - Manual entry
- **ai** - AI-generated
- **phone_call** - From call transcriptions
- **system** - System-generated

### Features
- **Full CRUD** operations
- **Source tracking**
- **Timestamped** entries
- **Rich text** support
- **AI recap** integration
- **Auto-recap** trigger on new notes

### API Endpoints
```
POST   /property-notes/                - Create note
GET    /property-notes/?property_id=5  - List notes for property
GET    /property-notes/{id}            - Get specific note
PUT    /property-notes/{id}            - Update note
DELETE /property-notes/{id}            - Delete note
```

### Voice Commands
- "Note that property 5 has a new fence installed"
- "Add a note: Seller motivated"
- "Show me notes for property 5"
- "Delete note 3"

### Database Tables
- `property_notes` - Note records
- Note fields: property_id, content, source, created_at

---

## 33. Conversation History

### Overview
Per-property audit trail of all actions and decisions.

### Tracked Actions
All MCP tool calls with `property_id` are automatically logged:
- Enrichments
- Skip traces
- Notes
- Contracts
- Phone calls
- Contacts
- Status changes
- And 100+ more actions

### Logged Data
- **Tool name** - Which action was taken
- **Input summary** - What was requested
- **Output summary** - What happened
- **Duration** - How long it took
- **Success/failure** - Result status
- **Timestamp** - When it happened

### Features
- **Zero configuration** - Automatic logging
- **Per-property** audit trail
- **Session history** tracking
- **Conversation context** for AI

### API Endpoints
```
POST   /context/history/log            - Log conversation entry
GET    /context/history                - Get session history
GET    /context/history/property/{id}  - Get property timeline
DELETE /context/history                - Clear history
```

### Voice Commands
- "What have we done on property 5?"
- "Get the conversation history"
- "What did we discuss?"
- "Clear the conversation history"
- "Start fresh"

### Database Tables
- `conversation_history` - Audit trail
- Fields: property_id, tool_name, input_summary, output_summary, duration, success, timestamp

---

## 34. Workflow Templates

### Overview
Pre-built multi-step workflows for common operations.

### Available Workflows

#### 1. New Lead Setup
**Steps:** Enrich → Skip trace → Attach contracts → Generate recap
**Use:** New properties entering pipeline

#### 2. Deal Closing
**Steps:** Check readiness → Final contracts → Recap
**Use:** Properties near completion

#### 3. Property Enrichment
**Steps:** Zillow data → Recap generation
**Use:** Adding data to properties

#### 4. Skip Trace & Outreach
**Steps:** Skip trace → Cold call owner
**Use:** Off-market lead generation

#### 5. AI Contract Setup
**Steps:** AI suggest → Apply suggestions → Check readiness
**Use:** Contract setup automation

### Features
- **Pre-configured** action sequences
- **One-click** execution
- **Progress tracking**
- **Error handling**

### API Endpoints
```
GET    /workflows/                     - List workflows
POST   /workflows/{template}/execute   - Execute workflow
```

### Voice Commands
- "What workflows are available?"
- "Run the new lead workflow on property 5"
- "Execute deal closing workflow for property 3"

---

## 35. Voice Campaigns

### Overview
Automated bulk outreach phone call campaigns.

### Campaign Features

#### Campaign Management
- **Create** campaigns
- **Start/pause** campaigns
- **Track** progress
- **View** statistics

#### Target Management
- **Add properties** to campaigns
- **Add contacts** to campaigns
- **Filter** by criteria
- **Bulk import** targets

#### Campaign Types
- **Cold calling** - Skip trace outreach
- **Follow-ups** - Past contacts
- **Announcements** - Property updates
- **Deadline reminders** - Contract urgencies

### API Endpoints
```
POST   /campaigns/create              - Create campaign
POST   /campaigns/{id}/start          - Start campaign
POST   /campaigns/{id}/pause          - Pause campaign
GET    /campaigns/{id}/status         - Get campaign status
GET    /campaigns/                    - List campaigns
POST   /campaigns/{id}/targets        - Add targets
```

### Voice Commands
- "Create a campaign for cold calling owners"
- "Start campaign 3"
- "Pause campaign 3"
- "How is campaign 3 doing?"
- "Show me all campaigns"
- "Add properties 5-10 to campaign 3"

### Database Tables
- `voice_campaigns` - Campaign definitions
- `campaign_targets` - Target properties/contacts
- `campaign_calls` - Call history

---

## 36. Proactive Notifications

### Overview
System alerts and updates pushed to agents.

### Notification Types

#### System Notifications
- **Task completed** - Scheduled task done
- **Contract signed** - DocuSeal webhook
- **Pipeline advanced** - Status changed
- **Property enriched** - Zillow data added
- **Daily digest** - Morning briefing

#### Alert Priorities
- **URGENT** - Immediate attention needed
- **HIGH** - Important but not urgent
- **MEDIUM** - Standard priority
- **LOW** - Informational

### Features
- **Push notifications** to agents
- **Priority filtering**
- **Read/unread** tracking
- **Acknowledge** functionality
- **Polling** for updates

### API Endpoints
```
POST   /notifications/                - Send notification
GET    /notifications/                - List notifications
POST   /notifications/{id}/acknowledge - Mark as read
GET    /notifications/summary         - Get summary
POST   /notifications/poll            - Check for new
```

### Voice Commands
- "Any notifications?"
- "Show me alerts"
- "Acknowledge notification 5"
- "Get notification summary"
- "Poll for updates"

### Database Tables
- `notifications` - Alert records
- Fields: agent_id, type, priority, title, message, read_at, created_at

---

## 37. Real-Time Activity Feed

### Overview
Live event tracking via WebSocket.

### Tracked Events
All events tracked in real-time:
- Property CRUD operations
- Enrichments
- Skip traces
- Contracts
- Phone calls
- MCP tool executions
- Notifications

### Features
- **WebSocket** connection
- **Live updates** as they happen
- **Event filtering**
- **Multi-client** support
- **Reconnection** handling

### WebSocket Endpoint
```
ws://localhost:8000/ws
```

### Display Commands
```
POST /display/command
```

### Implementation
- **FastAPI WebSocket** support
- **Background** event broadcasting
- **JSON** event format

---

## 38. Customer Portal

### Overview
Client-facing portal for document sharing and deal tracking.

### Portal Features

#### Authentication
- **JWT tokens** for secure access
- **Per-property** access control
- **Role-based** permissions
- **Activity tracking**

#### Access Levels
- **view** - View property details
- **sign** - Sign contracts
- **full** - Full access

#### Client Features
- **View properties** they're involved with
- **Sign contracts** via DocuSeal
- **View documents**
- **Track progress**
- **Activity history**

### API Endpoints
```
POST   /portal/auth/login             - Client login
POST   /portal/auth/refresh           - Refresh token
GET    /portal/properties             - List accessible properties
GET    /portal/properties/{id}        - View property details
GET    /portal/contracts              - View contracts
POST   /portal/contracts/{id}/sign    - Sign contract
GET    /portal/activity               - View activity
```

### Database Tables
- `portal_users` - Client accounts
- `property_access` - Access control
- `portal_activity` - Client actions

---

## 39. Compliance Engine

### Overview
AI-powered real estate compliance checking.

### Compliance Categories

#### Federal Regulations
- **RESPA** (Real Estate Settlement Procedures Act)
- **TILA** (Truth in Lending Act)
- **Fair Housing Act**
- **ECOA** (Equal Credit Opportunity Act)

#### State Requirements
- **Disclosure laws** per state
- **Purchase agreement** rules
- **Title insurance** requirements
- **Escrow** regulations

#### Local Ordinances
- **City-specific** disclosures
- **Zoning** requirements
- **Inspection** mandates
- **Transfer taxes**

### Features
- **AI analysis** via Claude
- **Requirement checking** by location
- **Issue identification**
- **Recommendations** for compliance
- **Audit trail**

### API Endpoints
```
POST   /compliance/check               - Run compliance check
GET    /compliance/requirements        - Get requirements for state/type
POST   /compliance/report              - Generate compliance report
```

### Voice Commands
- "Check compliance for property 5"
- "What are the requirements for California?"
- "Run a compliance check on this contract"
- "Generate a compliance report"

### Database Tables
- `compliance_checks` - Check results
- `compliance_requirements` - Rule database

---

## 40. Security Features

### Overview
Enterprise-grade security for data protection.

### Security Measures

#### Authentication & Authorization
- **API key authentication** for agents
- **JWT tokens** for portal users
- **Role-based access control** (RBAC)
- **Per-property permissions**

#### Webhook Security
- **HMAC-SHA256 signature verification** (Telnyx, DocuSeal)
- **Constant-time comparison** (prevents timing attacks)
- **Signature validation** on all webhooks
- **Secret management** via environment variables

#### Data Protection
- **HTTPS only** in production
- **CORS configuration** for cross-origin requests
- **SQL injection prevention** (SQLAlchemy ORM)
- **XSS protection** (input sanitization)

#### Token Management
- **Automatic token refresh** (Google Calendar)
- **5-minute buffer** before expiry
- **Refresh token rotation**
- **Secure token storage**

#### Rate Limiting
- **API rate limits** per endpoint
- **IP-based throttling**
- **DDoS protection**

#### Audit Trail
- **Conversation history** - All actions logged
- **Property audit trail** - Per-property tracking
- **Access logs** - Portal user activity
- **Compliance tracking**

### Recent Security Fixes (Feb 2026)
✅ **Webhook signature verification** - HMAC-SHA256 for Telnyx
✅ **Automatic token refresh** - Google Calendar tokens
✅ **Database indexes** - PhoneCall query performance
✅ **Portal user model fixes** - Naming conflicts resolved

### Environment Variables (Security)
```bash
# Authentication
API_KEY_HASH=your-hash-here
PORTAL_JWT_SECRET=your-jwt-secret

# Webhook Secrets
TELNYX_WEBHOOK_SECRET=your-webhook-secret
DOCUSEAL_WEBHOOK_SECRET=your-docuseal-secret

# Database
DATABASE_URL=postgresql://user:pass@host/db

# CORS
CORS_ORIGINS=https://your-domain.com
```

---

## Summary Statistics

### Platform Metrics
- **40 Major Feature Categories**
- **135 Voice Commands (MCP)**
- **200+ API Endpoints**
- **50+ Database Tables**
- **39 Marketing Hub Endpoints**
- **29 High-Level Feature Areas**

### Data Models
- **Property Management** - 2 tables
- **Contracts** - 4 tables
- **Phone Calls** - 1 table + 4 indexes
- **Marketing** - 12 tables
- **Intelligence** - 3 tables
- **Calendar** - 3 tables
- **And 30+ more...**

### Integration Points
- **Zillow API** - Property enrichment
- **Google Places API** - Address autocomplete
- **DocuSeal API** - E-signatures
- **VAPI API** - Phone calls
- **Telnyx API** - Telephony
- **ElevenLabs API** - Voice synthesis
- **Google Calendar API** - Calendar sync
- **Exa API** - Research
- **Anthropic Claude AI** - Intelligence
- **Facebook Ads API** - Marketing
- **Postiz API** - Social media

---

## Getting Started

### 1. Local Development
```bash
# Clone repository
git clone https://github.com/Thedurancode/ai-realtor.git
cd ai-realtor

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb ai_realtor
alembic upgrade head

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start server
uvicorn app.main:app --reload
```

### 2. Docker Deployment
```bash
# Build and start
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

### 3. Fly.io Production
```bash
# Deploy
fly deploy

# View logs
fly logs

# SSH into server
fly ssh console

# Database access
fly postgres connect -a ai-realtor-db
```

---

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## Support & Documentation

- **GitHub**: https://github.com/Thedurancode/ai-realtor
- **Issues**: https://github.com/Thedurancode/ai-realtor/issues
- **Documentation**: https://github.com/Thedurancode/ai-realtor/blob/main/CLAUDE.md

---

## License

Proprietary - All rights reserved

---

**Generated with [Claude Code](https://claude.ai/code)**
**via [Happy](https://happy.engineering)**

**Last Updated:** February 26, 2026
