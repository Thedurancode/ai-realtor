# 📘 Meta Ads Launch Guide - Zuckerbot Integration

## Overview

The Zuckerbot integration has **3 stages** for creating and launching Facebook ads:

1. **Preview** - Generate AI ad variants (draft only)
2. **Create** - Full campaign with strategy (still in Zuckerbot)
3. **Launch** - Push live to Meta Ads Manager ← **This requires Meta credentials**

---

## What You Need to Launch Campaigns

### Required Meta Credentials

To launch campaigns to Facebook Ads Manager, you need:

#### 1. Meta Access Token
**What:** A long-lived access token for the Meta Marketing API

**How to get it:**
```bash
# Go to Meta Developers: https://developers.facebook.com
# 1. Create an app (or use existing)
# 2. Go to Tools & Support → Graph API Explorer
# 3. Select your app
# 4. Get User Access Token with these permissions:
#    - ads_management
#    - ads_read
#    - read_insights
# 5. Click "Debug" → "Extend Access Token" (for 60-day token)
```

**Permissions needed:**
- `ads_management` - Create and manage ads
- `ads_read` - Read ad data
- `read_insights` - View performance metrics

**Your token will look like:**
```
EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxXXXXXXXXX
```

#### 2. Meta Ad Account ID
**What:** Your ad account ID in the format `act_XXXXXXXXX`

**How to find it:**
```bash
# Go to: https://business.facebook.com/ads/manager
# Look in the URL or account dropdown
# Example: https://business.facebook.com/ads/manager/account/act_1234567890
#                                                      ^^^^^^^^^^^
#                                                      This is your ID
```

**Format:** Must include the `act_` prefix
```
act_1234567890  ✅ Correct
1234567890      ❌ Missing act_ prefix
```

---

## Step-by-Step Launch Process

### Step 1: Create Campaign (Draft)

```bash
curl -X POST "http://localhost:8000/zuckerbot/campaigns/create" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "url": "https://www.zillow.com/homedetails/2640-Exposition-Blvd-Miami-FL-33133/20747378_zpid/",
    "campaign_type": "lead_generation",
    "budget": 100,
    "duration_days": 7
  }'
```

**Response:**
```json
{
  "id": "camp_mm2potawplv6ah",
  "status": "draft",
  "business_name": "2640 Exposition Blvd Miami Property",
  "variants": [
    {
      "headline": "Miami Dream Home",
      "copy": "Discover luxury...",
      "cta": "Learn More"
    }
  ],
  "strategy": { ... },
  "roadmap": { ... }
}
```

**Save the `id`** - you need it for launch!

### Step 2: Launch to Meta

```bash
curl -X POST "http://localhost:8000/zuckerbot/campaigns/launch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "campaign_id": "camp_mm2potawplv6ah",
    "meta_access_token": "EAAxxxxxx",
    "ad_account_id": "act_1234567890"
  }'
```

**Response:**
```json
{
  "status": "launching",
  "meta_campaign_id": "23842384238423842",
  "meta_ad_set_id": "23842384238423843",
  "meta_ad_ids": ["23842384238423844", "23842384238423845"],
  "meta_url": "https://www.facebook.com/ads/manager/act_1234567890/adgroups/23842384238423842"
}
```

### Step 3: View in Meta Ads Manager

Open the URL from the response:
```
https://www.facebook.com/ads/manager/act_1234567890/adgroups/23842384238423842
```

Your ad is now live! 🎉

---

## Environment Variables

Add these to your `.env` file:

```bash
# Zuckerbot API (for AI generation)
ZUCKERBOT_API_KEY=zb_live_your-key-here

# Meta Ads Manager (for launching)
META_ACCESS_TOKEN=EAAxxxxxx
META_AD_ACCOUNT_ID=act_1234567890
```

---

## Quick Launch Script

Save as `launch_facebook_ad.sh`:

```bash
#!/bin/bash

API_KEY="${API_KEY:-your-api-key}"
BASE_URL="${BASE_URL:-http://localhost:8000}"

# Step 1: Create campaign
echo "Creating campaign..."
CAMPAIGN=$(curl -s -X POST "$BASE_URL/zuckerbot/campaigns/create" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "url": "https://www.zillow.com/homedetails/2640-Exposition-Blvd-Miami-FL-33133/20747378_zpid/",
    "campaign_type": "lead_generation",
    "budget": 100,
    "duration_days": 7
  }')

CAMPAIGN_ID=$(echo "$CAMPAIGN" | jq -r '.id')
echo "✅ Campaign created: $CAMPAIGN_ID"

# Step 2: Launch to Meta
echo "Launching to Meta..."
LAUNCH=$(curl -s -X POST "$BASE_URL/zuckerbot/campaigns/launch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d "{
    \"campaign_id\": \"$CAMPAIGN_ID\",
    \"meta_access_token\": \"$META_ACCESS_TOKEN\",
    \"ad_account_id\": \"$META_AD_ACCOUNT_ID\"
  }")

META_URL=$(echo "$LAUNCH" | jq -r '.meta_url')
echo "✅ Launched! View at: $META_URL"
```

