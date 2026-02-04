# Complete Setup Guide - AI Realtor TV Display

This guide will walk you through setting up the amazing Remotion-powered TV display for your AI Realtor agent.

## Quick Start (5 minutes)

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Create environment file
cp .env.example .env

# 4. Start development server
npm run dev
```

Open `http://localhost:3025` in your browser! 🎉

## What You'll See

### Demo Mode
Press **`S`** on your keyboard to see the agent "speak" with:
- Animated avatar with moving mouth and blinking eyes
- Pulsing glow effects
- Real-time audio waveform visualization
- Live audio level indicators

Press **`Q`** to stop the animation.

## Full Integration Steps

### Step 1: Backend Setup

Make sure your FastAPI backend is running:

```bash
# In the root directory
python -m uvicorn app.main:app --reload
```

Backend should be accessible at `http://localhost:8000`

### Step 2: Frontend Configuration

Edit `.env` file in the `frontend/` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

### Step 3: Enable Real Voice Input (Optional)

To connect real microphone input, uncomment the voice integration in `app/page.tsx`:

```typescript
import { useVoiceIntegration } from '@/hooks/useVoiceIntegration'

// Inside your component:
const { isListening, startListening, stopListening } = useVoiceIntegration()

// Add a button to start/stop
<button onClick={isListening ? stopListening : startListening}>
  {isListening ? 'Stop' : 'Start'} Microphone
</button>
```

This will analyze your microphone in real-time and animate the avatar based on actual speech!

### Step 4: Enable WebSocket Updates (Optional)

For real-time backend updates, add WebSocket support to your FastAPI backend:

```python
# app/main.py
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Send updates to frontend
            await websocket.send_json({
                "type": "contract_update",
                "data": contracts
            })
            await asyncio.sleep(1)
    except Exception as e:
        print(f"WebSocket error: {e}")
```

Then uncomment the WebSocket hook in `app/page.tsx`:

```typescript
import { useWebSocket } from '@/hooks/useWebSocket'

const { isConnected } = useWebSocket('ws://localhost:8000/ws')
```

## TV Display Setup

### Hardware Setup

1. **Connect your computer to a TV/large display**
   - Use HDMI cable for best quality
   - Ensure TV is set to correct HDMI input

2. **Configure Display Settings**
   - Set TV as extended display (not mirrored)
   - Recommended resolution: 1920x1080 or higher
   - Disable screen sleep in system settings

3. **Browser Setup**
   - Open `http://localhost:3025` on the TV display
   - Press `F11` for fullscreen mode
   - Disable browser toolbars and extensions

### Software Configuration

For optimal TV display experience:

```bash
# Build production version for better performance
npm run build
npm start
```

Production build includes:
- Optimized bundle sizes
- GPU-accelerated animations
- Removed development warnings
- Better performance

## Customization

### Change Avatar Colors

Edit `components/remotion/AgentAvatar.tsx`:

```typescript
// Change gradient colors
<linearGradient id="gradient">
  <stop offset="0%" stopColor="#3B82F6" />  {/* Primary color */}
  <stop offset="100%" stopColor="#8B5CF6" /> {/* Secondary color */}
</linearGradient>
```

### Adjust Animation Speed

Change FPS in `components/TVDisplay.tsx`:

```typescript
<Player
  fps={30}  // Change to 60 for smoother animations
  // ... other props
/>
```

### Customize Waveform

Edit `components/remotion/AudioWaveform.tsx`:

```typescript
<AudioWaveform
  audioLevel={audioLevel}
  barCount={50}           // More bars = more detail
  color="#10B981"         // Change waveform color
/>
```

### Modify Layout

The TV display is a 2-column grid. Edit `components/TVDisplay.tsx`:

```typescript
{/* Change to single column for ultra-wide displays */}
<div className="grid grid-cols-1 gap-8">
  {/* Left column content */}
</div>
```

## Integration with AI Assistants

### OpenAI Assistant

```typescript
// Example OpenAI integration
import OpenAI from 'openai'

const openai = new OpenAI()

const response = await openai.chat.completions.create({
  model: "gpt-4",
  messages: [{ role: "user", content: "Send contract to john@example.com" }],
  functions: [
    {
      name: "send_contract",
      description: "Send a real estate contract",
      parameters: {
        type: "object",
        properties: {
          template_id: { type: "string" },
          property_id: { type: "number" },
          signers: { type: "array" }
        }
      }
    }
  ]
})

// Extract function call and send to your backend
const functionCall = response.choices[0].message.function_call
// Call your API...
```

