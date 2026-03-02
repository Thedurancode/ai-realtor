# 🎬 Docker Setup - Quick Start

## One-Command Launch

```bash
docker-compose up -d
```

That's it! This starts:
- ✅ PostgreSQL database
- ✅ Redis (for render queue)
- ✅ AI Realtor API (port 8000)
- ✅ Remotion render worker (background)

## What's Running

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8000 | Main API + render endpoints |
| Docs | http://localhost:8000/docs | Interactive API documentation |
| Worker | (background) | Processes video renders |
| PostgreSQL | localhost:5433 | Database |
| Redis | localhost:6379 | Job queue |

## Your First Render

```bash
curl -X POST "http://localhost:8000/v1/renders" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk_live_your-key" \
  -d '{
    "template_id": "captioned-reel",
    "composition_id": "CaptionedReel",
    "input_props": {
      "title": "Luxury Property",
      "subtitle": "$450,000 - Miami Beach",
      "backgroundUrl": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1080"
    }
  }'
```

## View Logs

```bash
# All services
docker-compose logs -f

# API only
docker-compose logs -f app

# Worker only
docker-compose exec app tail -f /app/log/worker.log

# Specific service
docker-compose logs -f postgres
docker-compose logs -f redis
```

## Stop Everything

```bash
docker-compose down

# With volumes (wipes database)
docker-compose down -v
```

## Environment Setup

Create `.env` file:

```bash
# Required
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ai_realtor
ANTHROPIC_API_KEY=sk-ant-your-key

# Optional (for rendering)
WORKER_ENABLED=1
REDIS_HOST=redis
REDIS_PORT=6379
WORKER_CONCURRENCY=1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_S3_BUCKET=ai-realtor-renders
```

## Troubleshooting

### Check if services are running:
```bash
docker-compose ps
```

### Restart a service:
```bash
docker-compose restart app
```

### Rebuild after code changes:
```bash
docker-compose up -d --build
```

### Enter container:
```bash
docker-compose exec app bash
```

## Next Steps

- 📖 [Full Deployment Guide](./DEPLOYMENT_GUIDE.md)
- 🎬 [Remotion Documentation](./REMOTION_README.md)
- ⚡ [Remotion Quickstart](./REMOTION_QUICKSTART.md)
