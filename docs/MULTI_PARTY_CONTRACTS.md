# Multi-Party Contract Signing

This system supports contracts that require multiple people to sign in specific roles with specific signing orders.

## Overview

Multi-party contracts allow documents to be signed by:
- **Owner/Seller** - Property owner
- **Lawyer/Attorney** - Legal counsel
- **Agent** - Real estate agent
- **Buyer** - Purchaser
- **Contractor** - General contractor
- And any other custom roles

## Key Features

✅ **Individual Tracking** - Each signer is tracked separately in the database
✅ **Sequential or Parallel** - Control signing order (sequential = one at a time, parallel = all at once)
✅ **Role-Based** - Each signer has a specific role in DocuSeal (Owner, Lawyer, Agent, etc.)
✅ **Status Tracking** - Track each signer's status: pending, opened, completed, declined
✅ **Voice Commands** - Natural language support for sending multi-party contracts
✅ **Webhook Updates** - Automatic status updates when signers take action

## Database Structure

### ContractSubmitter Model

Each person who needs to sign a contract gets their own `ContractSubmitter` record:

```python
class ContractSubmitter:
    id: int
    contract_id: int
    contact_id: int | None  # Optional link to Contact

    # Signer details
    name: str
    email: str
    role: str  # DocuSeal role: "Owner", "Lawyer", "Agent", etc.

    # Signing order
    signing_order: int  # 1, 2, 3... for sequential signing

    # Status tracking
    status: SubmitterStatus  # PENDING, OPENED, COMPLETED, DECLINED
    sent_at: datetime | None
    opened_at: datetime | None
    completed_at: datetime | None

    # DocuSeal integration
    docuseal_submitter_id: str | None
    docuseal_submitter_slug: str | None
```

## API Endpoints

### 1. Send Multi-Party Contract (Standard)

Send a contract to multiple people with specific roles and signing order.

**POST** `/contracts/{contract_id}/send-multi-party`

```json
{
  "submitters": [
    {
      "contact_id": 1,           // Optional: link to existing contact
      "name": "John Smith",
      "email": "john@email.com",
      "role": "Owner",           // DocuSeal role
      "signing_order": 1         // 1 = signs first
    },
    {
      "contact_id": 2,
      "name": "Emily Chen",
      "email": "emily@lawfirm.com",
      "role": "Lawyer",
      "signing_order": 2         // 2 = signs second
    },
    {
      "name": "Sarah Johnson",
      "email": "sarah@realty.com",
      "role": "Agent",
      "signing_order": 3         // 3 = signs third
    }
  ],
  "order": "preserved",          // "preserved" = sequential, "random" = parallel
  "message": "Please review and sign this purchase agreement."
}
```

**Response:**

```json
{
  "contract_id": 1,
  "submitters": [
    {
      "id": 1,
      "contract_id": 1,
      "contact_id": 1,
      "name": "John Smith",
      "email": "john@email.com",
      "role": "Owner",
      "signing_order": 1,
      "status": "pending",
      "sent_at": "2026-02-04T10:00:00Z",
      "opened_at": null,
      "completed_at": null,
      "created_at": "2026-02-04T10:00:00Z"
    },
    // ... more submitters
  ],
  "voice_confirmation": "Done! I've sent the Purchase Agreement to John Smith, Emily Chen, and Sarah Johnson for 456 Park Avenue. They will sign sequentially.",
  "docuseal_url": "https://docuseal.com/s/abc123"
}
```

### 2. Send Multi-Party Contract (Voice)

Voice-optimized endpoint for natural language commands.

**POST** `/contracts/voice/send-multi-party`

```json
{
  "address_query": "456 park",              // Partial address
  "contract_name": "purchase agreement",    // Partial contract name
  "contact_roles": ["owner", "lawyer", "agent"],  // Roles to send to
  "order": "preserved",                     // "preserved" or "random"
  "message": "Please sign ASAP."            // Optional
}
```

**Example Voice Commands:**
- "Send the purchase agreement to the owner, lawyer, and agent for 456 Park"
- "Send the listing agreement to the seller and lawyer for 141 Throop"
- "Send the contract to the buyer, agent, and attorney for Park Avenue"

**How It Works:**
1. Finds property by partial address match (`456 park` → `456 Park Avenue`)
2. Finds contract by partial name match (`purchase agreement` → `Purchase Agreement`)
3. Looks up each contact by role (owner → finds seller contact)
4. Special handling for "agent" - uses property's assigned agent
5. Creates submitters in order and sends via DocuSeal

## Signing Order

### Sequential Signing (order="preserved")

Signers must sign **in order**. Second person can't sign until first person completes.

```
Owner (1) → Lawyer (2) → Agent (3)
```

Use this when:
- Legal requirements dictate signing order
- You want approval workflow (owner must approve before lawyer reviews)
- Each party needs to see previous signatures

### Parallel Signing (order="random")

All signers can sign **simultaneously** in any order.

```
Owner (1) ←
Lawyer (2) ← All at once
Agent (3) ←
```

Use this when:
- No specific order required
- Faster turnaround needed
- All parties are equally authorized

## Role Mapping

When using voice commands, roles are automatically mapped:

| Voice Input | Contact Role | DocuSeal Role |
|------------|--------------|---------------|
| "owner" | SELLER | Owner |
| "seller" | SELLER | Seller |
| "buyer" | BUYER | Buyer |
| "lawyer" | LAWYER | Lawyer |
| "attorney" | ATTORNEY | Attorney |
| "agent" | (property.agent) | Agent |
| "contractor" | CONTRACTOR | Contractor |
| "inspector" | INSPECTOR | Inspector |

## Status Tracking

### Submitter Status Flow

```
PENDING → OPENED → COMPLETED
           ↓
        DECLINED
```

