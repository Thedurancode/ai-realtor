"""Orchestration API — trigger multi-agent goals and check status."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/orchestrate", tags=["orchestration"])

# Singleton boss agent (lazy init)
_boss = None


async def _get_boss():
    global _boss
    if _boss is None:
        from app.services.boss_agent import BossAgent
        _boss = BossAgent()
        try:
            await _boss.start()
        except Exception as e:
            _boss = None
            raise HTTPException(503, f"Agent bus unavailable: {e}")
    return _boss


class GoalRequest(BaseModel):
    goal: str
    params: dict = {}

    model_config = {"json_schema_extra": {"examples": [
        {
            "goal": "Find me a deal in Bergen County under 400K",
            "params": {"location": "Bergen County, NJ", "max_price": 400000},
        },
        {
            "goal": "Research this property",
            "params": {"address": "123 Main St, Newark, NJ", "property_id": 42},
        },
        {
            "goal": "Make an offer on this property",
            "params": {"address": "456 Oak Ave, Jersey City, NJ", "property_id": 15, "strategy": "aggressive"},
        },
    ]}}


@router.post("/goal")
async def execute_goal(request: GoalRequest):
    """Execute a high-level goal using multi-agent orchestration.

    The boss agent plans tasks, dispatches to workers, collects results,
    and returns a summary. Requires Redis and at least one worker running.
    """
    boss = await _get_boss()
    result = await boss.execute_goal(request.goal, request.params)
    return result


@router.get("/status")
async def orchestration_status():
    """Get status of the orchestration system — workers, queue depth, active goals."""
    boss = await _get_boss()
    return await boss.get_status()


@router.get("/goals")
async def list_goals():
    """List all goals and their current status."""
    boss = await _get_boss()
    return {
        "goals": [
            {
                "goal_id": g.goal_id,
                "description": g.description,
                "status": g.status,
                "tasks_completed": len(g.tasks_completed),
                "tasks_dispatched": len(g.tasks_dispatched),
            }
            for g in boss.goals.values()
        ]
    }
