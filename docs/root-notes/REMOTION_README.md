# 🎬 Remotion Video Rendering API

Async video rendering pipeline powered by Remotion, BullMQ, and Redis.

## Overview

Generate professional property videos programmatically using React components. The rendering happens asynchronously in background workers with real-time progress tracking and automatic S3 uploads.

## Features

- ✅ **2 Built-in Templates**: CaptionedReel (social media), Slideshow (property tours)
- ✅ **Async Processing**: BullMQ job queue with Redis backend
- ✅ **Real-time Progress**: Track frame-by-frame rendering progress
- ✅ **Auto-upload to S3**: Videos stored in AWS S3 with presigned URLs
- ✅ **Webhook Callbacks**: Get notified when renders complete
- ✅ **Cancel Support**: Stop renders mid-process
- ✅ **Retry Logic**: Automatic retries for transient failures
- ✅ **Worker Pooling**: Configurable concurrency for parallel renders

## Architecture

```
┌─────────────┐      ┌──────────┐      ┌────────────┐      ┌─────────┐
│   API       │ ───▶ │  Redis   │ ───▶ │  Worker    │ ───▶ │   S3    │
│  (FastAPI)  │      │  (BullMQ)│      │ (Remotion) │      │ (AWS)   │
└─────────────┘      └──────────┘      └────────────┘      └─────────┘
       │                                          │
       └──────────────────────────────────────────┘
                  (PostgreSQL for job state)
```

## Setup

### 1. Install Dependencies

**Python:**
```bash
pip install -r requirements.txt
```

**Node.js (Remotion):**
```bash
cd remotion
npm install
```

### 2. Configure Environment

Add to your `.env` file:
```bash
# Redis (for job queue)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Worker settings
WORKER_CONCURRENCY=1

# AWS S3 (for video storage)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
AWS_S3_BUCKET=ai-realtor-renders
```

### 3. Run Database Migration

```bash
alembic upgrade head
```

This creates the `render_jobs` table.

### 4. Start Redis

**Docker:**
```bash
docker run -d -p 6379:6379 redis:alpine
```

**macOS:**
```bash
brew install redis
brew services start redis
```

### 5. Start Services

**Terminal 1 - API Server:**
```bash
uvicorn app.main:app --reload
```

**Terminal 2 - Render Worker:**
```bash
python worker.py
```

## API Endpoints

### POST /v1/renders

Create a new render job.

**Request:**
```json
{
  "template_id": "captioned-reel",
  "composition_id": "CaptionedReel",
  "input_props": {
    "title": "Amazing Property!",
    "subtitle": "123 Main St",
    "backgroundUrl": "https://example.com/image.jpg",
    "overlayColor": "#000000",
    "overlayOpacity": 0.3
  },
  "webhook_url": "https://example.com/webhook"
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "progress": 0.0,
  "created_at": "2026-02-25T10:00:00Z"
}
```

### GET /v1/renders/:id

Get render job details.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 1.0,
  "output_url": "https://s3.amazonaws.com/...",
  "current_frame": 300,
  "total_frames": 300,
  "created_at": "2026-02-25T10:00:00Z",
  "finished_at": "2026-02-25T10:00:15Z"
}
```

### GET /v1/renders/:id/progress

Get real-time progress.

**Response:**
```json
{
  "status": "rendering",
  "progress": 0.45,
  "current_frame": 135,
  "total_frames": 300,
  "eta_seconds": 8
}
```

### POST /v1/renders/:id/cancel

Cancel a render job.

## Templates

### 1. CaptionedReel

Short, vertical videos (1080x1920) perfect for Instagram Reels, TikTok, YouTube Shorts.

**Props:**
```typescript
{
  title: string;           // Main headline
  subtitle: string;        // Subtitle (address, price, etc.)
  backgroundUrl: string;   // Image or video URL
  overlayColor: string;    // Overlay color (#000000)
  overlayOpacity: number;  // Overlay opacity (0-1)
}
```

**Duration:** 10 seconds (300 frames @ 30fps)

### 2. Slideshow

Image slideshow with transitions, perfect for property tours.

**Props:**
```typescript
{
  images: string[];          // Array of image URLs
  durationPerImage: number;  // Frames per image (default: 90)
  transitionDuration: number; // Transition frames (default: 15)
  showTitle: boolean;        // Show title overlay
  title: string;             // Title text
  showMusic: boolean;        // Include background music
}
```

**Duration:** 15 seconds + (image_count × duration_per_image)

## Usage Examples

### Example 1: Create Captioned Reel

```bash
curl -X POST "http://localhost:8000/v1/renders" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "template_id": "captioned-reel",
    "composition_id": "CaptionedReel",
    "input_props": {
      "title": "Miami Luxury Living",
      "subtitle": "123 Main St, Miami Beach",
      "backgroundUrl": "https://example.com/property.jpg",
      "overlayColor": "#000000",
      "overlayOpacity": 0.3
    }
  }'
