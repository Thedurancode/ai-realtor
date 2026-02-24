# AI Property Recap & VAPI Phone Calls

## Overview

The AI Realtor platform now features **AI-generated property recaps** that automatically summarize property state and **VAPI-powered phone calls** that use this context to make intelligent calls about properties.

## What It Does

### 1. AI Property Recaps
- **Automatically** generates comprehensive property summaries
- Includes property details, contract status, enrichment data, contacts
- Creates both **detailed** and **voice-optimized** versions
- Stores structured context for AI assistants
- Updates whenever property data changes

### 2. VAPI Phone Calls
- Make AI-powered phone calls about properties
- AI assistant has full property context
- Can answer questions conversationally
- Three call types: updates, reminders, celebrations
- Recordings available after calls complete

## Architecture

```
Property Data Changes
       ↓
AI Recap Generated (Claude Sonnet 4)
       ↓
Stored in PropertyRecap Model
       ↓
Used for VAPI Phone Calls
       ↓
AI Assistant with Context
```

## API Endpoints

### Property Recap Endpoints

```bash
# Generate or update property recap
POST /property-recap/property/{property_id}/generate?trigger=manual

Response:
{
  "id": 1,
  "property_id": 1,
  "property_address": "123 Broadway, New York, NY",
  "recap_text": "Comprehensive 3-4 paragraph summary...",
  "voice_summary": "Concise 2-3 sentence summary for TTS...",
  "recap_context": {
    "property": {...},
    "contracts": [...],
    "readiness": {...},
    "ai_summary": {
      "key_facts": ["3 bed, 2 bath condo", "Ready to close"],
      "concerns": ["Missing lead paint disclosure"],
      "next_steps": ["Schedule final walkthrough"]
    }
  },
  "version": 1,
  "last_trigger": "manual"
}

# Get existing recap
GET /property-recap/property/{property_id}
```

### Phone Call Endpoints

```bash
# Make a phone call
POST /property-recap/property/{property_id}/call
{
  "phone_number": "+14155551234",  # E.164 format
  "call_purpose": "property_update"  # or contract_reminder, closing_ready
}

Response:
{
  "success": true,
  "call_id": "call_abc123",
  "status": "queued",
  "property_id": 1,
  "property_address": "123 Broadway, New York, NY",
  "phone_number": "+14155551234",
  "call_purpose": "property_update",
  "message": "Call initiated successfully"
}

# Check call status
GET /property-recap/call/{call_id}/status

# End ongoing call
POST /property-recap/call/{call_id}/end

# Get call recording
GET /property-recap/call/{call_id}/recording
```

## MCP Tools (Voice Integration)

### Property Recap Tools

**generate_property_recap**
```javascript
{
  "property_id": 1,
  "trigger": "manual"  // or "property_updated", "contract_signed", etc.
}
```
Returns: AI-generated comprehensive summary

**get_property_recap**
```javascript
{
  "property_id": 1
}
```
Returns: Existing recap (faster than generate)

### Phone Call Tool

**make_property_phone_call**
```javascript
{
  "property_id": 1,
  "phone_number": "+14155551234",  // E.164 format required
  "call_purpose": "property_update"  // property_update, contract_reminder, or closing_ready
}
```
Returns: Call initiated with call ID for tracking

## Call Types

### 1. Property Update (`property_update`)
**When to use:** General property updates or check-ins

**AI Assistant will:**
- Introduce itself as real estate assistant
- Provide comprehensive property update
- Answer questions about the property
- Offer to send more info via email

**First message:**
> "Hi! This is your real estate assistant calling with an update about the property at {address}. Do you have a moment?"

### 2. Contract Reminder (`contract_reminder`)
**When to use:** Pending contracts need attention

**AI Assistant will:**
- Politely remind about pending contracts
- Explain which contracts need attention
- Ask if they need help or have questions
- Offer to resend contract links

**First message:**
> "Hi! This is your real estate assistant calling about some pending contracts for {address}. Do you have a minute to discuss?"

### 3. Closing Ready (`closing_ready`)
**When to use:** All contracts complete, ready to celebrate!

**AI Assistant will:**
- Congratulate that all contracts are complete
- Confirm property is ready to close
- Discuss next steps (closing date, walkthrough)
- Answer questions

**First message:**
> "Hi! I have great news about the property at {address}! Do you have a moment to hear it?"

## Property Recap Content

Each recap includes:

### Detailed Recap (3-4 paragraphs)
- Comprehensive property overview
- Current status and transaction readiness
- Contract status and what's needed
- Key highlights and concerns
- Next steps

### Voice Summary (2-3 sentences)
- Ultra-concise for phone/TTS
- Focus on most critical info
- Natural conversational tone
- Perfect for "Tell me about this property"