### Anthropic Claude

```typescript
// Example Claude integration
import Anthropic from '@anthropic-ai/sdk'

const anthropic = new Anthropic()

const message = await anthropic.messages.create({
  model: "claude-3-opus-20240229",
  max_tokens: 1024,
  tools: [
    {
      name: "send_contract",
      description: "Send a real estate contract to signers",
      input_schema: {
        type: "object",
        properties: {
          template_id: { type: "string" },
          property_id: { type: "number" }
        }
      }
    }
  ],
  messages: [{ role: "user", content: "Send contract for property #5" }]
})

// Process tool calls...
```

### Voice Integration with Whisper

```typescript
// Speech-to-text with OpenAI Whisper
const transcribeAudio = async (audioBlob: Blob) => {
  const formData = new FormData()
  formData.append('file', audioBlob, 'audio.webm')
  formData.append('model', 'whisper-1')

  const response = await fetch('https://api.openai.com/v1/audio/transcriptions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
    },
    body: formData
  })

  const data = await response.json()
  return data.text
}
```

## Testing Checklist

- [ ] Backend API is running and accessible
- [ ] Frontend loads without errors
- [ ] Press `S` to simulate speaking - avatar animates correctly
- [ ] Press `Q` to stop - animations stop
- [ ] Contracts display with correct data
- [ ] Properties display with correct data
- [ ] Auto-refresh updates data every 5 seconds
- [ ] Fullscreen mode works (F11)
- [ ] Display looks good on TV/large screen

## Troubleshooting

### "Cannot connect to backend"

Check:
1. Backend is running: `python -m uvicorn app.main:app --reload`
2. Backend is accessible: Open `http://localhost:8000/docs`
3. `.env` file has correct `NEXT_PUBLIC_API_URL`
4. CORS is enabled in backend

### "Animations are laggy"

Solutions:
1. Use production build: `npm run build && npm start`
2. Close other applications
3. Reduce `fps` from 60 to 30
4. Reduce `barCount` in waveform
5. Use a more powerful computer/GPU

### "No data showing"

Check:
1. Create some test data in backend
2. Check Network tab for API calls
3. Look for errors in browser console
4. Verify API endpoint URLs are correct

### "Microphone not working"

Check:
1. Browser has microphone permission
2. Microphone is not being used by another app
3. `useVoiceIntegration` hook is properly initialized
4. HTTPS is enabled (required for mic access in production)

### "WebSocket connection fails"

Check:
1. Backend supports WebSocket endpoint at `/ws`
2. URL in `.env` is correct
3. Firewall is not blocking WebSocket connections
4. Backend is handling WebSocket messages correctly

## Performance Tips

1. **Use Hardware Acceleration**
   - Enable in browser settings
   - Use GPU-capable machine

2. **Optimize Polling**
   ```typescript
   // Reduce frequency if not needed
   setInterval(fetchData, 10000) // 10 seconds instead of 5
   ```

3. **Lazy Load Components**
   ```typescript
   const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
     loading: () => <div>Loading...</div>
   })
   ```

4. **Minimize Re-renders**
   - Use `React.memo()` for expensive components
   - Optimize state updates in Zustand store

## Production Deployment

### Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel
```

### Deploy to Netlify

```bash
# Install Netlify CLI
npm i -g netlify-cli

# Build and deploy
cd frontend
npm run build
netlify deploy --prod --dir=.next
```

### Environment Variables

Set these in your deployment platform:
- `NEXT_PUBLIC_API_URL` - Your production API URL
- `NEXT_PUBLIC_WS_URL` - Your WebSocket URL

## Next Steps

Now that your TV display is running, you can:

1. **Add More Animations** - Create new Remotion components
2. **Integrate Voice AI** - Connect OpenAI/Claude for natural language
3. **Add More Data** - Show tasks, calendar, analytics
4. **Customize Styling** - Match your brand colors
5. **Add Notifications** - Show alerts for important events

## Support

Need help? Check:
- `README.md` - General information
- GitHub Issues - Report bugs
- Remotion Docs - https://remotion.dev
- Next.js Docs - https://nextjs.org

---

**Enjoy your amazing AI Realtor TV display!** 🎬✨🏠
