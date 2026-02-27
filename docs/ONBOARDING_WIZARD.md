# Onboarding Wizard

Modern, mobile-friendly multi-step onboarding wizard for creating AI-powered real estate assistant accounts.

## Features

- **11-Step Wizard**: Comprehensive data collection from business card to AI personality
- **Business Card OCR**: Upload business card for automatic information extraction ✨
- **Modern UI**: Beautiful dark theme with gradient accents and smooth animations
- **Mobile-First**: Fully responsive design that works on all devices
- **Real-Time Preview**: Live preview of AI assistant configuration
- **Color Picker**: Custom brand colors with preset palettes
- **Schedule Builder**: Day-by-day schedule with time inputs
- **Social Media Integration**: Connect all major platforms
- **File Upload**: Support for contacts import (CSV, Excel, vCard)
- **Personality Sliders**: Fine-tune AI assistant behavior

## Steps Overview

| Step | Description | Fields |
|------|-------------|--------|
| 1 | 💳 Business Card | Upload business card with OCR auto-fill + manual entry (name, age, city, address, phone, email, business name) |
| 2 | 📅 Schedule | Mon-Fri working hours with day-off toggles |
| 3 | 🎨 Branding | Logo upload, brand colors (5 color pickers with presets) |
| 4 | 👥 Contacts | Upload contacts file (CSV/Excel/vCard) |
| 5 | 📱 Social Media | Facebook, Instagram, LinkedIn, Twitter, TikTok, YouTube |
| 6 | 🎵 Music | Work music preferences (15+ genres) |
| 7 | 🌴 Weekend | Weekend schedule (Sat-Sun) |
| 8 | 📄 Contracts | Common contract types used (8 options) |
| 9 | 🗓️ Calendar | Google Calendar connection |
| 10 | 📍 Locations | Primary market, secondary markets, service radius, offices |
| 11 | 🤖 AI Identity | Assistant name, style, personality traits (4 sliders) |

## Files Created

```
landing-page/
├── onboarding.html      # Main wizard HTML
├── onboarding.css       # Modern dark theme styles
└── onboarding.js        # Wizard logic and validation

app/
├── models/
│   └── agent_onboarding.py          # New database model
├── routers/
│   └── onboarding.py (updated)      # New complete endpoint
└── services/
    └── onboarding_service.py (updated)  # Process wizard data

alembic/versions/
└── 20250227_add_onboarding_wizard.py  # Database migration

scripts/
└── preview_onboarding.sh             # Quick preview script
```

## Usage

### Preview Locally

```bash
# Run the preview script
./scripts/preview_onboarding.sh

# Or open directly
open landing-page/onboarding.html
```

### Run with API

```bash
# Start the FastAPI server
uvicorn app.main:app --reload

# Then run the preview script
./scripts/preview_onboarding.sh
```

### Apply Database Migration

```bash
# Apply the migration to add the new table
alembic upgrade head
```

## API Endpoints

### POST /onboarding/complete

