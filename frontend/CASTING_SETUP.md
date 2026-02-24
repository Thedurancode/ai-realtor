# Chromecast & AirPlay Setup Guide

## Overview

The AI Realtor TV Display now supports **Google Chromecast** and **Apple AirPlay** for wireless streaming to your TV!

---

## 📺 Quick Start

### AirPlay (Easiest - No Setup Required)

**Requirements:**
- Apple TV, AirPlay-compatible smart TV, or receiver
- Safari browser on macOS/iOS

**Steps:**
1. Open AI Realtor TV Display in Safari
2. Click the cast button (top-right corner)
3. Select your Apple TV or AirPlay device
4. Start streaming!

**Supported Devices:**
- Apple TV (4th gen and later)
- AirPlay 2-compatible smart TVs (Samsung, LG, Sony, Vizio, etc.)
- HomePod

---

### Chromecast (Requires Setup)

**Requirements:**
- Chromecast, Chromecast Ultra, or built-in Cast TV
- Chrome, Edge, or Firefox browser

**Setup Steps:**

#### 1. Register Your Chromecast App (One-Time)

**For Development (No Registration):**
- Leave `NEXT_PUBLIC_CHROMECAST_APP_ID` empty
- Works with default Cast receiver
- **Limitation:** Shows "Cast SDK" message while casting

