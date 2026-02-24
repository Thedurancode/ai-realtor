# DocuSeal Integration Guide

## Overview

Full DocuSeal API integration for sending contracts to contacts and tracking their signing status.

## Setup

### 1. Get DocuSeal API Key

1. Sign up at https://www.docuseal.com
2. Get your API key from Settings → API
3. Create document templates in DocuSeal
4. Note your template IDs

### 2. Configure Environment

Add to your `.env` file:

```env
DOCUSEAL_API_KEY=your_api_key_here
DOCUSEAL_API_URL=https://api.docuseal.com
```

### 3. Create Database Tables

The server will automatically create the new contract tables with contact associations when it starts.

If you have an existing database, you'll need to recreate it or manually add:
- `contracts.contact_id` column (foreign key to contacts)

## API Endpoints

### Voice-Optimized (NEW!)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/contracts/voice/send` | POST | **Send contract using natural language** |

### Core Contract Operations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/contracts/` | POST | Create a new contract |
| `/contracts/{id}` | GET | Get contract details |
| `/contracts/{id}` | PATCH | Update contract |
| `/contracts/{id}` | DELETE | Delete contract |
| `/contracts/property/{property_id}` | GET | List contracts for property |
| `/contracts/contact/{contact_id}` | GET | List contracts for contact |

### DocuSeal Operations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/contracts/{id}/send` | POST | Send contract to email address |
| `/contracts/{id}/send-to-contact` | POST | **Send contract to existing contact** |
| `/contracts/{id}/status` | GET | **Check contract status** |
| `/contracts/{id}/cancel` | POST | Cancel/archive contract |
| `/contracts/webhook/docuseal` | POST | Webhook for status updates |

## Usage Examples

### 🎤 Voice Command (Easiest Way!)

```bash
curl -X POST http://localhost:8000/contracts/voice/send \
  -H "Content-Type: application/json" \
  -d '{
    "address_query": "141 throop",
    "contract_name": "property agreement",
    "contact_role": "lawyer"
  }'
```

**What it does:**
1. ✅ Finds property matching "141 throop"
2. ✅ Finds the lawyer contact for that property
3. ✅ Finds or creates a "property agreement" contract
4. ✅ Sends it to the lawyer via DocuSeal
5. ✅ Returns voice confirmation

**Response:**
```json
{
  "contract": { ... },
  "voice_confirmation": "Done! I've sent the Property Agreement to John Lawyer (lawyer) at john@lawfirm.com for 123 Main Street."
}
```

**More examples:**
```bash
# Send purchase agreement to buyer
{
  "address_query": "main street",
  "contract_name": "purchase agreement",
  "contact_role": "buyer"
}

# Send inspection waiver to inspector
{
  "address_query": "oak",
  "contract_name": "inspection waiver",
  "contact_role": "inspector"
}

# Send listing agreement to seller
{
  "address_query": "throop",
  "contract_name": "listing agreement",
  "contact_role": "seller"
}
```

### 1. Create Contract Linked to Contact

```bash
curl -X POST http://localhost:8000/contracts/ \
  -H "Content-Type: application/json" \
  -d '{
    "property_id": 1,
    "contact_id": 3,
    "name": "Purchase Agreement",
    "description": "Standard purchase agreement",
    "docuseal_template_id": "template_abc123"
  }'
```

### 2. Send Contract to Contact

```bash
curl -X POST http://localhost:8000/contracts/1/send-to-contact \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": 3,
    "recipient_role": "Buyer",
    "message": "Please review and sign the purchase agreement"
  }'
```

This will:
- ✅ Link the contract to the contact
- ✅ Send email via DocuSeal to contact's email
- ✅ Store DocuSeal submission ID
- ✅ Update contract status to "sent"

### 3. Check Contract Status

```bash
# Get latest status from DocuSeal
curl http://localhost:8000/contracts/1/status?refresh=true

# Get cached status (no API call)
curl http://localhost:8000/contracts/1/status?refresh=false
```

Response:
```json
{
  "contract_id": 1,
  "status": "in_progress",
  "docuseal_status": "pending",
  "submission_id": "12345",
  "submitters": [
    {
      "email": "buyer@example.com",
      "name": "John Buyer",
      "status": "pending",
      "role": "Buyer"
    }
  ],
  "created_at": "2026-02-04T14:00:00",
  "completed_at": null
}
```

### 4. List Contracts by Status

```bash
# All sent contracts for a property
curl "http://localhost:8000/contracts/property/1?status=sent"

# All contracts for a contact
curl "http://localhost:8000/contracts/contact/3"
```

### 5. Cancel Contract

```bash
curl -X POST http://localhost:8000/contracts/1/cancel
```

This will archive the submission in DocuSeal.

## Webhook Setup

### Configure in DocuSeal

1. Go to DocuSeal Settings → Webhooks
2. Add webhook URL: `https://your-domain.com/contracts/webhook/docuseal`
3. Select events: "Submission Completed", "Submission Updated"

### What It Does

The webhook automatically updates contract status when:
- ✅ Contact signs the document → Status: "completed"
- ✅ Document is in progress → Status: "in_progress"
- ✅ Document is archived → Status: "cancelled"

## Contract Status Flow

```
DRAFT → SENT → IN_PROGRESS → COMPLETED
          ↓
      CANCELLED
```

- **DRAFT**: Contract created, not sent
- **SENT**: Sent via DocuSeal, awaiting signature
- **IN_PROGRESS**: Recipient has opened/started signing
- **COMPLETED**: Fully signed by all parties
- **CANCELLED**: Cancelled or archived

## Features

### ✅ Contact Integration
- Link contracts to specific contacts
- Automatically use contact's email and name
- Validate contact belongs to same property

### ✅ Real-time Status Tracking
- Check signing status anytime
- Automatic webhook updates
- See which submitters have signed

### ✅ Error Handling
- Validates DocuSeal template ID exists
- Validates contact has email address
- Catches and reports DocuSeal API errors

### ✅ Audit Trail
- `sent_at` timestamp when contract is sent
- `completed_at` timestamp when fully signed
- Stores DocuSeal submission URL for viewing

## DocuSeal Client Methods

The `DocuSealClient` service provides:

```python
# Create and send submission
await docuseal_client.create_submission(
    template_id="template_123",
    submitters=[{"email": "buyer@example.com", "role": "Buyer"}],
    send_email=True,
    message="Please sign"
)

# Get submission status
await docuseal_client.get_submission(submission_id)

# List all submissions
await docuseal_client.list_submissions(template_id="template_123")

# Cancel submission
await docuseal_client.archive_submission(submission_id)

# Get available templates
await docuseal_client.get_templates()
```

## Testing Without DocuSeal

If you don't have a DocuSeal API key yet, the endpoints will return errors. To test:

1. Create contracts with `docuseal_template_id: null`
2. Manually update status using PATCH `/contracts/{id}`
3. Add API key later to enable real sending

## Next Steps

1. Get DocuSeal API key and add to `.env`
2. Create document templates in DocuSeal
3. Create a contract with template ID
4. Send to a contact
5. Check status
6. Set up webhook for automatic updates

## Troubleshooting

**Error: "DocuSeal API error"**
- Check your API key is correct in `.env`
- Verify template ID exists in your DocuSeal account

**Error: "Contact must have email"**
- Update contact record to include email address

**Webhook not working**
- Verify webhook URL is publicly accessible
- Check DocuSeal webhook configuration
- Test with a tool like ngrok for local development
