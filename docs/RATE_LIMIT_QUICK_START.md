# 🚦 Rate Limiting - Quick Reference

## Toggle Rate Limiting On/Off

### Disable (No Limits)
```bash
# .env file
RATE_LIMIT_ENABLED=false

# Or via environment variable
export RATE_LIMIT_ENABLED=false
```

### Enable (Default: 20/hour per agent)
```bash
# .env file
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=20/hour

# Or via environment variable
export RATE_LIMIT_ENABLED=true
export RATE_LIMIT_DEFAULT=20/hour
```

## Check Current Status

```bash
curl http://localhost:8000/rate-limit
```

## Test Rate Limiting

```bash
# Use first API key from csv
python scripts/test_rate_limit.py

# Use specific API key
python scripts/test_rate_limit.py --key sk_live_abc123...

# Check status only
python scripts/test_rate_limit.py --check-only
```

## Common Configurations

### 20 Requests Per Hour (Default)
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=20/hour
```

### 100 Requests Per Day
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100/day
```

### Tiered Access
```bash
RATE_LIMIT_FREE=20/hour
RATE_LIMIT_PRO=100/hour
RATE_LIMIT_ENTERPRISE=1000/hour
```

### Burst + Sustained
```bash
RATE_LIMIT_BURST=5/minute      # Allow bursts of 5/min
RATE_LIMIT_DEFAULT=100/hour    # But max 100/hour
```

## Rate Limit Format

`{number}/{period}`

**Periods:** `second`, `minute`, `hour`, `day`, `month`

**Examples:**
- `20/hour` - 20 requests per hour
- `100/day` - 100 requests per day
- `5/minute` - 5 requests per minute

## How It Works

1. ✅ Agent makes request with API key
2. 🔑 System extracts agent ID from API key
3. 📊 Checks rate limit for that agent
4. ✅ If under limit → request proceeds
5. ⚠️ If over limit → returns `429 Too Many Requests`

## When Rate Limited

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 3600

{
  "detail": "Rate limit exceeded: 20 per 1 hour"
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_ENABLED` | `true` | Toggle on/off |
| `RATE_LIMIT_DEFAULT` | `20/hour` | Default limit |
| `RATE_LIMIT_BURST` | `30/minute` | Burst limit |
| `RATE_LIMIT_FREE` | `20/hour` | Free tier |
| `RATE_LIMIT_PRO` | `100/hour` | Pro tier |
| `RATE_LIMIT_ENTERPRISE` | `1000/hour` | Enterprise tier |

## Fly.io Deployment

```bash
# Enable rate limiting
fly secrets set RATE_LIMIT_ENABLED=true --app ai-realtor

# Set custom limit
fly secrets set RATE_LIMIT_DEFAULT=100/hour --app ai-realtor

# Disable
fly secrets set RATE_LIMIT_ENABLED=false --app ai-realtor
```

## Full Documentation

See [docs/RATE_LIMITING.md](./RATE_LIMITING.md) for complete documentation.
