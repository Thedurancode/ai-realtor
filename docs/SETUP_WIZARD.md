# AI Realtor - Setup Wizard & Docker Startup Guide

Complete guide to the new setup wizard and Docker startup process.

---

## 🐳 Docker Startup Process

### What Happens When Docker Starts?

```
1. docker-compose up
   ↓
2. Containers initialize
   ├─ ai-realtor-sqlite starts
   │  ├─ Reads environment variables from .env file
   │  ├─ Initializes SQLite database
   │  ├─ Runs Alembic migrations (creates tables)
   │  ├─ Starts FastAPI server on port 8000
   │  └─ Starts background workers:
   │     • Campaign worker (phone calls every 15s)
   │     • Daily digest scheduler (8 AM daily)
   │     • Pipeline automation (every 5 min)
   │
   └─ nanobot-gateway starts (waits for ai-realtor)
      ├─ Reads environment variables
      ├─ Waits for ai-realtor health check
      ├─ Loads configuration from /root/.nanobot/config.json
      └─ Starts gateway server on port 18790
```

### Environment Variable Loading Order

1. **Docker Compose** (`environment:` section)
2. **.env file** (in project root)
3. **System environment** (host machine)

---

## 🎨 New Setup Wizard

A modern dark-themed web interface for configuring your AI Realtor platform without manually editing files.

### Features

✅ **Visual API Key Entry**
- Modern dark-themed UI
- Input fields with show/hide toggle
- Real-time validation
- Clear error messages

✅ **Live Validation**
- Tests each API key against the actual service
- Visual feedback (✓ green checkmark for valid, ✗ red X for invalid)
- Shows specific error messages

✅ **Progress Tracking**
- 4-step wizard with progress indicator
- Welcome → Essential Keys → Optional Keys → Complete
- Can go back and edit any time

✅ **Auto-Restart**
- Saves configuration to .env file
- Restarts Docker containers automatically
- Redirects to dashboard when ready

---

## 📁 Files Created

### Backend (FastAPI)

**`app/routers/setup.py`** (New file)
- `/api/setup/status` - Check if platform is configured
- `/api/setup/validate` - Validate API keys against services
- `/api/setup/save` - Save configuration to .env file
- `/api/setup/restart` - Restart Docker containers

**`app/main.py`** (Updated)
- Added setup_router import
- Added `/api/setup` to public paths (no auth required)
- Included setup_router in FastAPI app

### Frontend (Next.js)

**`frontend/app/setup/page.tsx`** (New file)
- Complete setup wizard UI
- 4-step process with validation
- Dark-themed modern design
- Responsive layout

**`frontend/components/SetupBanner.tsx`** (New file)
- Alert banner when setup is needed
- Shows missing required API keys count
- Dismissible with X button
- Links to setup page

**`frontend/app/layout.tsx`** (Updated)
- Added SetupBanner component
- Shows on all pages if setup incomplete

**`frontend/middleware.ts`** (New file)
- Auto-redirect to /setup if keys missing
- Checks setup status on every page load
- Skips setup page itself to avoid loops

---

## 🚀 How It Works

### First-Time Setup Flow

```
User opens http://localhost:3025
   ↓
Middleware checks /api/setup/status
   ↓
If not configured → Redirect to /setup
   ↓
User sees welcome screen
   ↓
Step 1: Enter essential API keys
   - Google Places API
   - RapidAPI Key
   - DocuSeal API Key
   - Telegram Bot Token
   - Zhipu AI API Key
   ↓
Each key validates on blur (when user leaves field)
   ↓
Visual feedback shows ✓ or ✗
   ↓
Step 2: Enter optional keys (can skip)
   - Anthropic Claude
   - VAPI
   - ElevenLabs
   - Resend
   - Exa AI
   ↓
Step 3: Complete & Restart
   - Saves to .env file
   - Restarts Docker containers
   - Shows success message
   ↓
Redirect to dashboard after 3 seconds
```

### Ongoing Usage

```
User opens http://localhost:3025
   ↓
Already configured → Goes to dashboard
   ↓
SetupBanner NOT shown
   ↓
User can access /setup anytime to:
   - Add optional keys later
   - Update existing keys
   - Re-validate keys
   - Re-run setup if needed
```

---

## 🔧 API Validation Details

### Google Places API
- Tests autocomplete endpoint
- Searches for "123 Main St"
- Returns valid if status is OK or ZERO_RESULTS
- Returns invalid if API key error

### RapidAPI
- Tests Zillow listings endpoint
- Searches for "123 Main St"
- Returns valid if HTTP 200
- Returns invalid if 401/403 (auth error)

### DocuSeal
- Tests /templates endpoint
- Returns valid if can list templates
- Returns invalid if 401 (bad key)

### Telegram Bot
- Tests /getMe endpoint
- Returns valid if bot info returned
- Returns invalid if bad token

### Zhipu AI
- Tests chat completion endpoint
- Sends 1-token test request
- Returns valid if HTTP 200
- Returns invalid if 401 (bad key)

### Anthropic Claude
- Tests messages endpoint
- Sends minimal test request
- Returns valid if HTTP 200
- Returns invalid if 401 (bad key)

### And more...
- VAPI, ElevenLabs, Resend, Exa AI all validated similarly

---

## 🎯 User Experience

### Setup Wizard Screens

#### 1. Welcome Screen
```
┌─────────────────────────────────────────┐
│  Welcome to AI Realtor 🏠              │
│                                         │
│  Let's configure your platform         │
│  in just a few minutes                 │
│                                         │
│  [🔑 Add API Keys]                      │
│  [✓ Validate Keys]                      │
│  [🌐 Start Using]                       │
│                                         │
│           [Get Started →]              │
└─────────────────────────────────────────┘
```

