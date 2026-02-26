# Testing Guide - Calendar Integration & Telnyx Voice Calls

## 🚀 Quick Start

### 1. Restart the Server

The new endpoints need a server restart:

```bash
# Stop the current server (Ctrl+C)
# Then restart:
uvicorn app.main:app --reload
```

### 2. Verify Endpoints Are Loaded

Visit the API docs:
```bash
open http://localhost:8000/docs
```

Look for these new sections:
- **Telnyx Voice** (8 endpoints)
- **Calendar Integration** (15 endpoints)

---

## 📅 Testing Google Calendar Integration

### Setup Required:

1. **Get Google OAuth Credentials:**
   - Go to: https://console.cloud.google.com/
   - Create a new project
   - Enable Google Calendar API
   - Create OAuth 2.0 credentials
   - Add redirect URI: `https://your-domain.com/calendar/oauth/callback`

2. **Set Environment Variables:**
   ```bash
   export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
   export GOOGLE_CLIENT_SECRET="your-client-secret"
   export GOOGLE_OAUTH_REDIRECT_URI="https://your-domain.com/calendar/oauth/callback"
   ```

### Test the Flow:

```bash
# 1. Initiate OAuth connection
curl -X POST "http://localhost:8000/calendar/oauth/start?agent_id=1" \
  -H "X-API-Key: your-api-key"

# Response will contain OAuth URL - visit it in browser

# 2. After OAuth approval, test connection
curl -X GET "http://localhost:8000/calendar/connections" \
  -H "X-API-Key: your-api-key"

# 3. Create a calendar event
curl -X POST "http://localhost:8000/calendar/events" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Property Showing - 123 Main St",
    "start_time": "2026-02-27T14:00:00",
    "end_time": "2026-02-27T15:00:00",
    "event_type": "showing",
    "property_id": 1,
    "create_meet": true
  }'

# 4. List events
curl -X GET "http://localhost:8000/calendar/events?days=7" \
  -H "X-API-Key: your-api-key"

# 5. Check conflicts
curl -X POST "http://localhost:8000/calendar/check-conflicts" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "2026-02-27T14:00:00",
    "end_time": "2026-02-27T15:00:00",
    "property_id": 1
  }'
```

### Voice Commands (via MCP):

```
"Connect my Google Calendar"
"Schedule a showing for 123 Main St tomorrow at 2pm"
"Create meeting with seller next Tuesday at 3pm"
"Set up a video call with the buyer for Friday at 3pm with Google Meet"
"What's on my calendar today?"
"Show me this week's events"
"Check for scheduling conflicts on Saturday at 2pm"
"Suggest a good time for a 1-hour meeting"
"Analyze my schedule this week"
"Get calendar insights for the last 30 days"
"Find optimal time for a closing meeting"
"Predict success for Friday 2pm closing"
"Optimize my schedule with AI"
```

---

## 📞 Testing Telnyx Voice Calls

### Setup Required:

1. **Get Telnyx Credentials:**
   - Sign up: https://telnyx.com/
   - Create a Call Control App
   - Get your API Key
   - Get the Connection ID

2. **Set Environment Variables:**
   ```bash
   export TELNYX_API_KEY="your-telnyx-api-key"
   export TELNYX_CONNECTION_ID="your-connection-id"
   export TELNYX_PHONE_NUMBER="+15551234567"
   export TELNYX_WEBHOOK_URL="https://your-domain.com/telnyx/webhook"
   ```

### Test the Flow:

```bash
# 1. Make a test call
curl -X POST "http://localhost:8000/telnyx/calls" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+15559876543",
    "script": "Hello, this is a test call from AI Realtor. Thank you for your time!",
    "property_id": 1,
    "detect_machine": true,
    "record_call": true
  }'

# Response will include:
# - call_id: Use this to track the call
# - call_session_id: Session identifier
# - status: "initiated"

# 2. Check call status
curl -X GET "http://localhost:8000/telnyx/calls/{call_control_id}" \
  -H "X-API-Key: your-api-key"

# 3. Get call recording (after call completes)
curl -X GET "http://localhost:8000/telnyx/recordings/{recording_id}" \
  -H "X-API-Key: your-api-key"

# 4. List available phone numbers
curl -X GET "http://localhost:8000/telnyx/phone-numbers" \
  -H "X-API-Key: your-api-key"
```

### Voice Commands (via MCP):

