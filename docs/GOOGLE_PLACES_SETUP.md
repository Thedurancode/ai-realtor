# Google Places Address Autocomplete

The onboarding wizard now includes **Google Places API** for smart address autocomplete with automatic city detection.

## Features

- ✅ **Real-time address suggestions** as user types
- ✅ **US-restricted addresses** for better accuracy
- ✅ **Auto-fill city field** from selected address
- ✅ **Visual feedback** when city is auto-filled
- ✅ **Formatted addresses** with proper capitalization
- ✅ **Dark theme styling** that matches the wizard

## Setup

### 1. Get Google Places API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services > Library**
4. Search for **"Places API"** and enable it
5. Search for **"Maps JavaScript API"** and enable it
6. Go to **APIs & Services > Credentials**
7. Click **"Create Credentials" > "API key"**
8. **Important**: Restrict the key:
   - Application: **Browser**
   - HTTP referrer: Add your domain (e.g., `http://localhost:8000/*`, `https://yourdomain.com/*`)
   - API restrictions: **Places API** and **Maps JavaScript API**

### 2. Configure the API Key

Run the configuration script:

```bash
./scripts/configure_google_places.sh YOUR_API_KEY_HERE
```

Or manually edit `landing-page/onboarding.html`:

```html
<script>
    window.GOOGLE_PLACES_API_KEY = 'YOUR_ACTUAL_API_KEY';
</script>
<script async defer
    src="https://maps.googleapis.com/maps/api/js?key=YOUR_ACTUAL_API_KEY&libraries=places&callback=initGooglePlaces">
</script>
```

### 3. Test It

```bash
./scripts/preview_onboarding.sh
```

Navigate to Step 1 and try typing in the address field!

## How It Works

### User Flow

1. User starts typing address in the address field
2. Google Places shows dropdown suggestions:
   ```
   123 Main St, New York, NY 10001, USA
   123 Main St, Brooklyn, NY 11201, USA
   123 Main St, Jersey City, NJ 07302, USA
   ```
3. User selects an address
4. System fills in:
   - ✅ Full formatted address in address field
   - ✅ City name (if city field is empty)
   - ✅ Visual green flash on city field
   - ✅ Notification: "Address auto-filled! City added from Google Maps ✨"

### Address Components Extracted

| Component | Example | Field Auto-Filled |
|-----------|---------|-------------------|
| Street Number | "123" | Full address |
| Street Name | "Main St" | Full address |
| City | "New York" | **City field** ✓ |
| State | "NY" | Full address |
| ZIP Code | "10001" | Full address |
| Formatted | "123 Main St, New York, NY 10001, USA" | **Address field** ✓ |

### Technical Details

**Frontend (onboarding.js):**
- `initGooglePlaces()` - Initializes autocomplete when DOM is ready
- `handleAddressSelect()` - Processes selected address
- Parses `place.address_components` to extract data
- Auto-fills city field with visual feedback

**API Endpoints Used:**
- `https://maps.googleapis.com/maps/api/js` - Maps JavaScript API
- Libraries: `places`
- Callback: `initGooglePlaces`

**Data Flow:**
```
User types → Google Places API → Suggestions dropdown
              ↓
         User selects address
              ↓
    handleAddressSelect() called
              ↓
    Parse address_components
              ↓
    Fill address field ✓
    Fill city field (if empty) ✓
    Show notification ✓
```

## Styling

The Google Places autocomplete dropdown is styled to match the wizard's dark theme:

```css
.pac-container {
    background-color: var(--bg-card);
    border: 1px solid var(--border-primary);
    border-radius: 0.5rem;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
}
```

Custom scrollbar, hover effects, and responsive design included.

## Cost & Limits

### Google Places API Pricing (as of 2025)

| Feature | Free Tier | Paid |
|---------|-----------|------|
| Autocomplete | $0/1000 requests | $2.83/1000 requests |
| Places Details | $0/1000 requests | $17.00/1000 requests |
| Monthly Credit | $200 free | - |

**Typical onboarding usage:**
- 1 autocomplete request per address field
- 1 places details request per address selection
- **1000 new users = ~$2.83** (after free credit)

### Best Practices

