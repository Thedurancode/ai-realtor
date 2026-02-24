#!/bin/bash

# AI Realtor - Quick Deployment Script for Fly.io
# Usage: ./deploy.sh

set -e  # Exit on error

echo "🚀 AI Realtor Deployment Script"
echo "================================"
echo ""

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl is not installed"
    echo ""
    echo "Install it with:"
    echo "  macOS:   brew install flyctl"
    echo "  Linux:   curl -L https://fly.io/install.sh | sh"
    echo "  Windows: pwsh -Command \"iwr https://fly.io/install.ps1 -useb | iex\""
    exit 1
fi

echo "✅ flyctl is installed"
echo ""

# Check if user is authenticated
if ! flyctl auth whoami &> /dev/null; then
    echo "⚠️  Not authenticated with Fly.io"
    echo "Running: fly auth login"
    flyctl auth login
fi

echo "✅ Authenticated with Fly.io"
echo ""

# Check if app exists
if ! flyctl status &> /dev/null; then
    echo "📦 App not found. Creating..."
    echo ""
    echo "This will:"
    echo "  1. Create app 'ai-realtor' on Fly.io"
    echo "  2. Use existing fly.toml configuration"
    echo "  3. NOT deploy yet (secrets needed first)"
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi

    flyctl launch --no-deploy

    echo ""
    echo "✅ App created!"
    echo ""
    echo "⚠️  IMPORTANT: Set your secrets before deploying:"
    echo ""
    echo "fly secrets set \\"
    echo "  GOOGLE_PLACES_API_KEY=\"your_key\" \\"
    echo "  DOCUSEAL_API_KEY=\"your_key\" \\"
    echo "  DOCUSEAL_API_URL=\"https://api.docuseal.com\" \\"
    echo "  RESEND_API_KEY=\"your_key\" \\"
    echo "  FROM_EMAIL=\"noreply@yourdomain.com\" \\"
    echo "  FROM_NAME=\"Real Estate Contracts\" \\"
    echo "  RAPIDAPI_KEY=\"your_key\" \\"
    echo "  SKIP_TRACE_API_HOST=\"skip-tracing-working-api.p.rapidapi.com\" \\"
    echo "  ZILLOW_API_HOST=\"private-zillow.p.rapidapi.com\""
    echo ""
    echo "After setting secrets, run this script again to deploy."
    exit 0
fi

echo "✅ App exists: ai-realtor"
echo ""

# Check if secrets are set
echo "🔐 Checking secrets..."
SECRET_COUNT=$(flyctl secrets list --json | jq length)

if [ "$SECRET_COUNT" -lt 5 ]; then
    echo "⚠️  Warning: Only $SECRET_COUNT secrets found"
    echo ""
    echo "Required secrets:"
    echo "  - GOOGLE_PLACES_API_KEY"
    echo "  - DOCUSEAL_API_KEY"
    echo "  - RESEND_API_KEY"
    echo "  - RAPIDAPI_KEY"
    echo "  - FROM_EMAIL"
    echo ""
    echo "Set them with:"
    echo "fly secrets set KEY=\"value\""
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled. Please set secrets first."
        exit 0
    fi
else
    echo "✅ Secrets configured ($SECRET_COUNT found)"
fi

echo ""

# Ask for confirmation
echo "📦 Ready to deploy!"
echo ""
echo "This will:"
echo "  1. Build Docker image"
echo "  2. Push to Fly.io"
echo "  3. Deploy to production"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "🚢 Deploying..."
flyctl deploy

echo ""
echo "✅ Deployment complete!"
echo ""

# Show app info
echo "📊 App Info:"
flyctl status

echo ""
echo "🌐 Your API is live at:"
flyctl info | grep Hostname | awk '{print "   https://" $2}'

echo ""
echo "📚 View API docs:"
flyctl info | grep Hostname | awk '{print "   https://" $2 "/docs"}'

echo ""
echo "📝 View logs:"
echo "   fly logs"

echo ""
echo "🎉 Deployment successful!"
