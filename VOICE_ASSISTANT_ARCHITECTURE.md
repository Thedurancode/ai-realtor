# 🤖 AI Voice Assistant - Architecture & Data Flow

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           CALLER                                    │
│                      (Potential Buyer)                              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ Calls
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          VAPI Platform                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  • Receives inbound call                                    │  │
│  │  • Handles telephony (audio recording, routing)            │  │
│  │  • Sends webhook to AI Realtor API                         │  │
│  │  • Streams real-time transcription                         │  │
│  │  • Executes AI function calls                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ POST /voice-assistant/incoming
                             │   (with call details)
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AI Realtor API                                  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Voice Assistant Service                   │  │
│  │  ─────────────────────────────────────────────────────────  │  │
│  │                                                               │  │
│  │  1. Create phone_call record (status: in_progress)          │  │
│  │  2. Configure AI response (greeting, prompt, voice)         │  │
│  │  3. Return config to VAPI                                   │  │
│  │  4. Process real-time callbacks:                            │  │
│  │     • transcript - Update transcription field               │  │
│  │     • function_call - Execute AI action                     │  │
│  │     • ended - Mark complete, generate summary               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  AI Function Calls:                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐   │
│  │ lookup_property  │  │ schedule_viewing │  │ create_offer   │   │
│  │                  │  │                  │  │                │   │
│  │ • Get property   │  │ • Ask name/date  │  │ • Get amount   │   │
│  │ • Get heartbeat  │  │ • Create task    │  │ • Create lead  │   │
│  │ • Return details │  │ • Confirm        │  │ • Alert agent  │   │
│  └──────────────────┘  └──────────────────┘  └────────────────┘   │
│                                                                      │
│  Database Updates:                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ phone_calls  │  │ ScheduledTask│  │    Offer     │             │
│  │              │  │              │  │              │             │
│  │ • status     │  │ • viewing    │  │ • lead       │             │
│  │ • transcript │  │ • follow-up  │  │ • offer      │             │
│  │ • summary    │  │              │  │              │             │
│  │ • outcome    │  │              │  │              │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Real-Time Call Flow

```
┌──────────┐
│  CALLER  │ "Tell me about 123 Main St"
└────┬─────┘
     │
     │ 1. CALL START
     ▼
┌─────────────┐
│    VAPI     │ Receives call
└────┬────────┘
     │
     │ 2. WEBHOOK: POST /voice-assistant/incoming
     │    {phone_number, vapi_call_id, vapi_phone_id}
     ▼
┌─────────────────────┐
│  AI Realtor API     │
│                     │ • Create phone_call record
│                     │ • Return AI config:
┌───────────────────┐ │   {greeting, prompt, voice_id}
│ Voice Assistant   │ │
│    Service        │ │ 3. AI GREETS
│                   │ │    "Thanks for calling Emprezario.
│ • handle_incoming │ │     How can I help?"
│ • build_response  │ │
└───────────────────┘ │
└─────────┬───────────┘
          │
          │ 4. CALLER SPEAKS
          │    "Tell me about 123 Main St"
          ▼
┌─────────────┐
│    VAPI     │ Detects intent: property_inquiry
└────┬────────┘
     │
     │ 5. CALLBACK: POST /voice-assistant/callback/{id}
     │    {event: "function_call", name: "lookup_property"}
     ▼
┌─────────────────────┐
│  AI Realtor API     │
│                     │ • Lookup property by address
┌───────────────────┐ │ • Get heartbeat status
│ Voice Assistant   │ │ • Return property details
│    Service        │ │
│                   │ │ 6. AI RESPONDS
│ _handle_function  │ │    "123 Main St is $850,000,
│ _lookup_property  │ │     3 bed, 2 bath, 1,800 sqft.
└───────────────────┘ │     Currently researched and healthy.
└─────────┬───────────┘      Want to schedule a viewing?"
          │
          │ 7. CALLER SPEAKS
          │    "Yes, tomorrow 2pm. I'm John, 555-1234"
          ▼
┌─────────────┐
│    VAPI     │ Detects intent: schedule_viewing
└────┬────────┘
     │
     │ 8. CALLBACK: POST /voice-assistant/callback/{id}
     │    {event: "function_call", name: "schedule_viewing"}
     ▼
┌─────────────────────┐
│  AI Realtor API     │
│                     │ • Create ScheduledTask
┌───────────────────┐ │ • Update phone_call outcome
│ Voice Assistant   │ │ • Confirm to caller
│    Service        │ │
│                   │ │ 9. AI CONFIRMS
│ _schedule_viewing │ │    "Great! Viewing scheduled for
└───────────────────┘ │     tomorrow at 2pm. Agent will call
└─────────┬───────────┘      555-1234 to confirm."
          │
          │ 10. CALLER HANGS UP
          ▼
┌─────────────┐
│    VAPI     │ Call duration: 127 seconds
└────┬────────┘
     │
     │ 11. CALLBACK: POST /voice-assistant/callback/{id}
     │     {event: "ended", status: "completed", duration: 127}
     ▼
┌─────────────────────┐
│  AI Realtor API     │
│                     │ • Update phone_call status
┌───────────────────┐ │ • Generate AI summary
│ Voice Assistant   │ │ • Transcribe full recording
│    Service        │ │
│                   │ │ 12. CALL LOGGED
│ _generate_summary  │ │    {
│ _handle_update    │ │      status: "completed",
└───────────────────┘ │      outcome: "viewing_scheduled",
└─────────┬───────────┘      caller: "John, 555-1234",
          │                   duration: 127s,
          │                   summary: "Property inquiry...
                               Viewing scheduled..."
                     }
```

