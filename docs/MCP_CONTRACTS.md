# MCP Contract Tools (DocuSeal Integration)

## Overview

The AI Realtor MCP server now includes **3 contract tools** for sending and managing DocuSeal contracts through Claude Desktop!

---

## New MCP Tools

### 1. send_contract
Send a contract to a contact for e-signature via DocuSeal.

**Usage Examples:**
```
"Send a purchase agreement to contact 5 for property 1"

"Send the lease agreement to the buyer for property 3"

"Create and send a contract to contact 2 for property 8"
```

**Parameters:**
- `property_id` (required) - Property ID
- `contact_id` (required) - Contact ID (must be linked to property)
- `contract_name` (optional) - Name (default: "Purchase Agreement")
- `docuseal_template_id` (optional) - Template ID (default: "1")

**What it does:**
1. Creates contract in database
2. Sends to contact via DocuSeal
3. Contact receives email with signing link
4. Returns contract details and submission info

---

### 2. check_contract_status
Check the current status of a contract with real-time updates from DocuSeal.

**Usage Examples:**
```
"Check the status of contract 5"

"What's the signing status for contract 3?"

"Has contract 8 been signed yet?"

"Show me who signed the contract for 141 throop"

"Check contract status for 123 main street"
```

**Parameters:**
- `contract_id` (optional) - Contract ID to check
- `address_query` (optional) - Fuzzy property address (e.g., "141 throop", "123 main st")
- **Note:** Either `contract_id` OR `address_query` must be provided

**Returns:**
- Contract status (draft, sent, in_progress, completed, cancelled)
- List of signers with their individual statuses
- Timestamps for sent, opened, completed
- DocuSeal submission details

---

### 3. list_contracts
List all contracts, optionally filtered by property ID or address.

**Usage Examples:**
```
"List all contracts"

"Show me contracts for property 5"

"What contracts do we have?"

"Show me contracts for 141 throop"

"List contracts for 123 main street"
```

**Parameters:**
- `property_id` (optional) - Filter by property ID
- `address_query` (optional) - Fuzzy property address (e.g., "141 throop", "123 main st")
- **Note:** Use either `property_id` OR `address_query` (not both)

**Returns:**
- List of contracts with name, status, property, dates
- Formatted summary + full JSON

---

## Complete MCP Tool Count

Your MCP server now has **14 tools total**:

### Property Tools (7)
1. list_properties
2. get_property
3. create_property
4. delete_property
5. enrich_property
6. skip_trace_property
7. add_contact

### Notification Tools (2)
8. send_notification
9. list_notifications

### Contract Tools (5) ✨ NEW
10. **send_contract**
11. **check_contract_status**
12. **list_contracts**
13. **list_contracts_voice** 🎤 VOICE TOOL
14. **check_contract_status_voice** 🎤 VOICE TOOL

---

## Example Workflows

### Scenario 1: Send Contract to Buyer

**You say to Claude:**
```
"For property 5, send a purchase agreement to the buyer (contact 12)"
```

**Claude does:**
1. Uses `send_contract` tool
2. Creates "Purchase Agreement" contract
3. Sends to contact 12 via DocuSeal
4. Contact receives email with signing link
5. Returns confirmation

**Response:**
```
✅ Contract sent for signing!

{
  "contract_id": 23,
  "name": "Purchase Agreement",
  "property_id": 5,
  "contact_id": 12,
  "status": "sent",
  "docuseal_url": "https://docuseal.../sign/abc123",
  "sent_at": "2026-02-04T21:30:00Z"
}
```

---

### Scenario 2: Check Contract Status

**You say:**
```
"Check if contract 23 has been signed"
```

**Claude does:**
1. Uses `check_contract_status` tool
2. Fetches latest status from DocuSeal
3. Shows signer details

**Response:**
```
Contract #23 Status: IN_PROGRESS

Signers:
  - Sarah Johnson (Buyer): completed
  - Michael Chen (Seller): pending

Full JSON: {...}
```

---

### Scenario 3: Complete Property Deal

**You say:**
```
"For property 8: create it at 456 Oak St for $500K, add Sarah as buyer, then send her a purchase agreement"
```

