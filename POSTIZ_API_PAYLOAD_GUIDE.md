# Postiz API Payload - What We're Sending

## Overview

This document explains exactly what data we're sending to the Postiz API and how we've optimized it.

## API Call Flow

```
1. Get Agent's Postiz API Key from Database
2. Get Integrations (connected social accounts)
3. Upload Media (if any) to get Postiz Media IDs
4. Build Post Payload with integration IDs
5. Send to Postiz API
```

## What We Send to Postiz API

### Step 1: Get Integrations

```http
GET /integrations
Authorization: <agent's_postiz_api_key>
```

**Response** (what we get back):
```json
{
  "integrations": [
    {
      "id": "fb_1234567890",
      "provider": "facebook",
      "name": "My Business Page",
      "avatar": "https://..."
    },
    {
      "id": "ig_0987654321",
      "provider": "instagram",
      "name": "my_business_account",
      "avatar": "https://..."
    },
    {
      "id": "x_111222333",
      "provider": "x",  // Note: Twitter is now "x"
      "name": "My Twitter Account",
      "avatar": "https://..."
    }
  ]
}
```

**We build a map:**
```python
{
  "facebook": "fb_1234567890",
  "instagram": "ig_0987654321",
  "x": "x_111222333",
  "twitter": "x_111222333"  # Alias for convenience
}
```

---

### Step 2: Upload Media (if images provided)

For each image URL:

```http
POST /upload
Authorization: <agent's_postiz_api_key>
Content-Type: multipart/form-data

file=@photo.jpg
```

**Response:**
```json
{
  "id": "img_abc123",
  "path": "https://cdn.postiz.com/uploads/photo.jpg"
}
```

**We store these media IDs to use in the post payload.**

---

### Step 3: Create Post Payload

This is the **final payload** we send to Postiz:

```http
POST /posts
Authorization: <agent's_postiz_api_key>
Content-Type: application/json

{
  "type": "now",                    // or "schedule"
  "date": "2026-02-25T10:00:00.000Z",
  "shortLink": false,
  "tags": ["#realestate", "#miami"], // Hashtags
  "posts": [
    {
      "integration": {
        "id": "fb_1234567890"        // From Step 1
      },
      "value": [
        {
          "content": "🏠 Just listed! Beautiful 3bd/2ba home in Miami. $450,000. DM for details!",
          "image": [
            {
              "id": "img_abc123",      // From Step 2
              "path": "https://cdn.postiz.com/uploads/photo.jpg"
            }
          ]
        }
      ],
      "settings": {
        "__type": "facebook"          // Platform type
      }
    },
    {
      "integration": {
        "id": "ig_0987654321"
      },
      "value": [
        {
          "content": "🏠 Just listed! Beautiful 3bd/2ba home in Miami. $450,000. DM for details! #realestate #miami",
          "image": [
            {
              "id": "img_abc123",
              "path": "https://cdn.postiz.com/uploads/photo.jpg"
            }
          ]
        }
      ],
      "settings": {
        "__type": "instagram",
        "post_type": "post"           // Optional: post, story, carousel
      }
    }
  ]
}
```

---

## Platform-Specific Settings

We add these settings automatically:

### Facebook
```json
{
  "__type": "facebook"
}
```

### Instagram
```json
{
  "__type": "instagram",
  "post_type": "post"  // or "story", "carousel"
}
```

### Twitter/X
```json
{
  "__type": "x",
  "who_can_reply_post": "everyone"
}
```

### LinkedIn
```json
{
  "__type": "linkedin",
  "post_as_images_carousel": false
}
```

### TikTok
```json
{
  "__type": "tiktok",
  "privacy_level": "public",
  "comment": true,
  "duet": false,
  "stitch": false
}
```

---

## What We Improved

### Before (Issues):
1. ❌ Used fake media IDs: `f"img_{hash(url)}"`
2. ❌ Didn't actually upload media to Postiz
3. ❌ Limited platform name mapping
4. ❌ Poor error handling for missing integrations
5. ❌ Didn't handle different API response formats

### After (Fixed):
1. ✅ Uploads media first, gets real Postiz media IDs
2. ✅ Uses actual uploaded media IDs in payload
3. ✅ Maps "twitter" → "x" automatically
4. ✅ Shows available integrations in error messages
5. ✅ Handles both `{"integrations": [...]}` and `[...]` response formats
6. ✅ Better logging for debugging

---

## Example: Property Post

When you call:
```bash
POST /social/api/property/5/publish?agent_id=1
{
  "platforms": ["facebook", "instagram"],
  "publish_immediately": true
}
```

**We do:**

1. **Fetch property** from database (ID: 5)
2. **Fetch property photos** from Zillow enrichment (up to 5)
3. **Upload each photo** to Postiz, get media IDs
4. **Generate caption** with property details
5. **Build payload** for each platform
6. **Send to Postiz API**

**Caption example:**
```
🏠 Miami, FL!

Price: $450,000
3 Bed | 2 Bath | 2,500 sqft

📍 123 Main St, Miami, FL

Contact Your Agent Name for details!
https://yourwebsite.com/properties/5
```

**Final payload sent:**
```json
{
  "type": "now",
  "date": "2026-02-25T15:30:00.000Z",
  "shortLink": false,
  "tags": ["#realestate", "#miami", "#homeforsale"],
  "posts": [
    {
      "integration": {"id": "fb_123"},
      "value": [{"content": "🏠 Miami...", "image": [{"id": "img_abc123", ...}]}],
      "settings": {"__type": "facebook"}
    },
    {
      "integration": {"id": "ig_456"},
      "value": [{"content": "🏠 Miami...", "image": [{"id": "img_abc123", ...}]}],
      "settings": {"__type": "instagram", "post_type": "post"}
    }
  ]
}
```

---

## Response We Get Back

```json
{
  "success": true,
  "post": {
    "id": "post_999888777",
    "status": "publishing",
    "platforms": {
      "facebook": "fb_post_111",
      "instagram": "ig_post_222"
    },
    "scheduledAt": "2026-02-25T15:30:00.000Z",
    "createdAt": "2026-02-25T15:29:00.000Z"
  }
}
```

**We store:**
- `post_id_postiz = "post_999888777"`
- `post_ids_platforms = {"facebook": "fb_post_111", "instagram": "ig_post_222"}`
- `status = "publishing"`

---

## Error Handling

If integrations not found:
```
Exception: No valid platform integrations found. Requested: ['tiktok'], Available: ['facebook', 'instagram', 'x']
```

If media upload fails:
```
ERROR: Failed to upload media https://example.com/photo.jpg: 404 Not Found
```

We log these errors and continue with what works.

---

## Is This the Best We Can Do?

### Current Implementation (Good):
✅ Real media uploads with proper IDs
✅ Platform-specific content
✅ Integration ID mapping
✅ Error handling
✅ Logging

### Possible Improvements (Future):
1. **Async media upload** - Upload all media in parallel for speed
2. **Media caching** - Don't re-upload if already uploaded
3. **Retry logic** - Retry failed uploads/posts
4. **Platform validation** - Validate content length per platform
5. **Hashtag optimization** - Add/adjust hashtags per platform
6. **Video support** - Handle video uploads and thumbnails
7. **Analytics polling** - Poll for post status updates
8. **Webhook support** - Receive status updates from Postiz webhooks

### Current Limitations:
- Media uploads are sequential (could be parallel)
- No caching of uploaded media
- No retry logic for transient failures
- No validation of content length limits
- Hashtags are the same across all platforms

**But for now, this is solid production-ready code that follows Postiz's API specification correctly.**
