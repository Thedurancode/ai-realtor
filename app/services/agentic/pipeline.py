import asyncio
import logging
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Awaitable, Callable

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.agentic_job import AgenticJob, AgenticJobStatus
from app.models.agentic_property import ResearchProperty
from app.models.comp_rental import CompRental
from app.models.comp_sale import CompSale
from app.models.dossier import Dossier
from app.models.evidence_item import EvidenceItem
from app.models.property import Property
from app.models.risk_score import RiskScore
from app.models.skip_trace import SkipTrace
from app.models.underwriting import Underwriting
from app.models.worker_run import WorkerRun
from app.models.zillow_enrichment import ZillowEnrichment
from app.schemas.agentic_research import ResearchInput
from app.services.agentic.orchestrator import AgentSpec, MultiAgentOrchestrator
from app.services.agentic.providers import (
    PortalFetcher,
    SearchProvider,
    build_search_provider_from_settings,
)
from app.services.agentic.utils import (
    build_evidence_hash,
    build_stable_property_key,
    new_trace_id,
    normalize_address,
    normalize_us_state_code,
    utcnow,
)
from app.services.agentic.workers._context import ServiceContext
from app.services.agentic.workers._shared import (
    compute_enrichment_status,
    find_matching_crm_property,
    resolve_enrichment_max_age_hours,
)
from app.services.agentic.workers.comps_workers import worker_comps_rentals, worker_comps_sales
from app.services.agentic.workers.dossier import worker_dossier_writer
from app.services.agentic.workers.environmental import (
    worker_epa_environmental,
    worker_flood_zone,
    worker_historic_places,
    worker_hud_opportunity,
    worker_school_district,
    worker_seismic_hazard,
    worker_wetlands,
    worker_wildfire_hazard,
)
from app.services.agentic.workers.geo import worker_normalize_geocode
from app.services.agentic.workers.neighborhood import worker_neighborhood_intel
from app.services.agentic.workers.public_records import (
    worker_permits_violations,
    worker_public_records,
    worker_subdivision_research,
)
from app.services.agentic.workers.rapidapi import (
    worker_redfin,
    worker_rentcast,
    worker_us_real_estate,
    worker_walk_score,
)
from app.services.agentic.workers.underwriting import worker_underwriting


@dataclass
class EvidenceDraft:
    category: str
    claim: str
    source_url: str
    raw_excerpt: str | None = None
    confidence: float | None = None


@dataclass
class WorkerExecution:
    worker_name: str
    status: str
    data: dict[str, Any] = field(default_factory=dict)
    unknowns: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    evidence: list[EvidenceDraft] = field(default_factory=list)
    web_calls: int = 0
    cost_usd: float = 0.0
    runtime_ms: int = 0


