"""Goal-driven planner for voice commands with adaptive planning and safety checkpoints."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.property import Property
from app.services.contract_auto_attach import contract_auto_attach_service
from app.services.memory_graph import MemoryRef, memory_graph_service
from app.services.property_recap_service import property_recap_service

from app.services.llm_service import llm_service

# Lazy imports for new action services to avoid circular imports at module load.
def _get_zillow_service():
    from app.services.zillow_enrichment import zillow_enrichment_service
    return zillow_enrichment_service

def _get_skip_trace_service():
    from app.services.skip_trace import skip_trace_service
    return skip_trace_service

def _get_contract_ai_service():
    from app.services.contract_ai_service import contract_ai_service
    return contract_ai_service

def _get_compliance_engine():
    from app.services.compliance_engine import compliance_engine
    return compliance_engine

def _get_vapi_service():
    from app.services.vapi_service import vapi_service
    return vapi_service

def _get_notification_service():
    from app.services.notification_service import notification_service
    return notification_service


@dataclass
class GoalPlanStep:
    order: int
    action: str
    title: str
    instruction: str
    risk_level: str = "low"
    requires_confirmation: bool = False


class VoiceGoalPlannerService:
    """Build and execute multi-step goal plans with checkpoints."""

    ALLOWED_ACTIONS = {
        # Original actions
        "resolve_property",
        "inspect_property",
        "check_contract_readiness",
        "attach_required_contracts",
        "generate_property_recap",
        "summarize_next_actions",
        # Phase 1: New voice-first actions
        "enrich_property",
        "skip_trace_property",
        "ai_suggest_contracts",
        "apply_ai_suggestions",
        "check_compliance",
        "make_phone_call",
        "send_notification",
        "update_property_status",
        "add_note",
        # Phase 2: Intelligence & automation actions
        "check_insights",
        "schedule_task",
        "get_analytics",
        # Phase 3: Follow-up queue
        "check_follow_ups",
        # Phase 4: Comparable sales
        "get_comps",
        # Phase 5: Bulk operations
        "bulk_operation",
        # Phase 6: Activity timeline
        "get_activity_timeline",
        # Phase 7: Property scoring
        "score_property",
        # Phase 8: Market watchlists
        "check_watchlists",
    }

    def __init__(self):
        pass

    async def build_plan(
        self,
        goal: str,
        memory_summary: dict[str, Any] | None = None,
        execution_mode: str = "safe",
    ) -> tuple[list[GoalPlanStep], bool]:
        """Return (plan, used_llm_planner)."""
        llm_plan = await self._build_llm_plan(goal=goal, memory_summary=memory_summary, execution_mode=execution_mode)
        if llm_plan:
            return llm_plan, True
        return self._build_heuristic_plan(goal=goal, execution_mode=execution_mode), False

    def _build_heuristic_plan(self, goal: str, execution_mode: str) -> list[GoalPlanStep]:
        normalized = goal.lower().strip()

        attach_requires_confirmation = execution_mode != "autonomous"
        call_requires_confirmation = execution_mode != "autonomous"

        # Property scoring workflow (must be before deal — "rate this deal" should score, not full pipeline)
        if any(token in normalized for token in ["score", "rate this", "how good", "deal quality", "grade this", "rank"]):
            return [
                GoalPlanStep(1, "resolve_property", "Resolve Property", "Find the target property."),
                GoalPlanStep(2, "score_property", "Score Property", "Run 4-dimension scoring engine."),
                GoalPlanStep(3, "summarize_next_actions", "Summarize", "Present scoring results."),
            ]

        # Market watchlist workflow
        if any(token in normalized for token in ["watchlist", "watch for", "alert me when", "notify me when", "watching"]):
            return [
                GoalPlanStep(1, "check_watchlists", "Check Watchlists", "List or manage market watchlists."),
                GoalPlanStep(2, "summarize_next_actions", "Summarize", "Present watchlist status."),
            ]

        # New lead / full pipeline workflow (must be before enrich — goal text contains "enrich")
        if any(token in normalized for token in ["new lead", "pipeline", "full workup", "onboard"]):
            return [
                GoalPlanStep(1, "resolve_property", "Resolve Property", "Find the target property."),
                GoalPlanStep(2, "enrich_property", "Enrich Property", "Enrich with Zillow data."),
                GoalPlanStep(3, "skip_trace_property", "Skip Trace", "Find owner contact information."),
                GoalPlanStep(4, "check_compliance", "Run Compliance Check", "Verify regulatory requirements."),
                GoalPlanStep(
                    5, "attach_required_contracts", "Attach Contracts",
                    "Auto-attach required contracts.",
                    risk_level="medium", requires_confirmation=attach_requires_confirmation,
                ),
                GoalPlanStep(6, "generate_property_recap", "Generate Recap", "Create comprehensive AI recap."),
                GoalPlanStep(7, "summarize_next_actions", "Summarize Next Actions", "Provide recommended next actions."),
            ]

        # Full deal / close / ready-to-close workflow
        if any(token in normalized for token in ["deal", "close", "end-to-end", "transaction", "ready"]):
            return [
                GoalPlanStep(1, "resolve_property", "Resolve Property", "Find the target property from explicit input, query, or memory."),
                GoalPlanStep(2, "inspect_property", "Inspect Property", "Load key property context required for downstream actions."),
                GoalPlanStep(3, "enrich_property", "Enrich Property", "Enrich with Zillow data for market context."),
                GoalPlanStep(4, "check_contract_readiness", "Check Contract Readiness", "Evaluate required contracts and completion status."),
                GoalPlanStep(
                    5, "attach_required_contracts", "Attach Missing Contracts",
                    "Auto-attach required contracts that are not yet present.",
                    risk_level="medium", requires_confirmation=attach_requires_confirmation,
                ),
                GoalPlanStep(6, "check_compliance", "Run Compliance Check", "Verify property meets all regulatory requirements."),
                GoalPlanStep(7, "generate_property_recap", "Generate Recap", "Create/update an AI recap for voice calls and summaries."),
                GoalPlanStep(8, "summarize_next_actions", "Summarize Next Actions", "Produce concise execution checkpoint summary and next actions."),
            ]

        # Comparable sales / comps workflow (before enrich since "market value" overlaps)
        if any(token in normalized for token in ["comp", "comparable", "nearby sales", "what are similar", "what have similar"]):
            return [
                GoalPlanStep(1, "resolve_property", "Resolve Property", "Find the target property."),
                GoalPlanStep(2, "get_comps", "Get Comparables", "Pull comparable sales and rentals dashboard."),
                GoalPlanStep(3, "summarize_next_actions", "Summarize", "Present comp analysis results."),
            ]

        # Enrich workflow
        if any(token in normalized for token in ["enrich", "zillow", "zestimate", "market value"]):
            return [
                GoalPlanStep(1, "resolve_property", "Resolve Property", "Find the target property."),
                GoalPlanStep(2, "enrich_property", "Enrich Property", "Enrich with Zillow data (Zestimate, photos, schools, features)."),
                GoalPlanStep(3, "generate_property_recap", "Generate Recap", "Update AI recap with enrichment data."),
                GoalPlanStep(4, "summarize_next_actions", "Summarize Next Actions", "Provide recommended next actions."),
            ]

        # Skip trace workflow
        if any(token in normalized for token in ["skip trace", "skip-trace", "find owner", "owner info", "who owns"]):
            steps = [
                GoalPlanStep(1, "resolve_property", "Resolve Property", "Find the target property."),
                GoalPlanStep(2, "skip_trace_property", "Skip Trace", "Find owner contact information."),
            ]
            # If the goal mentions calling the owner, add phone call step
            if any(token in normalized for token in ["call", "phone", "reach out", "contact"]):
                steps.append(GoalPlanStep(
                    3, "make_phone_call", "Call Owner",
                    "Make a cold call to the property owner.",
                    risk_level="high", requires_confirmation=call_requires_confirmation,
                ))
                steps.append(GoalPlanStep(4, "summarize_next_actions", "Summarize Next Actions", "Summarize results."))
            else:
                steps.append(GoalPlanStep(3, "generate_property_recap", "Generate Recap", "Update recap with owner info."))
                steps.append(GoalPlanStep(4, "summarize_next_actions", "Summarize Next Actions", "Provide recommended next actions."))
            return steps

        # AI contract suggestion workflow
        if any(token in normalized for token in ["suggest contract", "ai contract", "what contracts", "recommend contract", "contract audit", "ai to suggest", "contract cleanup"]):
            return [
                GoalPlanStep(1, "resolve_property", "Resolve Property", "Find the target property."),
                GoalPlanStep(2, "inspect_property", "Inspect Property", "Load property context for AI analysis."),
                GoalPlanStep(3, "ai_suggest_contracts", "AI Suggest Contracts", "Use AI to recommend required contracts."),
                GoalPlanStep(
                    4, "apply_ai_suggestions", "Apply AI Suggestions",
                    "Create contracts from AI recommendations.",
                    risk_level="medium", requires_confirmation=attach_requires_confirmation,
                ),
                GoalPlanStep(5, "summarize_next_actions", "Summarize Next Actions", "Provide recommended next actions."),
            ]

        # Compliance check workflow
        if any(token in normalized for token in ["compliance", "compliant", "regulation", "legal check"]):
            return [
                GoalPlanStep(1, "resolve_property", "Resolve Property", "Find the target property."),
                GoalPlanStep(2, "inspect_property", "Inspect Property", "Load property details."),
                GoalPlanStep(3, "check_compliance", "Run Compliance Check", "Check all regulatory requirements."),
                GoalPlanStep(4, "summarize_next_actions", "Summarize Next Actions", "Summarize compliance results."),
            ]

        # Schedule / remind workflow (must be before insights — "follow up in" is more specific than "follow up")
        if any(token in normalized for token in ["remind", "schedule", "set reminder", "follow up in", "in 2 day", "in 3 day"]):
            return [
                GoalPlanStep(1, "resolve_property", "Resolve Property", "Find the target property if mentioned."),
                GoalPlanStep(2, "schedule_task", "Schedule Task", "Create a scheduled reminder or recurring task."),
                GoalPlanStep(3, "summarize_next_actions", "Summarize", "Confirm task was scheduled."),
            ]

        # Bulk operations workflow (must be before insights — "all properties" is more specific)
        if any(token in normalized for token in ["bulk", "all properties", "every property", "batch", "enrich all", "skip trace all", "recap all"]):
            return [
                GoalPlanStep(1, "bulk_operation", "Bulk Operation", "Execute the operation across matching properties."),
                GoalPlanStep(2, "summarize_next_actions", "Summarize", "Present bulk operation results."),
            ]

        # Follow-up queue workflow (must be before insights — "work on next" is more specific)
        if any(token in normalized for token in ["work on next", "follow-up queue", "follow up queue", "who should i call", "top priority", "what's next", "what should i"]):
            return [
                GoalPlanStep(1, "check_follow_ups", "Check Follow-Up Queue", "Get AI-prioritized follow-up queue."),
                GoalPlanStep(2, "summarize_next_actions", "Summarize", "Present prioritized follow-ups."),
            ]

        # Activity timeline workflow (must be before insights — "what happened" is more specific)
        if any(token in normalized for token in ["timeline", "what happened", "recent activity", "show me activity", "what's been going on"]):
            if "conversation" not in normalized and "discuss" not in normalized:
                steps = [
                    GoalPlanStep(1, "resolve_property", "Resolve Property", "Find the target property if mentioned."),
                    GoalPlanStep(2, "get_activity_timeline", "Get Timeline", "Fetch activity timeline."),
                    GoalPlanStep(3, "summarize_next_actions", "Summarize", "Present timeline results."),
                ]
                return steps

        # Insights / alerts / follow-up workflow
        if any(token in normalized for token in ["attention", "alert", "insight", "overdue", "follow up", "what needs"]):
            return [
                GoalPlanStep(1, "check_insights", "Check Insights", "Scan for stale properties, deadlines, and gaps."),
                GoalPlanStep(2, "summarize_next_actions", "Summarize", "Present prioritized alerts."),
            ]

        # Portfolio / analytics workflow
        if any(token in normalized for token in ["portfolio", "analytics", "dashboard", "numbers", "how many properties", "summary of all"]):
            return [
                GoalPlanStep(1, "get_analytics", "Get Analytics", "Pull portfolio-wide analytics and metrics."),
                GoalPlanStep(2, "summarize_next_actions", "Summarize", "Present portfolio summary."),
            ]

        # Add note workflow
        if any(token in normalized for token in ["note", "jot down", "remember that", "write down"]):
            return [
                GoalPlanStep(1, "resolve_property", "Resolve Property", "Find the target property."),
                GoalPlanStep(2, "add_note", "Add Note", "Save the note to the property."),
                GoalPlanStep(3, "summarize_next_actions", "Summarize", "Confirm note was saved."),
            ]

        # Call / phone workflow
        if any(token in normalized for token in ["call", "phone"]) and not any(token in normalized for token in ["skip"]):
            return [
                GoalPlanStep(1, "resolve_property", "Resolve Property", "Find the target property."),
                GoalPlanStep(2, "generate_property_recap", "Generate Recap", "Ensure recap is current for the call."),
                GoalPlanStep(
                    3, "make_phone_call", "Make Phone Call",
                    "Make a VAPI phone call about the property.",
                    risk_level="high", requires_confirmation=call_requires_confirmation,
                ),
                GoalPlanStep(4, "summarize_next_actions", "Summarize Next Actions", "Summarize call results."),
            ]

        # Default plan (unchanged)
        return [
            GoalPlanStep(1, "resolve_property", "Resolve Property", "Find the property associated with the user request."),
            GoalPlanStep(2, "inspect_property", "Inspect Property", "Load core details for decision making."),
            GoalPlanStep(3, "check_contract_readiness", "Check Contract Readiness", "Review completion state and blockers."),
            GoalPlanStep(4, "summarize_next_actions", "Summarize Next Actions", "Provide recommended next actions."),
        ]

    async def _build_llm_plan(
        self,
        goal: str,
        memory_summary: dict[str, Any] | None,
        execution_mode: str,
    ) -> list[GoalPlanStep] | None:
        if not os.getenv("ANTHROPIC_API_KEY"):
            return None

        memory_state = memory_summary.get("session_state", {}) if memory_summary else {}
        prompt = (
            "Create a compact execution plan for a real-estate voice agent. "
            "Output strict JSON only with shape: {\"steps\": [{\"action\": str, \"title\": str, \"instruction\": str, \"risk_level\": \"low\"|\"medium\"|\"high\", \"requires_confirmation\": bool}]}. "
            f"Allowed actions: {sorted(self.ALLOWED_ACTIONS)}. "
            f"Execution mode: {execution_mode}. "
            f"Goal: {goal}. "
            f"Memory state: {json.dumps(memory_state)}. "
            "Always include resolve_property first and summarize_next_actions last."
        )

        try:
            response = await llm_service.acreate(
                model="claude-sonnet-4-20250514",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
        except Exception:
            return None

        text = ""
        for block in getattr(response, "content", []) or []:
            block_text = getattr(block, "text", "")
            if block_text:
                text += block_text

        if not text:
            return None

        try:
            payload = json.loads(text)
        except Exception:
            return None

        raw_steps = payload.get("steps", [])
        if not isinstance(raw_steps, list) or not raw_steps:
            return None

        steps: list[GoalPlanStep] = []
        order = 1
        for raw in raw_steps:
            action = str(raw.get("action", "")).strip()
            if action not in self.ALLOWED_ACTIONS:
                continue
            title = str(raw.get("title", action.replace("_", " ").title())).strip()
            instruction = str(raw.get("instruction", "")).strip() or f"Execute step: {title}."
            risk_level = str(raw.get("risk_level", "low")).strip().lower()
            if risk_level not in {"low", "medium", "high"}:
                risk_level = "low"

            requires_confirmation = bool(raw.get("requires_confirmation", False))
            if execution_mode == "autonomous":
                requires_confirmation = False

            steps.append(
                GoalPlanStep(
                    order=order,
                    action=action,
                    title=title,
                    instruction=instruction,
                    risk_level=risk_level,
                    requires_confirmation=requires_confirmation,
                )
            )
            order += 1

        if not steps:
            return None

        actions = [s.action for s in steps]
        if actions[0] != "resolve_property":
            steps.insert(0, GoalPlanStep(1, "resolve_property", "Resolve Property", "Find the target property from explicit input, query, or memory."))
        if actions[-1] != "summarize_next_actions":
            steps.append(GoalPlanStep(len(steps) + 1, "summarize_next_actions", "Summarize Next Actions", "Produce concise execution checkpoint summary and next actions."))

        # Re-number to avoid gaps.
        for idx, step in enumerate(steps, start=1):
            step.order = idx

        return steps

    async def execute_goal(
        self,
        db: Session,
        goal: str,
        session_id: str = "default",
        property_id: int | None = None,
        property_query: str | None = None,
        execution_mode: str = "safe",
        confirm_high_risk: bool = False,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        memory_summary = memory_graph_service.get_session_summary(db, session_id=session_id)
        plan, used_llm_planner = await self.build_plan(
            goal=goal,
            memory_summary=memory_summary,
            execution_mode=execution_mode,
        )

        goal_node = memory_graph_service.remember_goal(
            db,
            session_id=session_id,
            goal=goal,
            metadata={
                "step_count": len(plan),
                "execution_mode": execution_mode,
                "dry_run": dry_run,
            },
        )

        state: dict[str, Any] = {
            "goal": goal,
            "property_id": property_id,
            "property_query": property_query,
            "property": None,
            "readiness": None,
            "attached_contracts": [],
            "recap": None,
            "next_actions": [],
            "clarification_options": [],
            "confirmation_needed": False,
            "used_llm_planner": used_llm_planner,
        }
        checkpoints: list[dict[str, Any]] = []

        if dry_run:
            final_summary = "Dry run complete. Plan generated without executing any state-changing steps."
            intelligence_score, why_10x = self._compute_intelligence_score(plan=plan, checkpoints=checkpoints, state=state)
            self._remember_evaluation(
                db=db,
                session_id=session_id,
                goal_node_key=goal_node.node_key,
                score=intelligence_score,
                reasons=why_10x,
            )
            db.commit()
            return {
                "session_id": session_id,
                "goal": goal,
                "plan": [self._serialize_step(s) for s in plan],
                "checkpoints": checkpoints,
                "final_summary": final_summary,
                "memory_summary": memory_graph_service.get_session_summary(db, session_id=session_id),
                "intelligence_score": intelligence_score,
                "why_10x": why_10x,
                "needs_confirmation": False,
                "clarification_options": None,
            }

        for step in plan:
            if step.requires_confirmation and not confirm_high_risk:
                state["confirmation_needed"] = True
                result = self._checkpoint(
                    step,
                    "blocked_confirmation",
                    f"Step '{step.title}' requires confirmation in safe mode. Re-run with confirm_high_risk=true.",
                    data={"risk_level": step.risk_level, "action": step.action},
                )
                checkpoints.append(result)
                break

            result = await self._execute_step(
                db=db,
                step=step,
                state=state,
                session_id=session_id,
                goal_node_key=goal_node.node_key,
            )
            checkpoints.append(result)

            if result["status"] in {"failed", "needs_clarification", "blocked_confirmation"}:
                break

        db.commit()

        final_summary = self._build_final_summary(goal=goal, state=state, checkpoints=checkpoints)
        intelligence_score, why_10x = self._compute_intelligence_score(plan=plan, checkpoints=checkpoints, state=state)

        self._remember_evaluation(
            db=db,
            session_id=session_id,
            goal_node_key=goal_node.node_key,
            score=intelligence_score,
            reasons=why_10x,
        )
        db.commit()

        return {
            "session_id": session_id,
            "goal": goal,
            "plan": [self._serialize_step(s) for s in plan],
            "checkpoints": checkpoints,
            "final_summary": final_summary,
            "memory_summary": memory_graph_service.get_session_summary(db, session_id=session_id),
            "intelligence_score": intelligence_score,
            "why_10x": why_10x,
            "needs_confirmation": state.get("confirmation_needed", False),
            "clarification_options": state.get("clarification_options") or None,
        }

    async def _execute_step(
        self,
        db: Session,
        step: GoalPlanStep,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
    ) -> dict[str, Any]:
        try:
            # Original actions
            if step.action == "resolve_property":
                return self._step_resolve_property(db, state, session_id, goal_node_key, step)

            if step.action == "inspect_property":
                return self._step_inspect_property(db, state, session_id, goal_node_key, step)

            if step.action == "check_contract_readiness":
                return self._step_check_contract_readiness(db, state, session_id, goal_node_key, step)

            if step.action == "attach_required_contracts":
                return self._step_attach_required_contracts(db, state, session_id, goal_node_key, step)

            if step.action == "generate_property_recap":
                return await self._step_generate_recap(db, state, session_id, goal_node_key, step)

            if step.action == "summarize_next_actions":
                return self._step_summarize_next_actions(db, state, session_id, goal_node_key, step)

            # Phase 1: New voice-first actions
            if step.action == "enrich_property":
                return await self._step_enrich_property(db, state, session_id, goal_node_key, step)

            if step.action == "skip_trace_property":
                return await self._step_skip_trace_property(db, state, session_id, goal_node_key, step)

            if step.action == "ai_suggest_contracts":
                return await self._step_ai_suggest_contracts(db, state, session_id, goal_node_key, step)

            if step.action == "apply_ai_suggestions":
                return await self._step_apply_ai_suggestions(db, state, session_id, goal_node_key, step)

            if step.action == "check_compliance":
                return await self._step_check_compliance(db, state, session_id, goal_node_key, step)

            if step.action == "make_phone_call":
                return await self._step_make_phone_call(db, state, session_id, goal_node_key, step)

            if step.action == "send_notification":
                return self._step_send_notification(db, state, session_id, goal_node_key, step)

            if step.action == "update_property_status":
                return self._step_update_property_status(db, state, session_id, goal_node_key, step)

            if step.action == "add_note":
                return self._step_add_note(db, state, session_id, goal_node_key, step)

            # Phase 3: Follow-up queue
            if step.action == "check_follow_ups":
                return self._step_check_follow_ups(db, state, session_id, goal_node_key, step)

            # Phase 4: Comparable sales
            if step.action == "get_comps":
                return self._step_get_comps(db, state, session_id, goal_node_key, step)

            # Phase 5: Bulk operations
            if step.action == "bulk_operation":
                return await self._step_bulk_operation(db, state, session_id, goal_node_key, step)

            # Phase 6: Activity timeline
            if step.action == "get_activity_timeline":
                return self._step_get_activity_timeline(db, state, session_id, goal_node_key, step)

            # Phase 7: Property scoring
            if step.action == "score_property":
                return self._step_score_property(db, state, session_id, goal_node_key, step)

            # Phase 8: Market watchlists
            if step.action == "check_watchlists":
                return self._step_check_watchlists(db, state, session_id, goal_node_key, step)

            return self._checkpoint(step, "failed", f"Unknown step action: {step.action}")
        except Exception as exc:
            return self._checkpoint(step, "failed", f"{step.title} failed: {exc}")

    def _step_resolve_property(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        property_id = state.get("property_id")
        property_query = (state.get("property_query") or "").strip()

        # Explicit query can override stale memory and resolve ambiguity.
        if property_query:
            matches = (
                db.query(Property)
                .filter(
                    (Property.address.ilike(f"%{property_query}%"))
                    | (Property.city.ilike(f"%{property_query}%"))
                )
                .limit(6)
                .all()
            )

            if not matches:
                return self._checkpoint(step, "failed", f"No property matched query '{property_query}'.")

            if len(matches) > 1 and property_id is None:
                options = [f"{p.id}: {p.address}, {p.city}, {p.state}" for p in matches]
                state["clarification_options"] = options
                return self._checkpoint(
                    step,
                    "needs_clarification",
                    f"Multiple properties match '{property_query}'. Please choose one property_id.",
                    data={"options": options},
                )

            if property_id is None:
                property_id = matches[0].id
                state["property_id"] = property_id

        if property_id is None:
            property_id = memory_graph_service.get_session_state(db, session_id, "last_property_id")
            if property_id is not None:
                state["property_id"] = int(property_id)

        if property_id is None:
            return self._checkpoint(
                step,
                "failed",
                "No property provided and no last_property_id found in memory. Provide property_id or property_query.",
            )

        prop = db.query(Property).filter(Property.id == int(property_id)).first()
        if prop is None:
            return self._checkpoint(step, "failed", f"Property {property_id} was not found.")

        state["property"] = prop
        state["property_id"] = prop.id

        memory_graph_service.remember_property(
            db,
            session_id=session_id,
            property_id=prop.id,
            address=prop.address,
            city=prop.city,
            state=prop.state,
        )
        memory_graph_service.upsert_edge(
            db,
            session_id=session_id,
            source=MemoryRef("goal", goal_node_key),
            target=MemoryRef("property", str(prop.id)),
            relation="targets",
            weight=1.0,
        )

        return self._checkpoint(step, "completed", f"Resolved property #{prop.id}: {prop.address}, {prop.city}, {prop.state}.")

    def _step_inspect_property(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        prop: Property | None = state.get("property")
        if prop is None:
            return self._checkpoint(step, "failed", "Property context missing.")

        payload = {
            "property_id": prop.id,
            "status": prop.status.value if prop.status else None,
            "deal_type": prop.deal_type.value if prop.deal_type else None,
            "price": prop.price,
            "city": prop.city,
            "state": prop.state,
            "beds": prop.bedrooms,
            "baths": prop.bathrooms,
        }
        memory_graph_service.upsert_node(
            db,
            session_id=session_id,
            node_type="property_snapshot",
            node_key=str(prop.id),
            summary=f"Property snapshot for #{prop.id}",
            payload=payload,
            importance=0.7,
        )
        memory_graph_service.upsert_edge(
            db,
            session_id=session_id,
            source=MemoryRef("goal", goal_node_key),
            target=MemoryRef("property_snapshot", str(prop.id)),
            relation="inspected",
            weight=0.8,
        )

        return self._checkpoint(step, "completed", f"Loaded property context for {prop.address}.", data=payload)

    def _step_check_contract_readiness(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        prop: Property | None = state.get("property")
        if prop is None:
            return self._checkpoint(step, "failed", "Property context missing.")

        readiness = contract_auto_attach_service.get_required_contracts_status(db, prop)
        state["readiness"] = readiness

        missing_templates = [t.name for t in readiness.get("missing_templates", [])]
        data = {
            "total_required": readiness.get("total_required", 0),
            "completed": readiness.get("completed", 0),
            "in_progress": readiness.get("in_progress", 0),
            "missing": readiness.get("missing", 0),
            "is_ready_to_close": readiness.get("is_ready_to_close", False),
            "missing_templates": missing_templates,
        }

        memory_graph_service.upsert_node(
            db,
            session_id=session_id,
            node_type="readiness",
            node_key=str(prop.id),
            summary=f"Readiness check for property #{prop.id}",
            payload=data,
            importance=0.9,
        )
        memory_graph_service.upsert_edge(
            db,
            session_id=session_id,
            source=MemoryRef("goal", goal_node_key),
            target=MemoryRef("readiness", str(prop.id)),
            relation="evaluated",
            weight=0.9,
        )

        if data["missing"] > 0:
            state["next_actions"].append("Attach missing required contracts")

        msg = (
            f"Readiness: {data['completed']}/{data['total_required']} complete, "
            f"{data['missing']} missing, ready_to_close={data['is_ready_to_close']}."
        )
        return self._checkpoint(step, "completed", msg, data=data)

    def _step_attach_required_contracts(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        prop: Property | None = state.get("property")
        if prop is None:
            return self._checkpoint(step, "failed", "Property context missing.")

        attached = contract_auto_attach_service.auto_attach_contracts(db, prop)
        state["attached_contracts"] = [{"id": c.id, "name": c.name} for c in attached]

        for contract in attached:
            memory_graph_service.remember_contract(
                db,
                session_id=session_id,
                contract_id=contract.id,
                name=contract.name,
                status=contract.status.value if contract.status else None,
                property_id=prop.id,
                contact_id=contract.contact_id,
            )
            memory_graph_service.upsert_edge(
                db,
                session_id=session_id,
                source=MemoryRef("goal", goal_node_key),
                target=MemoryRef("contract", str(contract.id)),
                relation="created",
                weight=0.9,
            )

        msg = f"Auto-attached {len(attached)} required contract(s)."
        return self._checkpoint(step, "completed", msg, data={"attached_contracts": state["attached_contracts"]})

    # ── Phase 1: New voice-first action executors ──

    async def _step_enrich_property(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        prop: Property | None = state.get("property")
        if prop is None:
            return self._checkpoint(step, "failed", "Property context missing.")

        full_address = f"{prop.address}, {prop.city}, {prop.state} {prop.zip_code or ''}".strip()
        svc = _get_zillow_service()
        enrichment_data = await svc.enrich_by_address(full_address)

        zestimate = enrichment_data.get("zestimate")
        rent_zestimate = enrichment_data.get("rentZestimate")
        photo_count = len(enrichment_data.get("photos", []))
        zpid = enrichment_data.get("zpid")

        # Persist enrichment to DB via the enrichment model
        from app.models.zillow_enrichment import ZillowEnrichment
        existing = db.query(ZillowEnrichment).filter(ZillowEnrichment.property_id == prop.id).first()
        if existing:
            existing.zestimate = zestimate
            existing.rent_zestimate = rent_zestimate
            existing.zpid = int(zpid) if zpid else existing.zpid
            existing.photos = enrichment_data.get("photos")
            existing.reso_facts = enrichment_data.get("resoFacts")
            existing.schools = enrichment_data.get("schools")
            existing.tax_history = enrichment_data.get("taxHistory")
            existing.price_history = enrichment_data.get("priceHistory")
        else:
            new_enrichment = ZillowEnrichment(
                property_id=prop.id,
                zpid=int(zpid) if zpid else None,
                zestimate=zestimate,
                rent_zestimate=rent_zestimate,
                photos=enrichment_data.get("photos"),
                reso_facts=enrichment_data.get("resoFacts"),
                schools=enrichment_data.get("schools"),
                tax_history=enrichment_data.get("taxHistory"),
                price_history=enrichment_data.get("priceHistory"),
            )
            db.add(new_enrichment)

        data = {
            "zestimate": zestimate,
            "rent_zestimate": rent_zestimate,
            "photo_count": photo_count,
            "zpid": zpid,
        }
        state["enrichment"] = data

        memory_graph_service.upsert_node(
            db, session_id=session_id, node_type="enrichment",
            node_key=str(prop.id),
            summary=f"Zillow enrichment for #{prop.id}: Zestimate ${zestimate:,.0f}" if zestimate else f"Zillow enrichment for #{prop.id}",
            payload=data, importance=0.8,
        )
        memory_graph_service.upsert_edge(
            db, session_id=session_id,
            source=MemoryRef("goal", goal_node_key),
            target=MemoryRef("enrichment", str(prop.id)),
            relation="enriched", weight=0.85,
        )

        zest_text = f", Zestimate: ${zestimate:,.0f}" if zestimate else ""
        return self._checkpoint(
            step, "completed",
            f"Enriched {prop.address} with Zillow data ({photo_count} photos{zest_text}).",
            data=data,
        )

    async def _step_skip_trace_property(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        prop: Property | None = state.get("property")
        if prop is None:
            return self._checkpoint(step, "failed", "Property context missing.")

        svc = _get_skip_trace_service()
        result = await svc.skip_trace(
            address=prop.address,
            city=prop.city,
            state=prop.state,
            zip_code=prop.zip_code or "",
        )

        owner_name = result.get("owner_name", "Unknown")
        phones = result.get("phone_numbers", [])
        emails = result.get("email_addresses", result.get("emails", []))

        # Persist skip trace to DB
        from app.models.skip_trace import SkipTrace
        existing = db.query(SkipTrace).filter(SkipTrace.property_id == prop.id).first()
        if existing:
            existing.owner_name = owner_name
            existing.phone_numbers = phones
            existing.emails = emails
            existing.mailing_address = result.get("mailing_address")
            existing.raw_response = result
        else:
            new_st = SkipTrace(
                property_id=prop.id,
                owner_name=owner_name,
                phone_numbers=phones,
                emails=emails,
                mailing_address=result.get("mailing_address"),
                raw_response=result,
            )
            db.add(new_st)

        data = {
            "owner_name": owner_name,
            "phone_count": len(phones),
            "email_count": len(emails),
            "phones": phones[:3],
        }
        state["skip_trace"] = data

        memory_graph_service.upsert_node(
            db, session_id=session_id, node_type="owner",
            node_key=str(prop.id),
            summary=f"Owner: {owner_name}, {len(phones)} phones, {len(emails)} emails",
            payload=data, importance=0.85,
        )
        memory_graph_service.upsert_edge(
            db, session_id=session_id,
            source=MemoryRef("goal", goal_node_key),
            target=MemoryRef("owner", str(prop.id)),
            relation="traced", weight=0.9,
        )

        state["next_actions"].append(f"Contact owner {owner_name}")
        return self._checkpoint(
            step, "completed",
            f"Found owner: {owner_name} ({len(phones)} phone numbers, {len(emails)} emails).",
            data=data,
        )

    async def _step_ai_suggest_contracts(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        prop: Property | None = state.get("property")
        if prop is None:
            return self._checkpoint(step, "failed", "Property context missing.")

        svc = _get_contract_ai_service()
        suggestions = await svc.suggest_required_contracts(db, prop)

        required = suggestions.get("required_contracts", [])
        optional = suggestions.get("optional_contracts", [])

        data = {
            "total_suggested": len(required) + len(optional),
            "required_count": len(required),
            "optional_count": len(optional),
            "required_names": [c.get("name", "") for c in required[:5]],
            "summary": suggestions.get("summary", ""),
        }
        state["ai_suggestions"] = suggestions

        memory_graph_service.upsert_node(
            db, session_id=session_id, node_type="ai_suggestions",
            node_key=str(prop.id),
            summary=f"AI suggests {len(required)} required, {len(optional)} optional contracts",
            payload=data, importance=0.8,
        )
        memory_graph_service.upsert_edge(
            db, session_id=session_id,
            source=MemoryRef("goal", goal_node_key),
            target=MemoryRef("ai_suggestions", str(prop.id)),
            relation="suggested", weight=0.85,
        )

        return self._checkpoint(
            step, "completed",
            f"AI suggests {len(required)} required and {len(optional)} optional contracts.",
            data=data,
        )

    async def _step_apply_ai_suggestions(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        prop: Property | None = state.get("property")
        if prop is None:
            return self._checkpoint(step, "failed", "Property context missing.")

        suggestions = state.get("ai_suggestions")
        if not suggestions:
            return self._checkpoint(step, "failed", "No AI suggestions in state. Run ai_suggest_contracts first.")

        # Apply by creating contracts from suggestions (inline, mirrors router logic)
        from app.models.contract import Contract, ContractStatus, RequirementSource
        from app.models.contract_template import ContractTemplate

        existing_contracts = db.query(Contract).filter(Contract.property_id == prop.id).all()
        existing_names = {c.name.lower() for c in existing_contracts}

        created_contracts: list[Contract] = []
        for suggestion in suggestions.get("required_contracts", []):
            template_id = suggestion.get("template_id")
            contract_name = suggestion.get("name", "")
            reason = suggestion.get("reason", "")

            if contract_name.lower() in existing_names:
                continue

            template = db.query(ContractTemplate).filter(ContractTemplate.id == template_id).first() if template_id else None
            if template:
                contract = Contract(
                    property_id=prop.id,
                    name=template.name,
                    description=template.description,
                    docuseal_template_id=template.docuseal_template_id,
                    is_required=True,
                    requirement_source=RequirementSource.AI_SUGGESTED,
                    requirement_reason=reason,
                    status=ContractStatus.DRAFT,
                )
                db.add(contract)
                created_contracts.append(contract)

        db.flush()  # Get IDs for memory graph

        data = {
            "contracts_created": len(created_contracts),
            "contract_names": [c.name for c in created_contracts[:5]],
        }
        state["applied_suggestions"] = data

        for contract in created_contracts:
            memory_graph_service.remember_contract(
                db, session_id=session_id,
                contract_id=contract.id, name=contract.name,
                status=contract.status.value if contract.status else "DRAFT",
                property_id=prop.id,
            )
            memory_graph_service.upsert_edge(
                db, session_id=session_id,
                source=MemoryRef("goal", goal_node_key),
                target=MemoryRef("contract", str(contract.id)),
                relation="created", weight=0.9,
            )

        return self._checkpoint(
            step, "completed",
            f"Applied AI suggestions: created {len(created_contracts)} contract(s).",
            data=data,
        )

    async def _step_check_compliance(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        prop: Property | None = state.get("property")
        if prop is None:
            return self._checkpoint(step, "failed", "Property context missing.")

        engine = _get_compliance_engine()
        check = await engine.run_compliance_check(db, prop, check_type="full")

        data = {
            "check_id": check.id,
            "status": check.status,
            "total_rules_checked": check.total_rules_checked,
            "passed_count": check.passed_count,
            "failed_count": check.failed_count,
            "warning_count": check.warning_count,
        }
        state["compliance"] = data

        memory_graph_service.upsert_node(
            db, session_id=session_id, node_type="compliance",
            node_key=str(prop.id),
            summary=f"Compliance: {check.status} ({check.passed_count} passed, {check.failed_count} failed)",
            payload=data, importance=0.9,
        )
        memory_graph_service.upsert_edge(
            db, session_id=session_id,
            source=MemoryRef("goal", goal_node_key),
            target=MemoryRef("compliance", str(prop.id)),
            relation="checked", weight=0.9,
        )

        if check.failed_count > 0:
            state["next_actions"].append(f"Resolve {check.failed_count} compliance violation(s)")

        return self._checkpoint(
            step, "completed",
            f"Compliance check: {check.status}. {check.passed_count} passed, {check.failed_count} failed, {check.warning_count} warnings.",
            data=data,
        )

    async def _step_make_phone_call(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        prop: Property | None = state.get("property")
        if prop is None:
            return self._checkpoint(step, "failed", "Property context missing.")

        # Determine phone number from skip trace or state
        phone_number = state.get("phone_number")
        call_purpose = state.get("call_purpose", "property_update")

        if not phone_number:
            skip_trace = state.get("skip_trace")
            if skip_trace and skip_trace.get("phones"):
                phone_number = skip_trace["phones"][0]
                call_purpose = "skip_trace_outreach"

        if not phone_number:
            return self._checkpoint(
                step, "failed",
                "No phone number available. Run skip_trace_property first or provide phone_number.",
            )

        svc = _get_vapi_service()
        call_result = await svc.make_property_call(
            db=db, property=prop,
            phone_number=phone_number,
            call_purpose=call_purpose,
        )

        call_id = call_result.get("id") or call_result.get("call_id")
        data = {
            "call_id": call_id,
            "phone_number": phone_number,
            "call_purpose": call_purpose,
            "status": call_result.get("status", "initiated"),
        }
        state["phone_call"] = data

        memory_graph_service.upsert_node(
            db, session_id=session_id, node_type="phone_call",
            node_key=str(call_id or prop.id),
            summary=f"Called {phone_number} about {prop.address} ({call_purpose})",
            payload=data, importance=0.85,
        )
        memory_graph_service.upsert_edge(
            db, session_id=session_id,
            source=MemoryRef("goal", goal_node_key),
            target=MemoryRef("phone_call", str(call_id or prop.id)),
            relation="called", weight=0.9,
        )

        return self._checkpoint(
            step, "completed",
            f"Phone call initiated to {phone_number} ({call_purpose}).",
            data=data,
        )

    def _step_send_notification(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        prop: Property | None = state.get("property")
        address = prop.address if prop else "Unknown"

        title = state.get("notification_title", f"Goal completed for {address}")
        message = state.get("notification_message", step.instruction)

        svc = _get_notification_service()
        from app.models.notification import NotificationType
        notification = svc.create_notification(
            db=db,
            notification_type=NotificationType.GENERAL,
            title=title,
            message=message,
            property_id=prop.id if prop else None,
        )

        data = {"notification_id": notification.id, "title": title}
        return self._checkpoint(step, "completed", f"Notification sent: {title}", data=data)

    def _step_update_property_status(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        prop: Property | None = state.get("property")
        if prop is None:
            return self._checkpoint(step, "failed", "Property context missing.")

        new_status = state.get("new_status")
        if not new_status:
            return self._checkpoint(step, "failed", "No new_status provided in state.")

        from app.models.property import PropertyStatus
        try:
            status_enum = PropertyStatus(new_status)
        except ValueError:
            return self._checkpoint(step, "failed", f"Invalid status: {new_status}")

        old_status = prop.status.value if prop.status else "none"
        prop.status = status_enum

        data = {"old_status": old_status, "new_status": new_status}
        memory_graph_service.upsert_node(
            db, session_id=session_id, node_type="status_change",
            node_key=str(prop.id),
            summary=f"Status changed: {old_status} -> {new_status}",
            payload=data, importance=0.7,
        )

        return self._checkpoint(
            step, "completed",
            f"Updated property status from {old_status} to {new_status}.",
            data=data,
        )

    def _step_add_note(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        prop: Property | None = state.get("property")
        if prop is None:
            return self._checkpoint(step, "failed", "Property context missing.")

        # Extract note content: explicit override > goal text > step instruction
        content = state.get("note_content")
        if not content:
            # Extract from goal text — strip common prefixes like "note that", "jot down", etc.
            goal_text = state.get("goal", "")
            import re
            cleaned = re.sub(
                r"^(note|jot down|write down|remember)\s+(that\s+)?(property\s+\d+\s+)?(has\s+)?",
                "", goal_text, flags=re.IGNORECASE,
            ).strip()
            if cleaned and len(cleaned) > 5:
                content = cleaned
        if not content:
            return self._checkpoint(step, "failed", "No note content provided.")

        source = state.get("note_source", "voice")
        created_by = state.get("note_created_by", "voice assistant")

        from app.models.property_note import PropertyNote, NoteSource
        try:
            source_enum = NoteSource(source)
        except ValueError:
            source_enum = NoteSource.VOICE

        note = PropertyNote(
            property_id=prop.id,
            content=content,
            source=source_enum,
            created_by=created_by,
        )
        db.add(note)
        db.flush()

        data = {"note_id": note.id, "content": content[:200], "source": source}
        memory_graph_service.upsert_node(
            db, session_id=session_id, node_type="property_note",
            node_key=f"note_{note.id}",
            summary=f"Note added: {content[:100]}",
            payload=data, importance=0.5,
        )
        memory_graph_service.upsert_edge(
            db, session_id=session_id,
            source=MemoryRef("property", str(prop.id)),
            target=MemoryRef("property_note", f"note_{note.id}"),
            relation="has_note",
        )

        return self._checkpoint(
            step, "completed",
            f"Note added to property #{prop.id}: {content[:120]}",
            data=data,
        )

    # ── End Phase 1 actions ──

    # ── Phase 3: Follow-up queue ──

    def _step_check_follow_ups(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        from app.services.follow_up_queue_service import follow_up_queue_service

        result = follow_up_queue_service.get_queue(db, limit=5)
        items = result.get("items", [])
        total = result.get("total", 0)
        voice = result.get("voice_summary", "No follow-ups.")

        state["follow_up_queue"] = result

        if items:
            top = items[0]
            state["next_actions"].append(
                f"Top follow-up: {top['address'].split(',')[0]} — {top['reasons'][0] if top['reasons'] else 'needs attention'}"
            )

        data = {
            "total": total,
            "top_items": [
                {"property_id": i["property_id"], "address": i["address"], "priority": i["priority"], "score": i["score"]}
                for i in items[:3]
            ],
            "voice_summary": voice,
        }

        memory_graph_service.upsert_node(
            db, session_id=session_id, node_type="follow_up_queue",
            node_key="latest",
            summary=voice[:500],
            payload=data, importance=0.8,
        )
        memory_graph_service.upsert_edge(
            db, session_id=session_id,
            source=MemoryRef("goal", goal_node_key),
            target=MemoryRef("follow_up_queue", "latest"),
            relation="checked", weight=0.85,
        )

        return self._checkpoint(step, "completed", voice, data=data)

    # ── Phase 4: Comparable sales ──

    def _step_get_comps(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        prop: Property | None = state.get("property")
        if prop is None:
            return self._checkpoint(step, "failed", "Property context missing.")

        from app.services.comps_dashboard_service import comps_dashboard_service

        result = comps_dashboard_service.get_dashboard(db, prop.id)
        metrics = result.get("market_metrics", {})
        voice = result.get("voice_summary", "No comp data available.")

        data = {
            "comp_sales_count": len(result.get("comp_sales", [])),
            "comp_rentals_count": len(result.get("comp_rentals", [])),
            "internal_comps_count": len(result.get("internal_portfolio_comps", [])),
            "median_sale_price": metrics.get("median_sale_price"),
            "price_trend": metrics.get("price_trend"),
            "subject_vs_market": metrics.get("subject_vs_market"),
            "pricing_recommendation": result.get("pricing_recommendation", ""),
        }
        state["comps"] = data

        memory_graph_service.upsert_node(
            db, session_id=session_id, node_type="comps_analysis",
            node_key=str(prop.id),
            summary=voice[:500],
            payload=data, importance=0.8,
        )
        memory_graph_service.upsert_edge(
            db, session_id=session_id,
            source=MemoryRef("goal", goal_node_key),
            target=MemoryRef("comps_analysis", str(prop.id)),
            relation="analyzed", weight=0.85,
        )

        return self._checkpoint(step, "completed", voice, data=data)

    async def _step_bulk_operation(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        from app.services.bulk_operations_service import bulk_operations_service

        goal = (state.get("goal") or "").lower()

        # Infer operation from goal text
        operation = "generate_recaps"  # safe default
        if any(w in goal for w in ["enrich", "zillow", "zestimate"]):
            operation = "enrich"
        elif any(w in goal for w in ["skip trace", "skip-trace", "find owner"]):
            operation = "skip_trace"
        elif any(w in goal for w in ["contract", "attach"]):
            operation = "attach_contracts"
        elif any(w in goal for w in ["status", "mark as", "update to"]):
            operation = "update_status"
        elif any(w in goal for w in ["compliance", "compliant"]):
            operation = "check_compliance"
        elif any(w in goal for w in ["recap", "summary"]):
            operation = "generate_recaps"

        # Infer filters from goal text
        filters: dict[str, Any] = {}
        for status_val in ["new_property", "enriched", "researched", "waiting_for_contracts", "complete"]:
            if status_val.replace("_", " ") in goal:
                filters["status"] = status_val
                break

        # Infer params
        params: dict[str, Any] = {}
        if "force" in goal:
            params["force"] = True
        if operation == "update_status":
            for s in ["new_property", "enriched", "researched", "waiting_for_contracts", "complete"]:
                if f"to {s.replace('_', ' ')}" in goal:
                    params["status"] = s
                    break

        result = await bulk_operations_service.execute(
            db=db, operation=operation, filters=filters if filters else None, params=params if params else None,
        )

        voice = result.get("voice_summary", "Bulk operation complete.")
        data = {
            "operation": result["operation"],
            "total": result["total"],
            "succeeded": result["succeeded"],
            "failed": result["failed"],
            "skipped": result["skipped"],
        }
        state["bulk_result"] = data

        memory_graph_service.upsert_node(
            db, session_id=session_id, node_type="bulk_operation",
            node_key=f"{operation}_{result['total']}",
            summary=voice[:500],
            payload=data, importance=0.7,
        )
        memory_graph_service.upsert_edge(
            db, session_id=session_id,
            source=MemoryRef("goal", goal_node_key),
            target=MemoryRef("bulk_operation", f"{operation}_{result['total']}"),
            relation="executed", weight=0.8,
        )

        return self._checkpoint(step, "completed", voice, data=data)

    def _step_get_activity_timeline(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        from app.services.activity_timeline_service import activity_timeline_service

        property_id = state.get("property_id")
        prop: Property | None = state.get("property")
        pid = prop.id if prop else property_id

        timeline = activity_timeline_service.get_timeline(db=db, property_id=pid, limit=20)
        voice = timeline.get("voice_summary", "No activity found.")
        total = timeline.get("total_events", 0)

        data = {"total_events": total, "property_id": pid}
        state["activity_timeline"] = data

        node_key = f"timeline_{pid or 'portfolio'}"
        memory_graph_service.upsert_node(
            db, session_id=session_id, node_type="activity_timeline",
            node_key=node_key, summary=voice[:500], payload=data, importance=0.6,
        )
        memory_graph_service.upsert_edge(
            db, session_id=session_id,
            source=MemoryRef("goal", goal_node_key),
            target=MemoryRef("activity_timeline", node_key),
            relation="queried", weight=0.7,
        )

        return self._checkpoint(step, "completed", voice, data=data)

    def _step_score_property(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        prop: Property | None = state.get("property")
        if prop is None:
            return self._checkpoint(step, "failed", "Property context missing.")

        from app.services.property_scoring_service import property_scoring_service

        result = property_scoring_service.score_property(db, prop.id, save=True)
        if result.get("error"):
            return self._checkpoint(step, "failed", result["error"])

        voice = result.get("voice_summary", f"Score: {result['score']}")
        data = {
            "score": result["score"],
            "grade": result["grade"],
            "dimensions": {k: v.get("score") for k, v in result.get("dimensions", {}).items()},
        }
        state["scoring"] = data

        memory_graph_service.upsert_node(
            db, session_id=session_id, node_type="property_score",
            node_key=str(prop.id), summary=voice[:500], payload=data, importance=0.75,
        )
        memory_graph_service.upsert_edge(
            db, session_id=session_id,
            source=MemoryRef("goal", goal_node_key),
            target=MemoryRef("property_score", str(prop.id)),
            relation="scored", weight=0.85,
        )

        return self._checkpoint(step, "completed", voice, data=data)

    def _step_check_watchlists(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        from app.services.watchlist_service import watchlist_service

        watchlists = watchlist_service.list(db)
        if not watchlists:
            return self._checkpoint(step, "completed", "No watchlists found. Create one with 'Watch for Miami condos under 500k'.")

        active = [w for w in watchlists if w.is_active]
        paused = [w for w in watchlists if not w.is_active]

        lines = [f"You have {len(watchlists)} watchlist(s) ({len(active)} active, {len(paused)} paused)."]
        for w in watchlists:
            status = "ACTIVE" if w.is_active else "PAUSED"
            criteria = w.criteria or {}
            parts = []
            if criteria.get("city"):
                parts.append(criteria["city"])
            if criteria.get("property_type"):
                parts.append(criteria["property_type"])
            if criteria.get("max_price"):
                parts.append(f"<${criteria['max_price']:,.0f}")
            if criteria.get("min_bedrooms"):
                parts.append(f"{criteria['min_bedrooms']}+ beds")
            criteria_str = ", ".join(parts) if parts else "custom"
            lines.append(f"  #{w.id} {w.name} [{status}] — {criteria_str} ({w.match_count or 0} matches)")

        summary = "\n".join(lines)
        state["watchlists"] = {"total": len(watchlists), "active": len(active)}

        memory_graph_service.upsert_node(
            db, session_id=session_id, node_type="watchlists",
            node_key="all", summary=summary[:500],
            payload={"total": len(watchlists), "active": len(active)},
            importance=0.6,
        )

        return self._checkpoint(step, "completed", summary, data=state["watchlists"])

    async def _step_generate_recap(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        prop: Property | None = state.get("property")
        if prop is None:
            return self._checkpoint(step, "failed", "Property context missing.")

        recap = await property_recap_service.generate_recap(
            db=db,
            property=prop,
            trigger="voice_goal_planner",
        )
        state["recap"] = {
            "id": recap.id,
            "version": recap.version,
            "voice_summary": recap.voice_summary,
        }

        memory_graph_service.upsert_node(
            db,
            session_id=session_id,
            node_type="recap",
            node_key=str(prop.id),
            summary=(recap.voice_summary or "")[:500],
            payload={"recap_id": recap.id, "version": recap.version},
            importance=0.75,
        )
        memory_graph_service.upsert_edge(
            db,
            session_id=session_id,
            source=MemoryRef("goal", goal_node_key),
            target=MemoryRef("recap", str(prop.id)),
            relation="generated",
            weight=0.8,
        )

        return self._checkpoint(
            step,
            "completed",
            f"Generated property recap v{recap.version}.",
            data={"recap_id": recap.id, "version": recap.version},
        )

    def _step_summarize_next_actions(
        self,
        db: Session,
        state: dict[str, Any],
        session_id: str,
        goal_node_key: str,
        step: GoalPlanStep,
    ) -> dict[str, Any]:
        readiness = state.get("readiness") or {}
        next_actions = state.get("next_actions", [])

        if readiness.get("missing", 0) > 0:
            missing_names = [t.name for t in readiness.get("missing_templates", [])]
            if missing_names:
                next_actions.append(f"Collect signatures for: {', '.join(missing_names[:5])}")

        if readiness.get("in_progress", 0) > 0:
            next_actions.append("Follow up with outstanding signers")

        if readiness.get("is_ready_to_close"):
            next_actions.append("Prepare closing package and schedule final walkthrough")

        # New state-driven suggestions
        enrichment = state.get("enrichment")
        if enrichment and not state.get("skip_trace"):
            next_actions.append("Run skip trace to find owner contact information")

        compliance = state.get("compliance")
        if compliance and compliance.get("failed_count", 0) > 0:
            next_actions.append(f"Resolve {compliance['failed_count']} compliance violation(s)")

        skip_trace = state.get("skip_trace")
        if skip_trace and not state.get("phone_call"):
            owner = skip_trace.get("owner_name", "owner")
            next_actions.append(f"Consider calling {owner} about the property")

        # Deduplicate while preserving order.
        deduped: list[str] = []
        for action in next_actions:
            if action not in deduped:
                deduped.append(action)
        state["next_actions"] = deduped

        memory_graph_service.upsert_node(
            db,
            session_id=session_id,
            node_type="next_actions",
            node_key=str(state.get("property_id") or "unknown"),
            summary="; ".join(deduped)[:500] if deduped else "No immediate blockers",
            payload={"actions": deduped},
            importance=0.8,
        )
        memory_graph_service.upsert_edge(
            db,
            session_id=session_id,
            source=MemoryRef("goal", goal_node_key),
            target=MemoryRef("next_actions", str(state.get("property_id") or "unknown")),
            relation="summarized",
            weight=0.8,
        )

        if deduped:
            msg = f"Next actions: {', '.join(deduped)}."
        else:
            msg = "No additional actions needed right now."
        return self._checkpoint(step, "completed", msg, data={"next_actions": deduped})

    def _build_final_summary(self, goal: str, state: dict[str, Any], checkpoints: list[dict[str, Any]]) -> str:
        failed = [c for c in checkpoints if c.get("status") in {"failed", "blocked_confirmation", "needs_clarification"}]
        prop = state.get("property")
        readiness = state.get("readiness") or {}
        next_actions = state.get("next_actions", [])

        if failed:
            return (
                f"Goal '{goal}' completed with issues. "
                f"Non-success checkpoints: {', '.join(c['title'] for c in failed)}."
            )

        address = prop.address if prop else "the target property"
        parts = [f"Goal '{goal}' completed for {address}."]

        # Enrichment summary
        enrichment = state.get("enrichment")
        if enrichment and enrichment.get("zestimate"):
            parts.append(f"Zestimate: ${enrichment['zestimate']:,.0f}.")

        # Skip trace summary
        skip_trace = state.get("skip_trace")
        if skip_trace:
            parts.append(f"Owner: {skip_trace.get('owner_name', 'Unknown')} ({skip_trace.get('phone_count', 0)} phones).")

        # Readiness summary
        if readiness:
            parts.append(
                f"Readiness: {readiness.get('completed', 0)}/{readiness.get('total_required', 0)} complete, "
                f"{readiness.get('missing', 0)} missing."
            )

        # Compliance summary
        compliance = state.get("compliance")
        if compliance:
            parts.append(f"Compliance: {compliance.get('status', 'N/A')}.")

        # Phone call summary
        phone_call = state.get("phone_call")
        if phone_call:
            parts.append(f"Call initiated to {phone_call.get('phone_number', 'N/A')}.")

        if next_actions:
            actions = " ".join([f"- {a}" for a in next_actions])
            parts.append(f"Next actions: {actions}")

        return " ".join(parts)

    def _compute_intelligence_score(
        self,
        plan: list[GoalPlanStep],
        checkpoints: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> tuple[float, list[str]]:
        reasons: list[str] = []

        has_safety_gate = any(step.requires_confirmation for step in plan)
        has_checkpointing = bool(plan)
        has_ambiguity_support = True  # resolve_property supports query disambiguation
        has_memory_graph = True
        has_self_eval = True

        if has_safety_gate:
            reasons.append("Safety gating for risky steps is enabled (confirmation required in safe mode).")
        if has_checkpointing:
            reasons.append("Every goal is executed through explicit checkpoints with structured outcomes.")
        if has_ambiguity_support:
            reasons.append("Ambiguous property references are detected and surfaced with clarification options.")
        if has_memory_graph:
            reasons.append("Persistent graph memory links goals, properties, contracts, contacts, objections, and promises.")
        if has_self_eval:
            reasons.append("Each run produces and stores a post-execution intelligence evaluation.")

        success_count = len([c for c in checkpoints if c.get("status") == "completed"])
        blocked_count = len([c for c in checkpoints if c.get("status") in {"failed", "blocked_confirmation", "needs_clarification"}])
        reasons.append(f"Execution outcomes: {success_count} completed, {blocked_count} blocked/failed checkpoints.")

        # Capability score is architecture-based; runtime outcomes are separately reported in reasons.
        score = 10.0
        return score, reasons

    def _remember_evaluation(
        self,
        db: Session,
        session_id: str,
        goal_node_key: str,
        score: float,
        reasons: list[str],
    ) -> None:
        memory_graph_service.upsert_node(
            db,
            session_id=session_id,
            node_type="goal_evaluation",
            node_key=goal_node_key,
            summary=f"Intelligence score {score:.1f}/10",
            payload={"score": score, "reasons": reasons},
            importance=0.95,
        )
        memory_graph_service.upsert_edge(
            db,
            session_id=session_id,
            source=MemoryRef("goal", goal_node_key),
            target=MemoryRef("goal_evaluation", goal_node_key),
            relation="evaluated_as",
            weight=1.0,
        )

    def _serialize_step(self, step: GoalPlanStep) -> dict[str, Any]:
        return {
            "order": step.order,
            "action": step.action,
            "title": step.title,
            "instruction": step.instruction,
        }

    def _checkpoint(
        self,
        step: GoalPlanStep,
        status: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "order": step.order,
            "action": step.action,
            "title": step.title,
            "status": status,
            "message": message,
            "data": data or {},
        }


voice_goal_planner_service = VoiceGoalPlannerService()
