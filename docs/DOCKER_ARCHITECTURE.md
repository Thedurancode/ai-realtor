# Docker + Database Architecture - Visual Guide

## 🎯 Quick Answer: How Does the Database Work with Docker?

**The database runs in a SEPARATE container, and the app connects to it over the internal Docker network.**

---

## 📊 Architecture Diagram

### Docker Compose Setup (Your Current Configuration)

```
┌─────────────────────────────────────────────────────────────────┐
│                         Your Machine                            │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                    Docker Network                            ││
│  │                  (ai_realtor_default)                        ││
│  │                                                                ││
│  │  ┌──────────────────┐              ┌──────────────────┐      ││
│  │  │                  │              │                  │      ││
│  │  │   App Container  │              │  Postgres Cont.  │      ││
│  │  │   (FastAPI)      │              │                  │      ││
│  │  │                  │   Connects   │                  │      ││
│  │  │   Port 8000 ◄────┼───────┐──────┼───► Port 5432    │      ││
│  │  │   Port 8001 ◄────┘       │      │   postgres:5432  │      ││
│  │  │                        │      │                  │      ││
│  │  │  DATABASE_URL=          │      │  postgres:5432   │      ││
│  │  │  postgresql://postgres │      │  postgres:5432   │      ││
│  │  │  @postgres:5432/... ────┘      │                  │      ││
│  │  │                                │  postgres_data   │      ││
│  │  │                                │  (Volume)        │      ││
│  │  └────────────────────────────────┘                  │      ││
│  │                                                   │         ││
│  └────────────────────────────────────────────────────┼─────────┘│
│                                                       │          │
│  ┌────────────────────────────────────────────────────▼─────────┐│
│  │                     Port Mappings (to your machine)          ││
│  │                                                                ││
│  │  App:8000  ──────► localhost:8000  (API)                    ││
│  │  App:8001  ──────► localhost:8001  (MCP SSE)                 ││
│  │  PG:5432   ──────► localhost:5433  (Database)                ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## 🔑 Key Concepts

### 1. **Internal Docker Network**
- Containers can reach each other by **service name** (not localhost)
- App uses: `postgresql://postgres:postgres@postgres:5432/ai_realtor`
- `postgres` = container name from docker-compose.yml
- `5432` = internal port (not 5433!)

### 2. **Port Mapping**
- **Internal** (inside Docker): Postgres on 5432
- **External** (your machine): Postgres on 5433
- This lets you access DB from your machine: `localhost:5433`

### 3. **Data Persistence**
- **Volume**: `postgres_data` stores database files
- Survives container restarts
- Only deleted with `docker-compose down -v`

---

## 📝 docker-compose.yml Breakdown

```yaml
services:
  postgres:                    # ← Container 1: Database
    image: postgres:16-alpine
    container_name: ai_realtor_postgres
    environment:
      POSTGRES_DB: ai_realtor
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5433:5432"            # ← Maps host:5433 to container:5432
    volumes:
      - postgres_data:/var/lib/postgresql/data  # ← Persistent storage

  app:                         # ← Container 2: FastAPI App
    build: .
    container_name: ai_realtor_app
    depends_on:
      - postgres               # ← Wait for postgres to start
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/ai_realtor
                          #           ↑         ↑       ↑    ↑
                          #           user     pass    host port
                          #                           (container name)
    ports:
      - "8000:8000"            # ← API port
      - "8001:8001"            # ← MCP SSE port

volumes:
  postgres_data:               # ← Named volume for persistence
```

---

## 🚀 What Happens When You Run `docker-compose up`?

### Step 1: Pull Images
```
Pulling postgres (postgres:16-alpine)...
Building app...
```

### Step 2: Create Network
```
Creating network "ai_realtor_default"
```

### Step 3: Start Postgres Container
```
Creating ai_realtor_postgres...
- Database: ai_realtor created
- User: postgres created
- Port 5432 exposed internally
- Port 5433 mapped to host
- Volume mounted for data
```

### Step 4: Start App Container
```
Creating ai_realtor_app...
- Waits for postgres to be ready
- Runs migrations (alembic upgrade head)
- Creates 41 tables
- Starts FastAPI on port 8000
- Starts MCP SSE on port 8001
```

### Step 5: Ready!
```
✅ API: http://localhost:8000
✅ Docs: http://localhost:8000/docs
✅ Database: localhost:5433
```

---

## 🔄 Data Flow Example

### Creating a Property:

```
1. Your Request
   ↓
   curl -X POST http://localhost:8000/properties/ ...
   ↓
2. Docker Routes to App Container
   ↓
3. App Processes Request
   ↓
4. App Connects to Postgres
   (via internal network: postgres:5432)
   ↓
5. Postgres Executes SQL
   INSERT INTO properties ...
   ↓
6. Postgres Returns Result
   ↓
7. App Returns JSON Response
   ↓
8. You See Response
   {"id": 1, "address": "123 Main St", ...}
```

---

## 💾 Database Persistence

### Where Data Lives:

```
Docker Volume: postgres_data
    ↓
Mounted at: /var/lib/postgresql/data
    ↓
Contains:
  - ai_realtor/          (database)
    - properties/        (table data)
    - contacts/          (table data)
    - contracts/         (table data)
    - ... 38 more tables
```

### Backup Commands:

```bash
# Backup to file
docker-compose exec postgres pg_dump -U postgres ai_realtor > backup.sql

# Restore from file
cat backup.sql | docker-compose exec -T postgres psql -U postgres ai_realtor

# Volume location (on your machine)
docker volume inspect ai_realtor_postgres_data
# Output: Mountpoint: /var/lib/docker/volumes/ai_realtor_postgres_data/_data
```

---

## 🌐 Accessing the Database

### From App Container (Internal):
```python
# In app code:
DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/ai_realtor"
#                  ↑user      ↑pass    ↑host       ↑port ↑db
#                                        (container name)
```

### From Your Machine (External):
```bash
# Option 1: psql
psql -h localhost -p 5433 -U postgres -d ai_realtor

# Option 2: Docker exec
docker-compose exec postgres psql -U postgres -d ai_realtor

# Option 3: From another container
docker run -it --rm \
  --network ai_realtor_default \
  postgres:16 \
  psql -h postgres -U postgres -d ai_realtor
```

---

## 🎯 Summary

| Question | Answer |
|----------|--------|
| **Where does the database run?** | In a separate Docker container |
| **How does the app connect?** | Via internal Docker network (`postgres:5432`) |
| **Is data persistent?** | Yes, stored in Docker volume `postgres_data` |
| **Can I access from my machine?** | Yes, via `localhost:5433` |
| **What if I restart?** | Data survives (volume persists) |
| **What if I run `down -v`?** | Data deleted (volume removed) |

---

## 🚀 Quick Commands

```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f

# Stop (keep data)
docker-compose down

# Stop (delete data)
docker-compose down -v

# Restart app only
docker-compose restart app

# Rebuild after code changes
docker-compose up -d --build

# Access database
docker-compose exec postgres psql -U postgres -d ai_realtor

# Run migrations
docker-compose exec app alembic upgrade head
```

---

**Bottom Line**: The database is just another container that your app talks to over the network. Docker makes this seamless with automatic networking and service discovery! 🎉