1. **Restrict your API key** to prevent abuse
2. **Enable caching** on backend for repeated addresses
3. **Monitor usage** in Google Cloud Console
4. **Set budget alerts** to avoid unexpected charges
5. **Use browser key restrictions** (HTTP referrer)

## Troubleshooting

### Autocomplete Not Working

**Problem:** No suggestions appear when typing

**Solutions:**
1. Check browser console for API errors
2. Verify API key is valid and enabled
3. Ensure both "Places API" and "Maps JavaScript API" are enabled
4. Check if API key has proper referrer restrictions
5. Try opening the page in an incognito window (cache issues)

### "RefererNotAllowedMapError"

**Problem:** API key restrictions blocking requests

**Solution:**
1. Go to Google Cloud Console > Credentials
2. Edit your API key
3. Under "Application restrictions", set to "HTTP referrer"
4. Add your domain: `http://localhost:8000/*` (for local testing)
5. Add your production domain: `https://yourdomain.com/*`

### City Not Auto-Filling

**Problem:** City field doesn't get filled after selecting address

**Solutions:**
1. Check that city field exists and has `name="city"`
2. Ensure city field is empty (only fills if empty)
3. Check browser console for JavaScript errors
4. Verify the selected address has a `locality` component

## Customization

### Change Country Restriction

Edit `onboarding.js`:

```javascript
addressAutocomplete = new google.maps.places.Autocomplete(addressInput, {
    types: ['address'],
    componentRestrictions: { country: 'us' }, // Change to 'ca', 'uk', etc.
    // Or remove to allow all countries:
    // componentRestrictions: null,
    fields: ['address_components', 'formatted_address', 'geometry', 'name']
});
```

### Add More Auto-Fill Fields

Edit `handleAddressSelect()` in `onboarding.js`:

```javascript
// Auto-fill state (if you add a state field)
if (addressData.state) {
    const stateInput = document.querySelector('input[name="state"]');
    if (stateInput && !stateInput.value) {
        stateInput.value = addressData.state;
    }
}

// Auto-fill ZIP code
if (addressData.zip_code) {
    const zipInput = document.querySelector('input[name="zip_code"]');
    if (zipInput && !zipInput.value) {
        zipInput.value = addressData.zip_code;
    }
}
```

### Disable Auto-Fill

To disable the city auto-fill feature, comment out this section in `handleAddressSelect()`:

```javascript
// Auto-fill city if it's empty
/*
if (addressData.city) {
    const cityInput = document.querySelector('input[name="city"]');
    if (cityInput && !cityInput.value) {
        cityInput.value = addressData.city;
        // ... rest of auto-fill code
    }
}
*/
```

## Security

### API Key Protection

1. ✅ **Browser restrictions** set on API key
2. ✅ **API restrictions** to only Places/Maps APIs
3. ✅ **HTTPS required** in production
4. ⚠️ **Never commit** real API keys to Git
5. ⚠️ **Use environment variables** for deployment

### .gitignore

Add to `.gitignore`:
```
# Google Places API key backup
landing-page/onboarding.html.backup
```

### Production Deployment

For production, use environment variables:

```javascript
// In onboarding.html
<script>
    window.GOOGLE_PLACES_API_KEY = window.GOOGLE_PLACES_API_KEY || '{{ GOOGLE_PLACES_API_KEY }}';
</script>
```

Then render the template with your backend (FastAPI example):

```python
# In your route handler
return templates.TemplateResponse(
    "onboarding.html",
    {"request": request, "GOOGLE_PLACES_API_KEY": os.getenv("GOOGLE_PLACES_API_KEY")}
)
```

## Files Modified

```
landing-page/
├── onboarding.html          → Added Google Places script
├── onboarding.css          → Added .pac-container styling
└── onboarding.js           → Added initGooglePlaces(), handleAddressSelect()

scripts/
└── configure_google_places.sh  → Configuration helper script
```

## Links

- [Google Places API Documentation](https://developers.google.com/maps/documentation/javascript/places-autocomplete)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Places API Pricing](https://maps.google.com/pricing)
- [API Key Best Practices](https://developers.google.com/maps/faq#keysystem)

---

**Generated with [Claude Code](https://claude.ai/code)**
