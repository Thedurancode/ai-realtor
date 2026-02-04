# AI Realtor TV Display

An amazing real-time TV display built with Next.js and Remotion that shows animated visualizations while speaking to your AI real estate agent.

## Features

- **Animated Agent Avatar**: Realistic avatar with speaking animations, eye blinks, and mouth movements
- **Real-time Audio Visualization**: Waveform displays that react to voice input
- **Live Contract Display**: Beautiful animated cards showing contract status and signer progress
- **Property Showcases**: Animated property cards with details and status
- **Real-time Updates**: Auto-polling backend every 5 seconds for latest data
- **TV-Optimized**: Large fonts, high contrast, and glass-morphism effects perfect for large displays

## Tech Stack

- **Next.js 14**: React framework with App Router
- **Remotion**: For stunning animations and real-time rendering
- **Framer Motion**: Additional animation capabilities
- **Zustand**: Lightweight state management
- **TailwindCSS**: Utility-first styling
- **TypeScript**: Type-safe development

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Start development server
npm run dev
```

The app will be available at `http://localhost:3025`

### Build for Production

```bash
npm run build
npm start
```

## Usage

### Demo Mode (Keyboard Controls)

For testing without voice integration:

- Press **`S`** to simulate the agent speaking
- Press **`Q`** to stop speaking

### Real Voice Integration

To connect real voice input, you'll need to:

1. **Add Web Audio API** for microphone input analysis
2. **Connect Speech-to-Text** service (e.g., OpenAI Whisper, Google Speech-to-Text)
3. **Set up WebSocket** connection to your backend for real-time updates
4. **Integrate with AI Assistant** (e.g., OpenAI Assistant, Anthropic Claude)

Example WebSocket setup is commented in `app/page.tsx`

### Connecting to Backend

The app expects your FastAPI backend running on port 8000 with these endpoints:

- `GET /contracts/` - List all contracts
- `GET /contracts/{id}` - Get contract details
- `GET /contracts/{id}/status` - Get contract status
- `GET /properties/` - List all properties
- `POST /voice/send-contract` - Send contract via voice
- `POST /voice/create-property` - Create property via voice

## Architecture

```
frontend/
├── app/                      # Next.js App Router
│   ├── page.tsx             # Main TV display page
│   ├── layout.tsx           # Root layout
│   └── globals.css          # Global styles
├── components/
│   ├── TVDisplay.tsx        # Main TV display component
│   └── remotion/            # Remotion animated components
│       ├── AgentAvatar.tsx       # Animated agent face
│       ├── AgentComposition.tsx  # Main composition
│       ├── AudioWaveform.tsx     # Audio visualization
│       ├── ContractCard.tsx      # Contract display
│       └── PropertyCard.tsx      # Property display
├── lib/
│   └── api.ts               # API client
└── store/
    └── useAgentStore.ts     # Global state management
```

## Customization

### Changing Colors

Edit `tailwind.config.js`:

```js
theme: {
  extend: {
    colors: {
      primary: '#3B82F6',    // Blue
      secondary: '#8B5CF6',  // Purple
      accent: '#10B981',     // Green
    },
  },
}
```

### Adjusting Animations

Remotion components in `components/remotion/` can be customized:

- **Avatar appearance**: Modify `AgentAvatar.tsx`
- **Waveform style**: Adjust `AudioWaveform.tsx`
- **Card animations**: Edit `ContractCard.tsx` and `PropertyCard.tsx`

### Polling Interval

Change data refresh rate in `TVDisplay.tsx`:

```typescript
// Poll every 5 seconds (5000ms)
const interval = setInterval(async () => {
  // ... fetch data
}, 5000)
```

## Real-time Features

### WebSocket Integration

Add to your backend (FastAPI example):

```python
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        # Send updates to frontend
        await websocket.send_json({
            "type": "agent_speaking",
            "message": "Processing your request...",
            "audioLevel": 0.75
        })
```

Connect in frontend (`app/page.tsx`):

```typescript
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/ws')

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    setIsSpeaking(data.type === 'agent_speaking')
    setCurrentMessage(data.message)
    setAudioLevel(data.audioLevel)
  }

  return () => ws.close()
}, [])
```

### Audio Input Analysis

Use Web Audio API to analyze microphone input:

```typescript
const audioContext = new AudioContext()
const analyser = audioContext.createAnalyser()

navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => {
    const source = audioContext.createMediaStreamSource(stream)
    source.connect(analyser)

    const dataArray = new Uint8Array(analyser.frequencyBinCount)

    const analyze = () => {
      analyser.getByteFrequencyData(dataArray)
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length
      setAudioLevel(average / 255)
      requestAnimationFrame(analyze)
    }

    analyze()
  })
```

## TV Display Setup

For optimal TV display:

1. **Connect your computer to TV via HDMI**
2. **Set browser to fullscreen** (F11)
3. **Adjust display settings** for large screens
4. **Disable screen sleep** in system settings
5. **Use 1920x1080 or higher resolution**

## Performance Optimization

- Remotion uses GPU acceleration for smooth 60fps animations
- React components are memoized to prevent unnecessary re-renders
- Polling is optimized to only update changed data
- TailwindCSS purges unused styles in production

## Troubleshooting

### Avatar not animating
- Check that Remotion Player is rendering correctly
- Verify `isSpeaking` state is being updated
- Check browser console for errors

### No data showing
- Ensure backend is running on `http://localhost:8000`
- Check API responses in Network tab
- Verify CORS is enabled on backend

### Slow performance
- Reduce polling interval
- Disable animations on lower-end hardware
- Use production build instead of dev mode

## Contributing

To add new features:

1. Create new Remotion components in `components/remotion/`
2. Add state to `store/useAgentStore.ts`
3. Update `TVDisplay.tsx` to include new components
4. Test with demo keyboard controls first

## License

MIT

## Support

For issues or questions, please open an issue on GitHub.

---

**Built with Remotion and Next.js for stunning real-time visualizations** 🎬✨
