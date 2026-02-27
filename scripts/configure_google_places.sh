#!/bin/bash

# Configure Google Places API Key for Onboarding Wizard
# This script helps you set up your Google Places API key

echo "🔧 Google Places API Configuration"
echo "==================================="
echo ""
echo "The onboarding wizard uses Google Places API for address autocomplete."
echo ""

# Check if API key is already set
if grep -q "YOUR_GOOGLE_PLACES_API_KEY" landing-page/onboarding.html 2>/dev/null; then
    echo "⚠️  Google Places API key is not configured!"
    echo ""
    echo "To get an API key:"
    echo "  1. Go to https://console.cloud.google.com/"
    echo "  2. Create a new project or select existing"
    echo "  3. Navigate to APIs & Services > Library"
    echo "  4. Search for 'Places API' and enable it"
    echo "  5. Go to APIs & Services > Credentials"
    echo "  6. Create an API key (restrict to Places API)"
    echo ""
    echo "Then run: $0 YOUR_API_KEY"
    echo ""
    exit 1
fi

if [ -z "$1" ]; then
    echo "Usage: $0 YOUR_GOOGLE_PLACES_API_KEY"
    echo ""
    echo "Example: $0 AIzaSyAbC123DefG456hijK789lmn0opqrs"
    echo ""
    exit 1
fi

API_KEY="$1"

# Validate API key format (basic check for Google API keys)
if ! [[ "$API_KEY" =~ ^AIza[A-Za-z0-9_-]{35}$ ]]; then
    echo "⚠️  Warning: API key format looks incorrect."
    echo "Google API keys typically start with 'AIza' and are about 39 characters."
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Backup the original file
cp landing-page/onboarding.html landing-page/onboarding.html.backup

# Replace the API key placeholder
sed -i '' "s|YOUR_GOOGLE_PLACES_API_KEY|$API_KEY|g" landing-page/onboarding.html

echo "✅ Google Places API key configured successfully!"
echo ""
echo "Changes made:"
echo "  - Updated landing-page/onboarding.html"
echo "  - Backup saved as landing-page/onboarding.html.backup"
echo ""
echo "📝 Note: Make sure to:"
echo "  1. Enable 'Places API' in your Google Cloud Console"
echo "  2. Enable 'Maps JavaScript API' in your Google Cloud Console"
echo "  3. Set up proper API key restrictions (recommended)"
echo "  4. Consider enabling billing (free tier: $200 credit/month)"
echo ""
echo "Test the autocomplete by running:"
echo "  ./scripts/preview_onboarding.sh"
echo ""
