# 🎬 Timeline Video Editor - Complete Guide

## Overview

The Timeline Video Editor lets you **visually arrange videos, images, and text on tracks** to create custom property videos that are dynamically rendered.

## Features

- **Visual Timeline Editor** - Drag-and-drop clips on multiple tracks
- **Real-time Preview** - See your video as you edit
- **Dynamic Rendering** - Render directly from the timeline
- **Save & Load** - Save projects and come back later
- **Multiple Tracks** - Video, Image, and Text layers
- **Transitions** - Fade, Slide, Zoom effects between clips
- **Custom Duration** - Set exact timing for each clip
- **Auto-Save to Cloud** - Projects saved to database

## Access the Editor

```
http://localhost:8000/static/timeline-editor.html
```

Or in production:
```
https://ai-realtor.fly.dev/static/timeline-editor.html
```

## How It Works

### 1. Create Your Timeline

**Add Clips:**
1. Choose track type (Video, Image, or Text)
2. Set source URL or text content
3. Set start time (in seconds)
4. Set duration (in seconds)
5. Choose transition effect
6. Click "Add Clip"

**Timeline Structure:**
```
Track 1: [Video Clip 1] [Video Clip 2]
Track 2:     [Image Overlay]
Track 3: [Title Text]       [Call to Action]
```

### 2. Visual Timeline

The timeline shows:
- **Track Type** - Video 🎥, Image 🖼️, or Text 📝
- **Clip Position** - Where it starts on the timeline
- **Clip Duration** - How long it plays
- **Transitions** - Fade, Slide, Zoom effects

**Clips are draggable** (in future updates) and can be layered.

### 3. Preview & Render

**Preview:**
- Click on clips to see details
- Timeline updates in real-time
- See total duration

**Render:**
1. Save your project
2. Click "Render Video"
3. Video renders in background
4. Download when complete

## API Endpoints

### Timeline Projects

```
POST   /v1/timeline                    # Create project
GET    /v1/timeline                    # List all projects
GET    /v1/timeline/{id}               # Get project details
PUT    /v1/timeline/{id}               # Update project
DELETE /v1/timeline/{id}               # Delete project
POST   /v1/timeline/{id}/render        # Render project to video
```

### Timeline Data Structure

```json
{
  "tracks": [
    {
      "id": "video",
      "type": "video",
      "clips": [
        {
          "id": "clip_1",
          "start": 0,
          "duration": 90,
          "type": "video",
          "src": "https://example.com/video.mp4",
          "transition": "fade"
        }
      ]
    }
  ],
  "duration": 900
}
```

## Clip Types

### 1. Video Clips

**Properties:**
- `type`: "video"
- `src`: Video URL (MP4, WebM)
- `start`: Frame number where clip starts
- `duration`: Duration in frames
- `transition`: "none" | "fade" | "slide" | "zoom"

**Example:**
```json
{
  "id": "clip_1",
  "type": "video",
  "src": "https://example.com/property-tour.mp4",
  "start": 0,
  "duration": 300,
  "transition": "fade"
}
```

### 2. Image Clips

**Properties:**
- `type`: "image"
- `src`: Image URL (JPG, PNG, WebP)
- `start`: Frame number
- `duration`: Duration in frames
- `transition`: Effect type

**Example:**
```json
{
  "id": "clip_2",
  "type": "image",
  "src": "https://example.com/property-photo.jpg",
  "start": 300,
  "duration": 150,
  "transition": "zoom"
}
```

### 3. Text Clips

**Properties:**
- `type`: "text"
- `text`: Text content
- `style`: CSS styles object
- `start`: Frame number
- `duration`: Duration in frames
- `transition`: Effect type

**Example:**
```json
{
  "id": "clip_3",
  "type": "text",
  "text": "Luxury Property - $450,000",
  "start": 0,
  "duration": 90,
  "style": {
    "fontSize": 80,
    "color": "#fff",
    "fontWeight": "bold",
    "textAlign": "center"
  },
  "transition": "slide"
}
```

## Transitions

### None
```
Clip A | Clip B
       ^ (hard cut)
```

### Fade
```
Clip A [====\\
         \\==== Clip B (fade in/out)
```

### Slide
```
Clip A [====→
         →==== Clip B (slide in from left)
```

### Zoom
```
Clip A [==== (zooms to 1.2x)
         ====] Clip B (starts at 0.8x)
```

## Workflow Examples

### Example 1: Property Slideshow

```json
{
  "tracks": [
    {
      "id": "image",
      "type": "image",
      "clips": [
        {
          "id": "photo1",
          "type": "image",
          "src": "https://example.com/photo1.jpg",
          "start": 0,
          "duration": 90,
          "transition": "fade"
        },
        {
          "id": "photo2",
          "type": "image",
          "src": "https://example.com/photo2.jpg",
          "start": 90,
          "duration": 90,
          "transition": "fade"
        },
        {
          "id": "photo3",
          "type": "image",
          "src": "https://example.com/photo3.jpg",
          "start": 180,
          "duration": 90,
          "transition": "fade"
        }
      ]
    },
    {
      "id": "text",
      "type": "text",
      "clips": [
        {
          "id": "title",
          "type": "text",
          "text": "123 Main St - Miami Beach",
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
  "duration": 270
}
```