class AgenticResearchService:
    URBAN_RADIUS_CITIES = {
        "new york",
        "newark",
        "jersey city",
        "hoboken",
        "philadelphia",
        "boston",
        "chicago",
        "los angeles",
        "san francisco",
        "washington",
        "miami",
        "atlanta",
        "houston",
        "dallas",
        "seattle",
    }
    HIGH_TRUST_DOMAINS = {
        ".gov",
        "tax.nj.gov",
        "countyoffice.org",
        "arcgis.com",
        "esri.com",
    }
    MEDIUM_TRUST_DOMAINS = {
        "realtor.com",
        "redfin.com",
        "zillow.com",
        "trulia.com",
        "loopnet.com",
        "crexi.com",
    }

    def __init__(self, search_provider: SearchProvider | None = None):
        self.search_provider = search_provider or build_search_provider_from_settings()
        self.portal_fetcher = PortalFetcher()
        self.logger = logging.getLogger("agentic_research")

    def _build_service_context(self) -> ServiceContext:
        return ServiceContext(
            search_provider=self.search_provider,
            portal_fetcher=self.portal_fetcher,
            urban_radius_cities=self.URBAN_RADIUS_CITIES,
            high_trust_domains=self.HIGH_TRUST_DOMAINS,
            medium_trust_domains=self.MEDIUM_TRUST_DOMAINS,
        )

    def _get_enrichment_status_for_research_property(
        self, db: Session, research_property: ResearchProperty, max_age_hours: int | None = None
    ) -> dict[str, Any]:
        crm_property = find_matching_crm_property(db=db, rp=research_property)
        skip_trace = None
        zillow = None
        if crm_property:
            skip_trace = (
                db.query(SkipTrace)
                .filter(SkipTrace.property_id == crm_property.id)
                .order_by(SkipTrace.created_at.desc())
                .first()
            )
            zillow = (
                db.query(ZillowEnrichment)
                .filter(ZillowEnrichment.property_id == crm_property.id)
                .first()
            )
        return compute_enrichment_status(
            crm_property=crm_property,
            skip_trace=skip_trace,
            zillow=zillow,
            max_age_hours=max_age_hours,
        )

    def get_property_enrichment_status(
        self, db: Session, property_id: int, max_age_hours: int | None = None
    ) -> dict[str, Any] | None:
        rp = db.query(ResearchProperty).filter(ResearchProperty.id == property_id).first()
        if rp is None:
            return None
        return self._get_enrichment_status_for_research_property(
            db=db,
            research_property=rp,
            max_age_hours=max_age_hours,
        )

    def _assert_required_enrichment(self, db: Session, job: AgenticJob) -> None:
        require_enriched_data = bool((job.assumptions or {}).get("require_enriched_data"))
        if not require_enriched_data:
            return

        rp = db.query(ResearchProperty).filter(ResearchProperty.id == job.research_property_id).first()
        if rp is None:
            raise ValueError("Research property not found")

        max_age_hours = resolve_enrichment_max_age_hours(
            assumptions=job.assumptions or {},
            strict_required=True,
        )

        enrichment_status = self._get_enrichment_status_for_research_property(
            db=db,
            research_property=rp,
            max_age_hours=max_age_hours,
        )
        if enrichment_status.get("is_enriched"):
            if enrichment_status.get("is_fresh"):
                return
            raise RuntimeError(
                "assumptions.require_enriched_data=true but enrichment is stale: "
                f"age_hours={enrichment_status.get('age_hours')} max_age_hours={max_age_hours}"
            )

        missing = enrichment_status.get("missing") or []
        missing_text = ", ".join(missing) if missing else "unknown"
        raise RuntimeError(
            f"assumptions.require_enriched_data=true but enrichment is incomplete: {missing_text}"
        )

    async def create_job(self, db: Session, payload: ResearchInput) -> AgenticJob:
        normalized_state = normalize_us_state_code(payload.state)
        stable_key = build_stable_property_key(
            address=payload.address,
            city=payload.city,
            state=normalized_state or payload.state,
            zip_code=payload.zip,
            apn=payload.apn,
        )
        normalized = normalize_address(
            address=payload.address,
            city=payload.city,
            state=normalized_state or payload.state,
            zip_code=payload.zip,
        )

        research_property = (
            db.query(ResearchProperty)
            .filter(ResearchProperty.stable_key == stable_key)
            .first()
        )

        if research_property is None:
            research_property = ResearchProperty(
                stable_key=stable_key,
                raw_address=payload.address,
                normalized_address=normalized,
                city=payload.city,
                state=normalized_state,
                zip_code=payload.zip,
                apn=payload.apn,
            )
            db.add(research_property)
            db.flush()
        else:
            research_property.raw_address = payload.address
            research_property.normalized_address = normalized
            research_property.city = payload.city or research_property.city
            research_property.state = normalized_state or research_property.state
            research_property.zip_code = payload.zip or research_property.zip_code
            research_property.apn = payload.apn or research_property.apn

        job = AgenticJob(
            trace_id=new_trace_id(),
            research_property_id=research_property.id,
            status=AgenticJobStatus.PENDING,
            strategy=payload.strategy,
            assumptions=payload.assumptions,
            limits={**payload.limits.model_dump(), "execution_mode": payload.mode},
            progress=0,
            current_step="queued",
        )

        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    async def run_job(self, job_id: int) -> None:
        db = SessionLocal()
        job: AgenticJob | None = None
        try:
            job = db.query(AgenticJob).filter(AgenticJob.id == job_id).first()
            if job is None:
                return

            job.status = AgenticJobStatus.IN_PROGRESS
            job.started_at = utcnow()
            job.progress = 1
            job.current_step = "starting"
            db.commit()

            output = await self._execute_pipeline(db=db, job=job)

            job.results = output
            job.status = AgenticJobStatus.COMPLETED
            job.progress = 100
            job.current_step = "complete"
            job.completed_at = utcnow()
            db.commit()

        except Exception as exc:
            self.logger.exception("Agentic job failed: job_id=%s", job_id)
            db.rollback()
            if job is not None:
                job.status = AgenticJobStatus.FAILED
                job.error_message = str(exc)
                job.current_step = "failed"
                job.completed_at = utcnow()
                db.commit()
        finally:
            db.close()

    async def run_sync(self, payload: ResearchInput) -> AgenticJob:
        db = SessionLocal()
        try:
            job = await self.create_job(db=db, payload=payload)
            job_id = job.id
        finally:
            db.close()

        await self.run_job(job_id=job_id)

        db = SessionLocal()
        try:
            completed = db.query(AgenticJob).filter(AgenticJob.id == job_id).first()
            if completed is None:
                raise ValueError("Job vanished after execution")
            return completed
        finally:
            db.close()

    async def _execute_pipeline(self, db: Session, job: AgenticJob) -> dict[str, Any]:
        limits = job.limits or {}
        max_steps = int(limits.get("max_steps", 9))
        max_web_calls = int(limits.get("max_web_calls", 30))
        timeout_seconds = int(limits.get("timeout_seconds_per_step", 20))
        execution_mode = str(limits.get("execution_mode", "pipeline")).strip().lower()
        self._assert_required_enrichment(db=db, job=job)

        if execution_mode == "orchestrated":
            return await self._execute_orchestrated_pipeline(
                db=db,
                job=job,
                max_steps=max_steps,
                max_web_calls=max_web_calls,
                timeout_seconds=timeout_seconds,
                max_parallel_agents=int(limits.get("max_parallel_agents", 3)),
            )

        svc = self._build_service_context()
        context: dict[str, Any] = {}
        total_web_calls = 0
        workers: list[tuple[str, Callable[[], Awaitable[dict[str, Any]]]]] = [
            ("normalize_geocode", lambda: worker_normalize_geocode(db, job, context, svc)),
            ("public_records", lambda: worker_public_records(db, job, context, svc)),
            ("permits_violations", lambda: worker_permits_violations(db, job, context, svc)),
            ("comps_sales", lambda: worker_comps_sales(db, job, context, svc)),
            ("comps_rentals", lambda: worker_comps_rentals(db, job, context, svc)),
            ("neighborhood_intel", lambda: worker_neighborhood_intel(db, job, context, svc)),
            ("flood_zone", lambda: worker_flood_zone(db, job, context, svc)),
            ("underwriting", lambda: worker_underwriting(db, job, context, svc)),
            ("dossier_writer", lambda: worker_dossier_writer(db, job, context, svc)),
        ]

        workers = workers[:max_steps]
        for idx, (worker_name, worker_fn) in enumerate(workers, start=1):
            job.current_step = worker_name
            job.progress = int((idx - 1) * 100 / len(workers))
            db.commit()

            execution = await self._run_worker(
                worker_name=worker_name,
                worker_fn=worker_fn,
                timeout_seconds=timeout_seconds,
            )
            total_web_calls += execution.web_calls
            self._persist_worker_run(db=db, job=job, execution=execution)
            if execution.evidence:
                self._persist_evidence(db=db, job=job, evidence_drafts=execution.evidence)
            context[worker_name] = execution.data

            if total_web_calls > max_web_calls:
                raise RuntimeError(
                    f"Job exceeded web call limit ({total_web_calls} > {max_web_calls})"
                )

        return self.get_full_output(db=db, property_id=job.research_property_id, job_id=job.id)

    async def _execute_orchestrated_pipeline(
        self,
        db: Session,
        job: AgenticJob,
        max_steps: int,
        max_web_calls: int,
        timeout_seconds: int,
        max_parallel_agents: int,
    ) -> dict[str, Any]:
        svc = self._build_service_context()
        context: dict[str, Any] = {}
        total_web_calls = 0

        worker_fns: dict[str, Callable[[], Awaitable[dict[str, Any]]]] = {
            "normalize_geocode": lambda: worker_normalize_geocode(db, job, context, svc),
            "public_records": lambda: worker_public_records(db, job, context, svc),
            "permits_violations": lambda: worker_permits_violations(db, job, context, svc),
            "comps_sales": lambda: worker_comps_sales(db, job, context, svc),
            "comps_rentals": lambda: worker_comps_rentals(db, job, context, svc),
            "neighborhood_intel": lambda: worker_neighborhood_intel(db, job, context, svc),
            "flood_zone": lambda: worker_flood_zone(db, job, context, svc),
            "underwriting": lambda: worker_underwriting(db, job, context, svc),
            "dossier_writer": lambda: worker_dossier_writer(db, job, context, svc),
            "subdivision_research": lambda: worker_subdivision_research(db, job, context, svc),
            # Extensive research workers (opt-in)
            "epa_environmental": lambda: worker_epa_environmental(db, job, context, svc),
            "wildfire_hazard": lambda: worker_wildfire_hazard(db, job, context, svc),
            "hud_opportunity": lambda: worker_hud_opportunity(db, job, context, svc),
            "wetlands": lambda: worker_wetlands(db, job, context, svc),
            "historic_places": lambda: worker_historic_places(db, job, context, svc),
            "seismic_hazard": lambda: worker_seismic_hazard(db, job, context, svc),
            "school_district": lambda: worker_school_district(db, job, context, svc),
            # RapidAPI Tier 1 workers (opt-in)
            "us_real_estate": lambda: worker_us_real_estate(db, job, context, svc),
            "walk_score": lambda: worker_walk_score(db, job, context, svc),
            "redfin": lambda: worker_redfin(db, job, context, svc),
            "rentcast": lambda: worker_rentcast(db, job, context, svc),
        }

        specs = self._build_agent_specs(job=job, max_steps=max_steps)
        spec_names = {spec.name for spec in specs}

        # Drop dependencies that are not scheduled due to max_steps slice.
        for spec in specs:
            spec.dependencies = {dep for dep in spec.dependencies if dep in spec_names}

        orchestrator = MultiAgentOrchestrator(max_parallel_agents=max_parallel_agents)

        async def _run_agent(name: str) -> WorkerExecution:
            worker_fn = worker_fns.get(name)
            if worker_fn is None:
                raise ValueError(f"No worker function registered for agent '{name}'")
            execution = await self._run_worker(
                worker_name=name,
                worker_fn=worker_fn,
                timeout_seconds=timeout_seconds,
            )
            # Make each completed worker's data immediately available to dependents.
            context[name] = execution.data
            return execution

        executions = await orchestrator.run(
            specs=specs,
            run_agent=_run_agent,
            max_steps=max_steps,
        )

        total_planned = max(1, len(specs))
        for idx, (worker_name, execution) in enumerate(executions, start=1):
            job.current_step = worker_name
            job.progress = int(idx * 100 / total_planned)
            db.commit()

            total_web_calls += execution.web_calls
            self._persist_worker_run(db=db, job=job, execution=execution)
            if execution.evidence:
                self._persist_evidence(db=db, job=job, evidence_drafts=execution.evidence)
            context[worker_name] = execution.data

            if total_web_calls > max_web_calls:
                raise RuntimeError(
                    f"Job exceeded web call limit ({total_web_calls} > {max_web_calls})"
                )

        return self.get_full_output(db=db, property_id=job.research_property_id, job_id=job.id)

    def _build_agent_specs(self, job: AgenticJob, max_steps: int | None = None) -> list[AgentSpec]:
        core_specs = [
            AgentSpec(name="normalize_geocode", dependencies=set()),
            AgentSpec(name="public_records", dependencies={"normalize_geocode"}),
            AgentSpec(name="permits_violations", dependencies={"normalize_geocode"}),
            AgentSpec(name="comps_sales", dependencies={"normalize_geocode"}),
            AgentSpec(name="comps_rentals", dependencies={"normalize_geocode"}),
            AgentSpec(name="neighborhood_intel", dependencies={"normalize_geocode"}),
            AgentSpec(name="flood_zone", dependencies={"normalize_geocode"}),
            AgentSpec(
                name="underwriting",
                dependencies={"normalize_geocode", "comps_sales", "comps_rentals"},
            ),
            AgentSpec(
                name="dossier_writer",
                dependencies={
                    "normalize_geocode",
                    "public_records",
                    "permits_violations",
                    "comps_sales",
                    "comps_rentals",
                    "neighborhood_intel",
                    "flood_zone",
                    "underwriting",
                },
            ),
        ]

        if max_steps is not None and max_steps <= len(core_specs):
            return core_specs[:max_steps]

        specs = list(core_specs)
        extra_agents = (job.assumptions or {}).get("extra_agents", [])
        allowed_extra_count = None
        if max_steps is not None:
            allowed_extra_count = max(0, max_steps - len(core_specs))

        if isinstance(extra_agents, list) and "subdivision_research" in extra_agents:
            if allowed_extra_count is not None and allowed_extra_count <= 0:
                return specs
            # Run this late so it can use enriched context from records/comps.
            specs.insert(
                -1,
                AgentSpec(
                    name="subdivision_research",
                    dependencies={"normalize_geocode", "public_records", "permits_violations"},
                ),
            )
            specs[-1].dependencies.add("subdivision_research")

        # Extensive research: 7 additional government data workers
        if isinstance(extra_agents, list) and "extensive" in extra_agents:
            extensive_specs = [
                AgentSpec(name="epa_environmental", dependencies={"normalize_geocode"}),
                AgentSpec(name="wildfire_hazard", dependencies={"normalize_geocode"}),
                AgentSpec(name="hud_opportunity", dependencies={"normalize_geocode"}),
                AgentSpec(name="wetlands", dependencies={"normalize_geocode"}),
                AgentSpec(name="historic_places", dependencies={"normalize_geocode"}),
                AgentSpec(name="seismic_hazard", dependencies={"normalize_geocode"}),
                AgentSpec(name="school_district", dependencies={"normalize_geocode"}),
                # RapidAPI Tier 1
                AgentSpec(name="us_real_estate", dependencies={"normalize_geocode"}),
                AgentSpec(name="walk_score", dependencies={"normalize_geocode"}),
                AgentSpec(name="redfin", dependencies={"normalize_geocode"}),
                AgentSpec(name="rentcast", dependencies={"normalize_geocode"}),
            ]
            added = 0
            for espec in extensive_specs:
                if allowed_extra_count is not None and added >= allowed_extra_count:
                    break
                # Insert before dossier_writer so it can use the data
                specs.insert(-1, espec)
                # Make dossier_writer depend on these too
                specs[-1].dependencies.add(espec.name)
                added += 1

        return specs

    async def _run_worker(
        self,
        worker_name: str,
        worker_fn: Callable[[], Awaitable[dict[str, Any]]],
        timeout_seconds: int,
    ) -> WorkerExecution:
        start = perf_counter()
        execution = WorkerExecution(worker_name=worker_name, status="success")
        try:
            result = await asyncio.wait_for(worker_fn(), timeout=timeout_seconds)
            execution.data = result.get("data", {})
            execution.unknowns = result.get("unknowns", [])
            execution.errors = result.get("errors", [])
            execution.evidence = result.get("evidence", [])
            execution.web_calls = int(result.get("web_calls", 0))
            execution.cost_usd = float(result.get("cost_usd", 0.0))

            if execution.errors:
                execution.status = "partial"

        except asyncio.TimeoutError:
            execution.status = "failed"
            execution.errors = [f"Worker timed out after {timeout_seconds}s"]
        except Exception as exc:
            execution.status = "failed"
            execution.errors = [str(exc)]

        execution.runtime_ms = int((perf_counter() - start) * 1000)
        return execution

    def _persist_worker_run(self, db: Session, job: AgenticJob, execution: WorkerExecution) -> None:
        payload = jsonable_encoder(execution.data)
        unknowns = jsonable_encoder(execution.unknowns)
        errors = jsonable_encoder(execution.errors)
        db.add(
            WorkerRun(
                job_id=job.id,
                worker_name=execution.worker_name,
                status=execution.status,
                runtime_ms=execution.runtime_ms,
                cost_usd=execution.cost_usd,
                web_calls=execution.web_calls,
                data=payload,
                unknowns=unknowns,
                errors=errors,
            )
        )
        db.commit()

    def _persist_evidence(
        self,
        db: Session,
        job: AgenticJob,
        evidence_drafts: list[EvidenceDraft],
    ) -> None:
        for evidence in evidence_drafts:
            evidence_hash = build_evidence_hash(
                category=evidence.category,
                claim=evidence.claim,
                source_url=evidence.source_url,
                raw_excerpt=evidence.raw_excerpt,
            )
            existing = (
                db.query(EvidenceItem)
                .filter(EvidenceItem.hash == evidence_hash)
                .first()
            )

            if existing:
                existing.job_id = job.id
                existing.research_property_id = job.research_property_id
                existing.category = evidence.category
                existing.claim = evidence.claim
                existing.source_url = evidence.source_url
                existing.raw_excerpt = evidence.raw_excerpt
                existing.confidence = evidence.confidence
                existing.captured_at = utcnow()
            else:
                db.add(
                    EvidenceItem(
                        research_property_id=job.research_property_id,
                        job_id=job.id,
                        category=evidence.category,
                        claim=evidence.claim,
                        source_url=evidence.source_url,
                        captured_at=utcnow(),
                        raw_excerpt=evidence.raw_excerpt,
                        confidence=evidence.confidence,
                        hash=evidence_hash,
                    )
                )

        db.commit()

    def get_job(self, db: Session, job_id: int) -> AgenticJob | None:
        return db.query(AgenticJob).filter(AgenticJob.id == job_id).first()

    def get_latest_completed_job_for_property(self, db: Session, property_id: int) -> AgenticJob | None:
        return (
            db.query(AgenticJob)
            .filter(
                AgenticJob.research_property_id == property_id,
                AgenticJob.status == AgenticJobStatus.COMPLETED,
            )
            .order_by(AgenticJob.completed_at.desc())
            .first()
        )

    def get_full_output(self, db: Session, property_id: int, job_id: int | None = None) -> dict[str, Any] | None:
        if job_id is None:
            job = self.get_latest_completed_job_for_property(db=db, property_id=property_id)
            if not job:
                return None
            job_id = job.id

        rp = db.query(ResearchProperty).filter(ResearchProperty.id == property_id).first()
        if not rp:
            return None

        evidence_rows = (
            db.query(EvidenceItem)
            .filter(EvidenceItem.job_id == job_id)
            .order_by(EvidenceItem.id.asc())
            .all()
        )
        sales_rows = db.query(CompSale).filter(CompSale.job_id == job_id, CompSale.is_current.is_(True)).order_by(CompSale.similarity_score.desc()).all()
        rental_rows = db.query(CompRental).filter(CompRental.job_id == job_id, CompRental.is_current.is_(True)).order_by(CompRental.similarity_score.desc()).all()
        underwrite_row = db.query(Underwriting).filter(Underwriting.job_id == job_id, Underwriting.is_current.is_(True)).order_by(Underwriting.id.desc()).first()
        risk_row = db.query(RiskScore).filter(RiskScore.job_id == job_id, RiskScore.is_current.is_(True)).order_by(RiskScore.id.desc()).first()
        dossier_row = db.query(Dossier).filter(Dossier.job_id == job_id, Dossier.is_current.is_(True)).order_by(Dossier.id.desc()).first()
        worker_rows = db.query(WorkerRun).filter(WorkerRun.job_id == job_id).order_by(WorkerRun.id.asc()).all()

        # Extract worker data stored in worker_run JSON (no dedicated DB models)
        neighborhood_intel = None
        flood_zone = None
        extensive_data: dict[str, Any] = {}
        _extensive_keys = {
            "epa_environmental": "epa_environmental",
            "wildfire_hazard": "wildfire_hazard",
            "hud_opportunity": "hud_opportunity",
            "wetlands": "wetlands",
            "historic_places": "historic_places",
            "seismic_hazard": "seismic_hazard",
            "school_district": "school_district",
            "us_real_estate": "us_real_estate",
            "walk_score": "walk_score",
            "redfin": "redfin",
            "rentcast": "rentcast",
        }
        for wr in worker_rows:
            if wr.worker_name == "neighborhood_intel" and wr.data:
                neighborhood_intel = wr.data.get("neighborhood_intel")
            elif wr.worker_name == "flood_zone" and wr.data:
                flood_zone = wr.data.get("flood_zone")
            elif wr.worker_name in _extensive_keys and wr.data:
                data_key = _extensive_keys[wr.worker_name]
                extensive_data[data_key] = wr.data.get(data_key)

        profile = rp.latest_profile or {
            "normalized_address": rp.normalized_address,
            "geo": {"lat": rp.geo_lat, "lng": rp.geo_lng},
            "apn": rp.apn,
            "parcel_facts": {},
            "zoning": None,
            "owner_names": [],
            "mailing_address": None,
            "assessed_values": {},
            "tax_status": None,
            "transaction_history": [],
            "enrichment_status": {
                "has_crm_property_match": False,
                "has_skip_trace_owner": False,
                "has_zillow_enrichment": False,
                "is_enriched": False,
                "is_fresh": None,
                "age_hours": None,
                "max_age_hours": None,
                "matched_property_id": None,
                "skip_trace_id": None,
                "zillow_enrichment_id": None,
                "missing": ["crm_property_match", "skip_trace_owner", "zillow_enrichment"],
                "last_enriched_at": None,
            },
        }

        underwrite = {
            "arv_estimate": {
                "low": underwrite_row.arv_low if underwrite_row else None,
                "base": underwrite_row.arv_base if underwrite_row else None,
                "high": underwrite_row.arv_high if underwrite_row else None,
            },
            "rent_estimate": {
                "low": underwrite_row.rent_low if underwrite_row else None,
                "base": underwrite_row.rent_base if underwrite_row else None,
                "high": underwrite_row.rent_high if underwrite_row else None,
            },
            "rehab_tier": underwrite_row.rehab_tier if underwrite_row else "medium",
            "rehab_estimated_range": {
                "low": underwrite_row.rehab_low if underwrite_row else None,
                "base": ((underwrite_row.rehab_low + underwrite_row.rehab_high) / 2.0) if underwrite_row and underwrite_row.rehab_low is not None and underwrite_row.rehab_high is not None else None,
                "high": underwrite_row.rehab_high if underwrite_row else None,
            },
            "offer_price_recommendation": {
                "low": underwrite_row.offer_low if underwrite_row else None,
                "base": underwrite_row.offer_base if underwrite_row else None,
                "high": underwrite_row.offer_high if underwrite_row else None,
            },
            "fees": underwrite_row.fees if underwrite_row else {},
            "sensitivity_table": underwrite_row.sensitivity if underwrite_row else [],
        }

        risk = {
            "title_risk": risk_row.title_risk if risk_row else None,
            "data_confidence": risk_row.data_confidence if risk_row else None,
            "compliance_flags": risk_row.compliance_flags if risk_row else [],
            "notes": risk_row.notes if risk_row else None,
        }

        return {
            "property_profile": profile,
            "evidence": [
                {
                    "id": item.id,
                    "property_id": item.research_property_id,
                    "category": item.category,
                    "claim": item.claim,
                    "source_url": item.source_url,
                    "captured_at": item.captured_at.isoformat() if item.captured_at else None,
                    "raw_excerpt": item.raw_excerpt,
                    "confidence": item.confidence,
                    "hash": item.hash,
                }
                for item in evidence_rows
            ],
            "comps_sales": [
                {
                    "address": item.address,
                    "distance_mi": item.distance_mi,
                    "sale_date": item.sale_date.isoformat() if item.sale_date else None,
                    "sale_price": item.sale_price,
                    "sqft": item.sqft,
                    "beds": item.beds,
                    "baths": item.baths,
                    "year_built": item.year_built,
                    "similarity_score": item.similarity_score,
                    "source_url": item.source_url,
                }
                for item in sales_rows
            ],
            "comps_rentals": [
                {
                    "address": item.address,
                    "distance_mi": item.distance_mi,
                    "rent": item.rent,
                    "date_listed": item.date_listed.isoformat() if item.date_listed else None,
                    "sqft": item.sqft,
                    "beds": item.beds,
                    "baths": item.baths,
                    "similarity_score": item.similarity_score,
                    "source_url": item.source_url,
                }
                for item in rental_rows
            ],
            "underwrite": underwrite,
            "risk_score": risk,
            "neighborhood_intel": neighborhood_intel,
            "flood_zone": flood_zone,
            "extensive": extensive_data if extensive_data else None,
            "dossier": {"markdown": dossier_row.markdown if dossier_row else ""},
            "worker_runs": [
                {
                    "worker_name": run.worker_name,
                    "status": run.status,
                    "runtime_ms": run.runtime_ms,
                    "cost_usd": run.cost_usd,
                    "web_calls": run.web_calls,
                    "unknowns": run.unknowns or [],
                    "errors": run.errors or [],
                }
                for run in worker_rows
            ],
        }


agentic_research_service = AgenticResearchService()
