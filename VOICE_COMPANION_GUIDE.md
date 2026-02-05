# Voice Companion Display - Integration Guide

This guide explains how to integrate your MCP voice agent with the Bloomberg terminal companion display.

## Overview

The Voice Companion provides a real-time visual display that syncs with your voice agent conversations through MCP. It shows what you're discussing, displays live transcripts, and focuses on relevant entities.

## Features

1. **Live Voice Status Indicator** - Shows when voice is active (top-right corner)
2. **Current Context Display** - Shows what topic you're discussing (top-center)
3. **Live Conversation Transcript** - Real-time chat display (bottom-left)
4. **Focused Entity Display** - Full-screen overlay when discussing specific properties

## Integration from MCP Tools

### 1. Update Voice Context

When the user asks about a specific topic, call this from your MCP tool:

```javascript
window.updateVoiceContext({
  type: 'property',  // 'property' | 'contract' | 'contact' | 'general'
  entityId: 123,     // Optional: ID of the entity being discussed
  topic: 'Upper West Side Condo',  // Human-readable topic
  timestamp: new Date()
})
```

### 2. Add Conversation Messages

Add messages to the live transcript:

```javascript
// User spoke
window.addVoiceMessage('user', 'Show me properties in Manhattan', {
  type: 'property',
  topic: 'Manhattan Properties'
})

// Agent responded
window.addVoiceMessage('agent', 'I found 5 luxury properties in Manhattan. The highest priced is...', {
  type: 'property'
})
```

### 3. Focus on Specific Entity

When discussing a specific property, contract, or contact:

```javascript
// Fetch the entity data
const property = await fetch('https://ai-realtor.fly.dev/properties/1').then(r => r.json())

// Show full-screen focus
window.setVoiceFocus(property)

// Later, clear the focus
window.clearVoiceFocus()
```

## Example MCP Tool Implementation

```python
# In your MCP server tool
async def discuss_property(property_id: int, user_query: str):
    # Fetch property data
    property_data = await get_property(property_id)

    # Update the companion display
    return {
        "voice_ui_update": {
            "type": "updateVoiceContext",
            "context": {
                "type": "property",
                "entityId": property_id,
                "topic": property_data["title"],
                "timestamp": datetime.now().isoformat()
            }
        },
        "transcript": {
            "user": user_query,
            "agent": f"This is a {property_data['bedrooms']} bedroom property at {property_data['address']}..."
        },
        "focus_entity": property_data  # Shows full-screen
    }
```

## Frontend API Reference

All these functions are globally available via `window`:

### `window.updateVoiceContext(context: VoiceContext)`
Update what's being discussed.

**Parameters:**
- `type`: 'property' | 'contract' | 'contact' | 'general'
- `entityId` (optional): ID of the entity
- `topic` (optional): Display name
- `timestamp`: Date object

### `window.addVoiceMessage(speaker: 'user' | 'agent', text: string, context?: VoiceContext)`
Add a message to the live transcript.

**Parameters:**
- `speaker`: 'user' or 'agent'
- `text`: The message content
- `context` (optional): Related context

### `window.setVoiceFocus(entity: any)`
Show full-screen focus on an entity (property, contract, contact).

**Parameters:**
- `entity`: The full entity object (must have appropriate fields)

### `window.clearVoiceFocus()`
Clear the full-screen focus.

## Visual Indicators

- **Green pulsing dot** = Voice is active
- **Orange banner** = Discussing a property
- **Purple banner** = Discussing a contract
- **Blue banner** = Discussing a contact
- **Cyan banner** = General conversation

## Example Flow

1. User says: "Tell me about the Tribeca Penthouse"
2. MCP tool calls:
   ```javascript
   window.updateVoiceContext({
     type: 'property',
     topic: 'Tribeca Penthouse'
   })
   window.addVoiceMessage('user', 'Tell me about the Tribeca Penthouse')
   ```
3. Agent fetches property data
4. MCP tool calls:
   ```javascript
   const property = await fetchProperty(9)
   window.setVoiceFocus(property)
   window.addVoiceMessage('agent', 'This is a stunning 4-bedroom penthouse...')
   ```
5. Full-screen display shows property details with image
6. User can click anywhere to close focus and return to normal view

## Testing

Test the integration with browser console:

```javascript
// Test context update
window.updateVoiceContext({
  type: 'property',
  topic: 'Test Property',
  timestamp: new Date()
})

// Test adding message
window.addVoiceMessage('user', 'Show me this property')

// Test focus (replace with actual property data)
window.setVoiceFocus({
  title: 'Test Property',
  price: 5000000,
  address: '123 Main St',
  city: 'New York',
  bedrooms: 3,
  bathrooms: 2,
  square_feet: 2000
})
```

## Backend WebSocket Integration

For true real-time sync, you can send events from your backend:

```python
# In your FastAPI/backend
@app.websocket("/voice-ws")
async def voice_websocket(websocket: WebSocket):
    await websocket.accept()

    while True:
        # When voice agent does something
        await websocket.send_json({
            "type": "context_update",
            "context": {
                "type": "property",
                "entityId": 123,
                "topic": "Manhattan Condo"
            }
        })

        await websocket.send_json({
            "type": "message",
            "speaker": "agent",
            "text": "I found this property for you..."
        })
```

## Styling

All companion displays use the Bloomberg terminal theme:
- Orange: Properties
- Purple: Contracts
- Blue: Contacts
- Cyan: General/API activity
- Green: Success/Active states

The displays are designed to be non-intrusive but highly visible when needed.
