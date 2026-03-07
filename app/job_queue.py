"""Background job queue backed by Redis via arq.

Provides durable, restartable background jobs that survive server restarts.
Falls back to FastAPI BackgroundTasks when Redis is unavailable.

Usage in routers:
    from app.job_queue import enqueue

    # Instead of: background_tasks.add_task(some_func, arg1, arg2)
    await enqueue("some_func", arg1, arg2)

    # Or with FastAPI BackgroundTasks fallback:
    from app.job_queue import enqueue_or_fallback
    await enqueue_or_fallback(background_tasks, some_func, arg1, arg2)
"""

import asyncio
import logging
import os
from typing import Any

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

logger = logging.getLogger(__name__)

_pool: ArqRedis | None = None
_pool_lock = asyncio.Lock()
_redis_available: bool | None = None


def get_redis_settings() -> RedisSettings:
    return RedisSettings(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        database=int(os.getenv("REDIS_DB", 0)),
        conn_retries=0,  # fail fast — don't block startup
        conn_timeout=2,
    )


async def get_pool() -> ArqRedis | None:
    """Get or create the arq Redis connection pool. Returns None if Redis is down."""
    global _pool, _redis_available

    async with _pool_lock:
        if _pool is not None:
            try:
                await _pool.ping()
                return _pool
            except Exception:
                _pool = None

        try:
            _pool = await create_pool(get_redis_settings(), retry=0)
            if _redis_available is not True:
                logger.info("Redis connected for job queue")
                _redis_available = True
            return _pool
        except Exception as e:
            if _redis_available is not False:
                logger.warning("Redis unavailable, jobs will use in-process fallback: %s", e)
                _redis_available = False
            return None


async def enqueue(job_name: str, *args: Any, _queue_name: str = "arq:queue", **kwargs: Any) -> str | None:
    """Enqueue a job to Redis. Returns job ID or None if Redis is down."""
    pool = await get_pool()
    if pool is None:
        return None
    job = await pool.enqueue_job(job_name, *args, _queue_name=_queue_name, **kwargs)
    if job:
        logger.debug("Enqueued job %s: %s", job_name, job.job_id)
        return job.job_id
    return None


async def enqueue_or_fallback(background_tasks, func, *args, **kwargs) -> str | None:
    """Try to enqueue to Redis. If unavailable, fall back to BackgroundTasks.

    The function name must match a registered worker function.
    """
    job_id = await enqueue(func.__name__, *args, **kwargs)
    if job_id:
        return job_id

    # Fallback: run in-process (not durable, but works without Redis)
    if asyncio.iscoroutinefunction(func):
        background_tasks.add_task(func, *args, **kwargs)
    else:
        background_tasks.add_task(func, *args, **kwargs)
    logger.debug("Fallback: running %s in-process via BackgroundTasks", func.__name__)
    return None
