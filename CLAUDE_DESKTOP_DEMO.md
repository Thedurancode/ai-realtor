# Claude Desktop MCP Demo Script

## Setup

1. **Start Backend**
   ```bash
   python3 -m uvicorn app.main:app --reload --port 8000
   ```

2. **Start TV Display**
   ```bash
   cd frontend && npm run dev
   ```
   Open http://localhost:3025

3. **Open Claude Desktop**
   Ensure MCP server is configured

---

## Demo Scenarios

### Scenario 1: Property Management

**You say to Claude:**
```
"Create a property at 456 Oak Avenue, Brooklyn, NY for $425,000 with 3 bedrooms and 2 bathrooms"
```

**Claude does:**
- Uses `create_property` MCP tool
- Validates address via Google Places
- Creates property in database
- TV display shows new property card

**Follow up:**
```
"Now enrich that property with Zillow data"
```

**Claude does:**
- Uses `enrich_property` tool
- Fetches Zestimate, photos, schools
- TV display shows enrichment animation
- Property card updates with new data

**Check it:**
```
"Show me all properties"
```

**Claude does:**
- Uses `list_properties` tool
- Shows formatted list with all details

---

### Scenario 2: Notifications

**You say:**
```
"We just closed 10 deals this month! Send a celebration notification to the TV display 🎉"
```

**Claude does:**
- Uses `send_notification` tool
- Title: "🎉 Milestone Reached!"
- Message: "Congratulations! You've closed 10 deals this month."
- Priority: high
- TV shows animated orange toast notification

**Try urgent:**
```
"Send an urgent alert - the contract for 123 Main St expires in 2 hours"
```

**Claude does:**
- Uses `send_notification` tool
- Title: "⚠️ Contract Expiring Soon"
- Message: "123 Main St contract expires in 2 hours! Get final signatures."
- Priority: urgent
- TV shows red urgent notification that stays for 20 seconds

**Check history:**
```
"Show me recent notifications"
```

**Claude does:**
- Uses `list_notifications` tool
- Shows formatted list with icons, titles, messages
- Includes timestamps and priority levels

---

### Scenario 3: Skip Tracing

**You say:**
```
"Skip trace property 5 to find the owner"
```

**Claude does:**
- Uses `skip_trace_property` tool
- Fetches owner name, phone numbers, emails
- Returns: "Found Robert Johnson with 2 phone numbers and 1 email"

**Add notification:**
```
"Great! Send a notification about this"
```

**Claude does:**
- Uses `send_notification` tool
- Title: "🔍 Owner Information Found"
- Message: "Skip trace complete for property #5. Found Robert Johnson."
- Type: skip_trace_complete
- TV shows notification

---

### Scenario 4: Lead Management

**You say:**
```
"Add Sarah Johnson as a buyer for property 8. Her email is sarah@example.com and phone is 555-1234"
```

**Claude does:**
- Uses `add_contact` tool
- Creates contact with role "buyer"
- Auto-triggers notification (backend feature)
- TV shows: "🎯 New Lead: Sarah Johnson"

---

### Scenario 5: Combining Tools

**You say:**
```
"Create a property at 789 Park Lane for $1.2M, enrich it with Zillow data, skip trace it, and send me a notification when it's all done"
```

**Claude does:**
1. Uses `create_property` tool → Property created
2. Uses `enrich_property` tool → Zillow data added
3. Uses `skip_trace_property` tool → Owner info found
4. Uses `send_notification` tool → Summary notification

**TV Display shows:**
- New property appears
- Enrichment animation plays
- Final notification: "✅ Property 789 Park Lane fully processed with Zillow data and owner contact info"

---

### Scenario 6: Property Updates

**You say:**
```
"What properties do we have that are available?"
```

**Claude does:**
- Uses `list_properties` with status filter
- Shows all available properties

**Then:**
```
"Get detailed info for property 3"
```

