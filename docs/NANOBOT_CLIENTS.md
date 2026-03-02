# Nanobot Supported Clients/Channels

## Official Chat App Integrations

Nanobot supports **9 different chat platforms**:

| Platform | Setup Method | GUI Type | Difficulty |
|----------|--------------|----------|------------|
| **Telegram** | Bot token | Mobile/Desktop App | ⭐ Easy (Recommended) |
| **Discord** | Bot token | Desktop/Web App | ⭐ Easy |
| **WhatsApp** | QR code scan | Mobile App | ⭐ Easy |
| **Feishu** | App ID + Secret | Desktop/Web App | ⭐⭐ Medium |
| **Mochat** | Claw token (auto-setup) | Mobile App | ⭐ Easy |
| **DingTalk** | App Key + Secret | Desktop/Web App | ⭐⭐ Medium |
| **Slack** | Bot token | Desktop/Web App | ⭐ Easy |
| **Email** | IMAP/SMTP credentials | Email Client | ⭐⭐ Medium |
| **QQ** | App ID + Secret | Desktop/Mobile App | ⭐⭐ Medium |

---

## Recommended Options

### Option 1: Telegram (Best Choice)

**Why:**
- ✅ Easy to set up (5 minutes)
- ✅ Works on mobile and desktop
- ✅ Great GUI
- ✅ Voice messages supported
- ✅ File sharing
- ✅ Officially recommended

**Setup:**
1. Open Telegram, search `@BotFather`
2. Send `/newbot`, follow prompts
3. Copy the token
4. Add to config:

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allowFrom": ["YOUR_USER_ID"]
    }
  }
}
```

5. Restart nanobot
6. Chat with your bot in Telegram!

---

### Option 2: Discord

**Why:**
- ✅ Familiar interface
- ✅ Works on desktop/web
- ✅ Good for communities
- ✅ Voice channels

**Setup:**
1. Create Discord application at https://discord.com/developers/applications
2. Create a bot user
3. Enable "Message Content" intent
4. Copy bot token
5. Add to config:

```json
{
  "channels": {
    "discord": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allowFrom": ["YOUR_USER_ID"]
    }
  }
}
```

---

### Option 3: WhatsApp

**Why:**
- ✅ Everyone has it
- ✅ Mobile app
- ✅ Voice messages
- ✅ Easy QR code setup

**Setup:**
```bash
docker exec -it nanobot-gateway nanobot channels login
```
Then scan QR code with WhatsApp mobile app.

---

## Current Status

Your Nanobot has **NO channels enabled**:
```
Warning: No channels enabled
```

That's why you only have CLI access right now.

---

## How to Enable Telegram (Quick Start)

1. **Create Telegram Bot:**
   - Open Telegram
   - Search for `@BotFather`
   - Send: `/newbot`
   - Name your bot (e.g., "My AI Assistant")
   - Copy the token (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Find Your User ID:**
   - In Telegram settings, look for your username
   - Or use @userinfobot to get your numeric ID

3. **Update Nanobot Config:**

I can update the config for you. Just provide:
- Your Telegram bot token
- Your Telegram user ID

4. **Restart Nanobot:**
```bash
docker-compose -f docker-compose-local-nanobot.yml restart nanobot
```

5. **Start Chatting:**
   - Open Telegram
   - Search for your bot
   - Start chatting!

---

## Alternative: Web Client

I already created a simple web client for you:
```bash
open examples/web/nanobot-web-client.html
```

This gives you a basic chat interface in your browser.

---

## Summary

| Method | GUI | Ease of Use | Status |
|--------|-----|-------------|--------|
| CLI (Terminal) | ❌ No | ⭐ Easy | ✅ Currently working |
| Web Client | ✅ Yes | ⭐ Easy | ✅ Created, needs testing |
| Telegram | ✅ Yes | ⭐ Easy | ❌ Not configured |
| Discord | ✅ Yes | ⭐ Easy | ❌ Not configured |
| WhatsApp | ✅ Yes | ⭐ Easy | ❌ Not configured |
| Others | ✅ Yes | ⭐⭐ Medium | ❌ Not configured |

**Recommendation:** Set up **Telegram** for the best experience with a familiar mobile app GUI.

Would you like me to help you set up Telegram or another channel?
