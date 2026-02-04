# DocuSeal Webhook Setup Guide

This guide explains how to configure DocuSeal webhooks to automatically sync contract and signer statuses to your database.

## What Are Webhooks?

Webhooks allow DocuSeal to notify your system in real-time when events occur, such as:
- A signer opens a document
- A signer completes their signature
- All signatures are collected
- A signer declines to sign
- A submission expires

## Supported Events

### Form Events (Individual Signers)

| Event | Description | Database Update |
|-------|-------------|-----------------|
| `form.viewed` | Signer viewed the document | No status change (informational only) |
| `form.started` | Signer opened and started filling | `PENDING` → `OPENED` |
| `form.completed` | Signer completed their signature | `OPENED` → `COMPLETED` |
| `form.declined` | Signer declined to sign | Any → `DECLINED` + contract → `CANCELLED` |

### Submission Events (Overall Contract)

| Event | Description | Database Update |
|-------|-------------|-----------------|
| `submission.created` | Contract sent to signers | `DRAFT` → `SENT` |
| `submission.completed` | All signers completed | Any → `COMPLETED` |
| `submission.expired` | Submission deadline passed | Any → `EXPIRED` |
| `submission.archived` | Submission cancelled | Any → `CANCELLED` |

## Setup Instructions

### Step 1: Get Your Webhook URL

Your webhook URL is:

```
https://your-domain.com/contracts/webhook/docuseal
```

**For local development with ngrok:**

```bash
# Install ngrok if you haven't
brew install ngrok

# Start your server
uvicorn app.main:app --reload --port 8000

# In another terminal, start ngrok
ngrok http 8000

# Use the ngrok URL
https://abc123.ngrok.io/contracts/webhook/docuseal
```

### Step 2: Configure in DocuSeal

1. **Log in to DocuSeal** at https://docuseal.com
2. **Go to Settings** → **Webhooks**
3. **Enter your webhook URL** in the "Webhook URL" field
4. **Check ALL event boxes**:
   - ✅ form.viewed
   - ✅ form.started
   - ✅ form.completed
   - ✅ form.declined
   - ✅ submission.created
   - ✅ submission.completed
   - ✅ submission.expired
   - ✅ submission.archived
5. **Click SAVE**

### Step 3: Test the Webhook

Use the included test script:

```bash
python test_webhook.py
```

This will:
- Create test contracts
- Simulate all webhook events
- Show you what each event does
- Verify database updates

### Step 4: Test with Real DocuSeal

1. Create a contract with a DocuSeal template
2. Send it using the multi-party endpoint
3. DocuSeal will send webhooks as signers take action
4. Check your database to see automatic updates

## Webhook Payload Examples

### form.completed Event

```json
{
  "event_type": "form.completed",
  "data": {
    "submission_id": "sub_abc123",
    "submitter_id": "submitter_xyz789",
    "submitter": {
      "email": "john@example.com",
      "name": "John Smith"
    },
    "completed_at": "2026-02-04T12:30:00Z"
  }
}
```

**What happens:**
- Finds ContractSubmitter by `docuseal_submitter_id`
- Updates status to `COMPLETED`
- Sets `completed_at` timestamp
- Checks if all submitters are done
- If yes, updates Contract status to `COMPLETED`

### submission.completed Event

```json
{
  "event_type": "submission.completed",
  "data": {
    "id": "sub_abc123",
    "status": "completed",
    "completed_at": "2026-02-04T12:35:00Z"
  }
}
```

**What happens:**
- Finds Contract by `docuseal_submission_id`
- Updates contract status to `COMPLETED`
- Sets `completed_at` timestamp
- Marks all submitters as `COMPLETED` (if not already)

### form.declined Event

```json
{
  "event_type": "form.declined",
  "data": {
    "submission_id": "sub_abc123",
    "submitter_id": "submitter_xyz789",
    "submitter": {
      "email": "jane@example.com",
      "name": "Jane Doe"
    }
  }
}
```

**What happens:**
- Finds ContractSubmitter
- Updates submitter status to `DECLINED`
- Updates Contract status to `CANCELLED`
- No one else can sign (contract is cancelled)

## Status Flow Diagrams

### Individual Submitter Status Flow

```
PENDING
   ↓ (form.started)
OPENED
   ↓ (form.completed)
COMPLETED
```

Or:

```
PENDING → DECLINED (form.declined)
OPENED → DECLINED (form.declined)
```

### Overall Contract Status Flow

```
DRAFT
   ↓ (submission.created)
SENT
   ↓ (form.started by any signer)
IN_PROGRESS
   ↓ (form.completed by all signers)
COMPLETED
```

Or:

```
Any status → CANCELLED (form.declined or submission.archived)
Any status → EXPIRED (submission.expired)
```

## Monitoring Webhooks

### View Webhook Logs

