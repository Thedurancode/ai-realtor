# Property Video Editor - User Guide

## 🎬 How to Use the Video Editor

### Open the Editor
```bash
open examples/web/property_video_editor.html
```

The editor will open in your default browser with a live interactive interface.

---

## 🎨 Features

### 1. **Timeline Settings** (Left Panel)

#### Logo Intro Duration
- **Slider:** 1-10 seconds (default: 3s)
- **What it controls:** How long your company logo/brand intro plays
- **Best for:**
  - Quick: 1-2s
  - Standard: 3-4s
  - Premium: 5-7s

#### Photo Duration
- **Slider:** 2-10 seconds per photo (default: 4s)
- **What it controls:** How long each property photo displays
- **Best for:**
  - Fast-paced: 2-3s
  - Standard: 4-5s
  - Slow/relaxed: 6-10s

#### Transition Duration
- **Slider:** 0.5-2 seconds (default: 1s)
- **What it controls:** Black screen between logo and first photo
- **Best for:**
  - Quick: 0.5s
  - Standard: 1s
  - Dramatic: 1.5-2s

### 2. **Branding** (Left Panel)

#### Company Name
- Your company or brokerage name
- **Examples:** "Emprezario Inc", "Luxury Homes", "Smith Realty"

#### Tagline
- Your slogan or value proposition
- **Examples:**
  - "Finding Your Dream Home"
  - "Luxury Living Redefined"
  - "Your Dream Home Awaits"

#### Logo URL
- URL to your company logo
- **Recommended:** PNG with transparent background, 500×500px
- **Example:** `https://example.com/logo.png`

#### Colors
- **Primary Color:** Price badges, brand elements
  - Default: `#B45309` (gold/amber)
  - Try: Blue `#1E40AF`, Green `#059669`, Red `#DC2626`

- **Secondary Color:** Details badges, CTA buttons
  - Default: `#D97706` (orange)
  - Try: Light Blue `#3B82F6`, Teal `#14B8A6`, Pink `#EC4899`

### 3. **Property Details** (Right Panel)

#### Property Address
- Full property address
- **Format:** "123 Main St, New York, NY"

#### Price
- Listed price
- **Examples:** `$500,000`, `$1.2M`, "Price Upon Request"

#### Bedrooms/Bathrooms
- Number of beds and baths
- Bathrooms can be decimal (2.5 for 2.5 baths)

#### Square Feet
- Living area square footage
- **Example:** 2000, 3500, 5000

#### Property Type
- Choose from dropdown:
  - House
  - Condo
  - Townhouse
  - Apartment
  - Land
  - Commercial

### 4. **Property Photos** (Right Panel)

#### Adding Photos
1. Click **"+ Add Photo URL"** button
2. Paste image URL (max 10 photos)
3. Photos display in preview grid
4. Click **"×"** to remove a photo

#### Photo Sources
- **Zillow:** Automatically included if property is enriched
- **Unsplash:** `https://images.unsplash.com/photo-xxx`
- **Your server:** `https://yourdomain.com/photos/1.jpg`
- **Local:** Not supported (must be URLs)

#### Photo Best Practices
- **Resolution:** 1080×1920 (vertical 9:16)
- **Format:** JPG or PNG
- **Size:** Under 2MB each
- **Order:** Photos display in order added

---

## 📊 Live Timeline Preview

The editor shows a **real-time preview** of your video timeline:

```
┌─────────────────────────────────────────────────────────┐
│ 🏢 Logo Intro  ⚡  📸 Photo 1  📸 Photo 2  📸 Photo 3  │
│   3.0s       1.0s    4.0s       4.0s       4.0s      │
└─────────────────────────────────────────────────────────┘
```

### What the Colors Mean
- 🟣 **Purple** (Logo) - Company intro with branding
- ⬛ **Dark Gray** (Transition) - Black screen
- 🔴 **Pink Gradient** (Photos) - Property photos with overlays

### Duration Breakdown
Shows calculated durations in both **seconds** and **frames** (30 FPS):
- Logo Intro: 3.0s (90 frames)
- Transition: 1.0s (30 frames)
- Photos: 12.0s (360 frames)
- **TOTAL: 16.0s (480 frames)**

---

## 📤 Export Options

### 1. **Copy JSON**
Click **"Copy JSON"** button to copy the configuration to clipboard.

**Use with API:**
```bash
curl -X POST http://localhost:8000/v1/property-videos/generate \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "property_id": 3,
    "agent_id": 5,
    "logoUrl": "https://example.com/logo.png",
    "companyName": "Emprezario Inc",
    ...
  }'
```