**Claude does:**
1. Uses `create_property` → Property ID: 15
2. Uses `add_contact` → Contact ID: 34
3. Uses `send_contract` → Contract sent!

**Response:**
```
✅ Property created: #15 (456 Oak St)
✅ Contact added: Sarah (Buyer, ID: 34)
✅ Contract sent: Purchase Agreement

Sarah will receive an email with the signing link!
```

---

### Scenario 4: Monitor All Contracts

**You say:**
```
"Show me all contracts and their statuses"
```

**Claude does:**
Uses `list_contracts` tool

**Response:**
```
Found 5 contract(s):

📝 Purchase Agreement (ID: 23)
   Status: in_progress
   Property ID: 5
   Created: 2026-02-04T21:30:00Z

📝 Lease Agreement (ID: 24)
   Status: completed
   Property ID: 8
   Created: 2026-02-04T20:15:00Z

[... more contracts ...]
```

---

### Scenario 5: Context-Aware Contract Query ✨ NEW

**You say:**
```
"Show me who signed the contracts for 141 throop"
```

**Claude does:**
1. Uses `list_contracts` tool with `address_query="141 throop"`
2. Fuzzy matches "141 throop" → Property ID: 5 (141 Throop Avenue)
3. Returns contracts for that property

**Response:**
```
Found 2 contract(s) for address '141 throop':

📝 Purchase Agreement (ID: 23)
   Status: in_progress
   Property ID: 5
   Created: 2026-02-04T21:30:00Z

📝 Seller Disclosure (ID: 27)
   Status: completed
   Property ID: 5
   Created: 2026-02-03T18:45:00Z
```

**Follow-up:**
```
"Check the status of the purchase agreement"
```

**Claude does:**
Uses `check_contract_status` with `contract_id=23`

**Response:**
```
Contract #23 Status: IN_PROGRESS

Signers:
  - Sarah Johnson (Buyer): completed
  - Michael Chen (Seller): pending

Full JSON: {...}
```

**Or alternatively:**
```
"Check contract status for 141 throop"
```

**Claude does:**
Uses `check_contract_status` with `address_query="141 throop"`
(Returns status of the most recent contract)

---

## Natural Language Variations

Claude understands many ways to request contracts:

**Sending Contracts:**
- "Send a contract..."
- "Send the purchase agreement to..."
- "Create and send contract..."
- "Email the contract to..."

**Checking Status:**
- "Check contract status..."
- "Has contract X been signed?"
- "What's the status of..."
- "Did they sign contract Y?"
- "Show me who signed the contract for 141 throop" ✨ NEW
- "Check contract status for 123 main street" ✨ NEW

**Listing Contracts:**
- "Show all contracts"
- "List contracts"
- "What contracts do we have?"
- "Show me contracts for property X"
- "Show me contracts for 141 throop" ✨ NEW
- "List contracts for 123 main street" ✨ NEW

## Context-Aware Address Queries ✨ NEW

You can now use **natural language addresses** instead of property IDs when checking contract status or listing contracts!

### How It Works

The MCP tools use **fuzzy address matching** to find properties. You don't need to provide the exact address - just enough to identify the property:

**Examples:**
- "141 throop" → Finds "141 Throop Avenue, Brooklyn, NY 11206"
- "123 main" → Finds "123 Main Street"
- "oak ave" → Finds any property with "oak" and "ave" in the address
- "456 elm sf" → Finds "456 Elm Street, San Francisco, CA"

### Usage Examples

**Check Contract Status by Address:**
```
"Show me who signed the contract for 141 throop"
"Check contract status for 123 main street"
"Has the contract for oak avenue been completed?"
```

**List Contracts by Address:**
```
"Show me all contracts for 141 throop"
"List contracts for 123 main street"
"What contracts do we have for the oak avenue property?"
```

### Benefits

✅ **No Need to Remember IDs** - Use addresses you already know
✅ **Natural Language** - Speak as you naturally would
✅ **Fuzzy Matching** - Partial addresses work fine
✅ **Faster Workflow** - Skip the step of looking up property IDs