**For Production (Registered):**
1. Go to [Google Cast SDK Developer Console](https://cast.google.com/publish)
2. Sign in with your Google account
3. Click "Add new application"
4. Choose "Custom Receiver"
5. Fill in:
   - Application Name: `AI Realtor TV Display`
   - Application ID: `YOUR_APP_ID`
6. Copy the Application ID
7. Add to `.env.local`:
   ```bash
   NEXT_PUBLIC_CHROMECAST_APP_ID=YOUR_APP_ID_HERE
   ```

#### 2. Configure Environment

```bash
cd frontend
cp .env.example .env.local
```

Edit `.env.local`:
```bash
NEXT_PUBLIC_CHROMECAST_APP_ID=YOUR_APP_ID_HERE
```

#### 3. Start the App

```bash
npm run dev
```

#### 4. Start Casting

1. Open http://localhost:3025 in Chrome/Edge
2. Click the cast button (top-right)
3. Select your Chromecast device
4. Enjoy!

**Supported Devices:**
- Chromecast (3rd gen and later)
- Chromecast Ultra
- Chromecast with Google TV
- Built-in Cast on TVs (Android TV, Google TV)

---

## 🎨 Cast Button Features

### Cast Button Location
- **Fixed Position:** Top-right corner of the screen
- **Always Visible:** On all pages

### Visual States

1. **Disconnected (Default)**
   - White background with gray cast icon
   - Hover effect: Slight lift animation

2. **Scanning**
   - Pulsing animation
   - Shows available devices

3. **Connected**
   - Gradient blue-to-purple background
   - Animated pulse effect
   - Shows device name

### Device Menu

When you click the cast button, you'll see:

- **Connected:** Device name with disconnect button
- **Disconnected:** List of available devices
- **Instructions:** Tips for best quality

---

## 🔧 Troubleshooting

### Chromecast Issues

**No devices found:**
- ✓ Make sure Chromecast is on the same Wi-Fi network
- ✓ Check if Chromecast is powered on
- ✓ Try restarting Chromecast (unplug for 10 seconds)
- ✓ Disable VPN or proxy
- ✓ Check firewall settings (port 8008-8009)

**"Cast SDK" message appears:**
- ✓ Register your app at https://cast.google.com/publish
- ✓ Add your App ID to `.env.local`
- ✓ Restart the dev server

**Connection drops:**
- ✓ Check Wi-Fi signal strength
- ✓ Move router closer to Chromecast
- ✓ Update Chromecast firmware

### AirPlay Issues

**AirPlay icon not showing:**
- ✓ Use Safari browser (Chrome/Edge don't support AirPlay)
- ✓ Check macOS version (10.15+ required)
- ✓ Verify Apple TV is on same network
- ✓ Update Apple TV software

**Can't connect to Apple TV:**
- ✓ Make sure AirPlay is enabled on Apple TV
- ✓ Check Apple TV: Settings > AirPlay > On
- ✓ Restart Apple TV
- ✓ Check for software updates

---

## 📱 Browser Compatibility

| Feature | Chrome | Edge | Firefox | Safari |
|---------|--------|------|---------|--------|
| Chromecast | ✓ | ✓ | ✓ | ✗ |
| AirPlay | ✗ | ✗ | ✗ | ✓ |
| Both Supported | ✗ | ✗ | ✗ | ✓ |

**Recommendations:**
- **Chromecast:** Use Chrome or Edge
- **AirPlay:** Use Safari on macOS/iOS
- **Best Quality:** Safari with AirPlay (native support)

---

## 🎬 Casting Features

### What Gets Streamed

When casting, your TV will show:
- ✓ Animated agent avatar
- ✓ Real-time audio visualizations
- ✓ Live property cards
- ✓ Contract status displays
- ✓ All animations and transitions
- ✓ Auto-refreshing data

### Performance Tips

**For Best Quality:**
- Use wired Ethernet connection
- 5 GHz Wi-Fi (not 2.4 GHz)
- Strong router signal
- Close other bandwidth-heavy apps

**Lag Issues:**
- Reduce polling interval in `TVDisplay.tsx`
- Disable animations on slower connections
- Use 1080p instead of 4K

---

## 🔐 Security & Privacy

### Network Requirements

**Same Network Only:**
- Casting device and TV must be on same Wi-Fi
- No cross-network casting (security feature)

### Firewall Ports

If casting doesn't work, check these ports:

**Chromecast:**
- TCP 8008-8009 (communication)
- UDP 1900, 5353 (discovery)

**AirPlay:**
- TCP 7000, 7100, 49152-65535
- UDP 6000-6001, 6010, 7011

---

## 📚 Advanced Configuration

### Custom Cast Receiver

For production use, you can create a custom Cast receiver app:

1. Create a receiver app HTML file
2. Host on HTTPS server (required)
3. Register at Google Cast Console
4. Update `NEXT_PUBLIC_CHROMECAST_APP_ID`

### Auto-Cast on Load

To automatically start casting when page loads:

```typescript
// Add to useCast.ts
useEffect(() => {
  const lastDevice = localStorage.getItem('lastCastDevice');
  if (lastDevice) {
    const device = JSON.parse(lastDevice);
    startCast(device);
  }
}, []);
```

---

## 🎯 Use Cases

### Real Estate Office
- Cast to lobby TV for live property updates
- Show animated deal pipeline
- Display agent performance metrics

### Open House
- Stream property details to living room TV
- Show interactive property cards
- Engage buyers with visualizations

### Home Office
- Mirror display to secondary monitor
- Keep eye on operations while working
- Full-screen agent conversations

---

## 🆘 Getting Help

**Chromecast Support:**
- [Google Cast SDK Documentation](https://developers.google.com/cast/docs)
- [Chromecast Help Center](https://support.google.com/chromecast)

**AirPlay Support:**
- [Apple AirPlay Documentation](https://support.apple.com/guide/airplay/welcome/web)

**AI Realtor Support:**
- GitHub Issues: https://github.com/Thedurancode/ai-realtor/issues
- Documentation: Check `/frontend/README.md`

---

## 📝 Changelog

**v1.0.0** (Current)
- ✓ Chromecast support (Chrome/Edge/Firefox)
- ✓ AirPlay support (Safari)
- ✓ Floating cast button
- ✓ Device menu
- ✓ Connection status
- ✓ Visual feedback

---

**Happy Casting!** 🎉📺
