# Docker Deployment Guide - AI Realtor API

## 🐳 How Docker + Database Works

You have **3 options** for running the database with Docker:

---

## Option 1: Docker Compose (Recommended for Dev) 🌟

**Best for**: Local development, testing, quick setup

### How it Works:
- **PostgreSQL runs in a separate container**
- **Data persists in a Docker volume** (`postgres_data`)
- **App container connects to Postgres container** via internal Docker network
- **Ports mapped to localhost** for easy access

### Architecture:
```
┌─────────────────┐         ┌─────────────────┐
│   Docker Host   │         │   Docker Host   │
│  (your machine)  │         │  (your machine)  │
│                 │         │                 │
│  Port 5433  ◄──────┐     │  Port 8000  ◄────┐
│    (mapped)      │     │    (mapped)     │
└─────────────────┘ │     └─────────────────┘
                   │
         ┌─────────▼───────────┐
         │  Docker Network     │
         │                     │
    ┌────▼─────┐         ┌────▼─────┐
    │ Postgres │◄────────│  App     │
    │ Container│  :5432  │ Container│
    │ :5432    │         │ :8000    │
    └──────────┘         └──────────┘
         │
    ┌────▼──────┐
    │ postgres_ │
    │  data     │
    │  (volume) │
    └───────────┘
```

### Quick Start:
```bash
# 1. Start everything
docker-compose up -d

# 2. Check logs
docker-compose logs -f app

# 3. Run migrations (automatic in start.sh)
docker-compose exec app alembic upgrade head

# 4. Stop
docker-compose down

# 5. Stop and remove data
docker-compose down -v
```

### Database Connection Details:
- **Internal URL** (from app container): `postgresql://postgres:postgres@postgres:5432/ai_realtor`
- **External URL** (from your machine): `postgresql://postgres:postgres@localhost:5433/ai_realtor`
- **Host in app**: `postgres` (container name)
- **Port**: 5432 (internal), 5433 (external)
- **User**: `postgres`
- **Password**: `postgres`
- **Database**: `ai_realtor`

---

## Option 2: External Database (Recommended for Production) 🚀

**Best for**: Production, Fly.io, AWS, cloud deployment

### How it Works:
- **Database runs separately** (Fly.io Postgres, AWS RDS, etc.)
- **Only the app runs in Docker**
- **App connects to external database** via DATABASE_URL

### Architecture:
```
┌─────────────────┐         ┌─────────────────┐
│  Docker Container│         │  External DB    │
│                 │         │  (Fly.io/AWS)   │
│  Port 8000  ◄──────┐     │                 │
│    (mapped)      │     │  Port 5432      │
└─────────────────┘ │     │    (exposed)    │
                   │     └─────────────────┘
                   │              ▲
                   │              │
                   │   DATABASE_URL env var
                   │   (connection string)
```

### Quick Start:
```bash
# 1. Build image
docker build -t ai-realtor .

# 2. Run with external database
docker run -d \
  -p 8000:8000 \
  -p 8001:8001 \
  -e DATABASE_URL="postgresql://user:pass@your-db-host:5432/ai_realtor" \
  -e GOOGLE_PLACES_API_KEY="your-key" \
  -e ANTHROPIC_API_KEY="your-key" \
  --name ai-realtor-app \
  ai-realtor
```

### For Fly.io Production:
```bash
# Fly.io provides managed Postgres
fly postgres create  # Creates managed database
fly deploy           # Deploys app with DATABASE_URL set automatically
```

---

## Option 3: Single Container with Embedded DB (Not Recommended) ⚠️

**Best for**: Quick demos, testing only

### How it Works:
- **PostgreSQL runs in same container** as app
- **Data lost when container stops** (unless you mount a volume)
- **Not recommended for production**

### Quick Start:
```bash
docker run -d \
  -p 8000:8000 \
  -p 5432:5432 \
  -v $(pwd)/postgres_data:/var/lib/postgresql/data \
  ai-realtor
```

---

## 🚀 Fast Deployment Options

### Option A: Local Development (Docker Compose)

```bash
# 1. Clone the repo
git clone https://github.com/Thedurancode/ai-realtor.git
cd ai-realtor

# 2. Create .env file
cp .env.example .env
# Edit .env with your API keys

# 3. Start everything
docker-compose up -d

# 4. Check it's running
curl http://localhost:8000/

# 5. View logs
docker-compose logs -f
```

**Time to deploy**: ~5 minutes
**Database**: Automatic (included in compose)

---

### Option B: Production (Fly.io)

```bash
# 1. Install Fly.io CLI
curl -L https://fly.io/install.sh | sh

# 2. Login
fly auth login

# 3. Launch app
fly launch

# 4. Create database
fly postgres create --region ewr

# 5. Attach database to app
fly postgres attach --app ai-realtor

# 6. Set secrets
fly secrets set DATABASE_URL="postgresql://..."
fly secrets set GOOGLE_PLACES_API_KEY="..."
fly secrets set ANTHROPIC_API_KEY="..."

# 7. Deploy
fly deploy
```

