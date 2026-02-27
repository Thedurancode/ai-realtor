# Rate Limiting Configuration

The RealtorClaw API supports per-agent rate limiting with configurable tiers and easy on/off toggling.

## Quick Start

### Enable Rate Limiting (Default)

```bash
# .env file
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=20/hour

# Or environment variable
export RATE_LIMIT_ENABLED=true
export RATE_LIMIT_DEFAULT=20/hour
```

### Disable Rate Limiting

```bash
# .env file
RATE_LIMIT_ENABLED=false

# Or environment variable
export RATE_LIMIT_ENABLED=false
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_ENABLED` | `true` | Toggle rate limiting on/off |
| `RATE_LIMIT_DEFAULT` | `20/hour` | Default limit per agent |
| `RATE_LIMIT_BURST` | `30/minute` | Short-term burst limit |
| `RATE_LIMIT_FREE` | `20/hour` | Free tier agents |
| `RATE_LIMIT_PRO` | `100/hour` | Pro tier agents |
| `RATE_LIMIT_ENTERPRISE` | `1000/hour` | Enterprise tier agents |

### Rate Limit Format

Rate limits use the format: `{number}/{period}`

**Periods:**
- `second` - per second
- `minute` - per minute
- `hour` - per hour
- `day` - per day
- `month` - per month

**Examples:**
- `20/hour` - 20 requests per hour
- `100/day` - 100 requests per day
- `5/minute` - 5 requests per minute
- `1000/month` - 1000 requests per month

## How It Works

### Per-Agent Rate Limiting

Rate limits are applied **per agent** (based on API key), not per IP address.

**How it works:**
1. Agent makes request with `Authorization: Bearer sk_live_...`
2. System extracts agent ID from API key
3. Checks rate limit for that agent ID
4. If under limit: request proceeds
5. If over limit: returns `429 Too Many Requests`

### Rate Limit Tiers

Agents can be assigned different rate limit tiers:

```python
# Free tier (default)
RATE_LIMIT_FREE=20/hour

# Pro tier
RATE_LIMIT_PRO=100/hour

# Enterprise tier
RATE_LIMIT_ENTERPRISE=1000/hour
```

### Checking Rate Limit Status

```bash
curl http://localhost:8000/rate-limit
```

**Response:**
```json
{
  "rate_limiting": {
    "enabled": true,
    "message": "Rate limiting is ENABLED"
  },
  "limits": {
    "default": "20/hour",
    "burst": "30/minute"
  },
  "tiers": {
    "free": "20/hour",
    "pro": "100/hour",
    "enterprise": "1000/hour"
  }
}
```

## Examples

### 20 Requests Per Hour (Default)

```bash
# .env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=20/hour
```

### 100 Requests Per Day

```bash
# .env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100/day
```

### Multiple Time Windows

You can specify multiple limits for different time windows:

```bash
# .env
RATE_LIMIT_BURST=5/minute      # Allow bursts of 5 per minute
RATE_LIMIT_DEFAULT=100/hour    # But max 100 per hour
```

### Tiered Access

```bash
# .env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_FREE=20/hour
RATE_LIMIT_PRO=500/hour
RATE_LIMIT_ENTERPRISE=5000/hour
```

## API Response

When rate limited, the API returns:

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 3600

{
  "detail": "Rate limit exceeded: 20 per 1 hour"
}
```

## Headers

Rate limit information is included in response headers:

```http
X-RateLimit-Enabled: true
X-RateLimit-Tier: free
X-RateLimit-Default: 20/hour
```

## Troubleshooting

### Check if Rate Limiting is Enabled

```bash
curl http://localhost:8000/rate-limit
```

### Test Rate Limiting

```bash
# Make requests until you hit the limit
API_KEY="sk_live_..."
for i in {1..25}; do
  curl -H "Authorization: Bearer $API_KEY" http://localhost:8000/properties
done
```

### Disable for Development

```bash
# .env
RATE_LIMIT_ENABLED=false
```

### Reset Rate Limits (Redis)

If using Redis for rate limit storage:

```bash
# Clear all rate limits
redis-cli FLUSHALL

# Or clear specific agent
redis-cli DEL "limiter:agent:123"
```

## Production Deployment

### Using Redis for Distributed Rate Limiting

```bash
# .env
RATE_LIMIT_STORAGE_URI=redis://localhost:6379/0
```

This allows rate limiting to work across multiple server instances.

### Fly.io Deployment

```bash
# Set via fly secrets
fly secrets set RATE_LIMIT_ENABLED=true --app ai-realtor
fly secrets set RATE_LIMIT_DEFAULT=20/hour --app ai-realtor
```

## Best Practices

1. **Start with default limits** - 20/hour is reasonable for most use cases
2. **Use Redis in production** - For distributed systems
3. **Monitor rate limits** - Check `/rate-limit` endpoint regularly
4. **Set appropriate tiers** - Match limits to pricing tiers
5. **Communicate limits** - Document rate limits for API users

## Changing Limits at Runtime

Rate limits can be changed without restarting the server by updating environment variables and reloading:

```bash
# Update .env file
echo "RATE_LIMIT_DEFAULT=100/hour" >> .env

# Reload (if using hot-reload)
# Or restart server
uvicorn app.main:app --reload
```

## Monitoring

Check your rate limit usage:

```bash
# Get rate limit status
curl http://localhost:8000/rate-limit

# Monitor 429 responses in logs
grep "429" logs/app.log
```

## Disabling for Specific Endpoints

To exempt certain endpoints from rate limiting, add them to `PUBLIC_PATHS` in `main.py`:

```python
PUBLIC_PATHS = frozenset((
    "/",
    "/docs",
    "/redoc",
    "/webhooks/",  # Webhooks exempt from rate limiting
))
```
