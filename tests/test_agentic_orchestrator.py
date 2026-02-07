import asyncio
from datetime import date
from datetime import timedelta
from types import MethodType

from app.services.agentic.orchestrator import AgentSpec, MultiAgentOrchestrator
from app.services.agentic.pipeline import AgenticResearchService
from app.services.agentic.utils import utcnow
from app.schemas.agentic_research import ResearchInput


def test_multi_agent_orchestrator_respects_dependencies():
    specs = [
        AgentSpec(name="a", dependencies=set()),
        AgentSpec(name="b", dependencies={"a"}),
        AgentSpec(name="c", dependencies={"a"}),
        AgentSpec(name="d", dependencies={"b", "c"}),
    ]
    orchestrator = MultiAgentOrchestrator(max_parallel_agents=2)
    run_order: list[str] = []

    async def run_agent(name: str):
        await asyncio.sleep(0.01)
        run_order.append(name)
        return {"name": name}

    executions = asyncio.run(orchestrator.run(specs=specs, run_agent=run_agent, max_steps=10))
    names = [name for name, _ in executions]

    assert names == ["a", "b", "c", "d"]
    assert run_order == ["a", "b", "c", "d"]


def test_multi_agent_orchestrator_stops_at_max_steps():
    specs = [
        AgentSpec(name="a", dependencies=set()),
        AgentSpec(name="b", dependencies={"a"}),
        AgentSpec(name="c", dependencies={"a"}),
    ]
    orchestrator = MultiAgentOrchestrator(max_parallel_agents=2)

    async def run_agent(name: str):
        return {"name": name}

    executions = asyncio.run(orchestrator.run(specs=specs, run_agent=run_agent, max_steps=2))
    assert [name for name, _ in executions] == ["a", "b"]


def test_multi_agent_orchestrator_raises_on_unresolvable_plan():
    specs = [
        AgentSpec(name="a", dependencies={"b"}),
        AgentSpec(name="b", dependencies={"a"}),
    ]
    orchestrator = MultiAgentOrchestrator(max_parallel_agents=2)

    async def run_agent(name: str):
        return {"name": name}

    try:
        asyncio.run(orchestrator.run(specs=specs, run_agent=run_agent, max_steps=10))
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected RuntimeError for cyclic dependencies")


def test_build_agent_specs_adds_subdivision_when_enabled():
    service = AgenticResearchService()

    class _Job:
        assumptions = {"extra_agents": ["subdivision_research"]}

    specs = service._build_agent_specs(job=_Job())
    names = [spec.name for spec in specs]
    assert "subdivision_research" in names
    dossier = next(spec for spec in specs if spec.name == "dossier_writer")
    assert "subdivision_research" in dossier.dependencies


def test_build_agent_specs_preserves_core_chain_when_max_steps_is_core_default():
    service = AgenticResearchService()

    class _Job:
        assumptions = {"extra_agents": ["subdivision_research"]}

    specs = service._build_agent_specs(job=_Job(), max_steps=7)
    names = [spec.name for spec in specs]
    assert names == [
        "normalize_geocode",
        "public_records",
        "permits_violations",
        "comps_sales",
        "comps_rentals",
        "underwriting",
        "dossier_writer",
    ]


def test_research_input_defaults_to_pipeline_mode():
    payload = ResearchInput(address="123 Main St")
    assert payload.mode == "pipeline"
    assert payload.limits.max_parallel_agents == 1


def test_default_comp_radius_uses_city_market_type():
    service = AgenticResearchService()
    assert service._default_comp_radius_mi("Newark") == 1.0
    assert service._default_comp_radius_mi("Mountainside") == 3.0
    assert service._default_comp_radius_mi(None) == 3.0


def test_resolve_enrichment_max_age_hours_defaults_and_validation():
    service = AgenticResearchService()
    assert service._resolve_enrichment_max_age_hours({}, strict_required=False) is None
    assert service._resolve_enrichment_max_age_hours({}, strict_required=True) == 168
    assert service._resolve_enrichment_max_age_hours({"enriched_max_age_hours": 72}, strict_required=True) == 72

    try:
        service._resolve_enrichment_max_age_hours({"enriched_max_age_hours": 0}, strict_required=True)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for non-positive enriched_max_age_hours")