---

## 🗄️ Database Schema

```
┌─────────────────────────────────────────────────────────────────┐
│                         phone_numbers                           │
├─────────────────────────────────────────────────────────────────┤
│ id                  │ PK                                       │
│ agent_id            │ FK → agents.id                           │
│ phone_number        │ UNIQUE (E.164: +14155551234)             │
│ friendly_name       │ "Main Line", "Listings Hotline"          │
│ provider            │ "vapi", "twilio", "plivo"                │
│ provider_phone_id   │ VAPI phone UUID                           │
│ is_active           │ boolean                                  │
│ is_primary          │ boolean                                  │
│ greeting_message    │ "Thanks for calling..."                  │
│ ai_voice_id         │ ElevenLabs/VAPI voice                    │
│ ai_assistant_id     │ VAPI assistant UUID                       │
│ forward_to_number   │ Forward calls to...                      │
│ business_hours_start│ "09:00"                                 │
│ business_hours_end  │ "18:00"                                 │
│ total_calls         │ Count for stats                          │
│ total_minutes       │ Duration tracking                        │
│ total_cost          │ Cost in cents                            │
└─────────────────────────────────────────────────────────────────┘
                            │ 1:N
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         phone_calls                             │
├─────────────────────────────────────────────────────────────────┤
│ id                  │ PK                                       │
│ agent_id            │ FK → agents.id                           │
│ property_id         │ FK → properties.id (optional)            │
│ direction           │ "inbound" or "outbound"                  │
│ phone_number        │ Caller ID (inbound) or dest (outbound)   │
│ vapi_call_id        │ UNIQUE VAPI call UUID                    │
│ status              │ initiated, in_progress, completed,       │
│                     │ failed, no_answer, busy                  │
│ duration_seconds    │ Call length                              │
│ cost                │ Call cost USD                            │
│ transcription       │ Full call transcript (TEXT)              │
│ summary             │ AI-generated summary (TEXT)              │
│ intent              │ property_inquiry, schedule_viewing,      │
│                     │ make_offer, speak_agent, general         │
│ confidence_score    │ AI confidence 0-1                        │
│ outcome             │ information_provided, viewing_scheduled, │
│                     │ offer_created, message_taken             │
│ caller_name         │ If provided                             │
│ caller_phone        │ Verified caller number                   │
│ message             │ Message left for agent                  │
│ follow_up_created   │ Was task created?                        │
│ recording_url       │ VAPI recording URL                       │
│ created_at          │ Call timestamp                           │
│ started_at          │ Call start time                          │
│ ended_at            │ Call end time                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints Map

```
PHONE NUMBERS (6 endpoints)
│
├─ POST   /voice-assistant/phone-numbers
│   └─ Create new phone number
│
├─ GET    /voice-assistant/phone-numbers
│   └─ List all numbers
│
├─ GET    /voice-assistant/phone-numbers/{id}
│   └─ Get number details
│
├─ PUT    /voice-assistant/phone-numbers/{id}
│   └─ Update number config
│
├─ DELETE /voice-assistant/phone-numbers/{id}
│   └─ Delete number
│
└─ POST   /voice-assistant/phone-numbers/{id}/set-primary
    └─ Set as primary number

CALL HANDLING (2 endpoints)
│
├─ POST   /voice-assistant/incoming
│   └─ Handle inbound call (VAPI webhook)
│
└─ POST   /voice-assistant/callback/{call_id}
    └─ Call progress events (VAPI callback)

CALL HISTORY & ANALYTICS (8 endpoints)
│
├─ GET    /voice-assistant/phone-calls
│   └─ List all calls (filterable)
│
├─ GET    /voice-assistant/phone-calls/{id}
│   └─ Get specific call
│
├─ GET    /voice-assistant/phone-calls/recording/{id}
│   └─ Get recording URL
│
├─ GET    /voice-assistant/phone-calls/transcription/{id}
│   └─ Get transcript & summary
│
├─ GET    /voice-assistant/phone-calls/analytics/overview
│   └─ Analytics dashboard
│
└─ GET    /voice-assistant/phone-calls/analytics/by-property
    └─ Property-level stats
