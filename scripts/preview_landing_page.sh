#!/bin/bash
# Quick script to preview the landing page

echo "🦞 RealtorClaw API Landing Page"
echo "================================"
echo ""
echo "Starting local server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    cd landing-page
    python3 -m http.server 8000
elif command -v python &> /dev/null; then
    cd landing-page
    python -m SimpleHTTPServer 8000
else
    echo "❌ Python not found. Please install Python or use another server."
    echo ""
    echo "Alternatives:"
    echo "  npx serve landing-page"
    echo "  php -S localhost:8000 -t landing-page"
    exit 1
fi