def test_compute_enrichment_status_marks_stale_when_ttl_exceeded():
    service = AgenticResearchService()

    class _Obj:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    fresh_skip = _Obj(id=1, owner_name="Owner", created_at=utcnow())
    fresh_zillow = _Obj(id=2, updated_at=utcnow())
    crm = _Obj(id=3)
    fresh_status = service._compute_enrichment_status(
        crm_property=crm,
        skip_trace=fresh_skip,
        zillow=fresh_zillow,
        max_age_hours=24,
    )
    assert fresh_status["is_enriched"] is True
    assert fresh_status["is_fresh"] is True

    old_skip = _Obj(id=4, owner_name="Owner", created_at=utcnow() - timedelta(hours=200))
    old_zillow = _Obj(id=5, updated_at=utcnow() - timedelta(hours=200))
    stale_status = service._compute_enrichment_status(
        crm_property=crm,
        skip_trace=old_skip,
        zillow=old_zillow,
        max_age_hours=24,
    )
    assert stale_status["is_enriched"] is True
    assert stale_status["is_fresh"] is False
    assert stale_status["age_hours"] is not None
    assert stale_status["age_hours"] > 24


def test_source_quality_prefers_government_domains():
    service = AgenticResearchService()
    gov_score = service._source_quality_score("https://www.nj.gov/treasury/taxation/", category="public_records")
    listing_score = service._source_quality_score("https://www.zillow.com/homedetails/1", category="public_records")
    unknown_score = service._source_quality_score("https://random-example-site.test/page", category="public_records")
    assert gov_score > listing_score > unknown_score


def test_dedupe_and_rank_comps_uses_effective_score():
    service = AgenticResearchService()
    comps = [
        {
            "address": "1 Main St, Newark, NJ 07102",
            "source_url": "https://random-example-site.test/comp-1",
            "similarity_score": 0.8,
            "sale_date": date(2026, 1, 1),
            "details": {"source_quality": 0.45},
        },
        {
            "address": "2 Main St, Newark, NJ 07102",
            "source_url": "https://www.nj.gov/comp-2",
            "similarity_score": 0.8,
            "sale_date": date(2026, 1, 1),
            "details": {"source_quality": 0.95},
        },
    ]
    ranked = service._dedupe_and_rank_comps(comps=comps, top_n=2, date_field="sale_date")
    assert ranked[0]["address"].startswith("2 Main St")
    assert (ranked[0]["details"] or {}).get("effective_score") >= (ranked[1]["details"] or {}).get("effective_score")


def test_orchestrated_pipeline_shares_context_with_dependent_workers():
    service = AgenticResearchService()
    persisted: dict[str, object] = {}

    class _FakeDb:
        def commit(self):
            return None

    class _FakeJob:
        id = 999
        research_property_id = 999
        assumptions = {}
        current_step = None
        progress = 0

    async def _normalize(self, db, job, context):
        return {
            "data": {
                "property_profile": {
                    "normalized_address": "123 main st, newark, nj 07102",
                    "geo": {"lat": 40.0, "lng": -74.0},
                    "parcel_facts": {"sqft": 1500, "beds": 3, "baths": 2},
                }
            },
            "unknowns": [],
            "errors": [],
            "evidence": [],
            "web_calls": 0,
            "cost_usd": 0.0,
        }

    async def _public_records(self, db, job, context):
        return {"data": {"public_records_hits": []}, "unknowns": [], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

    async def _permits(self, db, job, context):
        return {"data": {"permit_violation_hits": []}, "unknowns": [], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

    async def _comps_sales(self, db, job, context):
        profile = context.get("normalize_geocode", {}).get("property_profile")
        if not profile:
            return {
                "data": {"comps_sales": []},
                "unknowns": [{"field": "comps_sales", "reason": "Missing property profile from prior worker."}],
                "errors": [],
                "evidence": [],
                "web_calls": 0,
                "cost_usd": 0.0,
            }
        return {
            "data": {"comps_sales": [{"address": "1 Main St", "similarity_score": 1.0, "source_url": "internal://test"}]},
            "unknowns": [],
            "errors": [],
            "evidence": [],
            "web_calls": 0,
            "cost_usd": 0.0,
        }

    def _persist_worker_run(self, db, job, execution):
        persisted[execution.worker_name] = execution

    def _persist_evidence(self, db, job, evidence_drafts):
        return None

    def _get_full_output(self, db, property_id, job_id):
        return {"ok": True}

    service._worker_normalize_geocode = MethodType(_normalize, service)
    service._worker_public_records = MethodType(_public_records, service)
    service._worker_permits_violations = MethodType(_permits, service)
    service._worker_comps_sales = MethodType(_comps_sales, service)
    service._persist_worker_run = MethodType(_persist_worker_run, service)
    service._persist_evidence = MethodType(_persist_evidence, service)
    service.get_full_output = MethodType(_get_full_output, service)

    result = asyncio.run(
        service._execute_orchestrated_pipeline(
            db=_FakeDb(),
            job=_FakeJob(),
            max_steps=4,
            max_web_calls=10,
            timeout_seconds=5,
            max_parallel_agents=2,
        )
    )

    assert result == {"ok": True}
    comps_execution = persisted["comps_sales"]
    assert comps_execution.status == "success"
    assert comps_execution.unknowns == []
    assert len(comps_execution.data["comps_sales"]) == 1