### Structured Context (JSON)
```json
{
  "property": {
    "id": 1,
    "address": "123 Broadway, New York, NY",
    "price": 1000000,
    "bedrooms": 2,
    "bathrooms": 2,
    "property_type": "condo",
    "status": "available"
  },
  "contracts": [
    {
      "id": 101,
      "name": "Purchase Agreement",
      "status": "completed",
      "is_required": true,
      "requirement_source": "auto_attached"
    }
  ],
  "readiness": {
    "is_ready_to_close": true,
    "total_required": 3,
    "completed": 3,
    "in_progress": 0,
    "missing": 0
  },
  "enrichment": {
    "zestimate": 1050000,
    "rent_zestimate": 3500,
    "schools": [...]
  },
  "contacts": [
    {
      "name": "John Doe",
      "role": "buyer",
      "email": "john@example.com",
      "phone": "+14155551234"
    }
  ],
  "ai_summary": {
    "key_facts": [
      "3 bed, 2 bath condo",
      "Ready to close",
      "All contracts signed"
    ],
    "concerns": [],
    "next_steps": [
      "Schedule final walkthrough",
      "Review closing documents"
    ]
  }
}
```

## Example Use Cases

### Use Case 1: Daily Update Calls
```bash
# Generate recap
POST /property-recap/property/1/generate?trigger=daily_update

# Make call to buyer
POST /property-recap/property/1/call
{
  "phone_number": "+14155551234",
  "call_purpose": "property_update"
}

# AI calls and says:
# "Hi! Your property at 123 Broadway is progressing well. All 3 required 
#  contracts are complete, and we're ready to schedule the final walkthrough.
#  Do you have any questions?"
```

### Use Case 2: Contract Reminder
```bash
# Property has 2 contracts in progress
POST /property-recap/property/2/call
{
  "phone_number": "+14155555678",
  "call_purpose": "contract_reminder"
}

# AI calls and says:
# "Hi! I wanted to remind you about 2 pending contracts for 456 Main St.
#  We're still waiting on your signature for the Purchase Agreement and
#  the Lead Paint Disclosure. Would you like me to resend the links?"
```

### Use Case 3: Closing Celebration
```bash
# All contracts just completed!
POST /property-recap/property/3/generate?trigger=all_contracts_complete

POST /property-recap/property/3/call
{
  "phone_number": "+14155559999",
  "call_purpose": "closing_ready"
}

# AI calls and says:
# "Hi! I have great news about 789 Oak Ave! All contracts have been
#  completed and signed. The property is officially ready to close!
#  When would you like to schedule the closing?"
```

### Use Case 4: Voice Assistant Integration
```
User: "Call my client about the Broadway property"

AI: Uses make_property_phone_call MCP tool
AI: "I've initiated a call to +14155551234 about 123 Broadway. The AI
     assistant will provide a property update including contract status."

User: "What did you tell them?"

AI: Uses get_property_recap MCP tool
AI: "The recap includes: Property is a 2bed/2bath condo listed at $1M,
     all 3 required contracts are complete, and it's ready to close."
```

## Environment Variables

```bash
# .env file
ANTHROPIC_API_KEY=sk-ant-...  # For AI recap generation
VAPI_API_KEY=your_vapi_key    # For phone calls
```

## Database Model

```python
class PropertyRecap(Base):
    id: int
    property_id: int  # FK to properties
    
    # AI-generated content
    recap_text: str  # Human-readable summary
    voice_summary: str  # Short version for TTS
    recap_context: dict  # Structured data for VAPI/AI
    
    # Metadata
    version: int  # Increments on each update
    last_trigger: str  # What caused the update
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
```

## Auto-Update Triggers (Future Enhancement)

The system is designed to automatically regenerate recaps when:
- Property is created
- Property details change (price, status, etc.)
- Contracts are signed or updated
- Enrichment data is added
- Contacts are added or modified

**Implementation:**
Add webhook calls in relevant endpoints to trigger:
```python
await property_recap_service.generate_recap(
    db, property, trigger="property_updated"
)
```

## VAPI Configuration

The AI assistant is configured with:
- **Model:** GPT-4 (via OpenAI)
- **Voice:** 11Labs Rachel (professional female)
- **Temperature:** 0.7 (conversational but accurate)
- **Recording:** Enabled
- **Features:** Transcription, hang detection, function calls

## Benefits

### For Agents
- Save time with automated property summaries
- Make intelligent phone calls without prep work
- Consistent messaging across all calls
- Recordings for compliance and review

### For Clients
- Regular updates about their property
- Quick answers via AI assistant
- Professional, organized experience
- Never miss important contract deadlines

### For Brokerages
- Scalable client communication
- Compliance with recording requirements
- Analytics on call outcomes
- Reduced manual outreach work

## Next Steps

1. **Set up environment variables** (ANTHROPIC_API_KEY, VAPI_API_KEY)
2. **Generate first recap** for a test property
3. **Make test call** to your own number
4. **Add auto-update triggers** to property/contract endpoints
5. **Monitor call recordings** for quality assurance

## Cost Considerations

- **AI Recaps:** ~$0.02-0.05 per property (Claude Sonnet 4)
- **VAPI Calls:** ~$0.10-0.30 per minute (depends on plan)
- **Recommendation:** Generate recaps on-demand rather than for all properties

## Summary

This system gives you:

✅ **AI-powered property summaries** that stay up-to-date
✅ **Intelligent phone calls** with full context
✅ **Voice integration** via MCP tools
✅ **Three call types** for different scenarios
✅ **Structured data** for AI assistants
✅ **Recordings** for compliance

Perfect for keeping clients informed and reducing manual outreach work!