---

## Integration with Other Tools

### Create Property → Add Contact → Send Contract
```
"Create a property at 789 Broadway for $1.2M, add Michael Chen as the buyer (michael@email.com), and send him a purchase agreement"
```

**Flow:**
1. `create_property` → Property ID
2. `add_contact` → Contact ID (triggers new lead notification)
3. `send_contract` → Contract sent via DocuSeal

---

### Enrich → Skip Trace → Add Contact → Send Contract
```
"For property 5: enrich it, skip trace it, add the owner as a contact, and send them a listing agreement"
```

**Flow:**
1. `enrich_property` → Zillow data added
2. `skip_trace_property` → Owner info found
3. `add_contact` → Owner added as contact
4. `send_contract` → Listing agreement sent

---

## Contract Status Types

| Status | Meaning |
|--------|---------|
| draft | Created but not sent |
| sent | Sent to signer(s), awaiting action |
| in_progress | At least one signer has opened/signed |
| completed | All signers have signed ✅ |
| cancelled | Contract was cancelled |
| declined | Signer declined to sign |

---

## Signer Status Types

| Status | Meaning |
|--------|---------|
| pending | Email sent, not opened yet |
| opened | Signer opened the document |
| completed | Signer finished signing ✅ |
| declined | Signer declined to sign ❌ |

---

## DocuSeal Integration Flow

```
Claude Desktop
      ↓
MCP: send_contract
      ↓
Backend API
      ↓
DocuSeal API
      ↓
Email to Signer → Signing Link
      ↓
Signer Signs
      ↓
DocuSeal Webhook → Backend
      ↓
Status Updated
      ↓
Notification on TV 🎉
```

---

## Example: Multi-Signer Contract

For contracts with multiple signers, you'll need to use the API directly:

```bash
# Create and send multi-party contract
curl -X POST http://localhost:8000/contracts/1/send-multi-party \
  -H "Content-Type: application/json" \
  -d '{
    "submitters": [
      {
        "name": "John Smith",
        "email": "john@email.com",
        "role": "Owner",
        "signing_order": 1
      },
      {
        "name": "Sarah Chen",
        "email": "sarah@email.com",
        "role": "Buyer",
        "signing_order": 2
      }
    ],
    "order": "preserved"
  }'
```

Then check status via Claude:
```
"Check the status of contract 1"
```

---

## Error Handling

### Contact Not Found
```
Error: Contact 99 not found
```
**Solution:** Use `add_contact` first or verify contact ID

### Property Mismatch
```
Error: Contact must belong to the same property
```
**Solution:** Ensure contact is linked to the property

### DocuSeal Error
```
Error: DocuSeal API error: Template not found
```
**Solution:** Verify template ID or use default

---

## Testing

### Via Claude Desktop

1. **Create test setup:**
```
"Create a test property at 123 Demo St for $500K"
"Add a buyer named Test User (test@example.com) to that property"
```

2. **Send contract:**
```
"Send a purchase agreement to that buyer"
```

3. **Check status:**
```
"Check the status of that contract"
```

4. **List all:**
```
"Show me all contracts"
```

---

## Automatic Notifications

When contracts are **fully signed**, the system automatically sends a notification to the TV display:

```
✅ Contract Fully Signed!
All parties signed Purchase Agreement for 123 Main Street
```

This happens via:
- DocuSeal webhook
- Backend status refresh
- Notification service
- WebSocket broadcast

---

## Best Practices

✅ **DO:**
- Add contacts before sending contracts
- Check status regularly during signing process
- Use descriptive contract names
- Link contracts to properties

❌ **DON'T:**
- Send contracts to contacts not linked to properties
- Forget to check DocuSeal template IDs
- Send duplicate contracts unnecessarily

---

## Future Enhancements

🔮 **Planned:**
- Multi-party contracts via MCP
- Contract templates management
- Bulk contract sending
- Contract reminders ("remind signer if not signed in 24h")
- Contract archiving
- Custom email messages

---

## Complete Tool List

All 12 MCP tools are now available:

