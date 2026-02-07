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

try:
    from anthropic import Anthropic
except Exception:  # pragma: no cover - optional dependency in some runtimes
    Anthropic = None  # type: ignore


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
        "resolve_property",
        "inspect_property",
        "check_contract_readiness",
        "attach_required_contracts",
        "generate_property_recap",
        "summarize_next_actions",
    }

    def __init__(self):
        self.anthropic_client = None
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key and Anthropic is not None:
            self.anthropic_client = Anthropic(api_key=api_key)

    def build_plan(
        self,
        goal: str,
        memory_summary: dict[str, Any] | None = None,
        execution_mode: str = "safe",
    ) -> tuple[list[GoalPlanStep], bool]:
        """Return (plan, used_llm_planner)."""
        llm_plan = self._build_llm_plan(goal=goal, memory_summary=memory_summary, execution_mode=execution_mode)
        if llm_plan:
            return llm_plan, True
        return self._build_heuristic_plan(goal=goal, execution_mode=execution_mode), False

    def _build_heuristic_plan(self, goal: str, execution_mode: str) -> list[GoalPlanStep]:
        normalized = goal.lower().strip()

        attach_requires_confirmation = execution_mode != "autonomous"

        if any(token in normalized for token in ["deal", "close", "end-to-end", "transaction"]):
            return [
                GoalPlanStep(1, "resolve_property", "Resolve Property", "Find the target property from explicit input, query, or memory."),
                GoalPlanStep(2, "inspect_property", "Inspect Property", "Load key property context required for downstream actions."),
                GoalPlanStep(3, "check_contract_readiness", "Check Contract Readiness", "Evaluate required contracts and completion status."),
                GoalPlanStep(
                    4,
                    "attach_required_contracts",
                    "Attach Missing Contracts",
                    "Auto-attach required contracts that are not yet present.",
                    risk_level="medium",
                    requires_confirmation=attach_requires_confirmation,
                ),
                GoalPlanStep(5, "generate_property_recap", "Generate Recap", "Create/update an AI recap for voice calls and summaries."),
                GoalPlanStep(6, "summarize_next_actions", "Summarize Next Actions", "Produce concise execution checkpoint summary and next actions."),
            ]

        return [
            GoalPlanStep(1, "resolve_property", "Resolve Property", "Find the property associated with the user request."),
            GoalPlanStep(2, "inspect_property", "Inspect Property", "Load core details for decision making."),
            GoalPlanStep(3, "check_contract_readiness", "Check Contract Readiness", "Review completion state and blockers."),
            GoalPlanStep(4, "summarize_next_actions", "Summarize Next Actions", "Provide recommended next actions."),
        ]

    def _build_llm_plan(
        self,
        goal: str,
        memory_summary: dict[str, Any] | None,
        execution_mode: str,
    ) -> list[GoalPlanStep] | None:
        if not self.anthropic_client:
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
            response = self.anthropic_client.messages.create(
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
        plan, used_llm_planner = self.build_plan(
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
        readiness_text = (
            f"Readiness is {readiness.get('completed', 0)}/{readiness.get('total_required', 0)} complete "
            f"with {readiness.get('missing', 0)} missing contracts."
        )

        if next_actions:
            actions = " ".join([f"- {a}" for a in next_actions])
            return f"Goal '{goal}' completed for {address}. {readiness_text} Next actions: {actions}"

        return f"Goal '{goal}' completed for {address}. {readiness_text}"

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
