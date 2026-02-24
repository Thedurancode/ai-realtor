# 🐳 AI Realtor - Docker SQLite Guide

Complete guide to running AI Realtor with SQLite in Docker - the easiest way to get started!

---

## 🎯 Why SQLite + Docker?

### Benefits

| Feature | SQLite + Docker | PostgreSQL |
|---------|-----------------|------------|
| **Setup Time** | ⚡ 1 command | 🔧 5-10 minutes |
| **Configuration** | ✅ Zero config | ⚠️ Database setup required |
| **Portability** | ✅ Single file | ❌ Server-based |
| **Performance** | ⚡ Great for single-user | 🚀 Better for concurrent |
| **Development** | ✅ Perfect | ⚠️ Overkill |
| **Production** | ⚠️ Small scale | ✅ Recommended |
| **Backups** | ✅ Copy file | ⚠️ Dump required |
| **Memory** | ✅ ~50MB | ❌ ~200MB+ |

### Perfect For

- ✅ **Local development** and testing
- ✅ **Personal use** or small deployments
- ✅ **Quick demos** and presentations
- ✅ **CI/CD pipelines** (fast setup)
- ✅ **Edge deployments** (limited resources)

### Not Recommended For

- ❌ High-traffic production sites (use PostgreSQL instead)
- ❌ Multiple concurrent users (write locks)
- ❌ Complex write operations

---

## 🚀 Quick Start (30 seconds)

### Option 1: Automated Setup (Recommended)

```bash
# Make the script executable
chmod +x docker-quick-start-sqlite.sh

# Run it!
./docker-quick-start-sqlite.sh
```

That's it! The app will be running at http://localhost:8000

---

### Option 2: Manual Setup

```bash
# 1. Build and start with Docker Compose
docker compose -f docker-compose.sqlite.yml up -d

# 2. View logs
docker compose -f docker-compose.sqlite.yml logs -f

# 3. Open browser
open http://localhost:8000/docs
```

---

## 📋 Prerequisites

- **Docker** (20.10+)
- **Docker Compose** (2.0+)
- **2GB RAM** minimum
- **1GB disk space**

### Check Installation

```bash
docker --version
docker compose version
```

---

## 🔧 Configuration

### Environment Variables

Edit `docker-compose.sqlite.yml` or create a `.env` file:

```bash
# Required for AI features
ANTHROPIC_API_KEY=sk-ant-xxx
GOOGLE_PLACES_API_KEY=xxx
RAPIDAPI_KEY=xxx

# Optional - for additional features
DOCUSEAL_API_KEY=xxx
VAPI_API_KEY=xxx
ELEVENLABS_API_KEY=xxx
EXA_API_KEY=xxx
```

### Minimum Working Setup

The app will start without API keys, but these features won't work:
- ❌ Property address lookup (need Google Places)
- ❌ Property enrichment (need RapidAPI + Zillow)
- ❌ Skip tracing (need RapidAPI)
- ❌ AI recaps and analysis (need Anthropic)

---

## 📂 File Structure

```
ai-realtor/
├── Dockerfile.sqlite              # SQLite-optimized Docker image
├── docker-compose.sqlite.yml      # Docker Compose configuration
├── start-sqlite.sh               # Enhanced startup script
├── docker-quick-start-sqlite.sh  # One-command setup
├── app/                          # Application code
│   ├── main.py                   # FastAPI app
│   ├── models/                   # Database models
│   ├── routers/                  # API endpoints
│   └── services/                 # Business logic
└── data/                         # (Created by Docker)
    └── ai_realtor.db            # SQLite database (in volume)
```

---

## 🐘 Common Commands

### Container Management

```bash
# Start the app
docker compose -f docker-compose.sqlite.yml up -d

# Stop the app
docker compose -f docker-compose.sqlite.yml down

# Restart the app
docker compose -f docker-compose.sqlite.yml restart

# Rebuild after code changes
docker compose -f docker-compose.sqlite.yml up -d --build

# View logs
docker compose -f docker-compose.sqlite.yml logs -f

# View logs for specific service
docker compose -f docker-compose.sqlite.yml logs -f ai-realtor

# Shell access into container
docker exec -it ai-realtor-sqlite bash
```

### Database Operations

```bash
# Access SQLite shell inside container
docker exec -it ai-realtor-sqlite sqlite3 /app/data/ai_realtor.db

# Backup database
docker exec ai-realtor-sqlite cp /app/data/ai_realtor.db /app/data/backups/ai_realtor_$(date +%Y%m%d).db

# Copy database to local machine
docker cp ai-realtor-sqlite:/app/data/ai_realtor.db ./ai_realtor_backup.db

# Copy local database to container
docker cp ./ai_realtor_backup.db ai-realtor-sqlite:/app/data/ai_realtor.db
```

### Volume Management

```bash
# List volumes
docker volume ls | grep ai_realtor

# Inspect volume
docker volume inspect ai_realtor_sqlite_data

# Delete volume (⚠️ deletes all data!)
docker volume rm ai_realtor_sqlite_data

# Backup entire volume
docker run --rm -v ai_realtor_sqlite_data:/data -v $(pwd):/backup ubuntu tar czf /backup/ai_realtor_backup.tar.gz /data
```

---

## 🔍 Troubleshooting

### Container won't start

```bash
# Check logs
docker compose -f docker-compose.sqlite.yml logs

# Check container status
docker compose -f docker-compose.sqlite.yml ps

# Check health
docker inspect ai-realtor-sqlite | grep -A 10 Health
```

