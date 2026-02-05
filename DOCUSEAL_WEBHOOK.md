# DocuSeal Webhook Integration

## Overview

The AI Realtor platform integrates with DocuSeal webhooks to automatically update contract status and regenerate property recaps when contracts are signed. This enables real-time synchronization between DocuSeal and the AI agent knowledge base.

## How It Works

1. **User signs contract in DocuSeal** → DocuSeal sends webhook event
2. **API receives webhook** → Verifies signature and processes event
3. **Contract status updated** → Database record updated (PENDING → COMPLETED)
4. **Property recap regenerated** → AI knowledge updated with new contract status
5. **Agent is informed** → Voice agent knows contract is signed

## Supported Events

The webhook endpoint (`POST /webhooks/docuseal`) handles the following DocuSeal events:

- `submission.created` - New submission created
- `submission.signed` - Individual signer completed their part
- `submission.completed` - All signers completed (contract fully executed)
- `submission.archived` - Submission archived
- `submission.viewed` - Submission viewed by signer

## Setup Instructions

### 1. Set Webhook Secret

For security, set the webhook secret environment variable:

```bash
# Local development
export DOCUSEAL_WEBHOOK_SECRET=your-secret-key-here

# Production (Fly.io)
fly secrets set DOCUSEAL_WEBHOOK_SECRET=your-secret-key-here --app ai-realtor
```

### 2. Configure DocuSeal

1. Log in to your DocuSeal account
2. Go to Settings → Webhooks
3. Add new webhook:
   - **URL**: `https://ai-realtor.fly.dev/webhooks/docuseal`
   - **Secret**: Same value as `DOCUSEAL_WEBHOOK_SECRET`
   - **Events**: Select the events you want to receive:
     - ✅ submission.created
     - ✅ submission.signed
     - ✅ submission.completed
     - ✅ submission.archived

### 3. Test Configuration

Use the MCP tool to verify webhook setup:

```
test_webhook_configuration()
```

This returns:
- Webhook URL
- Whether secret is configured
- Supported events
- Setup instructions

## How Contracts Are Matched

The webhook matches DocuSeal submissions to contracts using:

1. **Primary**: `docuseal_submission_id` - Exact match on submission ID
2. **Fallback**: `docuseal_template_id` - If no submission match, try template ID

When a match is found, the contract status is updated based on the DocuSeal event status:

| DocuSeal Status | Contract Status |
|-----------------|----------------|
| `pending` | `PENDING_SIGNATURE` |
| `completed` | `COMPLETED` |
| `archived` | `ARCHIVED` |

## Property Recap Regeneration

When a contract status changes, the property recap is automatically regenerated with:

```python
trigger=f"contract_signed:{contract.name}"
```

This ensures the AI agent always has up-to-date knowledge about contract status.

## API Endpoints

### POST /webhooks/docuseal

Receive DocuSeal webhook events.

**Headers:**
- `X-DocuSeal-Signature` - HMAC-SHA256 signature (format: `sha256=<hex_digest>`)

**Request Body:**
```json
{
  "event_type": "submission.completed",
  "data": {
    "id": "submission_123",
    "template": {
      "id": "template_456"
    },
    "status": "completed"
  }
}
```

**Response:**
```json
{
  "status": "received",
  "event_type": "submission.completed",
  "message": "Webhook processed successfully"
}
```

**Status Codes:**
- `200` - Webhook processed successfully
- `401` - Invalid signature
- `400` - Invalid JSON payload

### GET /webhooks/docuseal/test

Test webhook configuration and get setup instructions.

**Response:**
```json
{
  "webhook_url": "/webhooks/docuseal",
  "webhook_secret_configured": true,
  "supported_events": [
    "submission.created",
    "submission.completed",
    "submission.signed",
    "submission.archived",
    "submission.viewed"
  ],
  "instructions": {
    "1": "Set DOCUSEAL_WEBHOOK_SECRET environment variable",
    "2": "Configure webhook URL in DocuSeal: https://your-domain.com/webhooks/docuseal",
    "3": "Select events to subscribe to in DocuSeal settings",
    "4": "DocuSeal will send X-DocuSeal-Signature header for verification"
  }
}
```

