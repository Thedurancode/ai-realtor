# Telegram Bot Custom Menu Guide

## ✅ Already Configured

Your bot now has a **custom command menu** with 10 commands:
- `/start` - 🏠 Start AI Realtor Bot
- `/properties` - 📋 View all properties
- `/agents` - 👥 List all agents
- `/create` - ➕ Create new property
- `/enrich` - 📊 Enrich with Zillow data
- `/skiptrace` - 🔍 Skip trace property
- `/contracts` - 📄 View contracts
- `/search` - 🔎 Search properties
- `/help` - ❓ Get help
- `/status` - ✅ System status

Users access these by tapping the **menu button** (bottom left of chat).

---

## 🎨 Adding Interactive Buttons (Inline Keyboards)

You can add interactive buttons that appear under messages. Here's how:

### Example 1: Property Action Buttons

```python
# When showing a property, add action buttons
keyboard = {
    "inline_keyboard": [
        [
            {"text": "📊 Enrich", "callback_data": "enrich_1"},
            {"text": "🔍 Skip Trace", "callback_data": "skiptrace_1"}
        ],
        [
            {"text": "📄 Contracts", "callback_data": "contracts_1"},
            {"text": "📞 Call Owner", "callback_data": "call_1"}
        ],
        [
            {"text": "🏠 All Properties", "callback_data": "list_properties"}
        ]
    ]
}

# Send with keyboard
requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    json={
        "chat_id": chat_id,
        "text": "Property: 123 Main St\nPrice: $850,000",
        "reply_markup": keyboard
    }
)
```

### Example 2: Main Menu Keyboard

```python
main_menu = {
    "inline_keyboard": [
        [
            {"text": "📋 Properties", "callback_data": "menu_properties"},
            {"text": "👥 Agents", "callback_data": "menu_agents"}
        ],
        [
            {"text": "➕ Create Property", "callback_data": "menu_create"},
            {"text": "🔎 Search", "callback_data": "menu_search"}
        ],
        [
            {"text": "📊 Analytics", "callback_data": "menu_analytics"},
            {"text": "⚙️ Settings", "callback_data": "menu_settings"}
        ],
        [
            {"text": "❓ Help", "callback_data": "menu_help"}
        ]
    ]
}
```

### Example 3: Quick Actions Menu

```python
quick_actions = {
    "inline_keyboard": [
        [
            {"text": "🏠 New Property", "url": "https://ai-realtor.fly.dev/properties"},
            {"text": "📊 Dashboard", "url": "https://ai-realtor.fly.dev/docs"}
        ],
        [
            {"text": "💬 Chat Support", "url": "https://t.me/your_support"}
        ]
    ]
}
```

---

## 🔧 How to Implement

### Option 1: Add to Nanobot (Recommended)

Edit the nanobot channel configuration to handle callback queries:

```bash
# Edit nanobot config
docker exec -it nanobot-gateway vi /root/.nanobot/channels/telegram.py
```

Add callback query handler:

```python
async def _on_callback_query(self, callback_query):
    """Handle inline button presses"""
    data = callback_query.get('data', '')
    chat_id = callback_query['message']['chat']['id']

    if data.startswith('enrich_'):
        property_id = data.split('_')[1]
        # Call enrich API
        await self._enrich_property(chat_id, property_id)

    elif data == 'menu_properties':
        # Show properties list with keyboard
        await self._show_properties(chat_id)

    # Answer the callback query
    await self._api.answerCallbackQuery(
        callback_query_id=callback_query['id']
    )
```

### Option 2: Create Separate Bot Service

Build a lightweight Python service that:

1. Receives webhook updates from Telegram
2. Parses callback_data from buttons
3. Calls AI Realtor API
4. Sends responses with inline keyboards

```python
# telegram-bot-service.py
from fastapi import FastAPI, Request
import httpx

app = FastAPI()
AI_REALTOR_API = "http://ai-realtor:8000"
API_KEY = "nanobot-perm-key-2024"

@app.post("/webhook")
async def webhook(update: dict):
    if "callback_query" in update:
        await handle_callback(update["callback_query"])
    return {"ok": True}

async def handle_callback(callback):
    data = callback["data"]
    chat_id = callback["message"]["chat"]["id"]

    async with httpx.AsyncClient() as client:
        if data == "list_properties":
            resp = await client.get(
                f"{AI_REALTOR_API}/properties/",
                headers={"X-API-Key": API_KEY}
            )
            properties = resp.json()

            # Send with keyboard
            keyboard = build_properties_keyboard(properties)
            await send_message(chat_id, "Your properties:", keyboard)
```

---

## 📝 Testing Your Buttons

Send a test message with buttons:

```bash
# Test inline keyboard
curl -X POST "https://api.telegram.org/bot8392020900:AAEKlrigz4_B35slxdJpBIApSrotEf3ceiI/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "6690356751",
    "text": "🏠 *AI Realtor Menu*",
    "parse_mode": "Markdown",
    "reply_markup": {
      "inline_keyboard": [
        [
          {"text": "📋 Properties", "callback_data": "properties"},
          {"text": "👥 Agents", "callback_data": "agents"}
        ],
        [
          {"text": "➕ Create", "callback_data": "create"},
          {"text": "🔎 Search", "callback_data": "search"}
        ],
        [
          {"text": "❓ Help", "callback_data": "help"}
        ]
      ]
    }
  }'
```

---

## 🎯 Best Practices

1. **Group related actions** - Put similar functions in the same row
2. **Use emojis** - Makes buttons more visual and engaging
3. **Limit to 2-3 columns** - Keep buttons readable on mobile
4. **Provide feedback** - Show "Processing..." when button is clicked
5. **Handle errors gracefully** - Send error messages if API calls fail

---

## 🚀 Next Steps

1. **Decide implementation approach:**
   - Add to existing Nanobot (more complex, full integration)
   - Create separate service (simpler, more control)

2. **Design your button flows:**
   - Main menu → Category → Action → Result
   - Keep it 3-4 levels deep maximum

3. **Implement callback handlers:**
   - Each button needs a handler function
   - Call AI Realtor API
   - Send response with next set of buttons

4. **Test thoroughly:**
   - Test each button flow
   - Verify error handling
   - Check mobile display

---

## 📚 Resources

- Telegram Bot API Docs: https://core.telegram.org/bots/api#inlinekeyboardmarkup
- ReplyKeyboardMarkup (persistent keyboard): https://core.telegram.org/bots/api#replykeyboardmarkup
- Inline vs Reply Keyboards: Inline disappear after use, Reply stay visible
