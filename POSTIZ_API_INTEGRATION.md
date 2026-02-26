# Postiz API Integration - Complete Guide

## Overview

Added real Postiz API integration to AI Realtor platform for social media management. This replaces the mock implementation with actual API calls to Postiz.

## What Was Added

### 1. Postiz Service (`app/services/postiz_service.py`)

A complete service that integrates with the Postiz Public API:

**PostizAPIClient Class:**
- `upload_media()` - Upload images/videos from file path or URL
- `upload_media_from_url()` - Download and upload from URL
- `create_post()` - Create or schedule posts
- `get_integrations()` - Get connected social platforms
- `delete_post()` - Delete posts
- `get_post_status()` - Get post status

**PostizService Class:**
- `upload_media()` - Upload media for agent
- `publish_post()` - Publish post with platform-specific content
- `get_connected_platforms()` - Get agent's connected platforms

### 2. New API Endpoints (`app/routers/postiz.py`)

Added 6 new API endpoints under `/social/api/`:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/social/api/upload-media` | POST | Upload media to Postiz |
| `/social/api/publish` | POST | Publish custom post |
| `/social/api/property/{id}/publish` | POST | Auto-publish property post |
| `/social/api/batch-publish` | POST | Publish multiple properties |
| `/social/api/integrations` | GET | Get connected platforms |

### 3. MCP Voice Tools (`mcp_server/tools/postiz.py`)

6 new MCP tools for voice control:

| Tool | Description |
|------|-------------|
| `upload_media_to_postiz` | Upload images/videos |
| `publish_post` | Publish custom post |
| `publish_property_post` | Auto-generate property post |
| `batch_publish_properties` | Bulk publish properties |
| `get_connected_platforms` | List connected platforms |
| `schedule_social_media` | Schedule post for later |

## Voice Command Examples

```bash
# Publish a property to Facebook and Instagram
"Publish property 5 to Facebook and Instagram"

# Publish custom post
"Post 'Just listed a beautiful home in Miami!' to Twitter and LinkedIn"

# Batch publish multiple properties
"Publish properties 1, 2, and 3 to Facebook"

# Check connected platforms
"What social platforms are connected?"

# Schedule a post
"Schedule a post for property 5 to Facebook for tomorrow at 10 AM"

# Upload media
"Upload this image to Postiz: https://example.com/photo.jpg"
```

## API Usage Examples

### 1. Connect Postiz Account

```bash
POST /social/accounts/connect
{
  "agent_id": 1,
  "api_key": "your-postiz-api-key",
  "platforms": ["facebook", "instagram", "twitter"],
  "account_name": "My Social Account"
}
```

### 2. Upload Media

```bash
POST /social/api/upload-media?agent_id=1
Content-Type: multipart/form-data

