"""Goal-driven planner for voice commands with checkpointed execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.property import Property
from app.services.contract_auto_attach import contract_auto_attach_service
from app.services.memory_graph import MemoryRef, memory_graph_service
from app.services.property_recap_service import property_recap_service


@dataclass
class GoalPlanStep:
    order: int
    action: str
    title: str
    instruction: str


class VoiceGoalPlannerService:
    """Build and execute multi-step goal plans with checkpoints."""

    def build_plan(self, goal: str) -> list[GoalPlanStep]:
        normalized = goal.lower().strip()

        if any(token in normalized for token in ["deal", "close", "end-to-end", "transaction"]):
            return [
                GoalPlanStep(1, "resolve_property", "Resolve Property", "Find the target property from explicit input or memory."),
                GoalPlanStep(2, "inspect_property", "Inspect Property", "Load key property context required for downstream actions."),
                GoalPlanStep(3, "check_contract_readiness", "Check Contract Readiness", "Evaluate required contracts and completion status."),
                GoalPlanStep(4, "attach_required_contracts", "Attach Missing Contracts", "Auto-attach required contracts that are not yet present."),
                GoalPlanStep(5, "generate_property_recap", "Generate Recap", "Create/update an AI recap for voice calls and summaries."),
                GoalPlanStep(6, "summarize_next_actions", "Summarize Next Actions", "Produce concise execution checkpoint summary and next actions."),
            ]

        return [
            GoalPlanStep(1, "resolve_property", "Resolve Property", "Find the property associated with the user request."),
            GoalPlanStep(2, "inspect_property", "Inspect Property", "Load core details for decision making."),
            GoalPlanStep(3, "check_contract_readiness", "Check Contract Readiness", "Review completion state and blockers."),
            GoalPlanStep(4, "summarize_next_actions", "Summarize Next Actions", "Provide recommended next actions."),
        ]

    async def execute_goal(
        self,
        db: Session,
        goal: str,
        session_id: str = "default",
        property_id: int | None = None,
    ) -> dict[str, Any]:
        plan = self.build_plan(goal)
        goal_node = memory_graph_service.remember_goal(
            db,
            session_id=session_id,
            goal=goal,
            metadata={"step_count": len(plan)},
        )

        state: dict[str, Any] = {
            "property_id": property_id,
            "property": None,
            "readiness": None,
            "attached_contracts": [],
            "recap": None,
            "next_actions": [],
        }
        checkpoints: list[dict[str, Any]] = []

        for step in plan:
            result = await self._execute_step(
                db=db,
                step=step,
                state=state,
                session_id=session_id,
                goal_node_key=goal_node.node_key,
            )
            checkpoints.append(result)

            if result["status"] == "failed" and step.action == "resolve_property":
                # Hard stop: no meaningful way to continue without property context.
                break

        db.commit()

        final_summary = self._build_final_summary(goal=goal, state=state, checkpoints=checkpoints)
        memory_summary = memory_graph_service.get_session_summary(db, session_id=session_id)

        return {
            "session_id": session_id,
            "goal": goal,
            "plan": [
                {
                    "order": s.order,
                    "action": s.action,
                    "title": s.title,
                    "instruction": s.instruction,
                }
                for s in plan
            ],
            "checkpoints": checkpoints,
            "final_summary": final_summary,
            "memory_summary": memory_summary,
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
        if property_id is None:
            property_id = memory_graph_service.get_session_state(db, session_id, "last_property_id")
            if property_id is not None:
                state["property_id"] = int(property_id)

        if property_id is None:
            return self._checkpoint(
                step,
                "failed",
                "No property provided and no last_property_id found in memory. Please specify a property.",
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
        failed = [c for c in checkpoints if c.get("status") == "failed"]
        prop = state.get("property")
        readiness = state.get("readiness") or {}
        next_actions = state.get("next_actions", [])

        if failed:
            return (
                f"Goal '{goal}' completed with issues. "
                f"Failed checkpoints: {', '.join(c['title'] for c in failed)}."
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
