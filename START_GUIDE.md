# 🚀 Start AI Realtor Platform

## Current Status: ❌ NOT RUNNING

**Docker:** Not running
**FastAPI:** Not running
**Port 8000:** Available

---

## Quick Start

### **Option 1: Start with Docker (Recommended)**

```bash
# Build and start all services
docker-compose up -d --build

# Run database migrations
docker-compose exec app alembic upgrade head

# View logs
docker-compose logs -f app

# Test endpoints
curl http://localhost:8000/docs
```

**Your app will be available at:** http://localhost:8000

---

### **Option 2: Start Locally (Python)**

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env with your API keys

# 3. Run migrations
alembic upgrade head

# 4. Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Your app will be available at:** http://localhost:8000

---

## Verify It's Running

### **Check Docker:**
```bash
docker ps
```

**Should show:**
- `ai_realtor_app`
- `ai_realtor_postgres`

---

### **Check Port:**
```bash
lsof -i :8000
```

**Should show:** Python/FastAPI process

---

### **Test Endpoint:**
```bash
curl http://localhost:8000/
```

**Should return:** JSON response

---

## Test the System

Once running, execute the test script:

```bash
./test-docker.sh
```

Or test manually:

```bash
# Test API docs
open http://localhost:8000/docs

# Test new endpoints
curl http://localhost:8000/approval/config
curl http://localhost:8000/skills/discover
curl http://localhost:8000/sqlite/stats
```

---

## Stop the System

### **Docker:**
```bash
docker-compose down
```

### **Local:**
```bash
# Press Ctrl+C in the terminal running uvicorn
```

---

## View Logs

### **Docker:**
```bash
# All logs
docker-compose logs app

# Follow logs
docker-compose logs -f app
```

### **Local:**
```bash
# Logs are in the terminal where uvicorn is running
```

---

## Troubleshooting

### **Port already in use:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>
```

### **Docker build fails:**
```bash
# Clean build cache
docker-compose down
docker system prune -a
docker-compose up -d --build
```

### **Database connection error:**
```bash
# Ensure postgres is running
docker-compose up -d postgres

# Reset database
docker-compose down -v
docker-compose up -d
docker-compose exec app alembic upgrade head
```

---

**Ready to start? Run: `docker-compose up -d --build`** 🚀