### 2. **Python Code**
Click **"Python Code"** button to copy ready-to-use Python script.

**Save as:** `generate_video.py` then run:
```bash
python generate_video.py
```

### 3. **Save Config**
Click **"Save Config"** button to download configuration as JSON file.

**File:** `property-video-config.json`

**Load later:**
```python
import json
with open('property-video-config.json') as f:
    config = json.load(f)
# Use config in your script
```

---

## 🎯 Workflow Examples

### Example 1: Quick Instagram Reel
**Goal:** Short, attention-grabbing video under 30 seconds

**Settings:**
- Logo Duration: 2s
- Photo Duration: 3s
- Transition: 0.5s
- Photos: 5-7

**Result:** 17-21 seconds ✅

### Example 2: Premium Property Showcase
**Goal:** High-end luxury home video

**Settings:**
- Logo Duration: 5s
- Photo Duration: 6s
- Transition: 1.5s
- Photos: 10 (max)
- Colors: Primary `#B45309` (gold), Secondary `#D97706` (amber)

**Result:** ~67 seconds of premium content ✨

### Example 3: Fast-Paced Social Media
**Goal:** TikTok/Shorts style quick flip

**Settings:**
- Logo Duration: 1s
- Photo Duration: 2s
- Transition: 0.5s
- Photos: 3-5

**Result:** 8-11 seconds ⚡

---

## 🔧 Advanced Customization

### Custom Colors

**Real Estate Color Schemes:**

1. **Luxury Gold**
   - Primary: `#B45309` (gold)
   - Secondary: `#D97706` (amber)

2. **Modern Blue**
   - Primary: `#1E40AF` (blue)
   - Secondary: `#3B82F6` (light blue)

3. **Fresh Green**
   - Primary: `#059669` (green)
   - Secondary: `#10B981` (light green)

4. **Bold Red**
   - Primary: `#DC2626` (red)
   - Secondary: `#EF4444` (light red)

5. **Professional Gray**
   - Primary: `#374151` (dark gray)
   - Secondary: `#6B7280` (medium gray)

### Photo Order Strategy

**Recommended sequence:**
1. **Exterior front** - Curb appeal
2. **Living room** - Main gathering space
3. **Kitchen** - Important for buyers
4. **Master bedroom** - Retreat
5. **Bathroom** - If updated
6. **Backyard** - Outdoor living
7. **Unique feature** - Pool, view, etc.

---

## 💡 Tips & Tricks

### Duration Tips
- **For Instagram:** Keep under 60 seconds
- **For TikTok:** Best under 30 seconds
- **For YouTube:** Can be longer (2-3 minutes)
- **For Facebook:** 30-60 seconds optimal

### Photo Tips
- **Vertical format:** 1080×1920 (9:16 aspect ratio)
- **High quality:** Minimum 1920×1080 resolution
- **Good lighting:** Bright, well-lit photos
- **Variety:** Mix wide shots and close-ups
- **Staging:** Tidy and decluttered spaces

### Branding Tips
- **Logo:** Use transparent PNG for best results
- **Consistent:** Use same colors across all marketing
- **Tagline:** Keep it short (5 words or less)
- **Contact:** Consider adding phone number to tagline

---

## 📱 After Export

### View Your Video
Once generated, videos save to `/tmp/property_showcase.mp4`

**Open with:**
```bash
open /tmp/property_showcase.mp4  # Mac
```

### Upload to Social Media
**Supported platforms:**
- Instagram Reels, Stories
- TikTok
- YouTube Shorts
- Facebook Reels
- Pinterest Video

**Recommended:** Upload directly from the file (no re-encoding needed)

---

## 🐛 Troubleshooting

**Issue:** Timeline not updating
- **Fix:** Refresh the page and re-enter your settings

**Issue:** Photos not loading
- **Fix:** Make sure URLs are public and accessible

**Issue:** Duration calculation seems wrong
- **Fix:** Check that logoDuration + transition + (photos × photoDuration) = total

**Issue:** Colors not showing
- **Fix:** Use hex format with # (e.g., #FF0000)

---

## 📞 Need Help?

- **API Docs:** http://localhost:8000/docs
- **Property Videos Guide:** See `PROPERTY_VIDEO_FEATURE.md`
- **Remotion Docs:** https://www.remotion.dev

---

**Editor Location:** `examples/web/property_video_editor.html`

**Last Updated:** 2026-02-26
