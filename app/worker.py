"""arq worker — processes background jobs from Redis.

Run with:
    arq app.worker.WorkerSettings

Or via the helper script:
    python -m app.worker

All background job functions are registered here. When adding a new
background job, define the async function and add it to WORKER_FUNCTIONS.
"""

import asyncio
import logging
import os
import sys

from arq import cron
from arq.connections import RedisSettings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Job functions — each wraps an existing service call
# ---------------------------------------------------------------------------

async def run_auto_enrich_pipeline(ctx, property_id: int):
    """Auto-enrich a newly created property (Zillow, scoring, contracts)."""
    from app.database import SessionLocal
    from app.services.property_pipeline_service import auto_enrich_pipeline
    db = SessionLocal()
    try:
        await auto_enrich_pipeline(db, property_id)
    except Exception as e:
        logger.error("auto_enrich_pipeline failed for property %d: %s", property_id, e)
        raise
    finally:
        db.close()


async def schedule_compliance_check(ctx, property_id: int):
    """Run compliance check on a property."""
    from app.database import SessionLocal
    from app.services.scheduled_compliance import schedule_compliance_check as _check
    db = SessionLocal()
    try:
        _check(db, property_id)
    except Exception as e:
        logger.error("compliance_check failed for property %d: %s", property_id, e)
        raise
    finally:
        db.close()


async def regenerate_recap_background(ctx, property_id: int, trigger: str):
    """Regenerate property recap after changes."""
    from app.database import SessionLocal
    from app.services.property_recap_service import regenerate_recap_background as _regen
    db = SessionLocal()
    try:
        await _regen(property_id, trigger)
    except Exception as e:
        logger.error("regenerate_recap failed for property %d: %s", property_id, e)
    finally:
        db.close()


async def run_agentic_research(ctx, job_id: int):
    """Run full agentic research pipeline."""
    from app.services.agentic.orchestrator import agentic_research_service
    try:
        await agentic_research_service.run_job(job_id)
    except Exception as e:
        logger.error("agentic_research failed for job %d: %s", job_id, e)
        raise


async def perform_research(ctx, research_id: int):
    """Run a research task."""
    from app.database import SessionLocal
    from app.services.research_service import research_service
    db = SessionLocal()
    try:
        from app.models.research import Research
        research = db.query(Research).get(research_id)
        if research:
            await research_service.perform_research(db, research)
    except Exception as e:
        logger.error("perform_research failed for %d: %s", research_id, e)
        raise
    finally:
        db.close()


async def process_webhook_event(ctx, event_type: str, payload: dict):
    """Process an incoming webhook event."""
    from app.services.webhook_listener_service import process_webhook
    try:
        await process_webhook(event_type, payload)
    except Exception as e:
        logger.error("process_webhook failed for %s: %s", event_type, e)
        raise


async def execute_campaign(ctx, campaign_id: int):
    """Execute a direct mail or contact list campaign."""
    from app.database import SessionLocal
    from app.services.lob_service import execute_campaign as _exec
    db = SessionLocal()
    try:
        await _exec(campaign_id)
    except Exception as e:
        logger.error("execute_campaign failed for %d: %s", campaign_id, e)
        raise
    finally:
        db.close()


async def clone_voice_background(ctx, agent_id: int, agent_name: str, voice_sample_url: str):
    """Clone a voice for an agent brand."""
    from app.services.elevenlabs_service import clone_voice
    try:
        await clone_voice(agent_id, agent_name, voice_sample_url)
    except Exception as e:
        logger.error("clone_voice failed for agent %d: %s", agent_id, e)
        raise


async def generate_daily_digest(ctx):
    """Generate the daily digest."""
    from app.database import SessionLocal
    from app.services.daily_digest_service import daily_digest_service
    db = SessionLocal()
    try:
        digest = await daily_digest_service.generate_digest(db)
        logger.info("Daily digest generated: %d highlights", len(digest.get("key_highlights", [])))
    except Exception as e:
        logger.error("Daily digest generation failed: %s", e)
    finally:
        db.close()


async def run_task_loop_tick(ctx):
    """Single tick of the scheduled task runner (called by cron)."""
    from app.database import SessionLocal
    from app.services.scheduled_task_service import scheduled_task_service
    from app.services.task_runner import _execute_task

    db = SessionLocal()
    try:
        due_tasks = scheduled_task_service.get_due_tasks(db)
        for task in due_tasks:
            try:
                await _execute_task(db, task, scheduled_task_service)
            except Exception as e:
                logger.error("Task %d failed: %s", task.id, e)
                scheduled_task_service.mark_failed(db, task)
    except Exception as e:
        logger.error("Task loop tick error: %s", e)
    finally:
        db.close()


async def run_pipeline_check(ctx):
    """Run pipeline automation check (called by cron)."""
    from app.database import SessionLocal
    from app.services.pipeline_automation_service import pipeline_automation_service

    db = SessionLocal()
    try:
        result = pipeline_automation_service.run_pipeline_check(db)
        if result.get("transitioned", 0) > 0:
            logger.info("Pipeline check: %d transitions", result["transitioned"])
    except Exception as e:
        logger.error("Pipeline check error: %s", e)
    finally:
        db.close()


async def run_alert_check(ctx):
    """Run analytics alert check (called by cron)."""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        from app.services.analytics_alert_service import AnalyticsAlertService
        alert_service = AnalyticsAlertService(db)
        triggers = alert_service.check_alert_rules()
        if triggers:
            logger.info("Alert check: %d alerts triggered", len(triggers))
    except Exception as e:
        logger.error("Alert check error: %s", e)
    finally:
        db.close()


async def startup(ctx):
    """Worker startup hook."""
    logger.info("arq worker started")


async def shutdown(ctx):
    """Worker shutdown hook."""
    logger.info("arq worker shutting down")


# ---------------------------------------------------------------------------
# Worker config
# ---------------------------------------------------------------------------

# All job functions that can be enqueued
WORKER_FUNCTIONS = [
    run_auto_enrich_pipeline,
    schedule_compliance_check,
    regenerate_recap_background,
    run_agentic_research,
    perform_research,
    process_webhook_event,
    execute_campaign,
    clone_voice_background,
    generate_daily_digest,
    run_task_loop_tick,
    run_pipeline_check,
    run_alert_check,
]


class WorkerSettings:
    """arq worker settings — run with: arq app.worker.WorkerSettings"""

    functions = WORKER_FUNCTIONS
    on_startup = startup
    on_shutdown = shutdown

    redis_settings = RedisSettings(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        database=int(os.getenv("REDIS_DB", 0)),
    )

    # Cron jobs replace the old asyncio.create_task loops
    cron_jobs = [
        cron(run_task_loop_tick, minute={0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59}),  # every minute
        cron(run_pipeline_check, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}),  # every 5 min
        cron(run_alert_check, minute={0, 10, 20, 30, 40, 50}),  # every 10 min
    ]

    max_jobs = 10
    job_timeout = 600  # 10 minutes


if __name__ == "__main__":
    from arq import run_worker
    run_worker(WorkerSettings)  # type: ignore[arg-type]
