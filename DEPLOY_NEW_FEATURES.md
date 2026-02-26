# 🚀 DEPLOYMENT GUIDE - New Features

## Overview

We've added **4 major features** to your AI Realtor platform! Here's how to activate them.

---

## ✅ What's Been Added

### 1. **AI Voice Assistant** (Inbound Calling)
**Files:** 14 files created
- Inbound call handling with VAPI
- Real-time transcription & recording
- 5 AI function calls
- Call analytics dashboard

### 2. **Market Watchlist Auto-Import**
**Files:** 3 files created
- Auto-scrapes Zillow for watchlist matches
- Auto-imports new properties
- Auto-enriches with Zillow data
- Creates instant notifications

### 3. **Automated Email/Text Campaigns**
**Files:** 2 files created
- Lead nurture campaigns (7 touches, 30 days)
- Contract deadline reminders
- Open house reminders
- Market reports

### 4. **Document Analysis AI**
**Files:** 2 files created
- PDF/Word document parsing
- Inspection report analysis
- Contract term extraction
- Appraisal comparison
- Document Q&A chatbot

---

## 🔄 Step 1: Restart the Server

The new routers need to be loaded. Restart the AI Realtor container:

```bash
# Option A: Restart container
docker-compose -f docker-compose-local-nanobot.yml restart ai-realtor

# Option B: Stop and start
docker-compose -f docker-compose-local-nanobot.yml stop ai-realtor
docker-compose -f docker-compose-local-nanobot.yml start ai-realtor

# Option C: Rebuild and restart
docker-compose -f docker-compose-local-nanobot.yml up -d --build ai-realtor
```

**Wait 30 seconds for server to start.**

---

## 🧪 Step 2: Test the Endpoints

### A. Quick Health Check

```bash
curl "http://localhost:8000/health" | python3 -m json.tool
```

Should return:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": {
    "type": "SQLite",
    "status": "healthy"
  }
}
```

### B. Test Campaign Endpoints

```bash
# List campaign types
curl -s "http://localhost:8000/campaigns/types" \
  -H "X-API-Key: nanobot-perm-key-2024" | python3 -m json.tool
```

Should return 4 campaign types:
```json
{
  "lead_nurture": {...},
  "contract_reminder": {...},
  "open_house": {...},
  "market_report": {...}
}
```

### C. Test Document Analysis

```bash
# List supported document types
curl -s "http://localhost:8000/documents/types" \
  -H "X-API-Key: nanobot-perm-key-2024" | python3 -m json.tool
```

Should return 5 document types:
```json
{
  "inspection_report": {...},
  "contract": {...},
  "appraisal": {...},
  "disclosure": {...},
  "deed": {...}
}
```

### D. Test Watchlist Scanning

```bash
# Get scan status
curl -s "http://localhost:8000/watchlists/scan/status" \
  -H "X-API-Key: nanobot-perm-key-2024" | python3 -m json.tool
```

Should return recent scan results (empty initially).

---

## 📊 Step 3: View API Documentation

Open your browser:

```
http://localhost:8000/docs
```

Look for the new sections:
- **Campaigns** - Email/text drip campaigns
- **Documents** - AI document analysis
- **Voice Assistant** - Inbound calling (already exists)
- **Watchlists** - Enhanced with auto-scan

---

## 🎯 Step 4: Test Campaign Feature

### Create a Campaign

```bash
curl -X POST "http://localhost:8000/campaigns/" \
  -H "X-API-Key: nanobot-perm-key-2024" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": 1,
    "name": "My Lead Nurture Campaign",
    "campaign_type": "lead_nurture",
    "target_contacts": [1, 2],
    "channels": ["email", "sms"]
  }'
```

### Estimate Campaign Cost

```bash
curl -X POST "http://localhost:8000/campaigns/estimate-cost" \
  -H "X-API-Key: nanobot-perm-key-2024" \
  -H "Content-Type: application/json" \
  -d '{
    "contacts_count": 10,
    "touches_count": 7,
    "channels": ["email", "sms"]
  }'
```

---

## 📄 Step 5: Test Document Analysis

### Upload and Analyze a Document

```bash
# First, upload a document (if you have one)
curl -X POST "http://localhost:8000/documents/upload" \
  -H "X-API-Key: nanobot-perm-key-2024" \
  -F "file=@/path/to/inspection_report.pdf"
