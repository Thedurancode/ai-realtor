# 🆕 Address-Based Property References - Quick Guide

**No more property IDs needed! Reference properties naturally by address.**

---

## ✅ What Changed

### Before (ID-based)
```
❌ "Enrich property 5"
❌ "Skip trace property 3"
❌ "Send contract for property 12"
```

### After (Address-based)
```
✅ "Enrich the property at 123 Main St, New York"
✅ "Skip trace the Miami condo on Ocean Drive"
✅ "Send contract for the Brooklyn property near Prospect Park"
```

---

## 🎯 How It Works

The resolver searches through your properties and matches:
1. **Exact address:** "123 Main St, New York, NY"
2. **Partial address:** "123 Main St" or "Main St, Brooklyn"
3. **City only:** "Miami" or "Brooklyn"
4. **State:** "Florida" or "NY"
5. **Combinations:** "Main St, Brooklyn, NY"
6. **ID still works:** "property 5" (fallback)

---

## 📝 Example Prompts

### Property Management

```
"Enrich the property at 123 Main St, New York"
"Skip trace the Miami condo"
"Score the Brooklyn property"
"Get details for 456 Oak Avenue"
"Update the Austin property status to complete"
```

### Contract Management

```
"Attach contracts for the property at 123 Main St"
"Check if the Brooklyn property is ready to close"
"Send the Purchase Agreement for the Miami condo"
"AI suggest contracts for the property at 789 Broadway"
```

### Outreach

```
"Call the owner of 123 Main St"
"Create a voice campaign for the Miami properties"
"Add a note to the Austin property"
```

### Analytics

```
"Calculate the deal for the Brooklyn property"
"Get comps for the property at 456 Oak Ave"
"Score all my Florida properties"
```

---

## 🎮 Portal Usage

Clients can now search by address:
- Visit `/portal/properties`
- Use the search bar
- Type any part of the address
- Click to view details

---

## 🔧 API Endpoints

### Portal (Client-facing)

```
GET /portal/properties/search/{query}
GET /portal/properties/by-identifier/{address}
```

### Main API (Agent-facing)

The resolver is now integrated into all major endpoints:
- Properties
- Contracts
- Skip Trace
- Offers
- Notes
- Calls
- Campaigns

### MCP Server (Voice Control)

The address resolver is now integrated into all **135 MCP tools**! You can now use natural voice commands like:

```
"Enrich the property at 123 Main St"           # Instead of "Enrich property 5"
"Skip trace the Miami condo"                   # Instead of "Skip trace property 3"
"Score the Brooklyn property"                  # Instead of "Score property 12"
"Is 123 Main St ready to close?"               # Instead of "Is property 5 ready?"
"Send the Purchase Agreement for signing"     # Works without property reference
```

**Updated tool files:**
- `insights.py` - Property insights now support addresses
- `follow_ups.py` - Complete and snooze follow-ups by address
- `property_scoring.py` - Score properties by address
- `comps.py` - Get comparables by address
- `activity_timeline.py` - Timeline by address
- `scheduled_tasks.py` - Schedule tasks by address
- `contracts_ai.py` - Contract management by address
- `conversation.py` - Property history by address
- And many more!

**Pattern:**
```python
# Old way (still works!)
property_id = arguments.get("property_id")

# New way (voice-friendly!)
property_id = resolve_property_id(arguments)
# Supports both property_id and address parameters
```

---

## 📊 Examples by Use Case

### Real Estate Agent
```
"I'm working on the listing at 123 Main St"

→ Enrich, skip trace, score, attach contracts
→ All work with the address instead of ID
```

### Property Manager
```
"The Miami condos need attention"

→ Bulk operations work with city names
→ Enrich all, score all, check all
```

### Buyer's Agent
```
"My client is interested in the Brooklyn property"

→ Pull up details, share contract link
→ No need to remember IDs
```

---

## ⚠️ What About Ambiguous Matches?

If multiple properties match, you'll get a list to choose from:

```
You: "Enrich the Main St property"

API: Found 3 matches:
  1. 123 Main St, Brooklyn, NY
  2. 456 Main St, Queens, NY
  3. 789 Main St, New York, NY

→ "Be more specific"
```

Then you can say:
```
"Enrich 123 Main St, Brooklyn"
"Enrich the Brooklyn Main St property"
```

---

## 🚀 Migration Examples

### Old Way → New Way

| Old ❌ | New ✅ |
|--------|--------|
| "Enrich property 5" | "Enrich 123 Main St, New York" |
| "Skip trace 3" | "Skip trace the Miami condo" |
| "Score property 12" | "Score the Austin house" |
| "Contract for 8" | "Contract for 789 Broadway" |

---

## 🎓 Best Practices

### Be Specific When Needed
```
✅ "Enrich 123 Main St, Brooklyn"
✅ "Skip trace the property in Austin"
✅ "Score the Florida condo"

⚠️ "Enrich the property" (requires clarification if multiple)
```

### Use What You Have
```
✅ "Enrich my Brooklyn properties"
✅ "Skip trace all Miami condos"
✅ "Score all houses under $500k"
```

### Still Can Use IDs
```
✅ "Enrich property 5" (still works!)
✅ "Delete property 3"
```

---

## 📱 Portal Search Feature

The client portal now has address search:

1. Visit `/portal/properties`
2. Use the search bar
3. Type any part of the address
4. Results filter in real-time

---

## 🔍 Search Algorithms

The resolver uses fuzzy matching:
- Case-insensitive
- Partial matches (min 3 characters)
- Multiple string combinations
- City + state matching
- Address component matching

---

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)
