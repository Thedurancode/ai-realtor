# 🚀 Deployment Guide - AI Realtor with Remotion Rendering

Complete guide to deploy the AI Realtor platform with video rendering capabilities.

## Local Development (Docker Compose)

### Prerequisites
- Docker and Docker Compose installed
- API keys in `.env` file (see `.env.example`)

### Quick Start

1. **Create `.env` file:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

2. **Start all services:**
```bash
docker-compose up -d
```

This starts:
- PostgreSQL (port 5433)
- Redis (port 6379)
- AI Realtor API (port 8000) with render worker

3. **View logs:**
```bash
# All logs
docker-compose logs -f

# API only
docker-compose logs -f app

# Worker only
docker-compose exec app tail -f /app/log/worker.log
```

4. **Access API:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Render endpoints: http://localhost:8000/v1/renders

### Stopping Services

```bash
docker-compose down

# With volumes
docker-compose down -v
```

## Production Deployment (Fly.io)

### Prerequisites
- Fly.io CLI installed: `curl -L https://fly.io/install.sh | sh`
- Fly.io account: `fly auth login`
- AWS S3 bucket (for video storage)

### Setup

1. **Create S3 Bucket:**
```bash
aws s3 mb s3://ai-realtor-renders --region us-east-1
```

2. **Set Fly.io secrets:**
```bash
fly secrets set DATABASE_URL=postgresql://... \
  ANTHROPIC_API_KEY=sk-ant-... \
  GOOGLE_PLACES_API_KEY=... \
  REDIS_HOST=your-redis.fly.io \
  REDIS_PORT=6379 \
  AWS_ACCESS_KEY_ID=... \
  AWS_SECRET_ACCESS_KEY=... \
  AWS_S3_BUCKET=ai-realtor-renders
```

3. **Create Redis on Fly.io:**
```bash
fly redis create --name ai-realtor-redis --region ewr
```

4. **Deploy:**
```bash
fly deploy
```

5. **Check status:**
```bash
fly status
fly logs
```

### Scaling

```bash
# Scale to 2GB RAM, 2 CPUs
fly scale memory 2048 --vm-size shared-cpu-2x

# Scale regions
fly scale count ewr=2 sfo=1
```

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@host:5432/db` |
| `REDIS_HOST` | Redis host | `localhost` or `redis.fly.io` |
| `REDIS_PORT` | Redis port | `6379` |
| `ANTHROPIC_API_KEY` | Claude AI key | `sk-ant-xxxxx` |

### Optional (for Rendering)

| Variable | Description | Default |
|----------|-------------|---------|
| `WORKER_ENABLED` | Enable render worker | `1` |
| `WORKER_CONCURRENCY` | Parallel renders | `1` |
| `AWS_ACCESS_KEY_ID` | AWS key | - |
| `AWS_SECRET_ACCESS_KEY` | AWS secret | - |
| `AWS_S3_BUCKET` | S3 bucket | `ai-realtor-renders` |
| `AWS_REGION` | AWS region | `us-east-1` |

### Optional (API Features)

| Variable | Description |
|----------|-------------|
| `GOOGLE_PLACES_API_KEY` | Address autocomplete |
| `ZILLOW_API_KEY` | Property enrichment |
| `SKIP_TRACE_API_KEY` | Owner discovery |
| `DOCUSEAL_API_KEY` | E-signatures |
| `VAPI_API_KEY` | Phone calls |

## Health Checks

### API Health
```bash
curl http://localhost:8000/docs
```

### Redis Health
```bash
docker exec -it ai_realtor_redis redis-cli ping
```

### PostgreSQL Health
```bash
docker exec -it ai_realtor_postgres pg_isready -U postgres
```

### Worker Health
```bash
docker exec -it ai_realtor_app tail -20 /app/log/worker.log
```

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker-compose logs app
```

**Common issues:**
1. Database not ready → Wait for `postgres` healthcheck
2. Redis not ready → Wait for `redis` healthcheck
3. Port conflict → Change ports in `docker-compose.yml`

