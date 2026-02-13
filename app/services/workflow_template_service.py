"""Pre-defined multi-step workflow templates for voice-first operations.

Each template maps a single voice command to a multi-step goal that is
executed by the VoiceGoalPlannerService.  Templates encode best-practice
step sequences while the goal planner handles checkpoints, memory, and
safety gates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session


@dataclass
class WorkflowTemplate:
    name: str
    description: str
    trigger_phrases: list[str]
    goal_text: str  # Sent to VoiceGoalPlannerService as the goal string
    required_inputs: list[str] = field(default_factory=list)
    default_execution_mode: str = "safe"


# ── Registry ──

_TEMPLATES: dict[str, WorkflowTemplate] = {}


def _register(t: WorkflowTemplate) -> None:
    _TEMPLATES[t.name] = t


_register(WorkflowTemplate(
    name="new_lead",
    description="Full new-lead pipeline: enrich, skip trace, compliance, contracts, recap",
    trigger_phrases=["new lead", "onboard property", "full pipeline", "new property pipeline"],
    goal_text="New lead pipeline: enrich this property with Zillow data, skip trace to find the owner, "
              "run a compliance check, attach required contracts, and generate a comprehensive recap.",
    required_inputs=["property_id"],
    default_execution_mode="safe",
))

_register(WorkflowTemplate(
    name="ready_to_close",
    description="Verify property is ready for closing: contracts, compliance, recap",
    trigger_phrases=["ready to close", "closing checklist", "prepare for closing", "close deal"],
    goal_text="Close deal: check contract readiness, attach any missing required contracts, "
              "run a compliance check, and generate an updated recap.",
    required_inputs=["property_id"],
    default_execution_mode="safe",
))

_register(WorkflowTemplate(
    name="market_analysis",
    description="Market analysis: enrich with Zillow data and generate recap with insights",
    trigger_phrases=["market analysis", "property analysis", "market value", "run analysis"],
    goal_text="Market analysis: enrich this property with Zillow data and generate a comprehensive "
              "recap with market insights, Zestimate comparison, and recommendations.",
    required_inputs=["property_id"],
    default_execution_mode="autonomous",
))

_register(WorkflowTemplate(
    name="cold_call_owner",
    description="Skip trace the owner and make a cold call about selling",
    trigger_phrases=["cold call owner", "call the owner", "reach out to owner", "find and call owner"],
    goal_text="Cold call workflow: skip trace the property to find the owner, "
              "then make a phone call to ask if they are interested in selling.",
    required_inputs=["property_id"],
    default_execution_mode="safe",
))

_register(WorkflowTemplate(
    name="contract_cleanup",
    description="AI-suggest contracts, apply suggestions, and check readiness",
    trigger_phrases=["contract cleanup", "fix contracts", "contract review", "audit contracts"],
    goal_text="Contract audit: use AI to suggest required contracts for this property, "
              "apply the suggestions to create missing contracts, then check overall readiness.",
    required_inputs=["property_id"],
    default_execution_mode="safe",
))


class WorkflowTemplateService:
    """Execute pre-defined workflow templates via the Voice Goal Planner."""

    @staticmethod
    def list_templates() -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "trigger_phrases": t.trigger_phrases,
                "required_inputs": t.required_inputs,
            }
            for t in _TEMPLATES.values()
        ]

    @staticmethod
    def get_template(name: str) -> WorkflowTemplate | None:
        return _TEMPLATES.get(name)

    @staticmethod
    def match_from_voice(voice_input: str) -> WorkflowTemplate | None:
        """Match a voice utterance to a workflow template."""
        lower = voice_input.lower()
        for template in _TEMPLATES.values():
            for phrase in template.trigger_phrases:
                if phrase in lower:
                    return template
        return None

    async def execute(
        self,
        db: Session,
        template_name: str,
        property_id: int | None = None,
        property_query: str | None = None,
        session_id: str = "default",
        execution_mode: str | None = None,
        confirm_high_risk: bool = False,
    ) -> dict[str, Any]:
        template = _TEMPLATES.get(template_name)
        if not template:
            available = ", ".join(sorted(_TEMPLATES.keys()))
            return {
                "status": "error",
                "message": f"Unknown workflow '{template_name}'. Available: {available}",
            }

        if "property_id" in template.required_inputs and not property_id and not property_query:
            return {
                "status": "error",
                "message": "This workflow requires a property_id or property_query.",
            }

        from app.services.voice_goal_planner import voice_goal_planner_service

        mode = execution_mode or template.default_execution_mode
        result = await voice_goal_planner_service.execute_goal(
            db=db,
            goal=template.goal_text,
            session_id=session_id,
            property_id=property_id,
            property_query=property_query,
            execution_mode=mode,
            confirm_high_risk=confirm_high_risk,
        )

        return {
            "workflow": template.name,
            "description": template.description,
            "status": "blocked" if result.get("needs_confirmation") else "completed",
            "result": result,
        }


workflow_template_service = WorkflowTemplateService()
