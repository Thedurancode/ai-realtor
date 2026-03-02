# Resend Email Integration Setup

The AI Realtor platform uses [Resend](https://resend.com) for sending email notifications for analytics alerts, daily summaries, and weekly reports.

## Prerequisites

1. **Resend Account** - Sign up at https://resend.com
2. **Verified Domain** - You must verify a domain before sending emails

## Setup Steps

### 1. Get Your Resend API Key

1. Log in to https://resend.com
2. Go to **API Keys** (https://resend.com/api-keys)
3. Click **Create API Key**
4. Copy your API key (starts with `re_`)

### 2. Verify Your Domain

1. Go to **Domains** (https://resend.com/domains)
2. Click **Add Domain**
3. Enter your domain (e.g., `yourcompany.com`)
4. Add the DNS records provided by Resend to your domain's DNS
5. Wait for DNS propagation (usually a few minutes)

### 3. Configure Environment Variables

Add these to your `.env` file:

```bash
# Resend Email Configuration
RESEND_API_KEY=re_xxxxxxxxxxxxxxxx
RESEND_FROM_EMAIL=notifications@yourcompany.com
```

Or set them in your deployment environment:

```bash
fly secrets set RESEND_API_KEY=re_xxxxxxxxxxxxxxxx RESEND_FROM_EMAIL=notifications@yourcompany.com --app ai-realtor
```

### 4. Test Email Sending

```bash
curl -X POST "http://localhost:8000/analytics/alerts/summaries/daily/send?agent_id=3&email=you@example.com"
```

## Email Templates

The platform sends 3 types of emails:

### 1. Alert Notifications
Sent when analytics alerts trigger:
- 🚨 **Traffic Drop Alert** - Property views drop by 50%+
- 📉 **Conversion Rate Alert** - Conversion rate below 2%
- And any custom alerts you create

**Features:**
- Color-coded by severity (blue/amber/red)
- Current metric value displayed prominently
- Additional context included
- Triggered timestamp

### 2. Daily Summary
Daily analytics overview with:
- Property views
- Leads created
- Conversions
- Conversion rate

**Schedule:** Configurable (default 9 AM daily)

### 3. Weekly Summary
Weekly performance report with:
- Week-over-week changes
- Top performing properties
- Traffic sources breakdown
- Geographic distribution

**Schedule:** Weekly (configurable)

## Configuration Options

### Alert Rules

Create custom alert rules via API:

```bash
curl -X POST "http://localhost:8000/analytics/alerts/rules" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": 3,
    "name": "High Traffic Alert",
    "description": "Alert when property views exceed 1000",
    "alert_type": "traffic_spike",
    "metric_name": "property_views",
    "operator": "greater_than",
    "threshold_value": 1000,
    "time_window_minutes": 60,
    "notification_channels": ["email"],
    "notification_recipients": {
      "email": ["you@example.com"]
    },
    "severity": "medium"
  }'
```

### Available Operators

- `greater_than` - Value exceeds threshold
- `less_than` - Value below threshold
- `equals` - Value equals threshold
- `percentage_change` - Change exceeds % threshold
- `percentage_drop` - Drop exceeds % threshold
- `percentage_increase` - Increase exceeds % threshold

### Available Metrics

- `property_views` - Property view count
- `conversion_rate` - Conversion percentage
- `leads_created` - New leads count
- `active_properties` - Active property count

## Troubleshooting

### Email Not Sending

Check if Resend is configured:

```python
from app.services.email_service import email_service
print(email_service.enabled)  # Should be True
```

### Domain Not Verified Error

```
The ai-realtor.com domain is not verified
```

**Solution:** Verify your domain in Resend dashboard

### API Key Invalid

```
401 Unauthorized
```

**Solution:** Check your RESEND_API_KEY in .env file

## API Endpoints

### Send Daily Summary
```bash
POST /analytics/alerts/summaries/daily/send?agent_id=3&email=you@example.com
```

### Send Weekly Summary
```bash
POST /analytics/alerts/summaries/weekly/send?agent_id=3&email=you@example.com
```

### View Alert Rules
```bash
GET /analytics/alerts/rules?agent_id=3
```

### Create Alert Rule
```bash
POST /analytics/alerts/rules
```

## Cost

Resend pricing:
- **Free tier:** 3,000 emails/month
- **Paid:** Starts at $20/month for 50,000 emails

Most agents will stay within the free tier.

## Security

- API keys are stored as environment variables
- Emails are sent via HTTPS
- No sensitive data in email subjects
- Recipients are validated before sending

## Customization

To customize email templates, edit:
- `app/services/email_service.py` - Email HTML templates

To change sender name/domain:
```bash
RESEND_FROM_NAME="Your Company"
RESEND_FROM_EMAIL="notifications@yourcompany.com"
```

## Monitoring

View email logs:
1. Log in to https://resend.com
2. Go to **Logs** (https://resend.com/logs)
3. Filter by date, recipient, or status

## Best Practices

1. **Set reasonable cooldown periods** to avoid email spam
2. **Group similar alerts** to reduce notification frequency
3. **Use appropriate severity levels** for prioritization
4. **Test alert rules** before enabling them
5. **Monitor email deliverability** in Resend dashboard

## Support

- Resend Documentation: https://resend.com/docs
- Resend Support: support@resend.com
- AI Realtor Docs: https://ai-realtor.fly.dev/docs
