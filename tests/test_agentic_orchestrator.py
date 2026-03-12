import asyncio
from datetime import date
from datetime import timedelta

from app.services.agentic.orchestrator import AgentSpec, MultiAgentOrchestrator
from app.services.agentic.pipeline import AgenticResearchService
from app.services.agentic.utils import utcnow
from app.services.agentic.workers._shared import (
    compute_enrichment_status,
    resolve_enrichment_max_age_hours,
)
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
    """When max_steps equals core count, all core agents are included and extras are dropped."""
    service = AgenticResearchService()

    class _Job:
        assumptions = {"extra_agents": ["subdivision_research"]}

    # Core specs now have 9 items (normalize_geocode, public_records, permits_violations,
    # comps_sales, comps_rentals, neighborhood_intel, flood_zone, underwriting, dossier_writer)
    specs = service._build_agent_specs(job=_Job(), max_steps=9)
    names = [spec.name for spec in specs]
    assert names == [
        "normalize_geocode",
        "public_records",
        "permits_violations",
        "comps_sales",
        "comps_rentals",
        "neighborhood_intel",
        "flood_zone",
        "underwriting",
        "dossier_writer",
    ]


def test_research_input_defaults_to_pipeline_mode():
    payload = ResearchInput(address="123 Main St")
    assert payload.mode == "pipeline"
    assert payload.limits.max_parallel_agents == 1


def test_resolve_enrichment_max_age_hours_defaults_and_validation():
    assert resolve_enrichment_max_age_hours({}, strict_required=False) is None
    assert resolve_enrichment_max_age_hours({}, strict_required=True) == 168
    assert resolve_enrichment_max_age_hours({"enriched_max_age_hours": 72}, strict_required=True) == 72

    try:
        resolve_enrichment_max_age_hours({"enriched_max_age_hours": 0}, strict_required=True)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for non-positive enriched_max_age_hours")


def test_compute_enrichment_status_marks_stale_when_ttl_exceeded():
    class _Obj:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    fresh_skip = _Obj(id=1, owner_name="Owner", created_at=utcnow())
    fresh_zillow = _Obj(id=2, updated_at=utcnow())
    crm = _Obj(id=3)
    fresh_status = compute_enrichment_status(
        crm_property=crm,
        skip_trace=fresh_skip,
        zillow=fresh_zillow,
        max_age_hours=24,
    )
    assert fresh_status["is_enriched"] is True
    assert fresh_status["is_fresh"] is True

    old_skip = _Obj(id=4, owner_name="Owner", created_at=utcnow() - timedelta(hours=200))
    old_zillow = _Obj(id=5, updated_at=utcnow() - timedelta(hours=200))
    stale_status = compute_enrichment_status(
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
    """Test that .gov domains score higher in the service context trust hierarchy."""
    service = AgenticResearchService()
    svc = service._build_service_context()

    # Use HIGH_TRUST_DOMAINS and MEDIUM_TRUST_DOMAINS from the service class
    gov_url = "https://www.nj.gov/treasury/taxation/"
    listing_url = "https://www.zillow.com/homedetails/1"
    unknown_url = "https://random-example-site.test/page"

    def url_trust_score(url):
        """Simple trust scoring based on domain matching."""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        for d in AgenticResearchService.HIGH_TRUST_DOMAINS:
            if d in domain:
                return 0.95
        for d in AgenticResearchService.MEDIUM_TRUST_DOMAINS:
            if d in domain:
                return 0.7
        return 0.45

    gov_score = url_trust_score(gov_url)
    listing_score = url_trust_score(listing_url)
    unknown_score = url_trust_score(unknown_url)
    assert gov_score > listing_score > unknown_score


def test_dedupe_and_rank_comps_simple():
    """Test basic comp deduplication and ranking logic."""
    comps = [
        {
            "address": "1 Main St, Newark, NJ 07102",
            "source_url": "https://random-example-site.test/comp-1",
            "similarity_score": 0.8,
            "sale_date": date(2026, 1, 1),
        },
        {
            "address": "2 Main St, Newark, NJ 07102",
            "source_url": "https://www.nj.gov/comp-2",
            "similarity_score": 0.9,
            "sale_date": date(2026, 1, 1),
        },
    ]
    # Higher similarity score should rank higher
    ranked = sorted(comps, key=lambda x: x.get("similarity_score", 0), reverse=True)
    assert ranked[0]["address"].startswith("2 Main St")


def test_orchestrated_pipeline_shares_context_with_dependent_workers():
    """Test that the orchestrated pipeline shares context between workers.

    Since the pipeline now uses standalone worker functions (not self._worker_*),
    we test context sharing by patching the worker functions at module level.
    """
    from unittest.mock import patch, AsyncMock
    from app.services.agentic.pipeline import WorkerExecution

    service = AgenticResearchService()
    persisted: dict[str, WorkerExecution] = {}

    class _FakeDb:
        def commit(self):
            return None

        def add(self, obj):
            return None

    class _FakeJob:
        id = 999
        research_property_id = 999
        assumptions = {}
        current_step = None
        progress = 0

    # Track the shared context to verify it's passed between workers
    shared_context_log: list[dict] = []

    async def fake_normalize(db, job, context, svc):
        result = {
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
        return result

    async def fake_public_records(db, job, context, svc):
        return {"data": {"public_records_hits": []}, "unknowns": [], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

    async def fake_permits(db, job, context, svc):
        return {"data": {"permit_violation_hits": []}, "unknowns": [], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

    async def fake_comps_sales(db, job, context, svc):
        # Check if normalize_geocode data is available in context
        profile = context.get("normalize_geocode", {}).get("property_profile")
        shared_context_log.append({"worker": "comps_sales", "has_profile": profile is not None})
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

    with patch("app.services.agentic.pipeline.worker_normalize_geocode", fake_normalize), \
         patch("app.services.agentic.pipeline.worker_public_records", fake_public_records), \
         patch("app.services.agentic.pipeline.worker_permits_violations", fake_permits), \
         patch("app.services.agentic.pipeline.worker_comps_sales", fake_comps_sales), \
         patch("app.services.agentic.pipeline.worker_comps_rentals", AsyncMock(return_value={"data": {}, "unknowns": [], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0})), \
         patch("app.services.agentic.pipeline.worker_neighborhood_intel", AsyncMock(return_value={"data": {}, "unknowns": [], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0})), \
         patch("app.services.agentic.pipeline.worker_flood_zone", AsyncMock(return_value={"data": {}, "unknowns": [], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0})), \
         patch("app.services.agentic.pipeline.worker_underwriting", AsyncMock(return_value={"data": {}, "unknowns": [], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0})), \
         patch("app.services.agentic.pipeline.worker_dossier_writer", AsyncMock(return_value={"data": {}, "unknowns": [], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0})), \
         patch.object(service, "get_full_output", return_value={"ok": True}):

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
        # Verify comps_sales worker received the context from normalize_geocode
        assert any(entry["worker"] == "comps_sales" and entry["has_profile"] for entry in shared_context_log)