**Time to deploy**: ~15 minutes
**Database**: Managed Fly.io Postgres
**Cost**: ~$5-25/month depending on size

---

### Option C: Production (AWS/DigitalOcean/etc.)

```bash
# 1. Build image
docker build -t ai-realtor:latest .

# 2. Tag for registry
docker tag ai-realtor:latest registry.fly.io/ai-realtor:latest

# 3. Push to registry
docker push registry.fly.io/ai-realtor:latest

# 4. Run on server
docker run -d \
  -p 8000:8000 \
  -p 8001:8001 \
  -e DATABASE_URL="${DATABASE_URL}" \
  -e GOOGLE_PLACES_API_KEY="${GOOGLE_PLACES_API_KEY}" \
  --name ai-realtor \
  --restart unless-stopped \
  registry.fly.io/ai-realtor:latest
```

---

## 📊 Comparison

| Option | Setup Time | Data Persistence | Scalability | Cost | Best For |
|--------|-----------|------------------|-------------|------|----------|
| **Docker Compose** | 5 min | ✅ Volume | Limited | Free | Development |
| **External DB** | 15 min | ✅ Managed | ✅ Excellent | $5-25/mo | Production |
| **Single Container** | 2 min | ⚠️ Ephemeral | ❌ Poor | Free | Testing |

---

## 🔧 Database Initialization

### What Happens on First Start:

1. **Container starts**
2. **`start.sh` runs automatically**:
   ```bash
   alembic upgrade head  # Runs all migrations
   ```
3. **Database tables created** (41 tables)
4. **App starts** on port 8000
5. **Ready to accept requests**

### Migration History:
```
c8d2e4f5a7b9 → Property status pipeline (FIXED)
d1e2f3a4b5c6 → Indexes & soft deletes
20250222_add_workspace_and_security → Workspaces & security
20250222_add_intelligence → Intelligence models
```

---

## 🌐 Accessing the Database

### From Your Machine (Docker Compose):
```bash
# Using psql
psql -h localhost -p 5433 -U postgres -d ai_realtor

# Using Docker exec
docker-compose exec postgres psql -U postgres -d ai_realtor

# Example query
docker-compose exec postgres psql -U postgres -d ai_realtor -c "SELECT * FROM properties;"
```

### From Inside App Container:
```bash
docker-compose exec app bash
psql $DATABASE_URL
```

---

## 💡 Tips & Tricks

### 1. View Database Logs
```bash
docker-compose logs -f postgres
```

### 2. Restart App Only (Keep DB Running)
```bash
docker-compose restart app
```

### 3. Rebuild App After Code Changes
```bash
docker-compose up -d --build app
```

### 4. Backup Database
```bash
docker-compose exec postgres pg_dump -U postgres ai_realtor > backup.sql
```

### 5. Restore Database
```bash
cat backup.sql | docker-compose exec -T postgres psql -U postgres ai_realtor
```

### 6. Access Database from Another Container
```bash
docker run -it --rm \
  --network ai-realtor_default \
  postgres:16 \
  psql -h postgres -U postgres -d ai_realtor
```

---

## 🐛 Troubleshooting

### Problem: App Can't Connect to Database
**Solution**: Check if postgres container is running
```bash
docker-compose ps
docker-compose logs postgres
```

### Problem: Port 5433 Already in Use
**Solution**: Change port mapping in docker-compose.yml:
```yaml
ports:
  - "5434:5432"  # Use 5434 instead
```

### Problem: Data Lost on Restart
**Solution**: Ensure volume is created:
```bash
docker volume ls
docker volume inspect ai_realtor_postgres_data
```

### Problem: Migrations Fail
**Solution**: Manually run migrations:
```bash
docker-compose exec app alembic upgrade head
```

---

## ✅ Quick Reference

| Task | Command |
|------|---------|
| **Start all** | `docker-compose up -d` |
| **Stop all** | `docker-compose down` |
| **View logs** | `docker-compose logs -f` |
| **Restart app** | `docker-compose restart app` |
| **Run migrations** | `docker-compose exec app alembic upgrade head` |
| **Access DB** | `docker-compose exec postgres psql -U postgres -d ai_realtor` |
| **Rebuild** | `docker-compose up -d --build` |
| **Shell in app** | `docker-compose exec app bash` |

---

## 🎯 Recommendation

**For Development**: Use **Docker Compose** (Option 1)
- Fast setup
- Data persists
- Easy to reset
- Isolated environment

**For Production**: Use **External Database** (Option 2)
- Managed backup
- Better performance
- Easier scaling
- Separation of concerns

---

**Current Setup**: Your project already has Docker Compose configured! Just run:
```bash
docker-compose up -d
```

That's it! 🎉