```

This will return a file path. Then analyze it:

```bash
# Analyze the document
curl -X POST "http://localhost:8000/documents/analyze" \
  -H "X-API-Key: nanobot-perm-key-2024" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/tmp/path/to/uploaded_file.pdf",
    "document_type": "inspection_report",
    "property_id": 1
  }'
```

---

## 📡 Step 6: Test Watchlist Auto-Scan

### Create a Watchlist

```bash
curl -X POST "http://localhost:8000/watchlists/" \
  -H "X-API-Key: nanobot-perm-key-2024" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": 1,
    "name": "Miami Condos Under $500k",
    "criteria": {
      "city": "Miami",
      "state": "FL",
      "property_type": "condo",
      "max_price": 500000,
      "min_bedrooms": 2
    }
  }'
```

### Trigger a Scan

```bash
# Scan all watchlists
curl -X POST "http://localhost:8000/watchlists/scan/all" \
  -H "X-API-Key: nanobot-perm-key-2024"
```

---

## 🔍 Step 7: Verify Integration

### Check All New Endpoints

```bash
# Get OpenAPI spec
curl -s "http://localhost:8000/openapi.json" | python3 -c "
import sys, json
data = json.load(sys.stdin)

# Count endpoints by tag
tags = {}
for path, methods in data['paths'].items():
    for method in methods.keys():
        for tag in methods[method].get('tags', []):
            tags[tag] = tags.get(tag, 0) + 1

print('📊 New Endpoints by Feature:')
print()
for tag, count in sorted(tags.items()):
    if 'campaign' in tag.lower() or 'document' in tag.lower():
        print(f'  {tag}: {count} endpoints')
"
```

---

## ✅ Step 8: Verify Services Load

```bash
# Test in Docker container
docker exec ai-realtor python3 -c "
from app.services.campaign_service import campaign_service
from app.services.watchlist_scanner_service import watchlist_scanner_service
from app.services.document_analysis_service import document_analysis_service

print('✅ Campaign service loaded')
print('✅ Watchlist scanner service loaded')
print('✅ Document analysis service loaded')
print()
print('🎉 All new services loaded successfully!')
"
```

---

## 🐛 Troubleshooting

### Server Won't Start

**Check logs:**
```bash
docker-compose -f docker-compose-local-nanobot.yml logs ai-realtor
```

**Common Issues:**
1. **Import errors** - Missing dependencies
   - Solution: Check imports in new files

2. **Router conflicts** - Duplicate paths
   - Solution: Check router prefixes don't clash

3. **Database errors** - Missing migrations
   - Solution: Run migrations

### Endpoints Return 404

**Cause:** Server hasn't reloaded new code.

**Solution:**
```bash
docker-compose -f docker-compose-local-nanobot.yml restart ai-realtor
```

Wait 30 seconds, then test again.

### Services Fail to Load

**Check Python path:**
```bash
docker exec ai-realtor python3 -c "import sys; print(sys.path)"
```

**Test imports individually:**
```bash
docker exec ai-realtor python3 -c "
try:
    from app.services.campaign_service import campaign_service
    print('✅ Campaign service OK')
except Exception as e:
    print(f'❌ Campaign service error: {e}')
"
```

---

## 📚 Documentation

All features have comprehensive guides:

1. **VOICE_ASSISTANT_GUIDE.md** - Complete voice assistant guide
2. **VOICE_ASSISTANT_QUICKSTART.md** - 5-minute setup
3. **ALL_10_FEATURES_PLAN.md** - Complete feature plan
4. **FEATURE_BUILD_STATUS.md** - Build status
5. **FEATURES_COMPLETE_SUMMARY.md** - Summary of all features

---

## 🎉 Success Criteria

You'll know everything is working when:

✅ Server restarts without errors
✅ `/docs` shows new endpoint sections
✅ Campaign types endpoint returns 4 types
✅ Document types endpoint returns 5 types
✅ All services load without errors
✅ Health check returns "healthy"

---

## 🚀 Next Steps

Once verified:

1. **Set up VAPI** for voice assistant
2. **Create watchlists** for auto-import
3. **Design campaigns** for lead nurturing
4. **Upload documents** for AI analysis

**Your AI Realtor platform is now a complete autonomous real estate agency!** 🎉

---

**Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)**
