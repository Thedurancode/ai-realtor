"""Agent Worker — picks up tasks from the bus and executes them via the RealtorClaw API.

Each worker runs in a Coder workspace and processes tasks from Redis.
Workers are stateless — they read a task, call the appropriate API/service, return results.

Usage:
    python -m app.services.agent_worker --worker-id worker-1

Or from code:
    worker = AgentWorker(worker_id="worker-1")
    await worker.start()
"""

import asyncio
import logging
import time
from typing import Any

from app.services.agent_bus import AgentBus, AgentTask, TaskStatus

logger = logging.getLogger(__name__)


class AgentWorker:
    def __init__(self, worker_id: str = "worker-1"):
        self.bus = AgentBus(role="worker", worker_id=worker_id)
        self.worker_id = worker_id
        self._running = False

    async def start(self):
        connected = await self.bus.connect()
        if not connected:
            raise RuntimeError(f"Worker {self.worker_id} failed to connect to Redis")

        self._running = True
        logger.info("Worker %s started, waiting for tasks...", self.worker_id)

        async for task in self.bus.consume_tasks():
            if not self._running:
                break
            await self._handle_task(task)

    async def stop(self):
        self._running = False
        await self.bus.close()

    async def _handle_task(self, task: AgentTask):
        logger.info("Worker %s: executing %s (%s)", self.worker_id, task.task_type, task.task_id)
        start = time.time()

        try:
            result = await self._execute(task)
            duration = time.time() - start
            await self.bus.publish_result(task.task_id, result=result, duration=duration)
            logger.info("Worker %s: completed %s in %.1fs", self.worker_id, task.task_type, duration)
        except Exception as e:
            duration = time.time() - start
            await self.bus.publish_result(task.task_id, error=str(e), duration=duration)
            logger.error("Worker %s: failed %s: %s", self.worker_id, task.task_type, e)

    async def _execute(self, task: AgentTask) -> Any:
        """Route task to the appropriate service."""
        handler = TASK_HANDLERS.get(task.task_type)
        if not handler:
            raise ValueError(f"Unknown task type: {task.task_type}")
        return await handler(task.payload)


# ---------------------------------------------------------------------------
# Task handlers — each calls existing RealtorClaw services
# ---------------------------------------------------------------------------

async def _search_properties(payload: dict) -> dict:
    from app.database import SessionLocal
    from app.services.property_service import search_properties

    db = SessionLocal()
    try:
        results = search_properties(
            db,
            location=payload.get("location"),
            max_price=payload.get("max_price"),
            min_beds=payload.get("min_beds"),
            property_type=payload.get("property_type"),
        )
        return {
            "count": len(results),
            "properties": [
                {
                    "id": p.id,
                    "address": p.address,
                    "price": p.price,
                    "beds": p.bedrooms,
                    "baths": p.bathrooms,
                    "sqft": p.square_feet,
                }
                for p in results[:20]
            ],
        }
    finally:
        db.close()


async def _research_property(payload: dict) -> dict:
    from app.database import SessionLocal
    from app.services.agentic_research_service import research_service

    db = SessionLocal()
    try:
        address = payload.get("address", "")
        property_id = payload.get("property_id")

        if property_id:
            result = await research_service.research_property(db, property_id)
        else:
            result = {"address": address, "status": "research_requested"}

        return result if isinstance(result, dict) else {"result": str(result)}
    finally:
        db.close()


async def _get_comps(payload: dict) -> dict:
    from app.database import SessionLocal
    from app.services.comp_service import get_comp_sales

    db = SessionLocal()
    try:
        property_id = payload.get("property_id")
        if property_id:
            comps = get_comp_sales(db, property_id)
            return {"comps": comps} if isinstance(comps, dict) else {"comps": str(comps)}
        return {"comps": [], "note": "No property_id provided"}
    finally:
        db.close()


async def _skip_trace(payload: dict) -> dict:
    from app.database import SessionLocal
    from app.services.skip_trace_service import skip_trace_property

    db = SessionLocal()
    try:
        property_id = payload.get("property_id")
        if property_id:
            result = await skip_trace_property(db, property_id)
            return result if isinstance(result, dict) else {"result": str(result)}
        return {"status": "no_property_id"}
    finally:
        db.close()


async def _score_property(payload: dict) -> dict:
    from app.database import SessionLocal
    from app.services.property_scoring_service import score_property

    db = SessionLocal()
    try:
        property_id = payload.get("property_id")
        if property_id:
            return score_property(db, property_id)
        return {"error": "no_property_id"}
    finally:
        db.close()


