# Complete DocuSeal Integration Setup Guide

## Step-by-Step Setup

### 1. Get Your DocuSeal API Key

1. Go to **https://docuseal.com** (or your DocuSeal instance)
2. Sign up / Log in
3. Go to **Settings** → **API**
4. Copy your API key

### 2. Create a Template in DocuSeal

1. Go to **https://docuseal.com/templates**
2. Click **"New Template"**
3. Upload a PDF document (or create from scratch)
4. Add signing fields for each role:
   - **Seller** (or Owner)
   - **Lawyer** (or Attorney)
   - **Agent**
5. Assign fields to roles
6. Save the template
7. **Copy the Template ID** (you'll need this)

### 3. Configure Your `.env` File

Add these to your `.env`:

```env
# DocuSeal
DOCUSEAL_API_KEY=your_docuseal_api_key_here
DOCUSEAL_API_URL=https://api.docuseal.com

# Resend (Already configured)
RESEND_API_KEY=re_Vx7YxwHT_KQgyS8zPHhR1WRzuydZfgQBA
FROM_EMAIL=onboarding@resend.dev
FROM_NAME=Emprezario Inc
```

### 4. Restart Your Server

```bash
pkill -f "uvicorn"
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### 5. Run the Integration Test

```bash
python test_docuseal_integration.py
```

This will:
1. ✅ Create test property and contacts
2. ✅ Create a contract with your template
3. ✅ Send to multiple signers via DocuSeal
4. ✅ Send Resend notification emails
5. ✅ Track all signers in database
6. ✅ Show you the results

### 6. Configure Webhook (For Real-Time Updates)

**For Local Testing with ngrok:**

```bash
# Terminal 1: Your server
uvicorn app.main:app --reload --port 8000

# Terminal 2: ngrok
ngrok http 8000

# You'll get a URL like: https://abc123.ngrok.io
```

**In DocuSeal:**

1. Go to **Settings** → **Webhooks**
2. Enter your webhook URL:
   ```
   https://abc123.ngrok.io/contracts/webhook/docuseal
   ```
3. **Check ALL 8 event boxes:**
   - ✅ form.viewed
   - ✅ form.started
   - ✅ form.completed
   - ✅ form.declined
   - ✅ submission.created
   - ✅ submission.completed
   - ✅ submission.expired
   - ✅ submission.archived
4. Click **SAVE**

**For Production:**
```
https://yourdomain.com/contracts/webhook/docuseal
```

## Complete Flow

### 1. Send Contract

```bash
POST /contracts/voice/send-multi-party
{
  "address_query": "123 test street",
  "contract_name": "purchase agreement",
  "contact_roles": ["seller", "lawyer", "agent"],
  "order": "preserved",
  "message": "Please review and sign."
}
```

**What Happens:**
1. ✅ Creates DocuSeal submission
2. ✅ DocuSeal sends signing emails
3. ✅ Resend sends beautiful notification emails
4. ✅ Database records all 3 submitters
5. ✅ Contract status: DRAFT → SENT

### 2. Signer Opens Document

**DocuSeal sends webhook:**
```json
{
  "event_type": "form.started",
  "data": {
    "submission_id": "...",
    "submitter_id": "..."
  }
}
```

**Database Updates:**
- Submitter status: PENDING → OPENED
- Contract status: SENT → IN_PROGRESS

### 3. Signer Completes Signature

**DocuSeal sends webhook:**
```json
{
  "event_type": "form.completed",
  "data": {
    "submission_id": "...",
    "submitter_id": "..."
  }
}
```

**Database Updates:**
- Submitter status: OPENED → COMPLETED
- completed_at timestamp set

### 4. All Signers Complete

**DocuSeal sends webhook:**
```json
{
  "event_type": "submission.completed",
  "data": {
    "id": "...",
    "status": "completed"
  }
}
```

**Database Updates:**
- All submitters: COMPLETED
- Contract status: IN_PROGRESS → COMPLETED
- completed_at timestamp set

## Testing Checklist

- [ ] DocuSeal API key in `.env`
- [ ] Template created in DocuSeal
- [ ] Template has Seller, Lawyer, Agent roles
- [ ] Server running on port 8000
- [ ] Resend API key configured
- [ ] Run `python test_docuseal_integration.py`
- [ ] Enter your template ID
- [ ] Contract sends successfully
- [ ] Check email for signing requests
- [ ] Check email for Resend notifications
- [ ] Click signing link to test
- [ ] Webhook URL configured (optional for now)

## What You'll See

### In Your Email

**From DocuSeal:**
- Subject: "Sign: Test Purchase Agreement"
- DocuSeal-branded signing request

**From Resend (Your System):**
- Subject: "Signature Required: Test Purchase Agreement"
- Beautiful modern email with black button
- Contract and property details
- Signing order information

### In Your Database

**contracts table:**
```sql
SELECT id, name, status, docuseal_submission_id, sent_at
FROM contracts;
```

**contract_submitters table:**
```sql
SELECT name, role, status, signing_order, opened_at, completed_at
FROM contract_submitters
WHERE contract_id = 1;
```

### Via API

```bash
# Check contract status
curl http://localhost:8000/contracts/1/status

# Returns:
{
  "contract_id": 1,
  "status": "in_progress",
  "submitters": [
    {"name": "John Seller", "status": "completed"},
    {"name": "Lisa Lawyer", "status": "opened"},
    {"name": "Test Agent", "status": "pending"}
  ]
}
```

## Troubleshooting

### "DocuSeal API error: 401"

**Fix:** Check your API key in `.env`
```env
DOCUSEAL_API_KEY=your_actual_key_here
```

### "Template not found"

**Fix:** Use correct template ID from DocuSeal dashboard

### "Role not found in template"

**Fix:** Template must have these exact roles:
- Seller (or Owner)
- Lawyer (or Attorney)
- Agent

### Webhook not working

**Fix:**
1. Use ngrok for local testing
2. Check webhook URL is correct
3. Verify all 8 events are checked
4. Test with: `curl -X POST your-webhook-url`

## Production Deployment

### 1. Environment Variables

Set in your production environment:
```env
DOCUSEAL_API_KEY=prod_key_here
RESEND_API_KEY=prod_key_here
FROM_EMAIL=contracts@yourdomain.com
FROM_NAME=Your Company
```

### 2. Webhook URL

Configure in DocuSeal:
```
https://api.yourdomain.com/contracts/webhook/docuseal
```

### 3. Domain Verification

1. Go to resend.com/domains
2. Add your domain
3. Add DNS records
4. Update FROM_EMAIL to use your domain

## Next Steps

1. ✅ Run the test script
2. ✅ Send your first contract
3. ✅ Check emails
4. ✅ Sign the document
5. ✅ Watch database update
6. ✅ Configure webhook for real-time updates

🎉 You're ready to manage contracts at scale!
