# AgentClaw API - Landing Page

Modern, dark-themed SaaS landing page for AgentClaw API.

## Features

- ✅ Modern dark design with gradient accents
- ✅ Fully responsive (mobile, tablet, desktop)
- ✅ Smooth scroll animations
- ✅ Interactive pricing cards
- ✅ FAQ accordion
- ✅ Integration showcase
- ✅ Code preview window
- ✅ Hero section with stats
- ✅ Features grid
- ✅ Benefits section
- ✅ CTA sections

## Pricing Tiers

### Starter ($99 one-time)
- Complete API access
- Self-hosted
- Self-installed
- Free lifetime updates

### Professional ($299 one-time)
- Everything in Starter
- We help install
- Email support
- Free lifetime updates

### Enterprise ($500/year)
- Everything in Professional
- We host & maintain
- Priority support
- 99.9% uptime SLA
- Free lifetime updates

## Quick Start

### Option 1: Open Directly

Simply open `index.html` in your browser:

```bash
# macOS
open landing-page/index.html

# Linux
xdg-open landing-page/index.html

# Windows
start landing-page/index.html
```

### Option 2: Local Server

For best results, use a local server:

```bash
# Python 3
python3 -m http.server 8000 --directory landing-page

# Node.js (with npx)
npx serve landing-page

# PHP
php -S localhost:8000 -t landing-page
```

Then visit: http://localhost:8000

## Files

```
landing-page/
├── index.html    # Main HTML file
├── styles.css    # Dark theme styles
├── script.js     # Interactions & animations
└── README.md     # This file
```

## Customization

### Update Colors

Edit `styles.css` variables:

```css
:root {
    --accent-primary: #f97316;    /* Orange */
    --bg-primary: #0a0a0b;        /* Dark background */
    --text-primary: #ffffff;      /* White text */
}
```

### Update Content

Edit `index.html`:
- Hero text and stats
- Feature cards
- Pricing tiers
- FAQ items
- Footer links

### Update Pricing

Find the `.pricing-grid` section in `index.html` and modify:
- Price values
- Feature lists
- Plan names

## Deployment

### Static Hosting (Recommended)

Deploy to any static hosting service:

**Vercel:**
```bash
cd landing-page
vercel deploy
```

**Netlify:**
```bash
cd landing-page
netlify deploy
```

**GitHub Pages:**
1. Push to repository
2. Enable GitHub Pages
3. Select `landing-page` folder as source

### Custom Domain

Add a `CNAME` file in the landing-page folder:
```
api.agentclaw.com
```

## Performance

- ✅ No dependencies
- ✅ Minimal CSS (~15KB)
- ✅ Vanilla JavaScript (~5KB)
- ✅ Inline SVG icons
- ✅ Optimized fonts (Inter)
- ✅ Lazy loading animations
- ✅ Mobile-first responsive

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Opera 76+

## Analytics

Add your analytics code to `index.html` before the closing `</body>` tag:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

## License

Included with AgentClaw API license.
