# Social Media Preview Feature

## Overview

Preview your social media posts before publishing! See how your content will look on each platform with character counts, warnings, and platform-specific optimizations.

## New Endpoint

```
POST /social/api/preview
```

## Request Body

```json
{
  "agent_id": 1,
  "caption": "🏠 Just listed! Beautiful 3bd/2ba home in Miami. $450,000. DM for details!",
  "platforms": ["twitter", "facebook", "instagram"],
  "media_urls": ["https://example.com/photo1.jpg"],
  "hashtags": ["#RealEstate", "#Miami"],
  "property_id": 5
}
```

## Response Example

```json
{
  "agent_id": 1,
  "platforms": ["twitter", "facebook", "instagram"],
  "previews": [
    {
      "platform": "twitter",
      "platform_display": "X (Twitter)",
      "caption": "🏠 Just listed! Beautiful 3bd/2ba home...",
      "hashtags": ["#RealEstate", "#Miami"],
      "media_count": 1,
      "character_limit": 280,
      "character_count": 95,
      "character_remaining": 185,
      "warnings": [],
      "will_be_truncated": false,
      "property_context": {
        "address": "123 Main St, Miami",
        "price": "$450,000",
        "beds": 3,
        "baths": 2
      },
      "brand_applied": {
        "company": "Emprezario Inc",
        "tagline": "Your Dream Home Awaits"
      }
    },
    {
      "platform": "facebook",
      "platform_display": "Facebook",
      "character_limit": 63206,
      "character_count": 95,
      "character_remaining": 63111,
      "warnings": []
    },
    {
      "platform": "instagram",
      "platform_display": "Instagram",
      "character_limit": 2200,
      "character_count": 95,
      "character_remaining": 2105,
      "warnings": ["⚠️ Instagram posts perform better with images"]
    }
  ],
  "total_warnings": 1,
  "ready_to_post": true,
  "voice_summary": "Preview generated for 3 platforms. 1 platforms have warnings."
}
```

## Platform Character Limits

| Platform | Character Limit | Recommendations |
|----------|----------------|-----------------|
| X/Twitter | 280 | Max 3 hashtags, concise content |
| Facebook | 63,206 | No strict limit, CTA buttons work |
| Instagram | 2,200 | 10-30 hashtags, visuals required |
| LinkedIn | 3,000 | 100+ chars perform better, 3-5 hashtags |
| TikTok | 150 | Short, catchy, video-first |
| YouTube | 5,000 | Longer descriptions work |

## Automatic Warnings

The preview system automatically warns you about:

### Character Count Issues
- ⚠️ Exceeds character limit
- Shows exactly how many characters over

### Platform-Specific Issues
- **Twitter**: More than 3 hashtags
- **Instagram**: No images (posts perform better with visuals)
- **LinkedIn**: Under 100 characters (engagement drops)
- **TikTok**: No video provided

### Content Issues
- Missing call-to-action
- No property context
- No brand information

## Voice Commands

### Preview a post
```
"Preview this post: 'Just listed a beautiful home!' on Facebook and Twitter"
"Show me a preview for Instagram, LinkedIn with these hashtags"
```

### Preview with property
```
"Preview a post for property 5 on Facebook and Instagram"
"What will property 5's post look like on Twitter?"
```

### Preview before publishing
```
"Preview and then publish this to Facebook: 'New listing!'"
"Show me a preview before posting to LinkedIn"
```

## MCP Tool

```python
{
  "name": "preview_post",
  "description": "Preview a social media post before publishing...",
  "parameters": {
    "agent_id": 1,
    "caption": "Your post text",
    "platforms": ["facebook", "instagram"],
    "hashtags": ["#realestate"],
    "media_urls": ["https://..."]
  }
}
```

## Typical Workflow

```
1. Create Post Content
   ↓
2. Preview Post (/social/api/preview)
   ↓
3. Review Warnings
   ↓
4. Adjust if Needed
   ↓
5. Publish (/social/api/publish)
```

## Example Workflow with Voice

```
User: "Preview a post for property 5 on Facebook and Twitter"

AI: [Generates preview]
    "Post preview for 2 platforms:

    Facebook: 156/63206 chars (63150 remaining)

    X (Twitter): 156/280 chars (124 remaining)

    ✅ Ready to post!"

User: "Publish it"

AI: [Posts to both platforms]
    "Post published to Facebook, X/Twitter. Postiz ID: abc123"
```

## Integration with Your Workflow

### Before Publishing Property

```bash
# 1. Preview first
POST /social/api/preview
{
  "caption": "🏠 New Listing! $450,000...",
  "platforms": ["facebook", "instagram"],
  "property_id": 5
}

# 2. Review warnings
# Response: "⚠️ Instagram posts perform better with images"

# 3. Add images and preview again
POST /social/api/preview
{
  "caption": "🏠 New Listing! $450,000...",
  "platforms": ["facebook", "instagram"],
  "property_id": 5,
  "media_urls": ["photo1.jpg", "photo2.jpg"]
}

# 4. Publish
POST /social/api/property/5/publish
```

## Benefits

✅ **Avoid Mistakes** - Catch character limit issues before posting
✅ **Platform Optimization** - See platform-specific recommendations
✅ **Consistent Branding** - Ensure brand info is applied correctly
✅ **Better Engagement** - Follow best practices for each platform
✅ **Save Time** - Preview once, publish to multiple platforms

## API Usage Examples

### Example 1: Simple Preview

```bash
curl -X POST "http://localhost:8000/social/api/preview?agent_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "caption": "Check out this new listing!",
    "platforms": ["twitter"]
  }'
```

### Example 2: Property Preview with Images

```bash
curl -X POST "http://localhost:8000/social/api/preview?agent_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "caption": "🏠 Stunning Miami home!",
    "platforms": ["facebook", "instagram", "linkedin"],
    "property_id": 5,
    "media_urls": [
      "https://photos.zillow.com/...",
      "https://photos.zillow.com/..."
    ],
    "hashtags": ["#MiamiRealEstate", "#DreamHome"]
  }'
```

### Example 3: Check Character Limits

```bash
curl -X POST "http://localhost:8000/social/api/preview?agent_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "caption": "Lorem ipsum..." # Very long text
    "platforms": ["twitter"]
  }'
```

**Response:**
```json
{
  "previews": [{
    "character_count": 450,
    "character_limit": 280,
    "character_remaining": -170,
    "warnings": ["⚠️ Exceeds 280 character limit by 170 chars"],
    "will_be_truncated": true
  }],
  "ready_to_post": false
}
```

## Files Modified

- `app/routers/postiz.py` - Added `/social/api/preview` endpoint
- `mcp_server/tools/postiz.py` - Added `preview_post` MCP tool

## Testing

Start your server:
```bash
uvicorn app.main:app --reload
```

Test the preview:
```bash
curl -X POST "http://localhost:8000/social/api/preview?agent_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "caption": "Test post!",
    "platforms": ["twitter", "facebook"]
  }'
```

Or use voice commands once MCP server is running:
```
"Preview 'Just listed a new home!' on Twitter and Facebook"
```
