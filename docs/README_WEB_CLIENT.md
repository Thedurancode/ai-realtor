# How to Use Nanobot Web Client

## Quick Start

1. Open the HTML file in your browser:
   ```bash
   open examples/web/nanobot-web-client.html
   ```

   Or double-click the file to open it.

2. The page will connect to Nanobot at `ws://localhost:18790/ws`

3. Type commands like:
   - "Show me all properties"
   - "Create a property at 123 Main St"
   - "Enrich property 5 with Zillow data"

## Requirements

- Nanobot must be running: `docker ps | grep nanobot`
- Port 18790 must be accessible

## Troubleshooting

### "Error connecting to Nanobot"

1. Check if Nanobot is running:
   ```bash
   docker ps | grep nanobot
   ```

2. Check if port is exposed:
   ```bash
   docker port nanobot-gateway
   ```

3. Check Nanobot logs:
   ```bash
   docker logs nanobot-gateway
   ```

### WebSocket not working

Nanobot might not have WebSocket enabled by default. You may need to check the Nanobot documentation for WebSocket configuration.

## Alternative: Use Terminal

The simplest way to use Nanobot is through the terminal:

```bash
docker exec -it nanobot-gateway nanobot agent
```

Then type your commands directly.
