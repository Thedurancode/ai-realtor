# 🎬 Timeline Video Editor - Docker Quick Start

## Launch Everything

```bash
docker-compose up -d
```

This starts:
- ✅ PostgreSQL (port 5433)
- ✅ Redis (port 6379)
- ✅ AI Realtor API (port 8000)
- ✅ Render Worker (background)
- ✅ Timeline Editor (web UI)

## Access the Timeline Editor

```
http://localhost:8000/static/timeline-editor.html
```

## Your First Timeline Video

### Step 1: Open Editor
Open http://localhost:8000/static/timeline-editor.html in your browser

### Step 2: Add API Key
Enter your API key when prompted (or localStorage has it saved)

### Step 3: Add Clips

**Add Images:**
1. Track Type: 🖼️ Image
2. Source URL: `https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1080`
3. Start: 0 seconds
4. Duration: 3 seconds
5. Click "➕ Add Clip"

**Add Text:**
1. Track Type: 📝 Text
2. Text Content: "Luxury Property - $450,000"
3. Start: 0 seconds
4. Duration: 3 seconds
5. Click "➕ Add Clip"

### Step 4: Save & Render

1. Project Name: "My First Video"
2. Click "💾 Save Project"
3. Click "🎬 Render Video"

### Step 5: Monitor Progress

```bash
# Check render progress
curl "http://localhost:8000/v1/renders/{render_id}/progress" \
  -H "X-API-Key: your-key"
```

## Example Timeline from Property

Using your property's Zillow photos:

```python
import requests

# Get property
property = requests.get(
    f"http://localhost:8000/properties/{property_id}",
    headers={"X-API-Key": api_key}
).json()

# Extract photos
photos = property.get('zillow_enrichment', {}).get('photos', [])

# Create timeline project via API
timeline_data = {
    "tracks": [
        {
            "id": "image",
            "type": "image",
            "clips": [
                {
                    "id": f"photo_{i}",
                    "type": "image",
                    "src": photo,
                    "start": i * 90,  # 3 seconds each
                    "duration": 90,
                    "transition": "fade"
                }
                for i, photo in enumerate(photos[:10])
            ]
        },
        {
            "id": "text",
            "type": "text",
            "clips": [
                {
                    "id": "title",
                    "type": "text",
                    "text": property['address'],
                    "start": 0,
                    "duration": 90,
                    "style": {
                        "fontSize": 70,
                        "color": "#fff",
                        "textAlign": "center"
                    },
                    "transition": "slide"
                }
            ]
        }
    ],
    "duration": len(photos) * 90
}

# Save project
project = requests.post(
    "http://localhost:8000/v1/timeline",
    headers={"X-API-Key": api_key},
    json={
        "name": f"{property['address']} - Video",
        "timeline_data": timeline_data
    }
).json()

print(f"Project created: {project['id']}")
```

## Timeline Features

### Track Types
- 🎥 **Video** - Full motion video clips
- 🖼️ **Image** - Static photos
- 📝 **Text** - Text overlays

### Transitions
- **None** - Hard cut
- **Fade** - Fade in/out
- **Slide** - Slide in from left
- **Zoom** - Zoom effect

### Styling Text
```json
{
  "fontSize": 80,
  "fontWeight": "bold",
  "color": "#ffffff",
  "textAlign": "center",
  "textShadow": "2px 2px 8px rgba(0,0,0,0.8)"
}
```

## View Logs

```bash
# All services
docker-compose logs -f

# Worker (renders)
docker-compose exec app tail -f /app/log/worker.log

# API
docker-compose logs -f app
```

## Troubleshooting

### Editor Won't Load

```bash
# Check if static files are mounted
docker-compose exec app ls -la /app/static

# Should see timeline-editor.html
```

### Render Fails

```bash
# Check worker logs
docker-compose exec app cat /app/log/worker.log

# Check Remotion installation
docker-compose exec app npx remotion --help
```

### Timeline Not Saving

```bash
# Check database
docker-compose exec postgres psql -U postgres -d ai_realtor \
  -c "SELECT * FROM timeline_projects;"
```

## Production URLs

After deployment to Fly.io:

```
Timeline Editor: https://ai-realtor.fly.dev/static/timeline-editor.html
API Docs: https://ai-realtor.fly.dev/docs
```

## Next Steps

- 📖 [Full Timeline Guide](./TIMELINE_EDITOR_GUIDE.md)
- 🚀 [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- 🎬 [Remotion Docs](./REMOTION_README.md)

## Quick Tips

1. **Start Simple** - Add 2-3 images first
2. **Preview Often** - Check timeline before rendering
3. **Save Projects** - Reuse templates for similar properties
4. **Batch Render** - Create multiple projects, render overnight
5. **Optimize Images** - Use 1080p max for faster renders