Run it:
```bash
chmod +x launch_facebook_ad.sh
./launch_facebook_ad.sh
```

---

## Testing Your Meta Credentials

### Verify Access Token

```bash
curl -X GET "https://graph.facebook.com/v18.0/me/adaccounts" \
  -d "access_token=$META_ACCESS_TOKEN" \
  -d "fields=account_id,name,account_status"
```

Should return:
```json
{
  "data": [
    {
      "account_id": "act_1234567890",
      "name": "My Ad Account",
      "account_status": 1
    }
  ],
  "paging": {...}
}
```

### Check Ad Account Permissions

```bash
curl -X GET "https://graph.facebook.com/v18.0/act_1234567890" \
  -d "access_token=$META_ACCESS_TOKEN" \
  -d "fields=name,account_id,status"
```

---

## Troubleshooting

### Error: "Invalid OAuth access token"

**Problem:** Token expired or invalid

**Solution:**
1. Generate new token from Graph API Explorer
2. Make sure it has `ads_management` permission
3. Use "Extend Access Token" for 60-day token

### Error: "Ad account not found"

**Problem:** Wrong ad account ID or no permission

**Solution:**
1. Verify account ID includes `act_` prefix
2. Check you have admin access to the ad account
3. Verify token has `ads_management` permission

### Error: "Insufficient permissions"

**Problem:** Token missing required permissions

**Solution:**
1. Go to Meta Developers → Graph API Explorer
2. Grant these permissions:
   - `ads_management`
   - `ads_read`
   - `read_insights`
3. Generate new token

### Campaign Stuck in "Launching"

**Problem:** Meta API rate limit or processing delay

**Solution:**
1. Wait 5-10 minutes
2. Check status: `GET /zuckerbot/campaigns/{id}/performance`
3. Verify in Meta Ads Manager directly

---

## Complete Example

```python
import requests

API_KEY = "your-api-key"
BASE_URL = "http://localhost:8000"

# 1. Create campaign
response = requests.post(
    f"{BASE_URL}/zuckerbot/campaigns/create",
    headers={"X-API-Key": API_KEY},
    json={
        "url": "https://www.zillow.com/homedetails/2640-Exposition-Blvd-Miami-FL-33133/20747378_zpid/",
        "campaign_type": "lead_generation",
        "budget": 100,
        "duration_days": 7
    }
)
campaign = response.json()
campaign_id = campaign['id']
print(f"Created: {campaign_id}")

# 2. Launch to Meta
response = requests.post(
    f"{BASE_URL}/zuckerbot/campaigns/launch",
    headers={"X-API-Key": API_KEY},
    json={
        "campaign_id": campaign_id,
        "meta_access_token": os.getenv('META_ACCESS_TOKEN'),
        "ad_account_id": os.getenv('META_AD_ACCOUNT_ID')
    }
)
result = response.json()
print(f"Meta URL: {result['meta_url']}")
```

---

## Meta API Resources

- **Meta for Developers:** https://developers.facebook.com
- **Marketing API Docs:** https://developers.facebook.com/docs/marketing-apis
- **Graph API Explorer:** https://developers.facebook.com/tools/explorer/
- **Ad Account Help:** https://www.facebook.com/business/help

---

## Security Best Practices

### ✅ DO:
- Store tokens in `.env` file (never commit)
- Use long-lived tokens (60-day expiry)
- Rotate tokens regularly
- Monitor ad account spending
- Set budget caps
- Use test accounts for development

### ❌ DON'T:
- Commit tokens to git
- Share tokens via email/chat
- Use short-lived tokens (1-2 hours)
- Exceed daily budget limits
- Test with real credit cards

---

## Next Steps

1. **Get Meta Credentials** - Follow the steps above
2. **Set Environment Variables** - Add to `.env`
3. **Test Connection** - Verify with Graph API Explorer
4. **Launch Campaign** - Use the launch endpoint
5. **Monitor Performance** - Track in Meta Ads Manager

---

## Support

**Docs:** `/zuckerbot` endpoint in API docs
**Health Check:** `GET /zuckerbot/health`
**Issues:** https://github.com/Thedurancode/ai-realtor/issues