Processes the completed onboarding wizard and creates agent account.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "age": 35,
  "city": "Miami",
  "address": "123 Main St",
  "phone": "+1 555-123-4567",
  "email": "john@example.com",
  "schedule": {
    "monday": { "start": "09:00", "end": "17:00" },
    "tuesday": { "off": true }
  },
  "business_name": "Smith Realty",
  "logo": "https://example.com/logo.png",
  "colors": {
    "primary_color": "#f97316",
    "secondary_color": "#3b82f6",
    "accent_color": "#22c55e",
    "background_color": "#0a0a0b",
    "text_color": "#ffffff"
  },
  "social_media": {
    "facebook": "facebook.com/smithrealty",
    "instagram": "@smithrealty"
  },
  "music_preferences": ["Lo-Fi", "Jazz"],
  "contracts": ["purchase_agreement", "listing_agreement"],
  "connect_calendar": true,
  "primary_market": "Miami-Dade County, FL",
  "service_radius": "25 miles",
  "assistant_name": "Clawbot",
  "assistant_style": "Professional & Formal",
  "personality": {
    "responsiveness": 80,
    "proactivity": 60,
    "detail_level": 70,
    "formality": 90
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Account created successfully",
  "agent_id": 123,
  "session_id": "abc123...",
  "assistant_name": "Clawbot",
  "assistant_style": "Professional & Formal"
}
```

## Database Schema

### agent_onboarding Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| agent_id | Integer | Foreign key to agents (unique) |
| first_name | String(100) | Agent's first name |
| last_name | String(100) | Agent's last name |
| age | Integer | Agent's age |
| city | String(100) | Agent's city |
| address | Text | Full address |
| phone | String(50) | Phone number |
| email | String(255) | Email address |
| business_name | String(255) | Business name |
| logo_url | Text | Logo URL |
| colors | JSON | Brand color scheme |
| schedule | JSON | Weekday schedule |
| weekend_schedule | JSON | Weekend schedule |
| contacts_uploaded | Boolean | Whether contacts were uploaded |
| social_media | JSON | Social media handles |
| music_preferences | JSON | List of music genres |
| contracts_used | JSON | List of contract types |
| calendar_connected | Boolean | Google Calendar connected |
| primary_market | String(255) | Primary market area |
| secondary_markets | Text | Secondary markets (newline separated) |
| service_radius | String(100) | Service radius |
| office_locations | Text | Office locations (newline separated) |
| assistant_name | String(100) | Custom AI assistant name |
| assistant_style | String(100) | Communication style |
| personality_traits | JSON | Personality slider values |
| onboarded_at | DateTime | Onboarding started timestamp |
| completed_at | DateTime | Onboarding completed timestamp |
| onboarding_complete | Boolean | Onboarding completion status |

### agents Table (New Column)

| Column | Type | Description |
|--------|------|-------------|
| city | String | Agent's city (added) |

## Color Presets

The wizard includes 4 preset color schemes:

1. **Orange/Blue/Green** - Vibrant and modern (default)
2. **Pink/Purple/Cyan** - Bold and energetic
3. **Red/Amber/Emerald** - Warm and professional
4. **Indigo/Violet/Fuchsia** - Elegant and sophisticated

## AI Personality Traits

Four sliders control the AI assistant's personality:

| Trait | Range | Description |
|-------|-------|-------------|
| Responsiveness | 0-100 | Relaxed → Immediate |
| Proactivity | 0-100 | Reactive → Proactive |
| Detail Level | 0-100 | Brief → Detailed |
| Formality | 0-100 | Casual → Formal |

## Assistant Styles

Available communication styles:

- Professional & Formal
- Friendly & Casual
- Concise & Direct
- Enthusiastic & Energetic
- Witty & Humorous

## Business Card OCR Feature

The first step of the onboarding wizard features a prominent **business card upload** with automatic text extraction (OCR):

### How It Works

1. **Upload**: User takes a photo or uploads an existing business card image
2. **Preview**: Image preview appears with remove/change options
3. **OCR Extraction**: Information is automatically extracted from the card:
   - Name (first/last)
   - Email address
   - Phone number
   - Business name
   - City/location
4. **Auto-Fill**: Form fields are populated with animated highlight effect
5. **Manual Override**: Users can edit any auto-filled information

### Current Implementation

- **Frontend**: Image upload, preview, and simulated OCR extraction
- **Animation**: Fields flash green when auto-filled (1.5s effect)
- **Notification**: Success toast shows "Information extracted from business card! ✨"
- **Fallback**: Manual entry form always available below the upload area

### Future Enhancement

To implement real OCR, integrate with:
- **Tesseract.js** (client-side OCR)
- **Google Vision API** (cloud-based)
- **Amazon Textract** (AWS)
- **Azure Form Recognizer** (Microsoft)

Backend endpoint would be:
```
POST /onboarding/extract-business-card
Content-Type: multipart/form-data

Returns: { name, email, phone, business_name, city, ... }
```

## Customization

### Adding New Steps

Edit `landing-page/onboarding.js` and add to the `ONBOARDING_STEPS` array:

```javascript
{
    id: 'new_step',
    emoji: '🎯',
    title: 'New Step Title',
    subtitle: 'Description of the step',
    type: 'default', // or 'schedule', 'social_media', etc.
    fields: [
        {
            name: 'field_name',
            label: 'Field Label',
            type: 'text',
            placeholder: 'Placeholder text',
            required: true
        }
    ]
}
```

### Styling

Edit `landing-page/onboarding.css` to customize:

- Colors (CSS variables at top)
- Animations
- Layout
- Responsive breakpoints

## Integration with Main App

The "Get Started" buttons on the landing page now link to `onboarding.html` instead of `#pricing`.

Files updated:
- `landing-page/index.html` - Updated "Get Started" links

## Memory Graph Integration

Onboarding data is automatically stored in the memory graph for AI context:

- Identity (name, email, business, assistant name)
- Schedule preferences
- Market information
- Social media handles
- Music preferences
- Contract types used
- Assistant personality

This allows the AI to provide personalized assistance from day one.

## Future Enhancements

Potential improvements:

- [ ] OAuth social media connection
- [ ] Google Calendar OAuth flow in wizard
- [ ] Resume saved onboarding progress
- [ ] Multi-language support
- [ ] Video walkthrough for each step
- [ ] Live chat support during onboarding
- [ ] Import from existing CRM
- [ ] Team onboarding (multiple agents)
- [ ] API key generation in wizard
- [ ] First property creation flow

## Support

For issues or questions:

1. Check the browser console for JavaScript errors
2. Verify the API server is running on port 8000
3. Check the database migration was applied
4. Review the logs in the FastAPI terminal

---

**Generated with [Claude Code](https://claude.ai/code)**