```
1.  list_properties              - List properties
2.  get_property                 - Get property details
3.  create_property              - Create new property
4.  delete_property              - Delete property
5.  enrich_property              - Add Zillow data
6.  skip_trace_property          - Find owner info
7.  add_contact                  - Add contact to property
8.  send_notification            - Send TV notification
9.  list_notifications           - View notification history
10. send_contract                - Send DocuSeal contract ✨
11. check_contract_status        - Check signing status ✨
12. list_contracts               - List all contracts ✨
13. list_contracts_voice         - 🎤 Voice-optimized contract list
14. check_contract_status_voice  - 🎤 Voice-optimized status check
```

---

## 🎤 Voice Assistant Tools (NEW)

### list_contracts_voice

**Purpose:** List contracts with voice-optimized natural language response.

**Specifically designed for:**
- Siri
- Alexa
- Google Assistant
- Any text-to-speech system

**Usage Examples:**
```
"Show me contracts for one forty one troop"
"Um list contracts for twenty three main street"
"Contracts for oak ave"
```

**Response Format:**
```
🎤 VOICE RESPONSE:
Found 2 contracts for 141 Throop Avenue. Status breakdown: 1 in progress, 1 completed.

📊 DETAILS:
Count: 2
Address: 141 Throop Avenue

📝 CONTRACTS:
  • Purchase Agreement (in_progress)
  • Seller Disclosure (completed)
```

**Key Features:**
- ✅ Handles phonetic variations ("troop" → "throop")
- ✅ Converts spoken numbers ("one forty one" → "141")
- ✅ Removes filler words ("um", "like", "show me")
- ✅ Natural language response perfect for TTS
- ✅ Status summary in plain English

---

### check_contract_status_voice

**Purpose:** Check contract status with voice-optimized response.

**Usage Examples:**
```
"Check contract status for one forty one throop"
"What's the status for troop avenue"
"Um has the contract for main street been signed"
```

**Response Format:**
```
🎤 VOICE RESPONSE:
Contract number 23, the Purchase Agreement, is in progress. 1 of 2 signers have completed. Still waiting on Michael Chen.

📊 DETAILS:
Contract ID: 23
Status: in progress
```

**Key Features:**
- ✅ Natural sentence structure for TTS
- ✅ Lists pending signers by name
- ✅ Clear status updates
- ✅ All voice optimizations applied
- ✅ Conversational response style

---

## Voice Tool Examples

### Example 1: Voice Assistant Integration

**User speaks to Alexa:**
```
"Alexa, ask Claude to show contracts for one forty one troop"
```

**Alexa transcribes:**
```
"show contracts for one forty one troop"
```

**Claude uses:** `list_contracts_voice`

**Claude responds:**
```
Found 2 contracts for 141 Throop Avenue. Status breakdown: 1 in progress, 1 completed.
```

**Alexa speaks back:**
```
"Found two contracts for one forty one Throop Avenue. Status breakdown: one in progress, one completed."
```

---

### Example 2: Contract Status Check

**User speaks to Siri:**
```
"Hey Siri, ask Claude if the contract for main street has been signed"
```

**Siri transcribes:**
```
"check if contract for main street has been signed"
```

**Claude uses:** `check_contract_status_voice`

**Claude responds:**
```
Contract number 45, the Purchase Agreement, is completed. All signers have completed!
```

**Siri speaks back:**
```
"Contract number forty five, the Purchase Agreement, is completed. All signers have completed!"
```

---

## When to Use Voice Tools vs Regular Tools

### Use Regular Tools When:
- Using Claude Desktop directly (typing)
- Need detailed JSON output
- Building integrations
- Debugging

### Use Voice Tools When:
- Input is from voice assistant (Siri, Alexa, Google)
- Output will be spoken via TTS
- Need natural language summaries
- Want conversational responses

---

**🎉 Contract tools are now available in Claude Desktop!**

Try it:
```
"Create a property at 789 Main St for $600K, add John Smith as the buyer (john@email.com, 555-1234), and send him a purchase agreement!"
```

**🎤 Or try the voice tools:**
```
"Show me contracts for one forty one throop using voice mode"
```
