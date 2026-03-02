# 🎬 Remotion Video Rendering - Quick Start

## 5-Minute Setup

### 1. Install Dependencies

**Python:**
```bash
pip install redis boto3
```

**Node.js (for Remotion):**
```bash
cd remotion
npm install
```

### 2. Start Redis

```bash
# Docker
docker run -d -p 6379:6379 redis:alpine

# macOS
brew install redis && brew services start redis

# Linux
sudo systemctl start redis
```

### 3. Configure Environment

Add to `.env`:
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_S3_BUCKET=ai-realtor-renders
```

### 4. Run Migration

```bash
alembic upgrade head
```

### 5. Start Services

**Terminal 1 - API:**
```bash
uvicorn app.main:app --reload
```

**Terminal 2 - Worker:**
```bash
python worker.py
```

## Your First Video

### Create Captioned Reel

```bash
curl -X POST "http://localhost:8000/v1/renders" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "template_id": "captioned-reel",
    "composition_id": "CaptionedReel",
    "input_props": {
      "title": "Miami Luxury Living",
      "subtitle": "123 Main St, Miami Beach",
      "backgroundUrl": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1080",
      "overlayColor": "#000000",
      "overlayOpacity": 0.3
    }
  }'
```

### Create Property Slideshow

```bash
curl -X POST "http://localhost:8000/v1/renders" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "template_id": "slideshow",
    "composition_id": "Slideshow",
    "input_props": {
      "images": [
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1080",
        "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1080"
      ],
      "durationPerImage": 90,
      "showTitle": true,
      "title": "Property Tour"
    }
  }'
```

### Check Progress

```bash
curl "http://localhost:8000/v1/renders/{render_id}/progress" \
  -H "X-API-Key: your-api-key"
```

## Using with Property Media

### From Property Photos

```python
# Get property from your API
property = requests.get(
    f"http://localhost:8000/properties/{property_id}",
    headers={"X-API-Key": api_key}
).json()

# Extract photo URLs from Zillow enrichment
photos = property.get('zillow_enrichment', {}).get('photos', [])

# Create slideshow render
render = requests.post(
    "http://localhost:8000/v1/renders",
    headers={"X-API-Key": api_key},
    json={
        "template_id": "slideshow",
        "composition_id": "Slideshow",
        "input_props": {
            "images": photos[:10],  # First 10 photos
            "durationPerImage": 90,
            "showTitle": True,
            "title": f"{property['address']} - ${property['price']}"
        },
        "webhook_url": "https://your-app.com/webhook"
    }
).json()

print(f"Render ID: {render['id']}")
```

## CLI Scripts

### Create from File

```bash
# Save props to file
cat > props.json << EOF
{
  "title": "Luxury Condo",
  "subtitle": "$450,000 - Miami Beach",
  "backgroundUrl": "https://example.com/photo.jpg",
  "overlayColor": "#000000",
  "overlayOpacity": 0.3
}
EOF

# Create render
./scripts/create_render.sh props.json
```

### Poll Progress

```bash
./scripts/poll_render.sh <render_id>
```

### Cancel Render

```bash
./scripts/cancel_render.sh <render_id>
```

## Docker

```bash
docker-compose -f docker-compose-remotion.yml up -d
```

## Templates

### CaptionedReel
- **Size:** 1080x1920 (vertical)
- **Duration:** 10 seconds
- **Use case:** Instagram Reels, TikTok, YouTube Shorts

### Slideshow
- **Size:** 1080x1920 (vertical)
- **Duration:** 15s + (3s × image_count)
- **Use case:** Property tours, photo galleries

## Next Steps

- Create custom templates in `remotion/src/`
- Add music to Slideshow
- Customize colors and fonts
- Integrate with your property data

Full docs: [REMOTION_README.md](./REMOTION_README.md)