### Example 2: Video with Text Overlays

```json
{
  "tracks": [
    {
      "id": "video",
      "type": "video",
      "clips": [
        {
          "id": "main_video",
          "type": "video",
          "src": "https://example.com/property-tour.mp4",
          "start": 0,
          "duration": 900,
          "transition": "none"
        }
      ]
    },
    {
      "id": "text",
      "type": "text",
      "clips": [
        {
          "id": "intro",
          "type": "text",
          "text": "Welcome to 123 Main St",
          "start": 0,
          "duration": 120,
          "style": {"fontSize": 80, "color": "#fff"},
          "transition": "fade"
        },
        {
          "id": "price",
          "type": "text",
          "text": "$450,000",
          "start": 120,
          "duration": 90,
          "style": {"fontSize": 100, "color": "#28a745"},
          "transition": "fade"
        },
        {
          "id": "cta",
          "type": "text",
          "text": "Schedule a Viewing Today!",
          "start": 780,
          "duration": 120,
          "style": {"fontSize": 70, "color": "#ffc107"},
          "transition": "zoom"
        }
      ]
    }
  ],
  "duration": 900
}
```

## Using with Property Data

### Get Property Photos

```python
import requests

# Get property with Zillow enrichment
response = requests.get(
    f"http://localhost:8000/properties/{property_id}",
    headers={"X-API-Key": api_key}
)
property = response.json()

# Extract photos
photos = property['zillow_enrichment']['photos']

# Create timeline clips
clips = []
for i, photo in enumerate(photos[:10]):
    clips.append({
        "id": f"photo_{i}",
        "type": "image",
        "src": photo,
        "start": i * 90,  # 3 seconds each
        "duration": 90,
        "transition": "fade"
    })
```

### Create Project from Property

```python
# Create timeline project
timeline_data = {
    "tracks": [
        {
            "id": "image",
            "type": "image",
            "clips": clips
        }
    ],
    "duration": len(photos) * 90
}

project = requests.post(
    "http://localhost:8000/v1/timeline",
    headers={"X-API-Key": api_key},
    json={
        "name": f"{property['address']} - Video Tour",
        "description": f"Property video for {property['address']}",
        "timeline_data": timeline_data
    }
).json()
```

## Rendering

### Render via Web UI

1. Open timeline editor
2. Create your timeline
3. Click "Save Project"
4. Click "Render Video"
5. Monitor progress via `/v1/renders/{job_id}/progress`

### Render via API

```bash
curl -X POST "http://localhost:8000/v1/timeline/{project_id}/render" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"webhook_url": "https://your-app.com/webhook"}'
```

### Monitor Progress

```bash
render_id=<from_response>

# Check progress
curl "http://localhost:8000/v1/renders/$render_id/progress" \
  -H "X-API-Key: your-api-key"

# Get full details
curl "http://localhost:8000/v1/renders/$render_id" \
  -H "X-API-Key: your-api-key"
```

## Advanced Features

### Layering

Clips on different tracks play simultaneously:

```json
{
  "tracks": [
    {
      "id": "video",
      "type": "video",
      "clips": [{"start": 0, "duration": 300, "src": "..."}]
    },
    {
      "id": "text",
      "type": "text",
      "clips": [{"start": 0, "duration": 60, "text": "Overlay"}]
    }
  ]
}
```

Result: Text overlay appears on top of video.

### Styling Text

```json
{
  "style": {
    "fontSize": 80,
    "fontWeight": "bold",
    "color": "#ffffff",
    "fontFamily": "Arial",
    "textAlign": "center",
    "textShadow": "2px 2px 8px rgba(0,0,0,0.8)",
    "alignItems": "center",
    "justifyContent": "center",
    "padding": "20px",
    "backgroundColor": "rgba(0,0,0,0.5)"
  }
}
```

### Custom Resolution

```json
{
  "fps": 30,
  "width": 1920,  // Horizontal video
  "height": 1080
}
```

Or square:
```json
{
  "width": 1080,
  "height": 1080
}
```

## Troubleshooting

### Video Won't Render

**Check timeline data:**
- All clips must have `start` + `duration` <= total `duration`
- Video/image URLs must be accessible
- Text clips must have `text` property

### Clips Not Showing

**Verify track types:**
- Video clips go on "video" track
- Image clips go on "image" track
- Text clips go on "text" track

### Transitions Not Working

**Check transition values:**
- Must be: "none", "fade", "slide", or "zoom"
- Case-sensitive
- Default is "none"

## Performance Tips

1. **Optimize Images**: Use 1080p max (1920x1080 or 1080x1920)
2. **Compress Videos**: Use H.264 codec
3. **Use CDN**: Host media on Cloudflare, AWS CloudFront
4. **Limit Duration**: Keep under 60 seconds for fast renders
5. **Cache Projects**: Save and reuse templates

## Next Steps

- Create template projects for common property types
- Add logo overlays to all videos
- Include background music (audio track coming soon)
- Batch render multiple properties
- Integrate with property auto-posting

## Live Demo

Try the editor at:
```
http://localhost:8000/static/timeline-editor.html
```

Full API docs:
```
http://localhost:8000/docs
```
