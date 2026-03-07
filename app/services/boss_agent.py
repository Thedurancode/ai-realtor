"""Boss Agent — breaks high-level goals into tasks, dispatches to workers, makes decisions.

The boss agent:
1. Receives a goal (e.g. "Find me a deal in Bergen County under 400K")
2. Plans a sequence of tasks
3. Dispatches tasks to workers via AgentBus
4. Collects results
5. Makes decisions and dispatches follow-up tasks
6. Returns a final summary

Usage:
    boss = BossAgent()
    await boss.start()
    result = await boss.execute_goal("Find me a deal in Bergen County under 400K")
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.services.agent_bus import AgentBus, TaskResult, TaskStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Task type registry — maps task_type to what workers should do
# ---------------------------------------------------------------------------

TASK_TYPES = {
    # Research
    "search_properties": "Search for properties matching criteria",
    "research_property": "Deep research on a specific property",
    "get_comps": "Get comparable sales for a property",
    "skip_trace": "Find owner contact info",
    "market_trends": "Analyze market trends for an area",

    # Analysis
    "score_property": "Score a property on investment potential",
    "calculate_deal": "Run deal calculator (MAO, cash flow, ROI)",
    "predict_outcome": "Predict deal outcome probability",

    # Action
    "draft_offer": "Draft an offer letter",
    "prepare_contracts": "Prepare contract package",
    "create_video": "Create property marketing video",
    "post_social": "Post to social media platforms",
    "send_mail": "Send direct mail piece",
    "send_email": "Send email",

    # Communication
    "call_owner": "Make a phone call to property owner",
    "send_sms": "Send SMS to contact",
}


@dataclass
class Goal:
    goal_id: str
    description: str
    status: str = "planning"
    tasks_dispatched: list[str] = field(default_factory=list)
    tasks_completed: dict[str, Any] = field(default_factory=dict)
    decisions: list[str] = field(default_factory=list)
    summary: str = ""
    created_at: float = 0


@dataclass
class TaskPlan:
    """A planned task with optional dependencies."""
    task_type: str
    payload: dict
    depends_on: list[str] = field(default_factory=list)
    condition: str = ""  # e.g. "score > 70"


class BossAgent:
    def __init__(self):
        self.bus = AgentBus(role="boss", worker_id="boss-main")
        self.goals: dict[str, Goal] = {}
        self._connected = False

    async def start(self):
        self._connected = await self.bus.connect()
        if not self._connected:
            raise RuntimeError("Boss agent failed to connect to Redis")
        logger.info("Boss agent started")

    async def stop(self):
        await self.bus.close()

    # --- Goal execution ---

    async def execute_goal(self, description: str, params: dict | None = None) -> dict:
        goal = Goal(
            goal_id=f"goal-{uuid.uuid4().hex[:8]}",
            description=description,
            created_at=time.time(),
        )
        self.goals[goal.goal_id] = goal
        params = params or {}

        logger.info("Goal %s: %s", goal.goal_id, description)

        # Phase 1: Plan
        goal.status = "planning"
        plan = self._plan_goal(description, params)
        goal.decisions.append(f"Planned {len(plan)} tasks")

        # Phase 2: Execute in waves (respecting dependencies)
        goal.status = "executing"
        await self._execute_plan(goal, plan)

        # Phase 3: Summarize
        goal.status = "complete"
        goal.summary = self._summarize(goal)

        return {
            "goal_id": goal.goal_id,
            "status": goal.status,
            "tasks_completed": len(goal.tasks_completed),
            "decisions": goal.decisions,
            "summary": goal.summary,
            "results": goal.tasks_completed,
        }

    # --- Planning ---

    def _plan_goal(self, description: str, params: dict) -> list[TaskPlan]:
        desc_lower = description.lower()

        # Goal: Find a deal
        if any(w in desc_lower for w in ["find", "deal", "search", "properties"]):
            return self._plan_find_deal(params)

        # Goal: Research a specific property
        if any(w in desc_lower for w in ["research", "analyze"]) and params.get("address"):
            return self._plan_research_property(params)

        # Goal: Make an offer
        if any(w in desc_lower for w in ["offer", "buy", "acquire"]):
            return self._plan_make_offer(params)

        # Goal: Market a property
        if any(w in desc_lower for w in ["market", "promote", "advertise", "post"]):
            return self._plan_market_property(params)

        # Default: just search
        return self._plan_find_deal(params)

    def _plan_find_deal(self, params: dict) -> list[TaskPlan]:
        search_params = {
            "location": params.get("location", ""),
            "max_price": params.get("max_price", 500000),
            "min_beds": params.get("min_beds", 2),
            "property_type": params.get("property_type", ""),
        }

        return [
            # Wave 1: Search
            TaskPlan(
                task_type="search_properties",
                payload=search_params,
            ),
            # Wave 2: Score top results (depends on search)
            TaskPlan(
                task_type="score_properties",
                payload={"top_n": 5},
                depends_on=["search_properties"],
            ),
            # Wave 3: Deep research on best (depends on scoring)
            TaskPlan(
                task_type="research_property",
                payload={"pick": "highest_score"},
                depends_on=["score_properties"],
            ),
            TaskPlan(
                task_type="get_comps",
                payload={"pick": "highest_score"},
                depends_on=["score_properties"],
            ),
            TaskPlan(
                task_type="skip_trace",
                payload={"pick": "highest_score"},
                depends_on=["score_properties"],
            ),
            # Wave 4: Calculate deal (depends on research + comps)
            TaskPlan(
                task_type="calculate_deal",
                payload={},
                depends_on=["research_property", "get_comps"],
            ),
        ]

    def _plan_research_property(self, params: dict) -> list[TaskPlan]:
        address = params.get("address", "")
        return [
            # Wave 1: Parallel research
            TaskPlan(task_type="research_property", payload={"address": address}),
            TaskPlan(task_type="get_comps", payload={"address": address}),
            TaskPlan(task_type="skip_trace", payload={"address": address}),
            TaskPlan(task_type="market_trends", payload={"address": address}),
            # Wave 2: Analysis
            TaskPlan(
                task_type="score_property",
                payload={"address": address},
                depends_on=["research_property", "get_comps"],
            ),
            TaskPlan(
                task_type="calculate_deal",
                payload={"address": address},
                depends_on=["research_property", "get_comps"],
            ),
            TaskPlan(
                task_type="predict_outcome",
                payload={"address": address},
                depends_on=["score_property"],
            ),
        ]

    def _plan_make_offer(self, params: dict) -> list[TaskPlan]:
        address = params.get("address", "")
        return [
            # Wave 1: Research if not already done
            TaskPlan(task_type="research_property", payload={"address": address}),
            TaskPlan(task_type="get_comps", payload={"address": address}),
            # Wave 2: Calculate and score
            TaskPlan(
                task_type="calculate_deal",
                payload={"address": address},
                depends_on=["research_property", "get_comps"],
            ),
            # Wave 3: Draft offer
            TaskPlan(
                task_type="draft_offer",
                payload={"address": address, "strategy": params.get("strategy", "moderate")},
                depends_on=["calculate_deal"],
            ),
            # Wave 4: Prepare contracts
            TaskPlan(
                task_type="prepare_contracts",
                payload={"address": address},
                depends_on=["draft_offer"],
            ),
        ]

    def _plan_market_property(self, params: dict) -> list[TaskPlan]:
        address = params.get("address", "")
        return [
            # Wave 1: Research for content
            TaskPlan(task_type="research_property", payload={"address": address}),
            # Wave 2: Create content (parallel)
            TaskPlan(
                task_type="create_video",
                payload={"address": address},
                depends_on=["research_property"],
            ),
            TaskPlan(
                task_type="draft_offer",
                payload={"address": address, "type": "listing_description"},
                depends_on=["research_property"],
            ),
            # Wave 3: Distribute
            TaskPlan(
                task_type="post_social",
                payload={"address": address, "platforms": ["instagram", "facebook", "linkedin"]},
                depends_on=["create_video"],
            ),
            TaskPlan(
                task_type="send_mail",
                payload={"address": address, "type": "just_listed"},
                depends_on=["research_property"],
            ),
        ]

    # --- Execution ---

    async def _execute_plan(self, goal: Goal, plan: list[TaskPlan]):
        completed_types: set[str] = set()
        task_id_by_type: dict[str, str] = {}
        pending = list(plan)

        while pending:
            # Find tasks whose dependencies are met
            ready = [
                t for t in pending
                if all(dep in completed_types for dep in t.depends_on)
            ]

            if not ready:
                if pending:
                    logger.warning(
                        "Goal %s: %d tasks stuck with unmet dependencies",
                        goal.goal_id, len(pending),
                    )
                break

            # Dispatch ready tasks in parallel
            dispatched_ids = []
            dispatched_tasks = []
            for task_plan in ready:
                # Inject results from previous tasks into payload
                enriched_payload = self._enrich_payload(task_plan, goal)
                task_id = await self.bus.publish_task(
                    task_plan.task_type,
                    enriched_payload,
                    goal_id=goal.goal_id,
                )
                dispatched_ids.append(task_id)
                dispatched_tasks.append(task_plan)
                task_id_by_type[task_plan.task_type] = task_id
                goal.tasks_dispatched.append(task_id)

            logger.info(
                "Goal %s: dispatched %d tasks: %s",
                goal.goal_id,
                len(dispatched_ids),
                [t.task_type for t in dispatched_tasks],
            )

            # Wait for all dispatched tasks
            results = await self.bus.wait_for_results(dispatched_ids, timeout=300)

            # Process results
            for task_plan, task_id in zip(dispatched_tasks, dispatched_ids):
                result = results.get(task_id)
                if result and result.status == TaskStatus.COMPLETED:
                    goal.tasks_completed[task_plan.task_type] = result.result
                    completed_types.add(task_plan.task_type)
                    pending.remove(task_plan)
                    logger.info("Goal %s: %s completed", goal.goal_id, task_plan.task_type)
                elif result and result.status == TaskStatus.FAILED:
                    goal.decisions.append(f"Task {task_plan.task_type} failed: {result.error}")
                    pending.remove(task_plan)
                    completed_types.add(task_plan.task_type)  # Don't block dependents
                else:
                    goal.decisions.append(f"Task {task_plan.task_type} timed out")
                    pending.remove(task_plan)
                    completed_types.add(task_plan.task_type)

            # Decision point: check if we should continue or abort
            if not self._should_continue(goal):
                goal.decisions.append("Stopping early based on results")
                break

    def _enrich_payload(self, task_plan: TaskPlan, goal: Goal) -> dict:
        """Inject results from completed tasks into the payload."""
        payload = dict(task_plan.payload)

        # If this task depends on search results, inject the top properties
        if "search_properties" in task_plan.depends_on:
            search_results = goal.tasks_completed.get("search_properties", {})
            if isinstance(search_results, dict):
                payload["properties"] = search_results.get("properties", [])

        # If depends on scoring, inject the best property
        if "score_properties" in task_plan.depends_on:
            scores = goal.tasks_completed.get("score_properties", {})
            if isinstance(scores, dict) and scores.get("top_property"):
                payload["property"] = scores["top_property"]
                payload["address"] = scores["top_property"].get("address", payload.get("address", ""))

        # If depends on research, inject research data
        if "research_property" in task_plan.depends_on:
            research = goal.tasks_completed.get("research_property", {})
            if isinstance(research, dict):
                payload["research"] = research

        # If depends on comps, inject comp data
        if "get_comps" in task_plan.depends_on:
            comps = goal.tasks_completed.get("get_comps", {})
            if isinstance(comps, dict):
                payload["comps"] = comps

        # If depends on deal calc, inject numbers
        if "calculate_deal" in task_plan.depends_on:
            deal = goal.tasks_completed.get("calculate_deal", {})
            if isinstance(deal, dict):
                payload["deal_analysis"] = deal

        return payload

    def _should_continue(self, goal: Goal) -> bool:
        """Check if the goal should continue executing."""
        # If scoring found nothing good, stop
        scores = goal.tasks_completed.get("score_properties", {})
        if isinstance(scores, dict) and scores.get("top_score", 100) < 30:
            goal.decisions.append("Best property scored below 30 — not worth pursuing")
            return False
        return True

    def _summarize(self, goal: Goal) -> str:
        parts = [f"Goal: {goal.description}", ""]
        parts.append(f"Tasks completed: {len(goal.tasks_completed)}/{len(goal.tasks_dispatched)}")

        if goal.decisions:
            parts.append("\nDecisions:")
            for d in goal.decisions:
                parts.append(f"  - {d}")

        # Highlight key results
        if "score_property" in goal.tasks_completed:
            score = goal.tasks_completed["score_property"]
            if isinstance(score, dict):
                parts.append(f"\nProperty Score: {score.get('total_score', 'N/A')}/100")

        if "calculate_deal" in goal.tasks_completed:
            deal = goal.tasks_completed["calculate_deal"]
            if isinstance(deal, dict):
                parts.append(f"MAO: ${deal.get('mao', 'N/A'):,}")
                parts.append(f"Cash Flow: ${deal.get('monthly_cash_flow', 'N/A'):,}/mo")

        if "draft_offer" in goal.tasks_completed:
            parts.append("\nOffer letter drafted and ready for review.")

        return "\n".join(parts)

    # --- Status ---

    async def get_status(self) -> dict:
        workers = await self.bus.get_active_workers()
        queue_depth = await self.bus.get_queue_depth()
        return {
            "boss": "running",
            "active_workers": len(workers),
            "workers": workers,
            "queue_depth": queue_depth,
            "active_goals": len([g for g in self.goals.values() if g.status == "executing"]),
            "completed_goals": len([g for g in self.goals.values() if g.status == "complete"]),
        }