- **PENDING**: Email sent, awaiting action
- **OPENED**: Recipient opened the document
- **COMPLETED**: Recipient signed the document
- **DECLINED**: Recipient declined to sign

### Contract Status Flow

The overall contract status reflects progress:

```
DRAFT → SENT → IN_PROGRESS → COMPLETED
                    ↓
                CANCELLED
```

- **DRAFT**: Not sent yet
- **SENT**: Sent to first signer(s)
- **IN_PROGRESS**: At least one person has opened/signed
- **COMPLETED**: All signers have completed
- **CANCELLED**: Contract cancelled/archived

## Webhook Integration

The webhook endpoint automatically updates both contract and individual submitter statuses:

**POST** `/contracts/webhook/docuseal`

```json
{
  "id": "12345",
  "status": "pending",
  "submitters": [
    {
      "id": "sub_abc",
      "status": "completed",
      "completed_at": "2026-02-04T10:30:00Z"
    },
    {
      "id": "sub_def",
      "status": "opened",
      "opened_at": "2026-02-04T10:35:00Z"
    },
    {
      "id": "sub_ghi",
      "status": "pending"
    }
  ]
}
```

The webhook will:
1. Update overall contract status
2. Update each individual submitter's status
3. Set timestamps (opened_at, completed_at) automatically

## Example Workflow

### Scenario: Purchase Agreement

A purchase agreement needs three signatures in order:
1. **Owner** signs first (to authorize sale)
2. **Lawyer** reviews and signs second (legal approval)
3. **Agent** countersigns third (commission agreement)

#### Step 1: Create the contract

```bash
POST /contracts/
{
  "property_id": 1,
  "name": "Purchase Agreement",
  "docuseal_template_id": "tmpl_abc123"
}
```

#### Step 2: Send to all parties

```bash
POST /contracts/1/send-multi-party
{
  "submitters": [
    {
      "contact_id": 10,
      "name": "John Smith",
      "email": "john@email.com",
      "role": "Owner",
      "signing_order": 1
    },
    {
      "contact_id": 15,
      "name": "Emily Chen",
      "email": "emily@lawfirm.com",
      "role": "Lawyer",
      "signing_order": 2
    },
    {
      "name": "Sarah Johnson",
      "email": "sarah@realty.com",
      "role": "Agent",
      "signing_order": 3
    }
  ],
  "order": "preserved"
}
```

#### Step 3: Track progress

Each signer's status is tracked:
- John (Owner): `OPENED` - viewing document
- Emily (Lawyer): `PENDING` - can't access yet (sequential)
- Sarah (Agent): `PENDING` - can't access yet (sequential)

After John signs:
- John (Owner): `COMPLETED` ✅
- Emily (Lawyer): `OPENED` - now can access
- Sarah (Agent): `PENDING` - still waiting

After Emily signs:
- John (Owner): `COMPLETED` ✅
- Emily (Lawyer): `COMPLETED` ✅
- Sarah (Agent): `OPENED` - now can access

After Sarah signs:
- John (Owner): `COMPLETED` ✅
- Emily (Lawyer): `COMPLETED` ✅
- Sarah (Agent): `COMPLETED` ✅
- Contract status: `COMPLETED` 🎉

## Voice Command Examples

### Example 1: Simple multi-party

```
"Send the purchase agreement to the owner, lawyer, and agent for 456 Park Avenue"
```

System will:
- Find property matching "456 Park"
- Find contract matching "purchase agreement"
- Find owner (seller contact)
- Find lawyer contact
- Use property's agent
- Send in order: owner (1), lawyer (2), agent (3)

### Example 2: Two parties

```
"Send the listing agreement to the seller and lawyer for 141 Throop"
```

System will:
- Find property matching "141 Throop"
- Find contract matching "listing agreement"
- Find seller contact
- Find lawyer contact
- Send in order: seller (1), lawyer (2)

### Example 3: Custom order

For parallel signing (all at once):

```json
{
  "address_query": "park avenue",
  "contract_name": "disclosure",
  "contact_roles": ["buyer", "seller", "agent"],
  "order": "random"
}
```

All three parties can sign simultaneously.

## Testing

Run the included test script to verify multi-party functionality:

```bash
python3 tests/manual/simple_multi_party_test.py
```

This will:
1. Create test property and contacts
2. Create a test contract
3. Send multi-party contract via standard endpoint
4. Test voice endpoint
5. Show expected behavior (will get DocuSeal 401 error without API key)

## Configuration

In `.env`:

```env
DOCUSEAL_API_KEY=your_key_here
DOCUSEAL_API_URL=https://api.docuseal.com
```

## Best Practices

1. **Use sequential signing** when order matters legally
2. **Link to contacts** via `contact_id` when possible (better tracking)
3. **Set clear roles** that match your DocuSeal template roles
4. **Configure webhooks** for automatic status updates
5. **Use voice commands** for faster workflow during calls/meetings

## Troubleshooting

### Issue: "Role not found for property"
**Solution**: Make sure contacts exist with the requested roles. For "agent", the property must have an assigned agent.

### Issue: "Contract doesn't have DocuSeal template ID"
**Solution**: Set `docuseal_template_id` on the contract before sending.

### Issue: Webhook not updating statuses
**Solution**: Verify webhook URL is configured in DocuSeal settings: `https://your-domain.com/contracts/webhook/docuseal`

### Issue: Voice endpoint matches wrong route
**Solution**: This was fixed by reordering routes. `/voice/send-multi-party` now comes before `/{contract_id}/send-multi-party`.

## Next Steps

- Add email templates for custom notifications
- Support for conditional signing (e.g., buyer signs only if inspection passes)
- Reminders for pending signers
- Analytics dashboard for signing completion rates
