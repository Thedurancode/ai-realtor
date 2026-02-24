# 🏠 AI Realtor - SQLite Docker Quick Start

The easiest way to run AI Realtor! No database setup required - just Docker and you're ready to go.

---

## ⚡ Quick Start (One Command)

```bash
chmod +x docker-quick-start-sqlite.sh && ./docker-quick-start-sqlite.sh
```

That's it! Open http://localhost:8000/docs

---

## 📋 What You Need

- ✅ Docker installed
- ✅ 2GB RAM available
- ✅ 1GB disk space

---

## 🚀 Manual Setup

```bash
# 1. Build and start
docker compose -f docker-compose.sqlite.yml up -d

# 2. View logs
docker compose -f docker-compose.sqlite.yml logs -f

# 3. Access the app
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

---

## 🛠️ Common Commands

| Command | Description |
|---------|-------------|
| `make start` | Start containers |
| `make stop` | Stop containers |
| `make restart` | Restart containers |
| `make logs` | View logs |
| `make shell` | Open shell in container |
| `make db-backup` | Backup database |
| `make db-restore FILE=backups/xxx.db` | Restore backup |
| `make health` | Check app health |
| `make status` | Show container status |

---

## 📁 Where's My Data?

**Database Location:** Docker volume `ai_realtor_sqlite_data`

```bash
# List volumes
docker volume ls | grep ai_realtor

# Inspect volume
docker volume inspect ai_realtor_sqlite_data
```

---

## 💾 Backup & Restore

### Backup
```bash
# Quick backup
docker cp ai-realtor-sqlite:/app/data/ai_realtor.db ./backup_$(date +%Y%m%d).db

# Or use Make
make db-backup
```

### Restore
```bash
# Copy backup back
docker cp ./backup.db ai-realtor-sqlite:/app/data/ai_realtor.db
docker compose -f docker-compose.sqlite.yml restart

# Or use Make
make db-restore FILE=backup.db
```

---

## 🔧 Configuration

Create a `.env` file for API keys:

```bash
# Required for full functionality
GOOGLE_PLACES_API_KEY=your_key_here
RAPIDAPI_KEY=your_key_here
ANTHROPIC_API_KEY=sk-ant-your_key_here

# Optional
DOCUSEAL_API_KEY=your_key_here
VAPI_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
```

---

## 🐛 Troubleshooting

### Port already in use?
```bash
# Change ports in docker-compose.sqlite.yml
ports:
  - "8080:8000"  # Use 8080 instead
```

### Database errors?
```bash
# Check database
docker exec ai-realtor-sqlite ls -lh /app/data/

# Re-run migrations
docker exec ai-realtor-sqlite alembic upgrade head
```

### Reset everything?
```bash
docker compose -f docker-compose.sqlite.yml down -v
docker volume rm ai_realtor_sqlite_data
docker compose -f docker-compose.sqlite.yml up -d
```

---

## 📚 Full Documentation

See [DOCKER_SQLITE_GUIDE.md](./DOCKER_SQLITE_GUIDE.md) for complete documentation.

---

## ⬆️ Upgrade to PostgreSQL

Need more power? Switch to PostgreSQL:

```bash
# Export data
docker exec ai-realtor-sqlite sqlite3 /app/data/ai_realtor.db .dump > dump.sql

# Switch to PostgreSQL version
docker compose -f docker-compose.yml up -d
```

---

**Made with ❤️ by the AI Realtor Team**