file=@photo.jpg
```

Or from URL:

```bash
POST /social/api/upload-media?agent_id=1&image_url=https://example.com/photo.jpg
```

### 3. Publish Custom Post

```bash
POST /social/api/publish
{
  "agent_id": 1,
  "caption": "Just listed a stunning property in Miami! 🏠",
  "platforms": ["facebook", "instagram"],
  "media_urls": ["https://example.com/photo1.jpg", "https://example.com/photo2.jpg"],
  "hashtags": ["#realestate", "#miami", "#newlisting"],
  "publish_immediately": true
}
```

### 4. Auto-Publish Property Post

```bash
POST /social/api/property/5/publish?agent_id=1&publish_immediately=true
{
  "platforms": ["facebook", "instagram", "linkedin"]
}
```

Auto-generates:
- Caption with property details
- Photos from Zillow enrichment
- Agent branding

### 5. Batch Publish Properties

```bash
POST /social/api/batch-publish
{
  "agent_id": 1,
  "property_ids": [1, 2, 3, 4, 5],
  "platforms": ["facebook", "instagram"]
}
```

### 6. Get Connected Platforms

```bash
GET /social/api/integrations?agent_id=1
```

Returns:

```json
{
  "agent_id": 1,
  "platforms": [
    {"id": "fb-123", "provider": "facebook", "name": "My Page"},
    {"id": "ig-456", "provider": "instagram", "name": "my_account"}
  ],
  "total": 2
}
```

### 7. Schedule Post

```bash
POST /social/api/publish
{
  "agent_id": 1,
  "caption": "Open House this Sunday! 🚪",
  "platforms": ["facebook", "instagram"],
  "scheduled_at": "2026-02-27T14:00:00Z",
  "publish_immediately": false
}
```

## Supported Platforms

Postiz supports 32+ platforms. Common ones:

| Platform | `__type` | Features |
|----------|----------|----------|
| Facebook | `facebook` | Long posts, CTA buttons |
| Instagram | `instagram` | Visual, stories, carousels |
| X (Twitter) | `x` | Short posts, 280 chars |
| LinkedIn | `linkedin` | Professional tone |
| TikTok | `tiktok` | Video-first |
| YouTube | `youtube` | Video uploads |
| Pinterest | `pinterest` | Image-heavy |
| Reddit | `reddit` | Community-based |
| Telegram | `telegram` | No custom settings |
| Threads | `threads` | No custom settings |

## Database Tables

Already existing in `app/models/postiz.py`:

- `postiz_accounts` - Agent's Postiz connections
- `postiz_posts` - Created posts
- `postiz_campaigns` - Multi-post campaigns
- `postiz_templates` - Reusable templates
- `postiz_analytics` - Performance metrics
- `postiz_calendars` - Content calendar

## Setup Required

### 1. Get Postiz API Key

1. Go to [Postiz](https://postiz.com)
2. Create account/workspace
3. Settings → API Keys
4. Generate new API key

### 2. Connect Account

```bash
POST /social/accounts/connect
{
  "agent_id": 1,
  "api_key": "pk_xxxxx",
  "platforms": ["facebook", "instagram"]
}
```

### 3. Connect Social Platforms in Postiz

1. In Postiz UI, connect Facebook, Instagram, etc.
2. The API will use these connected accounts

## Platform-Specific Settings

The service automatically handles platform-specific content:

```python
# Facebook
{"__type": "facebook", "url": "optional_link"}

# Instagram
{"__type": "instagram", "post_type": "post", "collaborators": []}

# Twitter/X
{"__type": "x", "who_can_reply_post": "everyone"}

# LinkedIn
{"__type": "linkedin", "post_as_images_carousel": false}

# TikTok
{"__type": "tiktok", "privacy_level": "public", "comment": true}
```

## Error Handling

All endpoints return meaningful errors:

```json
{
  "detail": "No active Postiz account found"
}
```

```json
{
  "detail": "Failed to publish post: Integration not found for platform: twitter"
}
```

## Files Modified/Created

### Created:
- `app/services/postiz_service.py` - Postiz API client and service
- `mcp_server/tools/postiz.py` - MCP voice tools

### Modified:
- `app/routers/postiz.py` - Added new API endpoints
- `mcp_server/tools/__init__.py` - Registered Postiz tools

## Testing

```bash
# Test MCP server
python mcp_server/property_mcp.py

# Test API endpoint
curl -X POST "http://localhost:8000/social/api/publish" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": 1,
    "caption": "Test post from AI Realtor!",
    "platforms": ["facebook"],
    "publish_immediately": true
  }'
```

## Rate Limits

Postiz API has a **30 requests per hour** limit.

- Schedule multiple posts in a single request to maximize throughput
- Use batch operations for efficiency
- Each API call counts as one request

## Next Steps

1. Connect your Postiz account
2. Connect social platforms in Postiz UI
3. Try voice commands or API calls
4. Review published posts in Postiz dashboard

## Documentation

- Postiz API: https://docs.postiz.com
- Postiz Cloud: https://api.postiz.com/public/v1
- Generate payloads: https://platform.postiz.com/modal/dark/all