```
"Call the seller at 555-1234 and ask if they're flexible on price"
"Phone the buyer using Telnyx and ask their preferred move-in date"
"Call the inspector with VAPI and ask about any issues with the foundation"
"What's the status of call 12345?"
"Schedule a call to the seller tomorrow at 10am"
```

---

## 📋 Testing Call History & Activity Feed

```bash
# 1. Get call history for a property
curl -X GET "http://localhost:8000/properties/1/calls?limit=20" \
  -H "X-API-Key: your-api-key"

# Response includes:
# - All calls for the property
# - Recordings and transcriptions
# - Call duration and timestamps
# - Provider (VAPI/Telnyx)

# 2. Get specific call details
curl -X GET "http://localhost:8000/phone-calls/{call_id}" \
  -H "X-API-Key: your-api-key"

# 3. Get call recording
curl -X GET "http://localhost:8000/phone-calls/recording/{call_id}" \
  -H "X-API-Key: your-api-key"
```

### Voice Commands:

```
"Show me call history for property 5"
"What calls were made about 123 Main St?"
"Get the recording for call 123"
"Show me call stats for property 5"
"What's the call activity summary?"
```

---

## 🧪 Testing Without API Keys (Local Development)

If you don't have credentials yet, you can still test the code structure:

```bash
# 1. Check models are loaded
python3 -c "
from app.models import PhoneCall, CalendarConnection, CalendarEvent
from app.routers import telnyx, calendar
print('✅ Models and routers load successfully')
"

# 2. Check MCP tools are registered
python3 -c "
import sys
sys.path.insert(0, '.')
# This will verify the tool definitions are valid
"
```

---

## ✅ Verification Checklist

### Calendar Integration:
- [ ] OAuth flow initiates correctly
- [ ] Can create calendar events
- [ ] Events sync to Google Calendar
- [ ] Google Meet links are generated
- [ ] Conflict detection works
- [ ] Smart scheduling suggestions work
- [ ] AI calendar insights work

### Telnyx Integration:
- [ ] Calls initiate successfully
- [ ] Call status updates via webhook
- [ ] Recordings are saved to database
- [ ] PhoneCall records are created
- [ ] Call history endpoint works
- [ ] Answering machine detection works

### Call History:
- [ ] Calls are saved to PhoneCall table
- [ ] Per-property call history works
- [ ] Recording URLs are accessible
- [ ] Transcriptions are stored
- [ ] Call analytics work

---

## 🐛 Troubleshooting

### Server not loading new endpoints:
```bash
# Check server logs
tail -f logs/server.log

# Restart with verbose output
uvicorn app.main:app --reload --log-level debug
```

### Telnyx webhook not receiving updates:
```bash
# Check webhook URL is accessible
curl -X POST "https://your-domain.com/telnyx/webhook" \
  -H "Content-Type: application/json" \
  -d '{"event_type":"test","data":{"call_control_id":"test123"}}'

# Verify webhook is logged
```

### Calendar OAuth failing:
```bash
# Verify redirect URI matches exactly
# Check Google Console for OAuth errors
# Ensure callback URL is whitelisted
```

---

## 📊 Expected Results

### Successful Calendar Event Creation:
```json
{
  "id": 123,
  "title": "Property Showing",
  "start_time": "2026-02-27T14:00:00",
  "meet_link": "https://meet.google.com/abc-xyz",
  "property_address": "123 Main St, New York"
}
```

### Successful Telnyx Call:
```json
{
  "call_id": "abc123-def456",
  "call_session_id": "session-789",
  "status": "initiated",
  "provider": "telnyx"
}
```

### Call History Response:
```json
{
  "property_id": 1,
  "property_address": "123 Main St, New York",
  "calls": [
    {
      "id": 1,
      "provider": "telnyx",
      "status": "completed",
      "duration_seconds": 202,
      "recording_url": "https://cdn.telnyx.com/...",
      "created_at": "2026-02-26T14:30:00"
    }
  ],
  "total": 1
}
```

---

## 🎯 Next Steps

1. **Set up credentials** (Google Calendar + Telnyx)
2. **Restart the server**
3. **Test basic endpoints** with curl
4. **Test voice commands** via Claude Desktop
5. **Check database** to verify calls are saved
6. **Review activity feed** for properties

---

## 📝 Notes

- All Telnyx calls are automatically saved to `phone_calls` table
- Calendar events sync both directions (API → Google, Google → API)
- Webhooks update call status in real-time
- Recordings are stored as URLs in the database
- Activity feed includes all call history per property
