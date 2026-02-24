# MCP Notification Tools

## Overview

The AI Realtor MCP server now includes tools for sending and managing notifications through Claude Desktop using natural language commands.

---

## New MCP Tools

### 1. send_notification
Send custom notifications to the TV display from Claude Desktop.

**Usage Examples:**

```
"Send a notification saying we closed 10 deals this month 🎉"

"Alert the team that the contract for 123 Main St is expiring soon - make it urgent"

"Send a high priority notification about the new lead Sarah Johnson who's interested in luxury properties"

"Notify that property 5 just got enriched with Zillow data"
```

**Parameters:**
- `title` (required) - Notification title (keep under 50 chars)
- `message` (required) - Notification message
- `notification_type` (optional) - Type: general, contract_signed, new_lead, property_price_change, property_status_change, appointment_reminder, skip_trace_complete, enrichment_complete
- `priority` (optional) - Priority: low, medium, high, urgent
- `icon` (optional) - Emoji icon (e.g., 🎉, ⚠️, 📝, 🔔)
- `property_id` (optional) - Associate with a property
- `auto_dismiss_seconds` (optional) - Auto-dismiss timer (5-30 seconds, default: 10)

---

### 2. list_notifications
View recent notification history.

**Usage Examples:**

```
"Show me recent notifications"

"List the last 20 notifications"

"Show unread notifications only"

"What notifications have we received today?"
```

**Parameters:**
- `limit` (optional) - Number to return (default: 10)
- `unread_only` (optional) - Only show unread (default: false)

---

## Example Scenarios

### Scenario 1: Milestone Celebration
```
User: "We just closed our 10th deal this month! Send a celebration notification to the TV"

Claude: *Uses send_notification tool*
  title: "🎉 Milestone Reached!"
  message: "Congratulations! You've closed 10 deals this month."
  priority: "high"
  icon: "🎉"

→ Notification appears on TV display as animated toast
```

### Scenario 2: Urgent Alert
```
User: "The contract for 456 Oak Ave expires in 2 hours - send an urgent alert"

Claude: *Uses send_notification tool*
  title: "⚠️ Contract Expiring Soon"
  message: "456 Oak Ave contract expires in 2 hours! Get final signatures now."
  priority: "urgent"
  icon: "⚠️"
  auto_dismiss_seconds: 20

→ Red urgent notification appears on TV
```

### Scenario 3: Property Update
```
User: "Property 8 just got enriched, notify the team"

Claude: *Uses send_notification tool*
  title: "✨ Property Data Updated"
  message: "Property #8 enriched with Zestimate, photos, and school ratings"
  notification_type: "enrichment_complete"
  priority: "medium"
  icon: "✨"
  property_id: 8

→ Blue notification with property link
```

### Scenario 4: Check History
```
User: "What notifications did we get today?"

Claude: *Uses list_notifications tool*
  limit: 50

→ Shows formatted list of all notifications with timestamps
```

---

## Integration with Existing Tools

The notification tools work seamlessly with other MCP tools:

### Create Property + Notify
```
User: "Create a property at 789 Broadway for $1.2M and send a notification about it"

Claude:
1. *Uses create_property tool*
2. *Uses send_notification tool*
   title: "🏠 New Property Added"
   message: "789 Broadway added to listings at $1,200,000"
   property_id: [new_property_id]
```

### Enrich + Notify
```
User: "Enrich property 5 and let me know when it's done"

Claude:
1. *Uses enrich_property tool*
2. *Uses send_notification tool*
   title: "✨ Enrichment Complete"
   message: "Property #5 now has Zestimate ($425K) and 15 photos"
   notification_type: "enrichment_complete"
   property_id: 5
```

### Skip Trace + Notify
```
User: "Skip trace property 3 and alert me when you find the owner"

Claude:
1. *Uses skip_trace_property tool*
2. *Uses send_notification tool*
   title: "🔍 Owner Information Found"
   message: "Skip trace complete for property #3. Found Robert Johnson with 2 phone numbers."
   notification_type: "skip_trace_complete"
   property_id: 3
```

---

## Natural Language Examples

Claude understands many ways to request notifications:

**Sending Notifications:**
- "Send a notification..."
- "Alert the team that..."
- "Notify everyone about..."
- "Show a message on the TV that..."
- "Broadcast that..."
- "Let everyone know..."