### Database errors

```bash
# Check if database file exists
docker exec ai-realtor-sqlite ls -lh /app/data/

# Check database integrity
docker exec ai-realtor-sqlite sqlite3 /app/data/ai_realtor.db "PRAGMA integrity_check;"

# Re-run migrations
docker exec ai-realtor-sqlite alembic upgrade head
```

### Port already in use

```bash
# Check what's using port 8000
lsof -i :8000

# Or change ports in docker-compose.sqlite.yml:
ports:
  - "8080:8000"  # Use 8080 instead
```

### Out of memory

```bash
# Limit container memory in docker-compose.sqlite.yml:
services:
  ai-realtor:
    deploy:
      resources:
        limits:
          memory: 1G
```

---

## 📊 Monitoring

### Health Check

The container includes built-in health checks:

```bash
# Check health status
docker inspect ai-realtor-sqlite | grep -A 5 Health

# Manual health check
curl http://localhost:8000/health
```

### View Resource Usage

```bash
# Container stats
docker stats ai-realtor-sqlite

# Disk usage
docker exec ai-realtor-sqlite du -sh /app/data/
```

### Database Statistics

```bash
# Get table count
docker exec ai-realtor-sqlite sqlite3 /app/data/ai_realtor.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table';"

# Get database size
docker exec ai-realtor-sqlite sqlite3 /app/data/ai_realtor.db "SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();"
```

---

## 🔄 Backup & Restore

### Automated Backups

The container creates automatic backups on startup. To configure:

```bash
# Access container
docker exec -it ai-realtor-sqlite bash

# View backups
ls -lh /app/data/backups/

# Manually create backup
cp /app/data/ai_realtor.db /app/data/backups/ai_realtor_$(date +%Y%m%d_%H%M%S).db
```

### Manual Backup

```bash
# Method 1: Copy database file
docker cp ai-realtor-sqlite:/app/data/ai_realtor.db ./backup_$(date +%Y%m%d).db

# Method 2: SQL dump
docker exec ai-realtor-sqlite sqlite3 /app/data/ai_realtor.db .dump > backup.sql
```

### Restore from Backup

```bash
# Method 1: Restore from file copy
docker cp ./backup.db ai-realtor-sqlite:/app/data/ai_realtor.db
docker compose -f docker-compose.sqlite.yml restart

# Method 2: Restore from SQL dump
docker cp ./backup.sql ai-realtor-sqlite:/tmp/backup.sql
docker exec ai-realtor-sqlite sh -c "sqlite3 /app/data/ai_realtor.db < /tmp/backup.sql"
```

---

## 🚢 Production Deployment

### Security Recommendations

1. **Don't run as root** (already configured in Dockerfile)
2. **Use secrets** for API keys (Docker Swarm/Kubernetes)
3. **Enable HTTPS** with reverse proxy (nginx/caddy)
4. **Limit resources** to prevent DoS
5. **Regular backups** to external location

### Resource Limits

Add to `docker-compose.sqlite.yml`:

```yaml
services:
  ai-realtor:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Reverse Proxy (HTTPS)

```yaml
# Using Caddy (automatic HTTPS)
services:
  caddy:
    image: caddy:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
    depends_on:
      - ai-realtor
```

**Caddyfile:**
```
your-domain.com {
    reverse_proxy ai-realtor:8000
}
```

---

## 📈 Scaling Considerations

### When to Switch to PostgreSQL

Consider upgrading if you experience:

- 🔴 **Database locked** errors
- 🔴 **Slow queries** with joins
- 🔴 **Concurrent write** conflicts
- 🔴 **Need for replication**
- 🔴 **Full-text search** requirements

### Migration Path

```bash
# 1. Export SQLite data
docker exec ai-realtor-sqlite sqlite3 /app/data/ai_realtor.db .dump > dump.sql

# 2. Import to PostgreSQL
psql -h localhost -U postgres -d ai_realtor < dump.sql

# 3. Update DATABASE_URL
DATABASE_URL=postgresql://user:pass@host:5432/ai_realtor

# 4. Restart with docker-compose.yml (PostgreSQL version)
docker compose -f docker-compose.yml up -d
```

---

## 🧪 Development Tips

### Live Code Reload

For development with auto-reload:

```yaml
# Add to docker-compose.sqlite.yml
volumes:
  - ./app:/app/app
  - ./mcp_server:/app/mcp_server
```

### Debugging

```bash
# Enable debug logging
environment:
  - DEBUG=true

# Run with verbose logging
docker compose -f docker-compose.sqlite.yml logs --tail=100 -f
```

### Testing API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# List properties
curl http://localhost:8000/properties/

# Create property
curl -X POST http://localhost:8000/properties/ \
  -H "Content-Type: application/json" \
  -d '{"address": "123 Main St", "city": "New York", "state": "NY", "zip_code": "10001", "price": 500000}'
```

---

## 📚 Additional Resources

- **Main Documentation**: [CLAUDE.md](./CLAUDE.md)
- **API Documentation**: http://localhost:8000/docs
- **GitHub Repository**: https://github.com/Thedurancode/ai-realtor
- **Docker Hub**: (coming soon)

---

## 🤝 Support

Need help?

1. Check the logs: `docker compose -f docker-compose.sqlite.yml logs -f`
2. Read the troubleshooting section above
3. Open an issue on GitHub
4. Check the main documentation

---

## 📝 License

MIT License - See LICENSE file for details

---

**Made with ❤️ by the AI Realtor Team**

*Last Updated: February 2026*
