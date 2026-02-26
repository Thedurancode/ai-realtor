# 🧪 AI Realtor Platform - Local Testing Guide

## ✅ Current Status

- **Server**: ✅ Running (http://localhost:8000)
- **Database**: ✅ Connected (PostgreSQL)
- **Properties**: 2 test properties
- **Contracts**: 5 test contracts
- **API Docs**: http://localhost:8000/docs

---

## 🚀 Quick Start

### Swagger UI (Recommended)

1. Open: http://localhost:8000/docs
2. Click "Authorize" (🔒)
3. Enter API key
4. Try any endpoint

### cURL Commands

```bash
# Test root (no auth)
curl http://localhost:8000/

# List properties (needs auth)
curl -H "X-API-Key: your-key" http://localhost:8000/properties/

# List voices (no auth)
curl http://localhost:8000/v1/property-videos/voices
```

---

## 🧪 Key Endpoints to Test

### Properties
- GET /properties/
- POST /properties/
- GET /properties/{id}
- POST /properties/{id}/enrich
- POST /properties/{id}/skip-trace

### Videos & Voiceovers
- GET /v1/property-videos/voices
- POST /v1/property-videos/script-preview?property_id=1
- POST /v1/property-videos/generate
- POST /v1/property-videos/voiceover

### Analytics
- GET /analytics/portfolio
- GET /analytics/pipeline
- GET /insights
- GET /follow-ups/queue

### Scoring
- POST /scoring/property/{id}
- GET /scoring/top?limit=10

---

## 📝 For Full Testing Guide

See the complete documentation with all endpoints, test scenarios, and troubleshooting tips.

**Server is running at: http://localhost:8000**
**API Docs: http://localhost:8000/docs**
