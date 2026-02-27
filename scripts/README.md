# Scripts

Utility scripts for the RealtorClaw Platform.

## API Key Generator

Generate multiple API keys by hitting the `/register` endpoint. Useful for:
- Bulk API key creation for testing
- Pre-generating keys for distribution
- Load testing registration endpoint

### Quick Start

```bash
# Generate 109 API keys (default)
python scripts/generate_api_keys.py

# Generate 50 keys to custom location
python scripts/generate_api_keys.py --count 50 --output keys/test_batch.csv

# Target production server
python scripts/generate_api_keys.py --url https://ai-realtor.fly.dev --count 25

# High concurrency for faster generation
python scripts/generate_api_keys.py --count 200 --concurrent 20
```

### Output

Two CSV files are generated:

1. **`api_keys.csv`** - Successfully generated keys
   ```
   id,name,email,api_key,created_at
   1,API Agent 001,agent_001@api-generation.example.com,sk_live_abc123...,2026-02-27T10:30:00
   ```

2. **`api_keys_errors.csv`** - Failed registrations (if any)
   ```
   index,email,status,error
   5,agent_005@...,400,Email already registered
   ```

### Command-Line Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--count` | `-c` | 109 | Number of API keys to generate |
| `--output` | `-o` | api_keys.csv | Output CSV file path |
| `--url` | `-u` | http://localhost:8000 | API base URL |
| `--concurrent` | `-j` | 10 | Max concurrent requests |

### Examples

```bash
# Generate exactly 109 keys for production
python scripts/generate_api_keys.py \
  --count 109 \
  --url https://ai-realtor.fly.dev \
  --output production_keys_$(date +%Y%m%d).csv

# Quick test with 5 keys
python scripts/generate_api_keys.py --count 5 --output test.csv

# High-throughput generation (200 keys, 50 concurrent)
python scripts/generate_api_keys.py --count 200 --concurrent 50
```

### Notes

- **Email format**: Generated emails follow pattern: `agent_XXX@api-generation.example.com`
- **Concurrent requests**: Default is 10 concurrent to avoid overwhelming the server
- **Error handling**: Failed registrations are logged to separate error CSV
- **Confirmation**: Script asks for confirmation before starting (use `yes` command to bypass)

### Bypass Confirmation

For automation/cron jobs:

```bash
echo "y" | python scripts/generate_api_keys.py --count 109
```

Or use `yes`:

```bash
yes | python scripts/generate_api_keys.py --count 109
```

## Rate Limit Tester

Test rate limiting by making requests until hitting the limit.

### Quick Start

```bash
# Use first API key from api_keys.csv
python scripts/test_rate_limit.py

# Use specific API key
python scripts/test_rate_limit.py --key sk_live_abc123...

# Only check rate limit status
python scripts/test_rate_limit.py --check-only

# Test with custom request limit
python scripts/test_rate_limit.py --limit 30
```

### Command-Line Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--key` | `-k` | First from api_keys.csv | API key to use |
| `--url` | `-u` | http://localhost:8000 | API base URL |
| `--limit` | `-l` | 25 | Max requests to make |
| `--check-only` | - | false | Only check status, don't test |

### Output

```
🧪 Testing Rate Limiting
📡 Target: http://localhost:8000
🔑 API Key: sk_live_336641361f7a...
📊 Max Requests: 25
------------------------------------------------------------
✅ Request 1: Success (Remaining: 19)
✅ Request 2: Success (Remaining: 18)
...
⚠️  Request 21: RATE LIMITED (429)
   Response: {"detail": "Rate limit exceeded: 20 per 1 hour"}
------------------------------------------------------------
📊 RESULTS
✅ Successful: 20
⚠️  Rate Limited: Yes
⏱️  Elapsed: 4.52s
📈 Avg: 0.21s per request
```
