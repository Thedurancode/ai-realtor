#!/bin/bash

# Preview Onboarding Wizard
# This script opens the onboarding wizard in your browser for local testing

echo "🦞 Opening Onboarding Wizard Preview..."
echo ""
echo "The onboarding wizard will open in your default browser."
echo "Make sure the FastAPI server is running on http://localhost:8000"
echo ""
echo "To start the server, run:"
echo "  uvicorn app.main:app --reload"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LANDING_DIR="$SCRIPT_DIR/../landing-page"

# Convert to absolute path
LANDING_DIR="$(cd "$LANDING_DIR" && pwd)"

# Open the onboarding page in the default browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "file://$LANDING_DIR/onboarding.html"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open "file://$LANDING_DIR/onboarding.html"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    start "" "$LANDING_DIR\\onboarding.html"
else
    echo "Could not detect OS. Please open manually:"
    echo "  file://$LANDING_DIR/onboarding.html"
fi

echo "✨ Preview opened!"
echo ""
echo "Note: Form submission requires the API server to be running."
echo "The wizard will POST to http://localhost:8000/onboarding/complete"