**Checking Notifications:**
- "Show recent notifications"
- "What notifications came in?"
- "List notifications"
- "Check notification history"
- "Any new alerts?"

**Priority Levels:**
- "urgent notification" → urgent (red)
- "important alert" → high (orange)
- "standard notification" → medium (blue)
- "just FYI" → low (gray)

**Icons:**
- Automatically suggests appropriate emojis based on context
- You can specify: "with a party emoji", "use a warning symbol", etc.

---

## Notification Types

When Claude detects the context, it automatically sets the appropriate type:

| Context | Type | Example |
|---------|------|---------|
| Contract completed | contract_signed | "Contract for 123 Main St is fully signed" |
| New buyer/seller | new_lead | "Sarah Johnson interested in luxury homes" |
| Price changed | property_price_change | "Price reduced to $475K" |
| Status changed | property_status_change | "Property now pending" |
| Upcoming meeting | appointment_reminder | "Showing in 15 minutes" |
| Owner found | skip_trace_complete | "Found owner contact info" |
| Data loaded | enrichment_complete | "Zillow data added" |
| General message | general | "Closed 10 deals this month!" |

---

## Priority Guidelines

| Priority | When to Use | Color | Duration |
|----------|-------------|-------|----------|
| **Urgent** | Action needed NOW | Red | 20s |
| | Contract expiring soon | | |
| | Appointment in <15 min | | |
| | Critical issues | | |
| **High** | Important but not immediate | Orange | 15s |
| | New qualified leads | | |
| | Contract signed | | |
| | Major milestones | | |
| **Medium** | Standard notifications | Blue | 10s |
| | Property updates | | |
| | Data enrichments | | |
| | General alerts | | |
| **Low** | Informational only | Gray | 8s |
| | Background processes | | |
| | Minor updates | | |

---

## Best Practices

✅ **DO:**
- Use clear, concise titles
- Include relevant context in messages
- Set appropriate priority levels
- Use descriptive icons
- Associate with properties when relevant

❌ **DON'T:**
- Overuse urgent priority
- Send duplicate notifications
- Make titles too long (>50 chars)
- Set auto-dismiss too short (<5s)
- Include sensitive information

---

## Testing MCP Tools

### Via Claude Desktop

1. Ensure backend is running:
   ```bash
   python3 -m uvicorn app.main:app --reload --port 8000
   ```

2. Ensure TV display is open:
   ```
   http://localhost:3025
   ```

3. In Claude Desktop, try:
   ```
   "Send a test notification saying 'Hello from Claude Desktop!' with a wave emoji"

   "List recent notifications"

   "Send an urgent alert about a contract expiring"
   ```

### Verify in TV Display
- Notification should appear as animated toast in top-right corner
- Color matches priority level
- Auto-dismisses after specified time
- Can manually dismiss with X button

---

## Troubleshooting

### "Error: Connection refused"
**Solution:** Start the backend:
```bash
python3 -m uvicorn app.main:app --reload --port 8000
```

### Notification not appearing on TV
**Solution:**
1. Check TV display is open: http://localhost:3025
2. Check browser console for WebSocket connection
3. Verify backend is running

### MCP tool not found
**Solution:** Restart Claude Desktop to reload MCP server

---

## Future Enhancements

🔮 **Planned:**
- Notification templates (reusable patterns)
- Scheduled notifications ("remind me in 1 hour")
- Notification groups (batch related items)
- Reply to notifications (interactive)
- Notification forwarding (email/SMS)
- Custom notification sounds

---

## Complete Tool Definitions

### send_notification
```typescript
{
  name: "send_notification",
  description: "Send a custom notification to the TV display",
  parameters: {
    title: string (required),
    message: string (required),
    notification_type: enum (optional),
    priority: enum (optional),
    icon: string (optional),
    property_id: number (optional),
    auto_dismiss_seconds: number (optional)
  }
}
```

### list_notifications
```typescript
{
  name: "list_notifications",
  description: "List recent notifications from the system",
  parameters: {
    limit: number (optional, default: 10),
    unread_only: boolean (optional, default: false)
  }
}
```

---

**The MCP notification tools are now available in Claude Desktop!** 🎉

Try it out:
```
"Send a celebration notification for closing 10 deals this month!"
```
