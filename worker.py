#!/usr/bin/env python
"""
Remotion render worker.

Processes video render jobs from the BullMQ queue.
Usage: python worker.py
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.remotion_service import start_render_worker
from app.database import SessionLocal


if __name__ == "__main__":
    print("🎬 Starting Remotion render worker...")
    print(f"   Redis: {os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}")
    print(f"   Concurrency: {os.getenv('WORKER_CONCURRENCY', 1)}")
    print(f"   S3 Bucket: {os.getenv('AWS_S3_BUCKET', 'ai-realtor-renders')}")
    print()

    try:
        start_render_worker(SessionLocal)
    except KeyboardInterrupt:
        print("\n⚠️  Worker stopped by user")
    except Exception as e:
        print(f"\n❌ Worker error: {e}")
        sys.exit(1)
