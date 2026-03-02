# 🔍 How to Find & View Your Facebook Ad Campaigns

## Quick Reference

### Current Campaign
- **ID:** `camp_mm2rybvf4ssqkw`
- **Property:** 8801 Collins Ave 4D, North Miami Beach
- **Status:** Draft (not live)

---

## Method 1: View via Files (Local)

### Campaign ID
```bash
cat /tmp/campaign_id.txt
```
**Output:** `camp_mm2rybvf4ssqkw`

### Campaign Details (JSON)
```bash
cat /tmp/campaign_details.json | python3 -m json.tool
```
**Shows:** All campaign data including targeting, ads, budget

### Visual Preview (HTML)
```bash
open /tmp/facebook_ad_preview.html
```
**Opens:** Interactive preview in browser with all 3 ad variants

---

## Method 2: View via API

### Get Campaign Summary
```bash
curl -X GET "http://localhost:8000/zuckerbot/campaigns" \
  -H "x-api-key: YOUR_API_KEY"
```

### Get Specific Campaign
```bash
CAMPAIGN_ID="camp_mm2rybvf4ssqkw"

curl -X POST "http://localhost:8000/zuckerbot/campaigns/preview" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"campaign_id\": \"$CAMPAIGN_ID\"}"
```

---

## Method 3: View via Voice Commands

### Available Commands:
```
"Show me the campaign details"
"Get campaign status for camp_mm2rybvf4ssqkw"
"View ad preview"
"What campaigns do I have?"
```

---

## Method 4: View Campaign Data Directly

### Check All Campaign Files
```bash
ls -lh /tmp/campaign* /tmp/facebook*
```

### View Full Campaign Result
```bash
python3 << 'EOF'
import json
with open('/tmp/campaign_result.json') as f:
    data = json.load(f)
    print(json.dumps(data, indent=2))
EOF
```

---

## What You Can View

### 📊 Campaign Overview
- Campaign ID
- Property address
- Objective (leads, traffic, etc.)
- Status (draft, active, paused)
- Created date

### 🎯 Targeting Details
- Location (city, radius)
- Age range
- Interests (10-15 keywords)
- Behaviors
- Income level

### 📱 Ad Variants
- 3 different creative approaches
- Headlines
- Ad copy
- CTAs
- Psychological angles

### 💰 Budget & Projections
- Daily budget range
- Projected cost per lead (CPL)
- Monthly lead projections
- Recommended duration

---

## File Locations

| File | Location | What It Contains |
|------|----------|------------------|
| **Campaign ID** | `/tmp/campaign_id.txt` | Latest campaign ID only |
| **Campaign Details** | `/tmp/campaign_details.json` | Complete campaign data |
| **Campaign Result** | `/tmp/campaign_result.json` | Raw API response |
| **Visual Preview** | `/tmp/facebook_ad_preview.html` | Browser-based preview |

---

## How to Open Visual Preview

### Mac:
```bash
open /tmp/facebook_ad_preview.html
```

### Windows:
```bash
start /tmp/facebook_ad_preview.html
```

### Linux:
```bash
xdg-open /tmp/facebook_ad_preview.html
```

### Or manually:
1. Open Finder/Explorer
2. Navigate to `/tmp/` folder
3. Double-click `facebook_ad_preview.html`

---

## What the Visual Preview Shows

### 3 Ad Cards Side-by-Side
- **Variant 1:** Social Proof angle
- **Variant 2:** Urgency angle
- **Variant 3:** Value angle

### Each Card Shows:
- Facebook-style layout
- Sponsored label
- Headline
- Ad copy
- CTA button
- Meta campaign stats at bottom

### Bottom Section Shows:
- Budget recommendations
- Targeting details
- Link to Meta Ads Manager

---

## View Campaign Performance (After Launch)

Once campaign is live, track performance:

### Via Meta Ads Manager
```
https://business.facebook.com/ads/manager
```

### Via API
```bash
curl -X GET "http://localhost:8000/zuckerbot/campaigns/camp_mm2rybvf4ssqkw/performance" \
  -H "x-api-key: YOUR_API_KEY"
```

**Returns:**
- Impressions
- Clicks
- Spend
- Conversions
- CPL
- ROI

---

## Quick View Commands

```bash
# View campaign ID
echo "Campaign ID: $(cat /tmp/campaign_id.txt)"

# View summary
cat /tmp/campaign_details.json | python3 -m json.tool | head -30

# Open visual preview
open /tmp/facebook_ad_preview.html

# Count campaigns
ls /tmp/campaign_*.json | wc -l

# List all campaigns
ls -1 /tmp/campaign_*.json
```

---

## Campaign ID Format

All Zuckerbot campaign IDs follow this format:
```
camp_<random_string>
```

**Examples:**
- `camp_mm2rybvf4ssqkw` (current)
- `camp_mm2ru0qvgs3nqw` (previous)
- `camp_mm2rjfh282sl3s` (earlier)

---

## Viewing Multiple Campaigns

If you've created multiple campaigns:

```bash
# List all campaign IDs
grep -l "campaign_id" /tmp/campaign_*.json | while read file; do
    echo "File: $file"
    python3 -c "import json; print(json.load(open('$file'))['campaign_id'])"
    echo ""
done
```

---

## Troubleshooting

### Can't find campaign ID?
```bash
# Check if file exists
ls -la /tmp/campaign_id.txt

# If not, create a new campaign
curl -X POST "http://localhost:8000/zuckerbot/campaigns/create" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "PROPERTY_URL", "campaign_type": "lead_generation"}'
```

### Preview not opening?
1. Check file exists: `ls -la /tmp/facebook_ad_preview.html`
2. Try opening manually in browser
3. Generate new preview (re-run campaign creation)

---

## Summary

**Quickest Way to View:**
```bash
# 1. Get ID
cat /tmp/campaign_id.txt

# 2. See details
cat /tmp/campaign_details.json | python3 -m json.tool

# 3. See preview
open /tmp/facebook_ad_preview.html
```

**That's it!** 🎯