## MCP Tools

### test_webhook_configuration

**Description:** Check DocuSeal webhook configuration status and get setup instructions.

**Usage:**
```
test_webhook_configuration()
```

**Returns:**
- Webhook URL
- Secret configuration status
- Supported events
- Step-by-step setup guide

## Security

### Signature Verification

The webhook endpoint verifies all incoming requests using HMAC-SHA256 signature verification:

1. DocuSeal sends `X-DocuSeal-Signature` header
2. API calculates expected signature using `DOCUSEAL_WEBHOOK_SECRET`
3. Signatures are compared using constant-time comparison
4. Request rejected if signatures don't match

### Environment Variables

Required environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `DOCUSEAL_WEBHOOK_SECRET` | Yes | Secret key for webhook signature verification |

## Background Processing

Webhook events are processed in the background using FastAPI's `BackgroundTasks`:

```python
background_tasks.add_task(process_contract_signed, db, event_data)
```

This ensures:
- Fast webhook response (200 OK returned immediately)
- DocuSeal doesn't timeout waiting for processing
- Property recap regeneration happens asynchronously

## Example Flow

### User Signs Purchase Agreement

1. **DocuSeal sends webhook:**
```json
{
  "event_type": "submission.completed",
  "data": {
    "id": "sub_abc123",
    "template": {
      "id": "tmpl_xyz789"
    },
    "status": "completed"
  }
}
```

2. **API processes:**
   - Verifies signature
   - Finds contract with `docuseal_submission_id = "sub_abc123"`
   - Updates status: `PENDING_SIGNATURE` → `COMPLETED`
   - Sets `completed_at` timestamp

3. **Property recap regenerated:**
   - AI generates new summary including completed contract
   - Trigger: `"contract_signed:Purchase Agreement"`
   - Version incremented

4. **AI agent knows:**
   - "The Purchase Agreement was just signed and completed"
   - Can inform other contacts via phone call
   - Can check if property is ready to close

## Troubleshooting

### Webhook Not Receiving Events

1. Check webhook URL in DocuSeal settings
2. Verify webhook secret matches on both sides
3. Check DocuSeal webhook logs for errors
4. Test with `curl`:

```bash
curl -X POST https://ai-realtor.fly.dev/webhooks/docuseal \
  -H "Content-Type: application/json" \
  -H "X-DocuSeal-Signature: sha256=test" \
  -d '{
    "event_type": "submission.completed",
    "data": {
      "id": "test_123",
      "template": {"id": "tmpl_456"},
      "status": "completed"
    }
  }'
```

### Contract Not Updating

1. Verify contract has `docuseal_submission_id` or `docuseal_template_id` set
2. Check API logs for "Contract not found" warnings
3. Ensure DocuSeal IDs match database values

### Signature Verification Failing

1. Verify `DOCUSEAL_WEBHOOK_SECRET` is set correctly
2. Check secret matches in DocuSeal webhook settings
3. Look for "Invalid signature" errors in logs

## Implementation Files

- `app/routers/webhooks.py` - Webhook endpoint and signature verification
- `app/models/contract.py` - Contract model with new statuses (PENDING_SIGNATURE, ARCHIVED)
- `mcp_server/property_mcp.py` - MCP tool for webhook testing
- `app/services/property_recap_service.py` - Recap regeneration

## Future Enhancements

Potential improvements:

1. **Webhook event log** - Store all webhook events for debugging
2. **Retry mechanism** - Retry failed recap regenerations
3. **Notification on sign** - Send SMS/email when contract signed
4. **Activity feed integration** - Show "Contract signed" events in UI
5. **Multiple signer tracking** - Track individual signer progress
6. **Webhook health monitoring** - Alert if webhooks stop arriving

## Related Documentation

- [Context-Aware Contracts](./CONTEXT_AWARE_CONTRACTS.md) - Contract template system
- [AI Recaps & Phone Calls](./AI_RECAP_PHONE_CALLS.md) - Property recap generation