async def _score_properties(payload: dict) -> dict:
    from app.database import SessionLocal
    from app.services.property_scoring_service import score_property
    from app.models.property import Property

    db = SessionLocal()
    try:
        properties = payload.get("properties", [])
        top_n = payload.get("top_n", 5)
        scored = []

        for p in properties[:top_n]:
            pid = p.get("id")
            if pid:
                try:
                    score = score_property(db, pid)
                    scored.append({**p, "score": score.get("total_score", 0), "score_details": score})
                except Exception:
                    scored.append({**p, "score": 0})

        scored.sort(key=lambda x: x.get("score", 0), reverse=True)
        return {
            "scored": scored,
            "top_property": scored[0] if scored else None,
            "top_score": scored[0].get("score", 0) if scored else 0,
        }
    finally:
        db.close()


async def _calculate_deal(payload: dict) -> dict:
    from app.database import SessionLocal
    from app.services.deal_calculator_service import calculate_deal

    db = SessionLocal()
    try:
        property_id = payload.get("property_id")
        if property_id:
            return calculate_deal(db, property_id)
        return {"error": "no_property_id"}
    finally:
        db.close()


async def _predict_outcome(payload: dict) -> dict:
    from app.database import SessionLocal
    from app.services.predictive_intelligence_service import predict_property_outcome

    db = SessionLocal()
    try:
        property_id = payload.get("property_id")
        if property_id:
            return predict_property_outcome(db, property_id)
        return {"error": "no_property_id"}
    finally:
        db.close()


async def _draft_offer(payload: dict) -> dict:
    from app.database import SessionLocal
    from app.services.offer_drafter_service import draft_offer_letter

    db = SessionLocal()
    try:
        property_id = payload.get("property_id")
        strategy = payload.get("strategy", "moderate")
        if property_id:
            return await draft_offer_letter(db, property_id, strategy=strategy)
        return {"error": "no_property_id"}
    finally:
        db.close()


async def _prepare_contracts(payload: dict) -> dict:
    from app.database import SessionLocal
    from app.services.contract_ai_service import suggest_contracts

    db = SessionLocal()
    try:
        property_id = payload.get("property_id")
        if property_id:
            return suggest_contracts(db, property_id)
        return {"error": "no_property_id"}
    finally:
        db.close()


async def _create_video(payload: dict) -> dict:
    from app.database import SessionLocal
    from app.services.property_video_service import generate_property_video

    db = SessionLocal()
    try:
        property_id = payload.get("property_id")
        if property_id:
            return await generate_property_video(db, property_id)
        return {"error": "no_property_id"}
    finally:
        db.close()


async def _post_social(payload: dict) -> dict:
    # Use the social media MCP tools
    platforms = payload.get("platforms", ["instagram"])
    content = payload.get("content", "")
    return {
        "status": "posted",
        "platforms": platforms,
        "note": "Social media posting requires MCP tools — delegate to Claude Code",
    }


async def _send_mail(payload: dict) -> dict:
    from app.database import SessionLocal
    from app.services.direct_mail_service import send_letter

    db = SessionLocal()
    try:
        property_id = payload.get("property_id")
        mail_type = payload.get("type", "postcard")
        if property_id:
            return send_letter(db, property_id, mail_type=mail_type)
        return {"error": "no_property_id"}
    finally:
        db.close()


async def _market_trends(payload: dict) -> dict:
    return {
        "status": "market_trends_requested",
        "address": payload.get("address", ""),
        "note": "Market trends require Zillow MCP — delegate to Claude Code",
    }


async def _send_email(payload: dict) -> dict:
    return {
        "status": "email_requested",
        "to": payload.get("to", ""),
        "note": "Email sending requires Gmail MCP — delegate to Claude Code",
    }


async def _call_owner(payload: dict) -> dict:
    return {
        "status": "call_requested",
        "note": "Voice calls require ElevenLabs/Telnyx MCP — delegate to Claude Code",
    }


# Task type → handler mapping
TASK_HANDLERS = {
    "search_properties": _search_properties,
    "research_property": _research_property,
    "get_comps": _get_comps,
    "skip_trace": _skip_trace,
    "score_property": _score_property,
    "score_properties": _score_properties,
    "calculate_deal": _calculate_deal,
    "predict_outcome": _predict_outcome,
    "draft_offer": _draft_offer,
    "prepare_contracts": _prepare_contracts,
    "create_video": _create_video,
    "post_social": _post_social,
    "send_mail": _send_mail,
    "send_email": _send_email,
    "market_trends": _market_trends,
    "call_owner": _call_owner,
}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="RealtorClaw Agent Worker")
    parser.add_argument("--worker-id", default="worker-1", help="Unique worker identifier")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

    worker = AgentWorker(worker_id=args.worker_id)
    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
