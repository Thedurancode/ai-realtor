# Resend Email Integration

Beautiful, professional email notifications when contracts are sent for signing.

## What It Does

Automatically sends branded email notifications to signers when contracts are sent via DocuSeal. Emails include:
- 📧 Professional HTML email design
- 🔗 Direct link to sign the document
- 📄 Contract and property details
- ⏳ Signing order information (if sequential)
- 💬 Custom messages
- 🔒 Security notices

## Setup

### 1. Get Your Resend API Key

1. Go to [resend.com](https://resend.com)
2. Sign up for a free account
3. Add and verify your domain (or use resend.dev for testing)
4. Go to API Keys
5. Create a new API key

### 2. Configure Environment Variables

Add to your `.env` file:

```env
RESEND_API_KEY=re_your_api_key_here
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=Your Company Name
```

**For testing without a domain:**
```env
RESEND_API_KEY=re_your_api_key_here
FROM_EMAIL=onboarding@resend.dev
FROM_NAME=Your Company Name
```

### 3. Restart Your Server

```bash
# Kill existing server
pkill -f "uvicorn app.main:app"

# Start fresh
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

## Email Features

### Beautiful HTML Design

✅ Professional gradient header
✅ Clear contract details box
✅ Prominent "Review & Sign" button
✅ Signing order indicators
✅ Custom message support
✅ Security footer
✅ Mobile-responsive design

### Email Preview

```
┌─────────────────────────────────────────────┐
│        📝 Signature Required                │
├─────────────────────────────────────────────┤
│                                             │
│ Hi John Smith,                              │
│                                             │
│ You've been requested to sign the          │
│ following document as Owner:                │
│                                             │
│ ┌─────────────────────────────────────────┐│
│ │ CONTRACT DETAILS                        ││
│ │ 📄 Purchase Agreement                   ││
│ │ 🏠 789 Broadway, New York, NY           ││
│ └─────────────────────────────────────────┘│
│                                             │
│ ⏳ Signing Order: You're the first signer. │
│                                             │
│      [✍️ Review & Sign Document]           │
│                                             │
│ Need help? Contact the sender directly.    │
└─────────────────────────────────────────────┘
```

## How It Works

### Automatic Sending

Emails are sent automatically when you use the multi-party endpoints:

```python
# When you call this endpoint:
POST /contracts/voice/send-multi-party
{
  "address_query": "789 broadway",
  "contract_name": "purchase agreement",
  "contact_roles": ["owner", "lawyer", "agent"],
  "order": "preserved"
}

# Resend automatically sends emails to all 3 signers!
```

### What Gets Sent

**For Sequential Signing:**
- First signer: "You're the first signer" → Email sent immediately
- Second signer: "You're signer #2" → Email sent after first signs
- Third signer: "You're signer #3" → Email sent after second signs

**For Parallel Signing:**
- All signers get emails immediately
- No order indicators shown

## Email Content

### Sequential Signing Email

```html
Subject: 🏠 Please Sign: Purchase Agreement - 789 Broadway

Hi John Smith,

You've been requested to sign as Owner:

📄 Purchase Agreement
🏠 789 Broadway, New York, NY

⏳ Signing Order: You're the first signer.

💬 Custom Message: Please review carefully before signing.

[Review & Sign Document Button]
```

### Parallel Signing Email

```html
Subject: 🏠 Please Sign: Purchase Agreement - 789 Broadway

Hi John Smith,

You've been requested to sign as Owner:

📄 Purchase Agreement
🏠 789 Broadway, New York, NY

[Review & Sign Document Button]
```

## Testing

### Test Email Sending

```bash
python test_resend_email.py
```

This will:
- Create a test contract
- Simulate sending to multiple parties
- Show you the email sending results
- Let you verify everything works

### Check Resend Dashboard

1. Go to https://resend.com/emails
2. See all sent emails
3. View email previews
4. Check delivery status
5. See opens and clicks

## API Usage

### Send Single Notification

```python
from app.services.resend_service import resend_service

result = resend_service.send_contract_notification(
    to_email="john@example.com",
    to_name="John Smith",
    contract_name="Purchase Agreement",
    property_address="789 Broadway, NY",
    docuseal_url="https://docuseal.com/s/abc123",
    role="Owner",
    signing_order=1,
    is_sequential=True,
    custom_message="Please review carefully."
)

print(result)
# {"success": True, "email_id": "re_abc123", "to": "john@example.com"}
```

### Send Multi-Party Notifications

```python
submitters = [
    {
        "name": "John Smith",
        "email": "john@example.com",
        "role": "Owner",
        "docuseal_url": "https://docuseal.com/s/abc123",
        "signing_order": 1
    },
    {
        "name": "Emily Chen",
        "email": "emily@example.com",
        "role": "Lawyer",
        "docuseal_url": "https://docuseal.com/s/def456",
        "signing_order": 2
    }
]

results = resend_service.send_multi_party_notification(
    submitters=submitters,
    contract_name="Purchase Agreement",
    property_address="789 Broadway",
    is_sequential=True,
    custom_message="Please sign ASAP"
)

for result in results:
    print(f"{result['to']}: {'✅' if result['success'] else '❌'}")
```

## Customization

### Change Email Design

Edit `app/services/resend_service.py`:

```python
# Line 83: Update HTML email template
html_content = f"""
<!DOCTYPE html>
<html>
...your custom design...
</html>
"""
```

### Change Subject Line

Edit `app/services/resend_service.py`, line 72:

```python
subject = f"🏠 Please Sign: {contract_name} - {property_address}"
# Change to:
subject = f"Action Required: Sign {contract_name}"
```

### Add Your Logo

Add to the HTML email (line 95):

```html
<tr>
    <td style="padding: 20px; text-align: center;">
        <img src="https://yourdomain.com/logo.png" alt="Logo" style="max-width: 150px;">
    </td>
</tr>
```

## Features

### ✅ Professional Design
- Modern gradient header
- Clean, readable layout
- Mobile-responsive
- Security indicators

### ✅ Smart Content
- Shows signing order
- Includes custom messages
- Property details
- Contract information

### ✅ One-Click Action
- Prominent CTA button
- Direct link to DocuSeal
- No login required

### ✅ Delivery Tracking
- View sends in Resend dashboard
- Track opens and clicks
- Monitor delivery status
- Retry failed sends

## Resend Pricing

**Free Tier:**
- 100 emails/day
- 3,000 emails/month
- All features included
- Perfect for testing

**Paid Plans:**
- $20/month: 50,000 emails
- Custom domains
- Analytics
- Priority support

## Troubleshooting

### Emails Not Sending

1. **Check API key:**
   ```bash
   # In .env file
   RESEND_API_KEY=re_your_key_here
   ```

2. **Check domain verification:**
   - Go to resend.com/domains
   - Verify your domain is active
   - Or use resend.dev for testing

3. **Check logs:**
   ```bash
   # Look for Resend errors in console
   tail -f logs/app.log
   ```

### Wrong "From" Address

Update `.env`:
```env
FROM_EMAIL=contracts@yourdomain.com
FROM_NAME=My Real Estate Company
```

### Emails Going to Spam

1. Verify your domain in Resend
2. Add SPF and DKIM records
3. Use a real domain (not resend.dev)
4. Avoid spam trigger words

## Benefits

✅ **Professional Appearance** - Branded emails build trust
✅ **Better Delivery** - Resend optimizes deliverability
✅ **Tracking** - Know when emails are opened
✅ **Reliability** - 99.9% uptime guarantee
✅ **Easy Setup** - Just add API key
✅ **Free Tier** - Test with 3,000 emails/month

## Next Steps

1. Sign up at [resend.com](https://resend.com)
2. Get your API key
3. Add to `.env` file
4. Send a test contract
5. Check Resend dashboard

Your signers will receive beautiful, professional email notifications automatically! 📧✨
