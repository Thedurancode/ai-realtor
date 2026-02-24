# Quick Deploy to Fly.io - 5 Minutes ⚡

## TL;DR

```bash
# 1. Install Fly CLI
brew install flyctl

# 2. Login
fly auth login

# 3. Run deployment script
./deploy.sh

# 4. Set secrets when prompted
fly secrets set GOOGLE_PLACES_API_KEY="..." # etc

# 5. Run script again
./deploy.sh

# Done! 🎉
```

---

## Detailed Steps

### Step 1: Install Fly CLI (1 min)

**macOS:**
```bash
brew install flyctl
```

**Linux:**
```bash
curl -L https://fly.io/install.sh | sh
```

**Windows:**
```powershell
pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

---

### Step 2: Authenticate (30 seconds)

```bash
fly auth login
```

Opens browser → Sign in/Sign up

---

### Step 3: Run Deployment Script (1 min)

```bash
./deploy.sh
```

**First time:**
- Creates app on Fly.io
- Tells you to set secrets

**After secrets are set:**
- Builds Docker image
- Deploys to production
- Shows live URL

---

### Step 4: Set Your API Keys (2 min)

```bash
fly secrets set \
  GOOGLE_PLACES_API_KEY="your_google_key" \
  DOCUSEAL_API_KEY="your_docuseal_key" \
  DOCUSEAL_API_URL="https://api.docuseal.com" \
  RESEND_API_KEY="your_resend_key" \
  FROM_EMAIL="noreply@yourdomain.com" \
  FROM_NAME="Real Estate Contracts" \
  RAPIDAPI_KEY="your_rapidapi_key" \
  SKIP_TRACE_API_HOST="skip-tracing-working-api.p.rapidapi.com" \
  ZILLOW_API_HOST="private-zillow.p.rapidapi.com"
```

---

### Step 5: Deploy! (1 min)

```bash
./deploy.sh
```

Watch it build and deploy!

---

## Verify Deployment

### Check Status
```bash
fly status
```

### View Logs
```bash
fly logs
```

### Open App
```bash
fly open /docs
```

---

## Your App URL

After deployment, your API will be at:

```
https://ai-realtor.fly.dev
```

API Docs:
```
https://ai-realtor.fly.dev/docs
```

---

## Update Your Frontend

Update frontend `.env`:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=https://ai-realtor.fly.dev
NEXT_PUBLIC_WS_URL=wss://ai-realtor.fly.dev
```

---

## Deploy Updates

After making code changes:

```bash
git add .
git commit -m "Update"
./deploy.sh
```

Or just:
```bash
fly deploy
```

---

## Cost

**Your current setup:**
- Auto-stop enabled
- Starts on first request
- Stops after 5 minutes idle

**Monthly cost:** ~$2-5 (mostly $0 when not in use)

---

## Troubleshooting

### App not starting?

```bash
fly logs
```

Look for errors in startup.

### Can't connect?

```bash
fly status
```

Make sure machine is running.

### Need to restart?

```bash
fly machine restart
```

---

## Advanced

### Custom Domain

```bash
fly certs add yourdomain.com
fly ips list  # Add these to your DNS
```

### Scale Resources

```bash
# More memory
fly scale memory 2048

# More CPUs
fly scale count 2
```

### SSH into Machine

```bash
fly ssh console
```

---

## Complete Guide

See `DEPLOYMENT_GUIDE.md` for:
- Database options
- CI/CD setup
- Security best practices
- Monitoring
- Cost optimization

---

## Quick Reference

```bash
# Deploy
fly deploy

# Logs
fly logs

# Status
fly status

# Open app
fly open

# Secrets
fly secrets list
fly secrets set KEY="value"

# Restart
fly machine restart

# Dashboard
fly dashboard
```

---

**That's it!** Your AI Realtor API is now live at `https://ai-realtor.fly.dev` 🚀

Need help? Check:
- `DEPLOYMENT_GUIDE.md` - Complete guide
- `fly help` - CLI help
- https://fly.io/docs/ - Documentation