```

---

## 🎯 AI Intent Detection

```
CALLER SAYS                    │ AI INTENT              │ AI ACTION
────────────────────────────────┼────────────────────────┼────────────────────────────────────
"Tell me about [property]"      │ property_inquiry       │ lookup_property()
"What's the price?"            │                        │ → Get details + heartbeat
"How many bedrooms?"           │                        │ → Read info to caller
────────────────────────────────┼────────────────────────┼────────────────────────────────────
"I want to see this property"   │ schedule_viewing      │ schedule_viewing()
"Can I visit tomorrow?"         │                        │ → Ask name, phone, date
"Schedule a showing"            │                        │ → Create ScheduledTask
────────────────────────────────┼────────────────────────┼────────────────────────────────────
"I want to make an offer"       │ make_offer             │ create_offer()
"I'll offer $400k"             │                        │ → Ask amount, contingencies
"What's the offer process?"     │                        │ → Create Offer lead
────────────────────────────────┼────────────────────────┼────────────────────────────────────
"Let me talk to an agent"       │ speak_agent            │ take_message()
"Can I speak to someone?"       │                        │ → Take message
"I need to talk to a person"    │                        │ → Create follow-up task
────────────────────────────────┼────────────────────────┼────────────────────────────────────
"What properties do you have?"  │ general                │ search_properties()
"What areas do you serve?"      │                        │ → Search by city/price/beds
"How do I contact you?"         │                        │ → List matching properties
```

---

## 📊 Analytics Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│                    CALL ANALYTICS OVERVIEW                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📞 TOTAL CALLS              150                           │
│     ├─ Inbound               120 (80%)                     │
│     └─ Outbound               30 (20%)                     │
│                                                              │
│  ✅ COMPLETION RATE          90%                            │
│     ├─ Completed             135                           │
│     └─ Missed                15                            │
│                                                              │
│  ⏱️  TOTAL DURATION          480 minutes                    │
│  💰 TOTAL COST               $45.50                         │
│                                                              │
│  🎯 INTENT BREAKDOWN                                        │
│     ├─ Property inquiry      80 (53%)                      │
│     ├─ Schedule viewing      30 (20%)                      │
│     ├─ Make offer            15 (10%)                      │
│     └─ Speak to agent        25 (17%)                      │
│                                                              │
│  🎉 OUTCOME BREAKDOWN                                        │
│     ├─ Info provided         60 (40%)                      │
│     ├─ Viewing scheduled     25 (17%)                      │
│     ├─ Offer created         10 (7%)                       │
│     └─ Message taken         20 (13%)                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 PROPERTY CALL STATISTICS                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🏠 123 MAIN ST                                              │
│     Total Calls:         45                                  │
│     Inbound:            40                                   │
│     Unique Callers:     28                                   │
│     Viewings Scheduled: 12                                   │
│     Offers Created:      3                                   │
│                                                              │
│  🏠 456 OAK AVENUE                                            │
│     Total Calls:         32                                  │
│     Inbound:            28                                   │
│     Unique Callers:     19                                   │
│     Viewings Scheduled:  8                                   │
│     Offers Created:      1                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Security & Privacy

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. API KEY AUTHENTICATION                                  │
│     └─ All endpoints require X-API-Key header               │
│                                                              │
│  2. WEBHOOK VERIFICATION (Future)                           │
│     └─ HMAC-SHA256 signature from VAPI                      │
│                                                              │
│  3. CALL RECORDING                                          │
│     ├─ All calls recorded by default                        │
│     ├─ Stored securely in database                          │
│     └─ Retained per policy (configurable)                   │
│                                                              │
│  4. TRANSCRIPTION PRIVACY                                   │
│     ├─ Encrypted at rest                                    │
│     ├─ Access controlled by API key                         │
│     └─ Auto-summarized (PII filtered)                       │
│                                                              │
│  5. CALLER DATA                                             │
│     ├─ Phone numbers logged (E.164 format)                  │
│     ├─ Caller consent obtained                              │
│     └─ GDPR/CCPA compliant                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Deployment

```
DEVELOPMENT                          │ PRODUCTION
─────────────────────────────────────┼────────────────────────────
Local: http://localhost:8000         │ Fly.io: https://ai-realtor
                                     │       .fly.dev
─────────────────────────────────────┼────────────────────────────
Ngrok tunnel for VAPI webhook        │ Direct URL for VAPI webhook
─────────────────────────────────────┼────────────────────────────
SQLite database                      │ PostgreSQL on Fly.io
─────────────────────────────────────┼────────────────────────────
Test phone numbers                   │ Production phone numbers
─────────────────────────────────────┼────────────────────────────
No SSL verification (yet)            │ HMAC-SHA256 webhook verify
```

---

## ✅ Integration Checklist

```
□ Database migration run
□ VAPI account created
□ Phone number purchased
□ Assistant configured in VAPI
□ Webhook URL set in VAPI
□ Phone number created in system
□ Test call completed
□ Transcription working
□ Function calls working
│   ├─ lookup_property
│   ├─ schedule_viewing
│   ├─ create_offer
│   ├─ take_message
│   └─ search_properties
□ Tasks being created
□ Analytics dashboard checked
□ MCP tools tested (via Nanobot)
```

---

**Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)**