**Claude does:**
- Uses `get_property` tool
- Shows complete property data including:
  - Basic info
  - Zillow enrichment
  - Skip trace data
  - Photos
  - Schools
  - Tax history

---

### Scenario 7: Property Deletion

**You say:**
```
"Delete property 12 - it's no longer relevant"
```

**Claude does:**
- Uses `delete_property` tool
- Removes property and all related data:
  - Contacts
  - Contracts
  - Enrichments
  - Skip traces
- TV display updates (property disappears)
- Returns: "Deleted property 12 (456 Oak Avenue)"

---

### Scenario 8: Custom Notifications

**You say:**
```
"Send a low priority notification that we updated the website"
```

**Claude does:**
- Uses `send_notification` tool
- Priority: low (gray)
- Auto-dismiss: 8 seconds
- TV shows subtle gray notification

**Try different priorities:**
```
"Send a medium priority notification about the team meeting tomorrow"
→ Blue notification, 10 seconds

"Send a high priority notification - we got a new 5-star review"
→ Orange notification, 15 seconds

"Send an urgent notification - server is down"
→ Red notification, 20 seconds
```

---

### Scenario 9: Realistic Workflow

**You say:**
```
"We have a new property coming on the market tomorrow. Create it at 321 Elm Street, San Francisco for $2.5M with 4 beds and 3 baths. Then enrich it, skip trace it, and send a high priority notification to the team about this hot new listing."
```

**Claude does:**
1. Creates property
2. Enriches with Zillow (Zestimate, photos, etc.)
3. Skip traces for owner contact info
4. Sends notification:
   - Title: "🔥 New Hot Listing!"
   - Message: "321 Elm Street, SF - $2.5M | 4 bed, 3 bath | Enriched with Zillow data | Owner: [name] ([phone])"
   - Priority: high

**TV Display:**
- Shows property card with all enriched data
- Orange notification appears with details
- News ticker includes the new property

---

## Natural Language Variations

Claude understands many ways to request actions:

**Creating Properties:**
- "Create a property..."
- "Add a new listing..."
- "We have a property at..."
- "List a new property..."

**Sending Notifications:**
- "Send a notification..."
- "Alert the team that..."
- "Notify everyone about..."
- "Show on the TV that..."
- "Broadcast that..."

**Listing Things:**
- "Show me all properties"
- "List properties"
- "What properties do we have?"
- "Show recent notifications"
- "List notifications"

**Property Operations:**
- "Enrich property X"
- "Skip trace property Y"
- "Delete property Z"
- "Get details for property A"

---

## Tips for Best Results

✅ **DO:**
- Be specific with addresses ("456 Oak Avenue, Brooklyn, NY")
- Specify property details (price, beds, baths)
- Use natural language
- Chain multiple requests together
- Ask Claude to send notifications about completed tasks

❌ **DON'T:**
- Use incomplete addresses ("oak ave")
- Forget property IDs when needed
- Expect Claude to guess missing information
- Send too many notifications at once

---

## Troubleshooting

**"Backend not responding"**
- Start backend: `python3 -m uvicorn app.main:app --reload --port 8000`

**"TV display not updating"**
- Check it's open: http://localhost:3025
- Check browser console for errors

**"MCP tool not found"**
- Restart Claude Desktop
- Check MCP server configuration

**"Property not appearing on TV"**
- TV display polls every 3 seconds
- Wait a moment for update
- Refresh page if needed

---

## Advanced Use Cases

### Automated Reporting
```
"List all properties that were created today and send me a summary notification"
```

### Property Portfolio Review
```
"Show me all properties, then for each one that doesn't have Zillow data, enrich it"
```

### Lead Follow-up
```
"List all notifications from today that are about new leads"
```

### Data Quality Check
```
"List all properties and tell me which ones don't have skip trace data"
```

---

**Ready to try it out?** Start with a simple command:

```
"Create a test property at 123 Demo Street for $500,000 and send a notification about it!"
```

Watch the TV display come to life! 🚀
