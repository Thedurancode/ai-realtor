# 🤖 AI Voice Assistant - Quick Start

## 🎯 What Is It?

Your AI Realtor platform can now **answer phone calls 24/7** like a human receptionist. It can:
- Tell callers about properties
- Schedule viewings
- Create offer leads
- Take messages
- Answer questions

---

## 🚀 Setup (5 Minutes)

### Step 1: Run Database Migration

```bash
# From your project directory
docker exec ai-realtor alembic upgrade head
```

### Step 2: Get VAPI Account

1. Go to https://vapi.ai
2. Sign up (free trial available)
3. Buy a phone number (~$1/month)
4. Create an assistant
5. Get your:
   - Phone number (e.g., +14155551234)
   - Assistant ID

### Step 3: Configure VAPI Webhook

In VAPI dashboard, set your webhook URL:
```
https://ai-realtor.fly.dev/voice-assistant/incoming
```

Or for local testing:
```
https://your-ngrok-url.com/voice-assistant/incoming
```

### Step 4: Create Phone Number in System

```bash
curl -X POST "https://ai-realtor.fly.dev/voice-assistant/phone-numbers" \
  -H "X-API-Key: nanobot-perm-key-2024" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+14155551234",
    "friendly_name": "Main Line",
    "greeting_message": "Thanks for calling Emprezario Real Estate",
    "is_primary": true,
    "ai_assistant_id": "your-vapi-assistant-id-here"
  }'
```

### Step 5: Test It!

**Call your new number** and try saying:
- "Tell me about property 123 Main St"
- "I want to schedule a viewing"
- "I want to make an offer"
- "Let me talk to an agent"

---

## 📊 Check Call Analytics

```bash
# View recent calls
curl "https://ai-realtor.fly.dev/voice-assistant/phone-calls" \
  -H "X-API-Key: nanobot-perm-key-2024"

# Get analytics overview
curl "https://ai-realtor.fly.dev/voice-assistant/phone-calls/analytics/overview" \
  -H "X-API-Key: nanobot-perm-key-2024"

# See which properties get calls
curl "https://ai-realtor.fly.dev/voice-assistant/phone-calls/analytics/by-property" \
  -H "X-API-Key: nanobot-perm-key-2024"
```

---

## 🎤 Voice Commands (via Nanobot)

In Telegram (@your-bot):
```
"Show me my phone numbers"
"Show call analytics"
"Which properties get the most calls?"
"Get transcript for call 5"
```

---

## 💡 Pro Tips

### Multiple Numbers
Create different numbers for:
- **Main line** - General inquiries
- **Open house hotline** - Event-specific
- **High-end listings** - Luxury properties

### Business Hours
Set up forwarding:
```bash
curl -X PUT "https://ai-realtor.fly.dev/voice-assistant/phone-numbers/1" \
  -H "X-API-Key: nanobot-perm-key-2024" \
  -H "Content-Type: application/json" \
  -d '{
    "forward_to_number": "+19175551234",
    "forward_when": "after_hours",
    "business_hours_start": "09:00",
    "business_hours_end": "18:00"
  }'
```

### Custom Greetings
Change greeting for different numbers:
- "Thanks for calling our luxury division"
- "Open house hotline - we're open Sat-Sun 2-4pm"
- "Investment properties hotline"

---

## 🔥 Sample Call Flow

```
📞 Caller: (Dials number)

🤖 AI: "Thanks for calling Emprezario Real Estate. How can I help?"

📞 Caller: "Tell me about the property on 123 Main St"

🤖 AI: (Looks up property)
      "123 Main St is priced at $850,000 with 3 bedrooms and 2 bathrooms.
       It's 1,800 sqft and currently in the Researched stage.
       Would you like to schedule a viewing?"

📞 Caller: "Yes, tomorrow at 2pm. I'm John at 555-1234"

🤖 AI: (Creates scheduled task)
      "Great! I've scheduled a viewing for tomorrow at 2pm.
       The agent will call you at 555-1234 to confirm."

📞 Caller: "Thanks!"

🤖 AI: "You're welcome. Have a great day!"
```

---

## 📈 What Gets Logged

Every call creates:
- ✅ Call log (who called, when, duration)
- ✅ Full transcription (what was said)
- ✅ AI summary (intent & outcome)
- ✅ Follow-up tasks (if viewing scheduled)
- ✅ Offer leads (if offer made)
- ✅ Message taken (if caller wants agent)

---

## 🎯 Use Cases

### 1. Listing Hotline
Dedicated number for property listings:
- Never miss a lead
- Instant property info
- Capture caller data

### 2. After-Hours Reception
Forward main line to AI after 6pm:
- 24/7 availability
- Takes messages
- Schedules callbacks

### 3. Open House Hotline
Temporary number for open house:
- Pre-qualifies leads
- Schedules viewings
- Answers FAQ

---

## 🆘 Troubleshooting

**Calls not being received?**
- Check VAPI webhook is configured
- Verify phone number is active in system
- Check API logs for errors

**AI not responding correctly?**
- Verify ai_assistant_id is correct
- Check VAPI assistant configuration
- Review call transcript for issues

**Tasks not being created?**
- Check ScheduledTask model exists
- Verify agent_id is set
- Review API response for errors

---

## 📚 Full Documentation

See `VOICE_ASSISTANT_GUIDE.md` for complete documentation including:
- Architecture details
- All API endpoints
- AI prompts
- Analytics dashboard
- Security considerations

---

## ✅ You're Ready!

Your AI Realtor platform now has **24/7 inbound calling** with AI!

**What to do next:**
1. Run migration
2. Get VAPI account
3. Create phone number
4. Test with a call
5. Check analytics

**Estimated setup time:** 5-10 minutes

**Your AI receptionist is ready!** 🤖📞

---

**Questions?**
- Check VOICE_ASSISTANT_GUIDE.md for full docs
- Review API docs at /docs
- Use voice commands in Telegram