```

### Example 2: Create Property Slideshow

```bash
curl -X POST "http://localhost:8000/v1/renders" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "template_id": "slideshow",
    "composition_id": "Slideshow",
    "input_props": {
      "images": [
        "https://example.com/photo1.jpg",
        "https://example.com/photo2.jpg",
        "https://example.com/photo3.jpg"
      ],
      "durationPerImage": 90,
      "transitionDuration": 15,
      "showTitle": true,
      "title": "Property Tour"
    }
  }'
```

### Example 3: Poll Progress

```bash
./scripts/poll_render.sh 550e8400-e29b-41d4-a716-446655440000
```

## CLI Scripts

### Create Render

```bash
./scripts/create_render.sh input_props.json captioned-reel CaptionedReel
```

### Poll Progress

```bash
./scripts/poll_render.sh <render_id>
```

### Cancel Render

```bash
./scripts/cancel_render.sh <render_id>
```

## Custom Templates

Create your own Remotion compositions:

1. **Create composition** in `remotion/src/MyComposition.tsx`
2. **Register** in `remotion/src/index.ts`:
   ```tsx
   <Composition
     id="MyComposition"
     component={MyComposition}
     durationInFrames={300}
     fps={30}
     width={1080}
     height={1920}
   />
   ```
3. **Use** in API:
   ```json
   {
     "template_id": "my-template",
     "composition_id": "MyComposition",
     "input_props": { ... }
   }
   ```

## Job Status Flow

```
queued → rendering → uploading → completed
   ↓         ↓           ↓
canceled  failed    failed/canceled
```

## Webhook Callbacks

When a render completes, fails, or is canceled, a POST request is sent to the `webhook_url`:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "output_url": "https://s3.amazonaws.com/bucket/key.mp4",
  "error_message": null,
  "progress": 1.0,
  "created_at": "2026-02-25T10:00:00Z",
  "finished_at": "2026-02-25T10:00:15Z"
}
```

## Performance

**Typical render times:**
- 10-second CaptionedReel: ~10-20 seconds
- 15-second Slideshow (5 images): ~15-30 seconds

**Optimization tips:**
- Use `WORKER_CONCURRENCY` to run parallel renders
- Pre-optimize images (1080p max)
- Use CDN-hosted images for faster loading
- Enable Chromium caching in Docker

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Install Node.js for Remotion
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
RUN apt-get install -y nodejs

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Remotion
COPY remotion ./remotion
RUN cd remotion && npm install

# Copy app
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

# Set environment variables
ENV WORKER_CONCURRENCY=2
ENV PYTHONUNBUFFERED=1

# Run both API and worker
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 & python worker.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/ai_realtor
      - REDIS_HOST=redis
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
    depends_on:
      - redis
      - db

  worker:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/ai_realtor
      - REDIS_HOST=redis
      - WORKER_CONCURRENCY=2
    depends_on:
      - redis
      - db
    command: python worker.py

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=ai_realtor
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Troubleshooting

### Worker not processing jobs

```bash
# Check Redis connection
redis-cli ping

# Check BullMQ queue
redis-cli
> keys "bull:render-jobs:*"
> lrange "bull:render-jobs:waiting" 0 -1
```

### Render fails with "Remotion not found"

```bash
# Ensure Remotion is installed
cd remotion
npm install

# Test Remotion CLI
npx remotion render --help
```

### S3 upload fails

```bash
# Check AWS credentials
aws s3 ls

# Verify bucket exists
aws s3 mb s3://ai-realtor-renders --region us-east-1
```

### Slow rendering

- Increase `WORKER_CONCURRENCY`
- Use faster instance (more CPU)
- Pre-download images to local storage
- Reduce JPEG quality: `--jpeg-quality 70`

## Monitoring

### Redis Queue Stats

```bash
redis-cli
> scard "bull:render-jobs:waiting"   # Jobs waiting
> scard "bull:render-jobs:active"    # Jobs processing
> scard "bull:render-jobs:completed" # Jobs completed
> scard "bull:render-jobs:failed"    # Jobs failed
```

### Database Queries

```sql
-- Jobs by status
SELECT status, COUNT(*) FROM render_jobs GROUP BY status;

-- Average render time
SELECT
  AVG(EXTRACT(EPOCH FROM (finished_at - started_at))) as avg_seconds
FROM render_jobs
WHERE status = 'completed';

-- Failed jobs
SELECT id, error_message, created_at
FROM render_jobs
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 10;
```

## Cost Estimates

**AWS S3:**
- Storage: $0.023/GB/month
- Requests: $0.0004 per 1,000 requests
- 100 videos × 50MB = 5GB = ~$0.12/month

**Render time (on 2 vCPU):**
- CaptionedReel: ~15 seconds
- Slideshow: ~30 seconds
- 1000 renders/month = ~8 hours of compute

## License

MIT

## Support

For issues and questions:
- GitHub: https://github.com/Thedurancode/ai-realtor
- API Docs: http://localhost:8000/docs