#### 2. Essential Keys Screen
```
┌─────────────────────────────────────────┐
│  Essential API Keys                     │
│  Required for platform to work          │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ 🌍 Google Places API [Required] │   │
│  │ Address lookup & validation     │   │
│  │ [•••••••••••••••]  👁 ✓          │   │
│  │ ✓ API key is valid!             │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [← Back] [Validate All] [Next →]      │
└─────────────────────────────────────────┘
```

#### 3. Complete Screen
```
┌─────────────────────────────────────────┐
│         Setup Complete! 🎉             │
│                                         │
│  Your AI Realtor platform is now       │
│  configured and ready to use.          │
│                                         │
│  ✓ Google Places API                   │
│  ✓ RapidAPI                            │
│  ✓ DocuSeal                            │
│  ✓ Telegram Bot                        │
│  ✓ Zhipu AI                            │
│                                         │
│         [Go to Dashboard →]            │
└─────────────────────────────────────────┘
```

### Setup Banner (Shown on all pages when needed)

```
┌──────────────────────────────────────────────────────────┐
│ ⚠ Setup Required                    [Complete Setup] [✕] │
│ 3 required API keys are missing                         │
└──────────────────────────────────────────────────────────┘
```

---

## 🔒 Security Features

### API Key Protection
- Password field type (hidden by default)
- Eye icon to show/hide
- Never logged or stored in browser
- Only sent to backend over HTTPS
- Written to .env file on server only

### Validation Security
- Real API calls test key validity
- No keys stored until user saves
- Can test keys before committing
- Clear error messages for each service

### Access Control
- `/api/setup` endpoints are public (no auth required)
- But only work on first setup or when re-running
- Already configured systems show current values (masked)

---

## 📊 Before vs After

### Before (Manual Setup)
```bash
# 1. Create .env file
nano .env

# 2. Manually type keys (easy to mess up)
GOOGLE_PLACES_API_KEY=AIzaSy...
RAPIDAPI_KEY=7f9764...
DOCUSEAL_API_KEY=jnTC1...

# 3. Restart containers
docker-compose restart

# 4. Check if keys are valid
curl https://maps.googleapis.com/...

# 5. If invalid, edit .env again
nano .env

# 6. Restart again
docker-compose restart
```

### After (Setup Wizard)
```
1. Open http://localhost:3025/setup
2. Paste keys into nice form fields
3. See ✓ checkmarks appear automatically
4. Click "Complete Setup & Restart"
5. Done! 🎉
```

---

## 🚀 Getting Started

### For New Deployments

1. **Start Docker containers**
   ```bash
   docker-compose -f docker-compose-local-nanobot.yml up -d
   ```

2. **Open setup wizard**
   ```bash
   open http://localhost:3025
   # Will auto-redirect to /setup if needed
   ```

3. **Follow the 4-step wizard**
   - Enter essential API keys
   - Wait for validation (green checkmarks)
   - Add optional keys (or skip)
   - Click complete

4. **Done!** Platform is ready to use

### For Existing Deployments

Already running? You can still use the setup wizard:

1. **Open setup page**
   ```bash
   open http://localhost:3025/setup
   ```

2. **Update or add keys**
   - Add optional keys you didn't have before
   - Update existing keys
   - Re-validate all keys

3. **Save & restart** (optional)

---

## 🎨 Dark Mode Design

The setup wizard uses a modern dark theme with:

- **Background**: `bg-gray-950` (nearly black)
- **Cards**: `bg-gray-900` (dark gray)
- **Text**: `text-white` and `text-gray-400`
- **Borders**: `border-gray-700`
- **Accents**: Blue for primary actions, green for success, red for errors
- **Input fields**: Monospace font for API keys
- **Icons**: Lucide React icons throughout

---

## 🧪 Testing the Setup Wizard

### Locally

```bash
# 1. Clear existing .env to simulate first-time setup
mv .env .env.backup

# 2. Restart containers
docker-compose -f docker-compose-local-nanobot.yml restart

# 3. Open browser
open http://localhost:3025

# 4. Should redirect to /setup automatically

# 5. Complete the wizard

# 6. Restore .env when done
mv .env.backup .env
```

### Validation Testing

```bash
# Test Google Places API validation
curl -X POST http://localhost:8000/api/setup/validate \
  -H "Content-Type: application/json" \
  -d '{"key": "GOOGLE_PLACES_API_KEY", "value": "AIzaSyYourKey"}'

# Check setup status
curl http://localhost:8000/api/setup/status
```

---

## 📝 Summary

### What You Got

✅ **Setup Wizard** - Modern dark-themed UI for entering API keys
✅ **Live Validation** - Tests keys against actual services
✅ **Auto-Restart** - Saves .env and restarts containers
✅ **Setup Banner** - Shows when keys are missing
✅ **Middleware** - Auto-redirects to setup if needed
✅ **Security** - Password fields, no logging, proper validation

### Files Created/Modified

**Backend:**
- ✅ `app/routers/setup.py` (new)
- ✅ `app/main.py` (updated)

**Frontend:**
- ✅ `frontend/app/setup/page.tsx` (new)
- ✅ `frontend/components/SetupBanner.tsx` (new)
- ✅ `frontend/app/layout.tsx` (updated)
- ✅ `frontend/middleware.ts` (new)

### Next Steps

1. **Restart your containers** to load the new code
   ```bash
   docker restart ai-realtor-sqlite
   ```

2. **Visit the setup wizard**
   ```bash
   open http://localhost:3025/setup
   ```

3. **Test the validation** by entering some API keys

4. **Complete setup** and see your platform come to life! 🚀

---

**You now have a beautiful, modern setup wizard!** 🎨✨