### Worker Not Processing Jobs

**Check Redis:**
```bash
docker exec -it ai_realtor_redis redis-cli
> LLEN render-jobs
> LRANGE render-jobs 0 -1
```

**Check worker logs:**
```bash
docker exec -it ai_realtor_app cat /app/log/worker.log
```

### Remotion Render Fails

**Check Node.js:**
```bash
docker exec -it ai_realtor_app node --version
docker exec -it ai_realtor_app npx remotion --help
```

**Check temp directory:**
```bash
docker exec -it ai_realtor_app ls -la /app/tmp
```

### S3 Upload Fails

**Test S3 connection:**
```bash
docker exec -it ai_realtor_app python -c "
import boto3, os
s3 = boto3.client('s3')
print(s3.list_buckets())
"
```

**Check credentials:**
```bash
docker exec -it ai_realtor_app env | grep AWS
```

## Monitoring

### View Render Jobs

```bash
# Via API
curl http://localhost:8000/v1/renders \
  -H "X-API-Key: your-key"

# Via DB
docker exec -it ai_realtor_postgres psql -U postgres -d ai_realtor \
  -c "SELECT id, status, progress FROM render_jobs ORDER BY created_at DESC LIMIT 10;"
```

### Redis Queue Stats

```bash
docker exec -it ai_realtor_redis redis-cli
> SCARD bull:render-jobs:waiting
> SCARD bull:render-jobs:active
```

### Performance

**Container stats:**
```bash
docker stats ai_realtor_app
```

**Disk usage:**
```bash
docker exec -it ai_realtor_app df -h
```

## Backup & Restore

### PostgreSQL Backup

```bash
# Backup
docker exec -it ai_realtor_postgres pg_dump -U postgres ai_realtor > backup.sql

# Restore
docker exec -i ai_realtor_postgres psql -U postgres ai_realtor < backup.sql
```

### S3 Sync

```bash
# Sync all renders
aws s3 sync s3://ai-realtor-renders ./backups/

# List renders
aws s3 ls s3://ai-realtor-renders/renders/ --recursive
```

## Security

### Best Practices

1. **Use secrets management:**
   - Fly.io: `fly secrets set`
   - Docker Compose: Use `.env` (never commit)

2. **Enable HTTPS:**
   - Fly.io: Automatic
   - Self-hosted: Use Traefik/Nginx

3. **API key rotation:**
   ```bash
   # Generate new key
   fly secrets set API_KEY_HASH=...

   # Update agent records
   ```

4. **Network isolation:**
   - Redis: Internal only
   - PostgreSQL: Internal only
   - API: Public only

5. **Rate limiting:**
   - Already enabled with `slowapi`
   - Configure in `app/rate_limit.py`

## Performance Tuning

### Worker Concurrency

```bash
# docker-compose.yml
environment:
  WORKER_CONCURRENCY: 2  # 2 parallel renders
```

### Memory Limits

```yaml
# fly.toml
[[vm]]
  memory = '4gb'  # Increase for heavy rendering
  cpus = 4
```

### Database Pooling

```python
# app/database.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40
)
```

## CI/CD

### GitHub Actions Example

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Fly.io
        uses: superfly/flyctl-actions@master
        with:
          args: "deploy --remote-only"
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

## Cost Estimates

### Fly.io (Monthly)
- 1GB RAM, 1 CPU: ~$5-15/month
- 2GB RAM, 2 CPUs: ~$20-30/month
- Redis: ~$10-20/month
- **Total: ~$35-65/month**

### AWS S3 (Monthly)
- Storage: $0.023/GB
- 100 renders × 50MB = 5GB = ~$0.12/month
- Requests: Negligible

### Self-Hosted (Monthly)
- VPS (4GB RAM, 2 CPUs): ~$20-40/month
- **Total: ~$20-40/month**

## Support

- GitHub: https://github.com/Thedurancode/ai-realtor
- Issues: https://github.com/Thedurancode/ai-realtor/issues
- Live API: https://ai-realtor.fly.dev