Check your server logs to see incoming webhooks:

```bash
# If using uvicorn with --reload
# Logs appear in terminal automatically

# Look for lines like:
INFO: POST /contracts/webhook/docuseal HTTP/1.1 200 OK
```

### Webhook Response Format

Your endpoint returns:

```json
{
  "status": "success",
  "event": "form.completed",
  "contract_id": 123,
  "submitter": "John Smith",
  "submitter_status": "completed"
}
```

### Error Handling

If webhook fails:

```json
{
  "status": "error",
  "message": "Error description here"
}
```

DocuSeal will retry failed webhooks automatically.

## Testing Checklist

- [ ] Webhook URL configured in DocuSeal
- [ ] All events enabled (8 checkboxes checked)
- [ ] Test script runs successfully: `python test_webhook.py`
- [ ] Created real contract with DocuSeal template
- [ ] Sent contract to test email address
- [ ] Opened document (should trigger `form.started`)
- [ ] Completed signature (should trigger `form.completed`)
- [ ] Verified database updated:
  - [ ] Submitter status changed
  - [ ] Timestamps set
  - [ ] Contract status updated

## Troubleshooting

### Webhook not receiving events

1. **Check URL is publicly accessible**
   - Use ngrok for local development
   - Ensure no firewall blocking
   - Test with `curl -X POST your-webhook-url`

2. **Verify webhook URL in DocuSeal**
   - Settings → Webhooks
   - URL should end with `/contracts/webhook/docuseal`
   - All event checkboxes should be checked

3. **Check DocuSeal webhook logs**
   - DocuSeal dashboard shows webhook delivery status
   - Look for failed deliveries

### Database not updating

1. **Check submission IDs match**
   ```sql
   SELECT id, name, docuseal_submission_id, status
   FROM contracts
   WHERE docuseal_submission_id = 'your_submission_id';
   ```

2. **Check submitter IDs match**
   ```sql
   SELECT id, name, docuseal_submitter_id, status
   FROM contract_submitters
   WHERE docuseal_submitter_id = 'your_submitter_id';
   ```

3. **Check server logs for errors**
   - Look for exception messages
   - Verify database connection

### Status not updating correctly

1. **Verify webhook payload format**
   - Add debug logging to see exact payload
   - Check `event_type` field is present

2. **Check status mappings**
   - Review status enums match DocuSeal's values
   - Ensure case-insensitive matching (`.lower()`)

## Security Considerations

### For Production

1. **Use HTTPS** - Never use HTTP in production
2. **Validate webhook signature** - DocuSeal signs webhooks (optional)
3. **Rate limiting** - Protect against webhook flooding
4. **Authentication** - Consider adding webhook secret token

### Example: Adding Webhook Secret

In DocuSeal, you can set a secret token. Then verify it:

```python
@router.post("/webhook/docuseal", status_code=200)
async def docuseal_webhook(
    payload: dict,
    x_docuseal_signature: str = Header(None),
    db: Session = Depends(get_db),
):
    # Verify signature
    expected_signature = calculate_signature(payload)
    if x_docuseal_signature != expected_signature:
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Process webhook...
```

## Benefits of Webhook Integration

✅ **Real-time updates** - Status changes instantly
✅ **No polling** - Don't need to check DocuSeal API repeatedly
✅ **Automatic tracking** - Users always see current status
✅ **Multi-party support** - Track each signer individually
✅ **Audit trail** - Timestamps for all events
✅ **Error handling** - Know if someone declines or submission expires

## What Gets Updated

### When Signer Opens Document (form.started)

```
ContractSubmitter:
  status: PENDING → OPENED ✅
  opened_at: <timestamp> ✅

Contract:
  status: SENT → IN_PROGRESS ✅
```

### When Signer Completes (form.completed)

```
ContractSubmitter:
  status: OPENED → COMPLETED ✅
  completed_at: <timestamp> ✅

Contract:
  status: IN_PROGRESS → COMPLETED ✅ (if all done)
  completed_at: <timestamp> ✅ (if all done)
```

### When All Done (submission.completed)

```
All ContractSubmitters:
  status: → COMPLETED ✅
  completed_at: <timestamp> ✅

Contract:
  status: → COMPLETED ✅
  completed_at: <timestamp> ✅
```

## Next Steps

1. Configure webhook URL in DocuSeal (see Step 2)
2. Run test script: `python test_webhook.py`
3. Send a real contract and watch it update automatically
4. Check database to see real-time status changes
5. Build UI to show users their contract progress

## Additional Resources

- DocuSeal Webhook Documentation: https://docuseal.com/docs/webhooks
- Test script: `test_webhook.py`
- Multi-party contracts guide: `MULTI_PARTY_CONTRACTS.md`
- General DocuSeal integration: `DOCUSEAL_INTEGRATION.md`
