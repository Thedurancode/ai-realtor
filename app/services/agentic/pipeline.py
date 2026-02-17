import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from statistics import mean
from time import perf_counter
from typing import Any, Awaitable, Callable
from urllib.parse import urlparse

import httpx

from dateutil import parser as date_parser
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.agentic_job import AgenticJob, AgenticJobStatus
from app.models.agentic_property import ResearchProperty
from app.models.comp_rental import CompRental
from app.models.comp_sale import CompSale
from app.models.dossier import Dossier
from app.models.evidence_item import EvidenceItem
from app.models.property import Property, PropertyStatus
from app.models.risk_score import RiskScore
from app.models.skip_trace import SkipTrace
from app.models.underwriting import Underwriting
from app.models.worker_run import WorkerRun
from app.models.zillow_enrichment import ZillowEnrichment
from app.schemas.agentic_research import ResearchInput
from app.services.agentic.comps import (
    distance_proxy_mi,
    passes_hard_filters,
    similarity_score,
)
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
from app.services.google_places import google_places_service


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

    def _default_comp_radius_mi(self, city: str | None) -> float:
        """
        Deterministic default:
        - urban markets: 1.0mi
        - suburban/other markets: 3.0mi
        """
        normalized_city = (city or "").strip().lower()
        if normalized_city in self.URBAN_RADIUS_CITIES:
            return 1.0
        return 3.0

    def _source_quality_score(self, source_url: str | None, category: str | None = None) -> float:
        if not source_url:
            return 0.25
        if source_url.startswith("internal://"):
            return 0.95

        parsed = urlparse(source_url)
        host = (parsed.netloc or "").lower()
        host = host[4:] if host.startswith("www.") else host
        if not host:
            return 0.25

        if host.endswith(".gov") or any(host.endswith(domain) for domain in self.HIGH_TRUST_DOMAINS):
            return 0.95
        if any(host.endswith(domain) for domain in self.MEDIUM_TRUST_DOMAINS):
            return 0.70
        if category in {"public_records", "permits", "subdivision"}:
            return 0.45
        return 0.50

    def _effective_comp_score(self, comp: dict[str, Any]) -> float:
        similarity = float(comp.get("similarity_score") or 0.0)
        details = comp.get("details") or {}
        source_quality = details.get("source_quality")
        if source_quality is None:
            source_quality = self._source_quality_score(comp.get("source_url"), category="comps")
            details["source_quality"] = source_quality
            comp["details"] = details
        # Prioritize similarity while still rewarding trusted sources.
        return round((0.85 * similarity) + (0.15 * float(source_quality)), 6)

    def _compute_enrichment_status(
        self,
        crm_property: Property | None,
        skip_trace: SkipTrace | None,
        zillow: ZillowEnrichment | None,
        max_age_hours: int | None = None,
    ) -> dict[str, Any]:
        has_crm_match = crm_property is not None
        has_skip_owner = bool(skip_trace and skip_trace.owner_name)
        has_zillow = zillow is not None

        missing: list[str] = []
        if not has_crm_match:
            missing.append("crm_property_match")
        if not has_skip_owner:
            missing.append("skip_trace_owner")
        if not has_zillow:
            missing.append("zillow_enrichment")

        timestamps = []
        if skip_trace and skip_trace.created_at:
            timestamps.append(skip_trace.created_at)
        if zillow and zillow.updated_at:
            timestamps.append(zillow.updated_at)

        latest = max(timestamps) if timestamps else None
        age_hours = None
        is_fresh = None
        if max_age_hours is not None:
            if latest is None:
                is_fresh = False
            else:
                age_hours = round((utcnow() - latest).total_seconds() / 3600.0, 3)
                is_fresh = age_hours <= float(max_age_hours)

        return {
            "has_crm_property_match": has_crm_match,
            "has_skip_trace_owner": has_skip_owner,
            "has_zillow_enrichment": has_zillow,
            "is_enriched": has_crm_match and has_skip_owner and has_zillow,
            "is_fresh": is_fresh,
            "age_hours": age_hours,
            "max_age_hours": max_age_hours,
            "matched_property_id": crm_property.id if crm_property else None,
            "skip_trace_id": skip_trace.id if skip_trace else None,
            "zillow_enrichment_id": zillow.id if zillow else None,
            "missing": missing,
            "last_enriched_at": latest.isoformat() if latest else None,
        }

    def _resolve_enrichment_max_age_hours(
        self, assumptions: dict[str, Any] | None, *, strict_required: bool
    ) -> int | None:
        assumptions = assumptions or {}
        raw = assumptions.get("enriched_max_age_hours")
        if raw is None:
            return 168 if strict_required else None

        try:
            value = int(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError("assumptions.enriched_max_age_hours must be a positive integer") from exc

        if value <= 0:
            raise ValueError("assumptions.enriched_max_age_hours must be a positive integer")
        return value

    def _get_enrichment_status_for_research_property(
        self, db: Session, research_property: ResearchProperty, max_age_hours: int | None = None
    ) -> dict[str, Any]:
        crm_property = self._find_matching_crm_property(db=db, research_property=research_property)
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
        return self._compute_enrichment_status(
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

        max_age_hours = self._resolve_enrichment_max_age_hours(
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

        context: dict[str, Any] = {}
        total_web_calls = 0
        workers: list[tuple[str, Callable[[], Awaitable[dict[str, Any]]]]] = [
            ("normalize_geocode", lambda: self._worker_normalize_geocode(db, job, context)),
            ("public_records", lambda: self._worker_public_records(db, job, context)),
            ("permits_violations", lambda: self._worker_permits_violations(db, job, context)),
            ("comps_sales", lambda: self._worker_comps_sales(db, job, context)),
            ("comps_rentals", lambda: self._worker_comps_rentals(db, job, context)),
            ("neighborhood_intel", lambda: self._worker_neighborhood_intel(db, job, context)),
            ("flood_zone", lambda: self._worker_flood_zone(db, job, context)),
            ("underwriting", lambda: self._worker_underwriting(db, job, context)),
            ("dossier_writer", lambda: self._worker_dossier_writer(db, job, context)),
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
        context: dict[str, Any] = {}
        total_web_calls = 0

        worker_fns: dict[str, Callable[[], Awaitable[dict[str, Any]]]] = {
            "normalize_geocode": lambda: self._worker_normalize_geocode(db, job, context),
            "public_records": lambda: self._worker_public_records(db, job, context),
            "permits_violations": lambda: self._worker_permits_violations(db, job, context),
            "comps_sales": lambda: self._worker_comps_sales(db, job, context),
            "comps_rentals": lambda: self._worker_comps_rentals(db, job, context),
            "neighborhood_intel": lambda: self._worker_neighborhood_intel(db, job, context),
            "flood_zone": lambda: self._worker_flood_zone(db, job, context),
            "underwriting": lambda: self._worker_underwriting(db, job, context),
            "dossier_writer": lambda: self._worker_dossier_writer(db, job, context),
            "subdivision_research": lambda: self._worker_subdivision_research(db, job, context),
            # Extensive research workers (opt-in)
            "epa_environmental": lambda: self._worker_epa_environmental(db, job, context),
            "wildfire_hazard": lambda: self._worker_wildfire_hazard(db, job, context),
            "hud_opportunity": lambda: self._worker_hud_opportunity(db, job, context),
            "wetlands": lambda: self._worker_wetlands(db, job, context),
            "historic_places": lambda: self._worker_historic_places(db, job, context),
            "seismic_hazard": lambda: self._worker_seismic_hazard(db, job, context),
            "school_district": lambda: self._worker_school_district(db, job, context),
            # RapidAPI Tier 1 workers (opt-in)
            "us_real_estate": lambda: self._worker_us_real_estate(db, job, context),
            "walk_score": lambda: self._worker_walk_score(db, job, context),
            "redfin": lambda: self._worker_redfin(db, job, context),
            "rentcast": lambda: self._worker_rentcast(db, job, context),
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

    async def _worker_normalize_geocode(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        rp = db.query(ResearchProperty).filter(ResearchProperty.id == job.research_property_id).first()
        if rp is None:
            raise ValueError("Research property not found")

        unknowns: list[dict[str, Any]] = []
        errors: list[str] = []
        evidence: list[EvidenceDraft] = []
        web_calls = 0

        profile = {
            "normalized_address": rp.normalized_address,
            "geo": {"lat": rp.geo_lat, "lng": rp.geo_lng},
            "apn": rp.apn,
            "parcel_facts": {
                "sqft": None,
                "lot": None,
                "beds": None,
                "baths": None,
                "year": None,
            },
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

        evidence.append(
            EvidenceDraft(
                category="input",
                claim=f"Input address normalized to '{rp.normalized_address}'.",
                source_url="internal://input",
                raw_excerpt=rp.raw_address,
                confidence=1.0,
            )
        )

        if settings.google_places_api_key:
            try:
                suggestions = await google_places_service.autocomplete(input_text=rp.raw_address, country="us")
                web_calls += 1
                if suggestions:
                    details = await google_places_service.get_place_details(place_id=suggestions[0]["place_id"])
                    web_calls += 1
                    if details:
                        details_state = normalize_us_state_code(details.get("state"))
                        rp.city = rp.city or details.get("city")
                        rp.state = rp.state or details_state
                        rp.zip_code = rp.zip_code or details.get("zip_code")
                        rp.geo_lat = details.get("lat")
                        rp.geo_lng = details.get("lng")
                        profile["geo"] = {"lat": rp.geo_lat, "lng": rp.geo_lng}
                        evidence.append(
                            EvidenceDraft(
                                category="geocode",
                                claim="Address geocoded from Google Places details.",
                                source_url="internal://google_places/details",
                                raw_excerpt=details.get("formatted_address"),
                                confidence=0.95,
                            )
                        )
                    else:
                        unknowns.append({"field": "geo", "reason": "Place details lookup returned no result."})
                else:
                    unknowns.append({"field": "geo", "reason": "No geocoding candidates returned."})
            except Exception as exc:
                errors.append(f"Geocode lookup failed: {exc}")
        else:
            unknowns.append({"field": "geo", "reason": "GOOGLE_PLACES_API_KEY is not configured."})

        crm_property = self._find_matching_crm_property(db=db, research_property=rp)
        latest_skip_trace = None
        latest_zillow = None
        if crm_property:
            profile["parcel_facts"] = {
                "sqft": crm_property.square_feet,
                "lot": crm_property.lot_size,
                "beds": crm_property.bedrooms,
                "baths": crm_property.bathrooms,
                "year": crm_property.year_built,
            }

            evidence.append(
                EvidenceDraft(
                    category="property",
                    claim=f"Matched CRM property record #{crm_property.id} for parcel facts.",
                    source_url=f"internal://properties/{crm_property.id}",
                    raw_excerpt=f"{crm_property.address}, {crm_property.city}, {crm_property.state}",
                    confidence=0.85,
                )
            )

            skip_trace = (
                db.query(SkipTrace)
                .filter(SkipTrace.property_id == crm_property.id)
                .order_by(SkipTrace.created_at.desc())
                .first()
            )
            latest_skip_trace = skip_trace
            if skip_trace and skip_trace.owner_name:
                profile["owner_names"] = [skip_trace.owner_name]
                mailing_parts = [
                    skip_trace.mailing_address,
                    skip_trace.mailing_city,
                    skip_trace.mailing_state,
                    skip_trace.mailing_zip,
                ]
                profile["mailing_address"] = ", ".join([part for part in mailing_parts if part]) or None

                evidence.append(
                    EvidenceDraft(
                        category="owner",
                        claim="Owner name and mailing address sourced from skip trace data.",
                        source_url=f"internal://skip_traces/property/{crm_property.id}",
                        raw_excerpt=skip_trace.owner_name,
                        confidence=0.75,
                    )
                )
            else:
                unknowns.append({"field": "owner_names", "reason": "No skip trace owner data found."})

            zillow = (
                db.query(ZillowEnrichment)
                .filter(ZillowEnrichment.property_id == crm_property.id)
                .first()
            )
            latest_zillow = zillow
            if zillow:
                profile["assessed_values"] = {
                    "annual_tax_amount": zillow.annual_tax_amount,
                    "zestimate": zillow.zestimate,
                    "rent_zestimate": zillow.rent_zestimate,
                }
                profile["tax_status"] = "unknown"

                if isinstance(zillow.price_history, list):
                    for item in zillow.price_history[:8]:
                        profile["transaction_history"].append(
                            {
                                "date": item.get("date"),
                                "event": item.get("event"),
                                "amount": item.get("price"),
                                "source_url": zillow.zillow_url,
                            }
                        )

                evidence.append(
                    EvidenceDraft(
                        category="tax",
                        claim="Tax and transaction history pulled from Zillow enrichment record.",
                        source_url=zillow.zillow_url or f"internal://zillow_enrichments/{zillow.id}",
                        raw_excerpt=str(zillow.annual_tax_amount),
                        confidence=0.7,
                    )
                )
            else:
                unknowns.append({"field": "assessed_values", "reason": "No Zillow enrichment data found."})
        else:
            unknowns.append(
                {
                    "field": "parcel_facts",
                    "reason": "No matching property record in internal CRM dataset.",
                }
            )

        enrichment_max_age_hours = self._resolve_enrichment_max_age_hours(
            assumptions=job.assumptions or {},
            strict_required=bool((job.assumptions or {}).get("require_enriched_data")),
        )

        profile["enrichment_status"] = self._compute_enrichment_status(
            crm_property=crm_property,
            skip_trace=latest_skip_trace,
            zillow=latest_zillow,
            max_age_hours=enrichment_max_age_hours,
        )

        rp.latest_profile = profile
        db.commit()

        return {
            "data": {"property_profile": profile},
            "unknowns": unknowns,
            "errors": errors,
            "evidence": evidence,
            "web_calls": web_calls,
            "cost_usd": 0.0,
        }

    async def _worker_public_records(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        rp = db.query(ResearchProperty).filter(ResearchProperty.id == job.research_property_id).first()
        if rp is None:
            raise ValueError("Research property not found")

        query = f"{rp.normalized_address} assessor recorder parcel"
        results = await self.search_provider.search(query=query, max_results=5)
        results = sorted(
            results,
            key=lambda item: self._source_quality_score(item.get("url"), category="public_records"),
            reverse=True,
        )

        evidence: list[EvidenceDraft] = []
        unknowns: list[dict[str, Any]] = []

        if not results:
            unknowns.append(
                {
                    "field": "public_records",
                    "reason": "No public records hits returned by configured search provider.",
                }
            )

        for result in results:
            source_url = result.get("url", "internal://search/no-url")
            source_quality = self._source_quality_score(source_url, category="public_records")
            evidence.append(
                EvidenceDraft(
                    category="public_records",
                    claim=f"Public records candidate found: {result.get('title', 'unknown')}.",
                    source_url=source_url,
                    raw_excerpt=result.get("snippet"),
                    confidence=source_quality,
                )
            )
            result["source_quality"] = source_quality

        return {
            "data": {"public_records_hits": results},
            "unknowns": unknowns,
            "errors": [],
            "evidence": evidence,
            "web_calls": 1,
            "cost_usd": 0.0,
        }

    async def _worker_permits_violations(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        rp = db.query(ResearchProperty).filter(ResearchProperty.id == job.research_property_id).first()
        if rp is None:
            raise ValueError("Research property not found")

        query = f"{rp.normalized_address} permits violations open data"
        results = await self.search_provider.search(query=query, max_results=5)
        results = sorted(
            results,
            key=lambda item: self._source_quality_score(item.get("url"), category="permits"),
            reverse=True,
        )

        evidence: list[EvidenceDraft] = []
        unknowns: list[dict[str, Any]] = []

        if not results:
            unknowns.append(
                {
                    "field": "permits_violations",
                    "reason": "No permit or violation records returned by configured search provider.",
                }
            )

        for result in results:
            source_url = result.get("url", "internal://search/no-url")
            source_quality = self._source_quality_score(source_url, category="permits")
            evidence.append(
                EvidenceDraft(
                    category="permits",
                    claim=f"Permit/violation source candidate found: {result.get('title', 'unknown')}.",
                    source_url=source_url,
                    raw_excerpt=result.get("snippet"),
                    confidence=source_quality,
                )
            )
            result["source_quality"] = source_quality

        return {
            "data": {"permit_violation_hits": results},
            "unknowns": unknowns,
            "errors": [],
            "evidence": evidence,
            "web_calls": 1,
            "cost_usd": 0.0,
        }

    async def _worker_subdivision_research(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        rp = db.query(ResearchProperty).filter(ResearchProperty.id == job.research_property_id).first()
        if rp is None:
            raise ValueError("Research property not found")

        subdivision_goal = (job.assumptions or {}).get("subdivision_goal", "subdivide and build")
        query = (
            f"{rp.raw_address}, {rp.city or ''} {rp.state or ''} {rp.zip_code or ''} "
            f"zoning minimum lot size frontage subdivision requirements {subdivision_goal}"
        ).strip()

        results = await self.search_provider.search(query=query, max_results=8, include_text=True)
        results = sorted(
            results,
            key=lambda item: self._source_quality_score(item.get("url"), category="subdivision"),
            reverse=True,
        )
        evidence: list[EvidenceDraft] = []
        unknowns: list[dict[str, Any]] = []

        if not results:
            unknowns.append(
                {
                    "field": "subdivision_research",
                    "reason": "No subdivision sources returned by configured search provider.",
                }
            )

        for result in results[:8]:
            source_url = result.get("url", "internal://search/no-url")
            source_quality = self._source_quality_score(source_url, category="subdivision")
            evidence.append(
                EvidenceDraft(
                    category="subdivision",
                    claim=f"Subdivision source candidate found: {result.get('title', 'unknown')}.",
                    source_url=source_url,
                    raw_excerpt=(result.get("snippet") or "")[:500],
                    confidence=source_quality,
                )
            )

        summary_hits = [
            {
                "title": result.get("title"),
                "url": result.get("url"),
                "snippet": (result.get("snippet") or "")[:500],
                "source_quality": self._source_quality_score(result.get("url"), category="subdivision"),
            }
            for result in results[:8]
        ]

        return {
            "data": {
                "subdivision_research": {
                    "goal": subdivision_goal,
                    "query": query,
                    "hits": summary_hits,
                }
            },
            "unknowns": unknowns,
            "errors": [],
            "evidence": evidence,
            "web_calls": 1,
            "cost_usd": 0.0,
        }

    async def _worker_comps_sales(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
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

        rp = db.query(ResearchProperty).filter(ResearchProperty.id == job.research_property_id).first()
        if rp is None:
            raise ValueError("Research property not found")

        radius = float(
            (job.assumptions or {}).get(
                "sales_radius_mi",
                self._default_comp_radius_mi(rp.city),
            )
        )
        target_sqft = profile.get("parcel_facts", {}).get("sqft")
        target_beds = profile.get("parcel_facts", {}).get("beds")
        target_baths = profile.get("parcel_facts", {}).get("baths")

        errors: list[str] = []
        web_calls = 0

        # 1) Internal deterministic candidates (existing properties table).
        query = db.query(Property)
        if rp.state:
            query = query.filter(Property.state.ilike(rp.state))
        if rp.city:
            query = query.filter(Property.city.ilike(rp.city))

        candidates = query.limit(250).all()

        internal_selected: list[dict[str, Any]] = []
        for candidate in candidates:
            if candidate.address.strip().lower() == (rp.raw_address or "").strip().lower():
                continue

            candidate_date = (candidate.updated_at or candidate.created_at)
            candidate_sale_date = candidate_date.date() if candidate_date else None
            distance = distance_proxy_mi(
                target_zip=rp.zip_code,
                candidate_zip=candidate.zip_code,
                target_city=rp.city,
                candidate_city=candidate.city,
                target_state=rp.state,
                candidate_state=candidate.state,
            )

            if not passes_hard_filters(
                distance_mi=distance,
                radius_mi=radius,
                sale_or_list_date=candidate_sale_date,
                max_recency_months=12,
                target_sqft=target_sqft,
                candidate_sqft=candidate.square_feet,
                target_beds=target_beds,
                candidate_beds=candidate.bedrooms,
                target_baths=target_baths,
                candidate_baths=candidate.bathrooms,
            ):
                continue

            score = similarity_score(
                distance_mi=distance,
                radius_mi=radius,
                target_sqft=target_sqft,
                candidate_sqft=candidate.square_feet,
                target_beds=target_beds,
                candidate_beds=candidate.bedrooms,
                target_baths=target_baths,
                candidate_baths=candidate.bathrooms,
                sale_or_list_date=candidate_sale_date,
            )

            internal_selected.append(
                {
                    "address": f"{candidate.address}, {candidate.city}, {candidate.state} {candidate.zip_code}",
                    "distance_mi": distance,
                    "sale_date": candidate_sale_date,
                    "sale_price": candidate.price,
                    "sqft": candidate.square_feet,
                    "beds": candidate.bedrooms,
                    "baths": candidate.bathrooms,
                    "year_built": candidate.year_built,
                    "similarity_score": score,
                    "source_url": f"internal://properties/{candidate.id}",
                    "details": {
                        "property_id": candidate.id,
                        "origin": "internal_crm",
                        "source_quality": 0.95,
                    },
                }
            )

        # 2) External deterministic candidates from Exa text extraction.
        external_selected: list[dict[str, Any]] = []
        if len(internal_selected) < 8:
            external_selected, external_web_calls, external_errors = await self._build_external_comp_candidates(
                rp=rp,
                comp_type="sale",
                radius=radius,
                target_sqft=target_sqft,
                target_beds=target_beds,
                target_baths=target_baths,
                max_results=10,
                query_hint=f"{rp.city or ''} {rp.state or ''} {rp.zip_code or ''} recently sold homes",
            )
            web_calls += external_web_calls
            errors.extend(external_errors)

        selected = self._dedupe_and_rank_comps(
            comps=internal_selected + external_selected,
            top_n=8,
            date_field="sale_date",
        )

        min_sales_comps = int((job.assumptions or {}).get("min_sales_comps", 5))
        if len(selected) < min_sales_comps:
            fallback_radius = float(
                (job.assumptions or {}).get("sales_fallback_radius_mi", max(radius, 5.0))
            )
            if fallback_radius > radius:
                relaxed_external, relaxed_web_calls, relaxed_errors = await self._build_external_comp_candidates(
                    rp=rp,
                    comp_type="sale",
                    radius=fallback_radius,
                    target_sqft=target_sqft,
                    target_beds=target_beds,
                    target_baths=target_baths,
                    max_results=15,
                    query_hint=f"{rp.city or ''} {rp.state or ''} {rp.zip_code or ''} sold comps nearby",
                )
                web_calls += relaxed_web_calls
                errors.extend(relaxed_errors)
                selected = self._dedupe_and_rank_comps(
                    comps=internal_selected + external_selected + relaxed_external,
                    top_n=8,
                    date_field="sale_date",
                )

        db.query(CompSale).filter(CompSale.job_id == job.id).delete()
        for comp in selected:
            db.add(
                CompSale(
                    research_property_id=job.research_property_id,
                    job_id=job.id,
                    address=comp["address"],
                    distance_mi=comp["distance_mi"],
                    sale_date=comp["sale_date"],
                    sale_price=comp["sale_price"],
                    sqft=comp["sqft"],
                    beds=comp["beds"],
                    baths=comp["baths"],
                    year_built=comp["year_built"],
                    similarity_score=comp["similarity_score"],
                    source_url=comp["source_url"],
                    details=comp["details"],
                )
            )
        db.commit()

        evidence = [
            EvidenceDraft(
                category="comps_sales",
                claim=f"Selected sales comp: {comp['address']} with score {comp['similarity_score']:.3f}.",
                source_url=comp["source_url"],
                raw_excerpt=f"sale_price={comp.get('sale_price')}",
                confidence=max(0.5, min(0.98, float((comp.get("details") or {}).get("effective_score", comp.get("similarity_score", 0.5))))),
            )
            for comp in selected
        ]

        unknowns = []
        if not selected:
            unknowns.append(
                {
                    "field": "comps_sales",
                    "reason": "No sales comps matched hard filters (distance/recency/sqft/beds/baths).",
                }
            )
        elif len(selected) < min_sales_comps:
            unknowns.append(
                {
                    "field": "comps_sales",
                    "reason": f"Only {len(selected)} sales comps matched deterministic filters (target minimum {min_sales_comps}).",
                }
            )

        return {
            "data": {"comps_sales": selected},
            "unknowns": unknowns,
            "errors": errors,
            "evidence": evidence,
            "web_calls": web_calls,
            "cost_usd": 0.0,
        }

    async def _worker_comps_rentals(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        profile = context.get("normalize_geocode", {}).get("property_profile")
        if not profile:
            return {
                "data": {"comps_rentals": []},
                "unknowns": [{"field": "comps_rentals", "reason": "Missing property profile from prior worker."}],
                "errors": [],
                "evidence": [],
                "web_calls": 0,
                "cost_usd": 0.0,
            }

        rp = db.query(ResearchProperty).filter(ResearchProperty.id == job.research_property_id).first()
        if rp is None:
            raise ValueError("Research property not found")

        radius = float(
            (job.assumptions or {}).get(
                "rental_radius_mi",
                self._default_comp_radius_mi(rp.city),
            )
        )
        target_sqft = profile.get("parcel_facts", {}).get("sqft")
        target_beds = profile.get("parcel_facts", {}).get("beds")
        target_baths = profile.get("parcel_facts", {}).get("baths")

        errors: list[str] = []
        web_calls = 0

        # 1) Internal deterministic candidates.
        query = db.query(Property)
        if rp.state:
            query = query.filter(Property.state.ilike(rp.state))
        if rp.city:
            query = query.filter(Property.city.ilike(rp.city))

        candidates = query.limit(250).all()

        internal_selected: list[dict[str, Any]] = []
        for candidate in candidates:
            if candidate.address.strip().lower() == (rp.raw_address or "").strip().lower():
                continue

            rental_signal = None
            if candidate.status == PropertyStatus.RENTED:
                rental_signal = candidate.price

            zillow = (
                db.query(ZillowEnrichment)
                .filter(ZillowEnrichment.property_id == candidate.id)
                .first()
            )
            if zillow and zillow.rent_zestimate:
                rental_signal = zillow.rent_zestimate

            if rental_signal is None:
                continue

            candidate_date = (candidate.updated_at or candidate.created_at)
            candidate_listed_date = candidate_date.date() if candidate_date else None
            distance = distance_proxy_mi(
                target_zip=rp.zip_code,
                candidate_zip=candidate.zip_code,
                target_city=rp.city,
                candidate_city=candidate.city,
                target_state=rp.state,
                candidate_state=candidate.state,
            )

            if not passes_hard_filters(
                distance_mi=distance,
                radius_mi=radius,
                sale_or_list_date=candidate_listed_date,
                max_recency_months=12,
                target_sqft=target_sqft,
                candidate_sqft=candidate.square_feet,
                target_beds=target_beds,
                candidate_beds=candidate.bedrooms,
                target_baths=target_baths,
                candidate_baths=candidate.bathrooms,
            ):
                continue

            score = similarity_score(
                distance_mi=distance,
                radius_mi=radius,
                target_sqft=target_sqft,
                candidate_sqft=candidate.square_feet,
                target_beds=target_beds,
                candidate_beds=candidate.bedrooms,
                target_baths=target_baths,
                candidate_baths=candidate.bathrooms,
                sale_or_list_date=candidate_listed_date,
            )

            internal_selected.append(
                {
                    "address": f"{candidate.address}, {candidate.city}, {candidate.state} {candidate.zip_code}",
                    "distance_mi": distance,
                    "rent": rental_signal,
                    "date_listed": candidate_listed_date,
                    "sqft": candidate.square_feet,
                    "beds": candidate.bedrooms,
                    "baths": candidate.bathrooms,
                    "similarity_score": score,
                    "source_url": f"internal://properties/{candidate.id}",
                    "details": {
                        "property_id": candidate.id,
                        "origin": "internal_crm",
                        "source_quality": 0.95,
                    },
                }
            )

        # 2) External deterministic candidates from Exa text extraction.
        external_selected: list[dict[str, Any]] = []
        if len(internal_selected) < 8:
            external_selected, external_web_calls, external_errors = await self._build_external_comp_candidates(
                rp=rp,
                comp_type="rental",
                radius=radius,
                target_sqft=target_sqft,
                target_beds=target_beds,
                target_baths=target_baths,
                max_results=10,
                query_hint=f"{rp.city or ''} {rp.state or ''} {rp.zip_code or ''} homes for rent",
            )
            web_calls += external_web_calls
            errors.extend(external_errors)

        selected = self._dedupe_and_rank_comps(
            comps=internal_selected + external_selected,
            top_n=8,
            date_field="date_listed",
        )

        min_rental_comps = int((job.assumptions or {}).get("min_rental_comps", 5))
        if len(selected) < min_rental_comps:
            fallback_radius = float(
                (job.assumptions or {}).get("rental_fallback_radius_mi", max(radius, 5.0))
            )
            if fallback_radius > radius:
                relaxed_external, relaxed_web_calls, relaxed_errors = await self._build_external_comp_candidates(
                    rp=rp,
                    comp_type="rental",
                    radius=fallback_radius,
                    target_sqft=target_sqft,
                    target_beds=target_beds,
                    target_baths=target_baths,
                    max_results=15,
                    query_hint=f"{rp.city or ''} {rp.state or ''} {rp.zip_code or ''} homes for rent nearby",
                )
                web_calls += relaxed_web_calls
                errors.extend(relaxed_errors)
                selected = self._dedupe_and_rank_comps(
                    comps=internal_selected + external_selected + relaxed_external,
                    top_n=8,
                    date_field="date_listed",
                )

        db.query(CompRental).filter(CompRental.job_id == job.id).delete()
        for comp in selected:
            db.add(
                CompRental(
                    research_property_id=job.research_property_id,
                    job_id=job.id,
                    address=comp["address"],
                    distance_mi=comp["distance_mi"],
                    rent=comp["rent"],
                    date_listed=comp["date_listed"],
                    sqft=comp["sqft"],
                    beds=comp["beds"],
                    baths=comp["baths"],
                    similarity_score=comp["similarity_score"],
                    source_url=comp["source_url"],
                    details=comp["details"],
                )
            )
        db.commit()

        evidence = [
            EvidenceDraft(
                category="comps_rentals",
                claim=f"Selected rental comp: {comp['address']} with score {comp['similarity_score']:.3f}.",
                source_url=comp["source_url"],
                raw_excerpt=f"rent={comp.get('rent')}",
                confidence=max(0.5, min(0.98, float((comp.get("details") or {}).get("effective_score", comp.get("similarity_score", 0.5))))),
            )
            for comp in selected
        ]

        unknowns = []
        if not selected:
            unknowns.append(
                {
                    "field": "comps_rentals",
                    "reason": "No rental comps matched hard filters or had rental signal.",
                }
            )
        elif len(selected) < min_rental_comps:
            unknowns.append(
                {
                    "field": "comps_rentals",
                    "reason": f"Only {len(selected)} rental comps matched deterministic filters (target minimum {min_rental_comps}).",
                }
            )

        return {
            "data": {"comps_rentals": selected},
            "unknowns": unknowns,
            "errors": errors,
            "evidence": evidence,
            "web_calls": web_calls,
            "cost_usd": 0.0,
        }

    def _dedupe_and_rank_comps(
        self,
        comps: list[dict[str, Any]],
        top_n: int,
        date_field: str,
    ) -> list[dict[str, Any]]:
        seen: set[tuple[str, str]] = set()
        deduped: list[dict[str, Any]] = []
        for item in comps:
            key = (
                (item.get("address") or "").strip().lower(),
                (item.get("source_url") or "").strip().lower(),
            )
            if key in seen:
                continue
            seen.add(key)
            details = item.get("details") or {}
            details["effective_score"] = self._effective_comp_score(item)
            item["details"] = details
            deduped.append(item)

        return sorted(
            deduped,
            key=lambda item: (
                (item.get("details") or {}).get("effective_score", item.get("similarity_score", 0.0)),
                item.get("similarity_score", 0.0),
                item.get(date_field) or date.min,
            ),
            reverse=True,
        )[:top_n]

    async def _build_external_comp_candidates(
        self,
        rp: ResearchProperty,
        comp_type: str,
        radius: float,
        target_sqft: int | None,
        target_beds: int | None,
        target_baths: float | None,
        max_results: int,
        query_hint: str,
    ) -> tuple[list[dict[str, Any]], int, list[str]]:
        web_calls = 0
        errors: list[str] = []

        try:
            hits = await self.search_provider.search(
                query=query_hint,
                max_results=max_results,
                include_text=True,
            )
            web_calls += 1
        except Exception as exc:
            return [], web_calls, [f"External comp search failed: {exc}"]

        extracted: list[dict[str, Any]] = []
        for hit in hits:
            text_blob = " ".join(
                part
                for part in [
                    hit.get("title") or "",
                    hit.get("snippet") or "",
                    hit.get("text") or "",
                ]
                if part
            )

            for row in self._extract_comp_entries_from_text(
                text=text_blob,
                comp_type=comp_type,
                source_url=hit.get("url") or "internal://search/no-url",
                published_date=hit.get("published_date"),
            ):
                source_quality = self._source_quality_score(row.get("source_url"), category="comps")
                distance = distance_proxy_mi(
                    target_zip=rp.zip_code,
                    candidate_zip=row.get("zip_code"),
                    target_city=rp.city,
                    candidate_city=row.get("city"),
                    target_state=rp.state,
                    candidate_state=row.get("state"),
                )

                candidate_date = row.get("date")
                if not passes_hard_filters(
                    distance_mi=distance,
                    radius_mi=radius,
                    sale_or_list_date=candidate_date,
                    max_recency_months=12,
                    target_sqft=target_sqft,
                    candidate_sqft=row.get("sqft"),
                    target_beds=target_beds,
                    candidate_beds=row.get("beds"),
                    target_baths=target_baths,
                    candidate_baths=row.get("baths"),
                ):
                    continue

                score = similarity_score(
                    distance_mi=distance,
                    radius_mi=radius,
                    target_sqft=target_sqft,
                    candidate_sqft=row.get("sqft"),
                    target_beds=target_beds,
                    candidate_beds=row.get("beds"),
                    target_baths=target_baths,
                    candidate_baths=row.get("baths"),
                    sale_or_list_date=candidate_date,
                )

                if comp_type == "sale":
                    extracted.append(
                        {
                            "address": row.get("address"),
                            "distance_mi": distance,
                            "sale_date": candidate_date,
                            "sale_price": row.get("price"),
                            "sqft": row.get("sqft"),
                            "beds": row.get("beds"),
                            "baths": row.get("baths"),
                            "year_built": None,
                            "similarity_score": score,
                            "source_url": row.get("source_url"),
                            "details": {
                                "origin": "external_exa",
                                "source_quality": source_quality,
                            },
                        }
                    )
                else:
                    extracted.append(
                        {
                            "address": row.get("address"),
                            "distance_mi": distance,
                            "rent": row.get("price"),
                            "date_listed": candidate_date,
                            "sqft": row.get("sqft"),
                            "beds": row.get("beds"),
                            "baths": row.get("baths"),
                            "similarity_score": score,
                            "source_url": row.get("source_url"),
                            "details": {
                                "origin": "external_exa",
                                "source_quality": source_quality,
                            },
                        }
                    )

        return extracted, web_calls, errors

    def _extract_comp_entries_from_text(
        self,
        text: str,
        comp_type: str,
        source_url: str,
        published_date: str | None,
    ) -> list[dict[str, Any]]:
        if not text:
            return []

        published = self._parse_date_safe(published_date)
        address_pattern = re.compile(
            r"(?P<address>\d{1,6}\s+[A-Za-z0-9 .#-]+,\s*[A-Za-z .-]+,\s*[A-Z]{2}\s*\d{5})"
        )
        matches = list(address_pattern.finditer(text))
        if not matches:
            return []

        rows: list[dict[str, Any]] = []
        for match in matches[:40]:
            address = match.group("address").strip()
            address = re.sub(r"^(?:19|20)\d{2}\s+(\d{1,6}\s+.+)$", r"\1", address)
            parsed = self._parse_address_components(address)
            if not parsed:
                continue

            window_after = text[match.end(): min(len(text), match.end() + 260)]
            window = text[max(0, match.start() - 120): min(len(text), match.end() + 260)]
            price = self._extract_price(window_after, comp_type=comp_type) or self._extract_price(window, comp_type=comp_type)
            beds = self._extract_int(window_after, r"(\d{1,2})\s*(?:bds?|beds?)") or self._extract_int(window, r"(\d{1,2})\s*(?:bds?|beds?)")
            baths = self._extract_float(window_after, r"(\d{1,2}(?:\.\d+)?)\s*(?:ba|baths?)") or self._extract_float(window, r"(\d{1,2}(?:\.\d+)?)\s*(?:ba|baths?)")
            sqft = self._extract_int(window_after, r"([0-9][0-9,]{2,})\s*(?:sq\s*ft|sqft)") or self._extract_int(window, r"([0-9][0-9,]{2,})\s*(?:sq\s*ft|sqft)")

            candidate_date = self._extract_relative_zillow_days(window_after) or self._extract_date_from_text(window_after) or self._extract_relative_zillow_days(window) or self._extract_date_from_text(window) or published
            if candidate_date is None:
                continue
            if price is None:
                continue

            rows.append(
                {
                    "address": address,
                    "city": parsed["city"],
                    "state": parsed["state"],
                    "zip_code": parsed["zip_code"],
                    "price": price,
                    "beds": beds,
                    "baths": baths,
                    "sqft": sqft,
                    "date": candidate_date,
                    "source_url": source_url,
                }
            )

        return rows

    def _parse_address_components(self, full_address: str) -> dict[str, str] | None:
        m = re.match(r"^(.+?),\s*([^,]+),\s*([A-Z]{2})\s*(\d{5})$", full_address.strip())
        if not m:
            return None
        return {
            "street": m.group(1).strip(),
            "city": m.group(2).strip(),
            "state": m.group(3).strip(),
            "zip_code": m.group(4).strip(),
        }

    def _extract_int(self, text: str, pattern: str) -> int | None:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if not m:
            return None
        try:
            return int(m.group(1).replace(",", ""))
        except Exception:
            return None

    def _extract_float(self, text: str, pattern: str) -> float | None:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if not m:
            return None
        try:
            return float(m.group(1))
        except Exception:
            return None

    def _extract_price(self, text: str, comp_type: str) -> float | None:
        if comp_type == "rental":
            rent_match = re.search(r"\$\s*([0-9][0-9,]{2,})\s*(?:/\s*mo|/mo|per\s*month)", text, flags=re.IGNORECASE)
            if rent_match:
                return float(rent_match.group(1).replace(",", ""))

        price_values = [
            float(value.replace(",", ""))
            for value in re.findall(r"\$\s*([0-9][0-9,]{2,})", text)
        ]
        if not price_values:
            return None

        if comp_type == "rental":
            # Rental signals are typically in lower ranges.
            rental_prices = [value for value in price_values if value <= 15000]
            return rental_prices[0] if rental_prices else None

        sale_prices = [value for value in price_values if value >= 50000]
        return sale_prices[0] if sale_prices else None

    def _extract_relative_zillow_days(self, text: str) -> date | None:
        m = re.search(r"(\d{1,3})\s+days\s+on\s+zillow", text, flags=re.IGNORECASE)
        if not m:
            return None
        try:
            days = int(m.group(1))
            return date.today() - timedelta(days=days)
        except Exception:
            return None

    def _extract_date_from_text(self, text: str) -> date | None:
        m = re.search(
            r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{4})",
            text,
            flags=re.IGNORECASE,
        )
        if not m:
            return None
        return self._parse_date_safe(m.group(1))

    def _parse_date_safe(self, value: str | None) -> date | None:
        if not value:
            return None
        try:
            return date_parser.parse(value).date()
        except Exception:
            return None

    async def _worker_underwriting(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        assumptions = job.assumptions or {}

        profile = context.get("normalize_geocode", {}).get("property_profile", {})
        sales = context.get("comps_sales", {}).get("comps_sales", [])
        rentals = context.get("comps_rentals", {}).get("comps_rentals", [])

        sale_prices = [float(item["sale_price"]) for item in sales if item.get("sale_price") is not None]
        rents = [float(item["rent"]) for item in rentals if item.get("rent") is not None]

        arv_base = mean(sale_prices) if sale_prices else None
        arv_low = (arv_base * 0.9) if arv_base is not None else None
        arv_high = (arv_base * 1.1) if arv_base is not None else None

        rent_base = mean(rents) if rents else None
        rent_low = (rent_base * 0.9) if rent_base is not None else None
        rent_high = (rent_base * 1.1) if rent_base is not None else None

        rehab_tier = assumptions.get("rehab_tier", "medium")
        if rehab_tier not in {"light", "medium", "heavy"}:
            rehab_tier = "medium"

        sqft = profile.get("parcel_facts", {}).get("sqft")
        rehab_per_sqft = {"light": 15.0, "medium": 35.0, "heavy": 60.0}[rehab_tier]
        rehab_base = float(sqft * rehab_per_sqft) if sqft else None
        rehab_low = (rehab_base * 0.8) if rehab_base is not None else None
        rehab_high = (rehab_base * 1.2) if rehab_base is not None else None

        fees = {
            "closing": float(assumptions.get("closing_cost", 5000.0)),
            "holding": float(assumptions.get("holding_cost", 3000.0)),
            "assignment": float(assumptions.get("assignment_fee", 10000.0 if job.strategy == "wholesale" else 0.0)),
            "misc": float(assumptions.get("misc_fee", 1500.0)),
        }
        total_fees = sum(fees.values())

        offer_base: float | None = None
        if arv_base is not None:
            if job.strategy == "wholesale":
                offer_base = (arv_base * 0.70) - (rehab_high or 0.0) - total_fees
            elif job.strategy == "flip":
                target_margin = float(assumptions.get("target_margin", 0.20))
                offer_base = (arv_base * (1.0 - target_margin)) - (rehab_base or 0.0) - total_fees
            else:
                rent_cap = (rent_base * 100.0) if rent_base is not None else arv_base * 0.75
                offer_base = min(arv_base * 0.80, rent_cap) - (rehab_base or 0.0) - total_fees

        offer_low = (offer_base * 0.9) if offer_base is not None else None
        offer_high = (offer_base * 1.1) if offer_base is not None else None

        underwrite = {
            "arv_estimate": {"low": arv_low, "base": arv_base, "high": arv_high},
            "rent_estimate": {"low": rent_low, "base": rent_base, "high": rent_high},
            "rehab_tier": rehab_tier,
            "rehab_estimated_range": {"low": rehab_low, "base": rehab_base, "high": rehab_high},
            "offer_price_recommendation": {"low": offer_low, "base": offer_base, "high": offer_high},
            "fees": fees,
            "sensitivity_table": [
                {
                    "scenario": "conservative",
                    "arv_multiplier": 0.95,
                    "rent_multiplier": 0.95,
                    "offer_adjustment": -0.08,
                },
                {
                    "scenario": "base",
                    "arv_multiplier": 1.0,
                    "rent_multiplier": 1.0,
                    "offer_adjustment": 0.0,
                },
                {
                    "scenario": "optimistic",
                    "arv_multiplier": 1.05,
                    "rent_multiplier": 1.05,
                    "offer_adjustment": 0.08,
                },
            ],
        }

        evidence = [
            EvidenceDraft(
                category="underwriting",
                claim="Underwriting calculations generated deterministically from comps and configured assumptions.",
                source_url=f"internal://agentic_jobs/{job.id}/underwriting",
                raw_excerpt=f"strategy={job.strategy}",
                confidence=1.0,
            )
        ]

        unknowns = []
        if arv_base is None:
            unknowns.append({"field": "arv_estimate", "reason": "No qualified sales comps available."})
        if rent_base is None:
            unknowns.append({"field": "rent_estimate", "reason": "No qualified rental comps available."})

        db.query(Underwriting).filter(Underwriting.job_id == job.id).delete()
        db.add(
            Underwriting(
                research_property_id=job.research_property_id,
                job_id=job.id,
                strategy=job.strategy,
                assumptions=assumptions,
                arv_low=arv_low,
                arv_base=arv_base,
                arv_high=arv_high,
                rent_low=rent_low,
                rent_base=rent_base,
                rent_high=rent_high,
                rehab_tier=rehab_tier,
                rehab_low=rehab_low,
                rehab_high=rehab_high,
                offer_low=offer_low,
                offer_base=offer_base,
                offer_high=offer_high,
                fees=fees,
                sensitivity=underwrite["sensitivity_table"],
            )
        )

        # Expert-style risk score derived from coverage, source quality and contradiction checks.
        evidence_rows = db.query(EvidenceItem).filter(EvidenceItem.job_id == job.id).all()
        evidence_count = len(evidence_rows)
        coverage = min(1.0, evidence_count / 12.0)
        evidence_confidences = [float(item.confidence) for item in evidence_rows if item.confidence is not None]
        mean_evidence_confidence = mean(evidence_confidences) if evidence_confidences else 0.5
        quality_adjustment = (mean_evidence_confidence - 0.5) * 0.4

        unknown_penalty = min(0.6, len(unknowns) * 0.1)
        contradiction_penalty = 0.0
        title_risk = 0.75 if not profile.get("owner_names") else 0.35

        compliance_flags = []
        if not profile.get("owner_names"):
            compliance_flags.append("owner_not_verified")
        if not sales:
            compliance_flags.append("insufficient_sales_comps")
        if not rentals:
            compliance_flags.append("insufficient_rental_comps")

        valuation_conflict_threshold = float(assumptions.get("valuation_conflict_threshold", 0.30))
        zestimate = (profile.get("assessed_values") or {}).get("zestimate")
        if arv_base is not None and zestimate is not None:
            denom = max(abs(float(zestimate)), 1.0)
            diff_ratio = abs(float(arv_base) - float(zestimate)) / denom
            if diff_ratio > valuation_conflict_threshold:
                compliance_flags.append("valuation_conflict_zestimate_vs_comps")
                contradiction_penalty += 0.12

        rent_zestimate = (profile.get("assessed_values") or {}).get("rent_zestimate")
        if rent_base is not None and rent_zestimate is not None:
            denom = max(abs(float(rent_zestimate)), 1.0)
            diff_ratio = abs(float(rent_base) - float(rent_zestimate)) / denom
            if diff_ratio > valuation_conflict_threshold:
                compliance_flags.append("rent_conflict_zestimate_vs_comps")
                contradiction_penalty += 0.10

        data_confidence = max(
            0.0,
            min(1.0, coverage - unknown_penalty + 0.25 + quality_adjustment - contradiction_penalty),
        )

        risk_score = {
            "title_risk": round(title_risk, 3),
            "data_confidence": round(data_confidence, 3),
            "compliance_flags": compliance_flags,
            "notes": (
                "Risk score combines deterministic coverage, evidence quality, and cross-source "
                "contradiction checks."
            ),
        }

        db.query(RiskScore).filter(RiskScore.job_id == job.id).delete()
        db.add(
            RiskScore(
                research_property_id=job.research_property_id,
                job_id=job.id,
                title_risk=risk_score["title_risk"],
                data_confidence=risk_score["data_confidence"],
                compliance_flags=risk_score["compliance_flags"],
                notes=risk_score["notes"],
            )
        )
        db.commit()

        return {
            "data": {"underwrite": underwrite, "risk_score": risk_score},
            "unknowns": unknowns,
            "errors": [],
            "evidence": evidence,
            "web_calls": 0,
            "cost_usd": 0.0,
        }

    # ── NEW: Neighborhood Intelligence Worker ──
    async def _worker_neighborhood_intel(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        """Search for neighborhood data: crime, schools, demographics, walkability, trends."""
        profile = context.get("normalize_geocode", {}).get("property_profile", {})
        address = profile.get("normalized_address", "")
        geo = profile.get("geo", {})
        evidence: list[EvidenceDraft] = []
        web_calls = 0

        # Extract city/state for neighborhood queries
        parts = [p.strip() for p in address.split(",")]
        city = parts[1] if len(parts) > 1 else ""
        state = parts[2].split()[0] if len(parts) > 2 else ""
        location = f"{city}, {state}".strip(", ")

        neighborhood_data: dict[str, Any] = {
            "crime": [],
            "schools": [],
            "demographics": [],
            "market_trends": [],
            "walkability": [],
        }

        search = build_search_provider_from_settings()

        # Search 1: Crime & safety
        if location:
            crime_results = await search.search(
                query=f"{location} crime rate safety statistics neighborhood",
                max_results=5,
                include_text=True,
            )
            web_calls += 1
            for r in crime_results:
                neighborhood_data["crime"].append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("snippet", "")[:300],
                })
                evidence.append(EvidenceDraft(
                    category="neighborhood",
                    claim=f"Crime/safety data: {r.get('title', 'unknown')}",
                    source_url=r.get("url", ""),
                    raw_excerpt=r.get("snippet", "")[:300],
                    confidence=self._source_quality(r.get("url", "")),
                ))

        # Search 2: Schools & demographics
        if location:
            school_results = await search.search(
                query=f"{location} school ratings demographics population income median home value",
                max_results=5,
                include_text=True,
            )
            web_calls += 1
            for r in school_results:
                neighborhood_data["schools"].append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("snippet", "")[:300],
                })
                evidence.append(EvidenceDraft(
                    category="neighborhood",
                    claim=f"School/demographic data: {r.get('title', 'unknown')}",
                    source_url=r.get("url", ""),
                    raw_excerpt=r.get("snippet", "")[:300],
                    confidence=self._source_quality(r.get("url", "")),
                ))

        # Search 3: Market trends & gentrification
        if location:
            trend_results = await search.search(
                query=f"{location} real estate market trends 2025 2026 home prices appreciation inventory",
                max_results=5,
                include_text=True,
            )
            web_calls += 1
            for r in trend_results:
                neighborhood_data["market_trends"].append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("snippet", "")[:300],
                })
                evidence.append(EvidenceDraft(
                    category="neighborhood",
                    claim=f"Market trend data: {r.get('title', 'unknown')}",
                    source_url=r.get("url", ""),
                    raw_excerpt=r.get("snippet", "")[:300],
                    confidence=self._source_quality(r.get("url", "")),
                ))

        # Use Claude to synthesize if available
        ai_summary = None
        cost_usd = 0.0
        if settings.anthropic_api_key and any(
            neighborhood_data[k] for k in neighborhood_data
        ):
            try:
                from app.services.llm_service import llm_service as _llm

                snippets_text = ""
                for category, items in neighborhood_data.items():
                    if items:
                        snippets_text += f"\n### {category.upper()}\n"
                        for item in items[:3]:
                            snippets_text += f"- {item['title']}: {item['snippet']}\n"

                ai_summary = _llm.generate(
                    f"""You are a real estate investment analyst. Based on these neighborhood data snippets for {location}, write a concise neighborhood analysis (150-250 words). Cover: safety, schools, demographics, market trends, and overall investment outlook. Be specific with any numbers or ratings found. If data is sparse, note what's missing.

{snippets_text}

Write the analysis as prose paragraphs, not bullet points. Focus on what matters for a real estate investor.""",
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=600,
                )
                cost_usd = 0.01  # Approximate Sonnet cost
            except Exception as e:
                ai_summary = None
                logging.warning(f"Claude neighborhood synthesis failed: {e}")

        neighborhood_data["ai_summary"] = ai_summary

        return {
            "data": {"neighborhood_intel": neighborhood_data},
            "unknowns": [{"field": "neighborhood", "reason": "No location data"}] if not location else [],
            "errors": [],
            "evidence": evidence,
            "web_calls": web_calls,
            "cost_usd": cost_usd,
        }

    # ── NEW: FEMA Flood Zone Worker ──
    async def _worker_flood_zone(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        """Check FEMA flood zone data using free FEMA API."""
        profile = context.get("normalize_geocode", {}).get("property_profile", {})
        geo = profile.get("geo", {})
        lat = geo.get("lat")
        lng = geo.get("lng")
        evidence: list[EvidenceDraft] = []

        flood_data: dict[str, Any] = {
            "flood_zone": None,
            "description": None,
            "panel_number": None,
            "in_floodplain": None,
            "insurance_required": None,
            "source": "FEMA National Flood Hazard Layer",
        }

        if not lat or not lng:
            return {
                "data": {"flood_zone": flood_data},
                "unknowns": [{"field": "flood_zone", "reason": "No geocode available for FEMA lookup"}],
                "errors": [],
                "evidence": [],
                "web_calls": 0,
                "cost_usd": 0.0,
            }

        web_calls = 0
        try:
            # FEMA National Flood Hazard Layer (NFHL) ArcGIS REST API
            # This is the official free FEMA endpoint
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query",
                    params={
                        "geometry": f"{lng},{lat}",
                        "geometryType": "esriGeometryPoint",
                        "inSR": "4326",
                        "spatialRel": "esriSpatialRelIntersects",
                        "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF,STATIC_BFE,DFIRM_ID",
                        "returnGeometry": "false",
                        "f": "json",
                    },
                    timeout=15.0,
                )
                web_calls += 1
                response.raise_for_status()
                data = response.json()

                features = data.get("features", [])
                if features:
                    attrs = features[0].get("attributes", {})
                    zone = attrs.get("FLD_ZONE", "")
                    zone_subtype = attrs.get("ZONE_SUBTY", "")
                    sfha = attrs.get("SFHA_TF", "")

                    # Decode flood zone
                    zone_descriptions = {
                        "A": "High risk - 1% annual chance flood (100-year floodplain)",
                        "AE": "High risk - 1% annual chance flood with base flood elevations",
                        "AH": "High risk - 1% annual chance of shallow flooding (1-3 ft)",
                        "AO": "High risk - 1% annual chance of sheet flow flooding",
                        "V": "High risk - coastal flood with wave action",
                        "VE": "High risk - coastal flood with base flood elevations",
                        "X": "Moderate to low risk - 0.2% annual chance flood (500-year) or minimal",
                        "B": "Moderate risk - between 100-year and 500-year floodplain",
                        "C": "Minimal risk - outside 500-year floodplain",
                        "D": "Undetermined risk - possible but not analyzed",
                    }

                    is_high_risk = zone in ("A", "AE", "AH", "AO", "AR", "V", "VE")
                    description = zone_descriptions.get(zone, f"Zone {zone}")
                    if zone_subtype:
                        description += f" ({zone_subtype})"

                    flood_data["flood_zone"] = zone
                    flood_data["description"] = description
                    flood_data["panel_number"] = attrs.get("DFIRM_ID")
                    flood_data["in_floodplain"] = is_high_risk
                    flood_data["insurance_required"] = is_high_risk

                    evidence.append(EvidenceDraft(
                        category="flood_zone",
                        claim=f"FEMA flood zone: {zone} - {description}. Insurance {'required' if is_high_risk else 'not required'}.",
                        source_url=f"https://msc.fema.gov/portal/search?AddressQuery={lat},{lng}",
                        raw_excerpt=f"FLD_ZONE={zone}, SFHA_TF={sfha}, ZONE_SUBTY={zone_subtype}",
                        confidence=0.95,
                    ))
                else:
                    flood_data["flood_zone"] = "X"
                    flood_data["description"] = "No FEMA data — likely minimal flood risk"
                    flood_data["in_floodplain"] = False
                    flood_data["insurance_required"] = False

                    evidence.append(EvidenceDraft(
                        category="flood_zone",
                        claim="No FEMA flood zone data found for this location — likely minimal risk.",
                        source_url=f"https://msc.fema.gov/portal/search?AddressQuery={lat},{lng}",
                        raw_excerpt="No features returned from NFHL query",
                        confidence=0.80,
                    ))

        except Exception as e:
            logging.warning(f"FEMA flood zone lookup failed: {e}")
            return {
                "data": {"flood_zone": flood_data},
                "unknowns": [{"field": "flood_zone", "reason": f"FEMA API error: {str(e)[:100]}"}],
                "errors": [str(e)],
                "evidence": [],
                "web_calls": web_calls,
                "cost_usd": 0.0,
            }

        return {
            "data": {"flood_zone": flood_data},
            "unknowns": [],
            "errors": [],
            "evidence": evidence,
            "web_calls": web_calls,
            "cost_usd": 0.0,
        }

    # ── EXTENSIVE RESEARCH WORKERS (opt-in via extra_agents: ["extensive"]) ──

    async def _worker_epa_environmental(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        """Check EPA environmental hazards: Superfund, brownfields, toxic releases, hazardous waste within 5 miles (8047m)."""
        profile = context.get("normalize_geocode", {}).get("property_profile", {})
        geo = profile.get("geo", {})
        lat, lng = geo.get("lat"), geo.get("lng")
        evidence: list[EvidenceDraft] = []
        web_calls = 0

        epa_data: dict[str, Any] = {
            "superfund_sites": [],
            "brownfields": [],
            "toxic_releases": [],
            "hazardous_waste": [],
            "nearest_hazard_miles": None,
            "risk_summary": None,
        }

        if not lat or not lng:
            return {"data": {"epa_environmental": epa_data}, "unknowns": [{"field": "epa", "reason": "No geocode"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

        base_url = "https://geopub.epa.gov/arcgis/rest/services/EMEF/efpoints/MapServer"
        base_params = {
            "geometry": f"{lng},{lat}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "distance": "8047",
            "units": "esriSRUnit_Meter",
            "outFields": "primary_name,location_address,city_name,state_code,registry_id",
            "returnGeometry": "false",
            "f": "json",
        }

        layers = [
            (0, "superfund_sites", "Superfund (NPL) site"),
            (5, "brownfields", "Brownfield site"),
            (1, "toxic_releases", "Toxic Release Inventory facility"),
            (4, "hazardous_waste", "Hazardous waste handler"),
        ]

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                for layer_id, key, label in layers:
                    resp = await client.get(f"{base_url}/{layer_id}/query", params=base_params)
                    web_calls += 1
                    resp.raise_for_status()
                    features = resp.json().get("features", [])
                    for feat in features[:10]:
                        attrs = feat.get("attributes", {})
                        site = {
                            "name": attrs.get("primary_name", "Unknown"),
                            "address": attrs.get("location_address", ""),
                            "city": attrs.get("city_name", ""),
                            "state": attrs.get("state_code", ""),
                        }
                        epa_data[key].append(site)
                        evidence.append(EvidenceDraft(
                            category="environmental",
                            claim=f"{label} within 5 miles: {site['name']}",
                            source_url=f"https://enviro.epa.gov/enviro/epa_home.aspx",
                            raw_excerpt=f"{site['name']} at {site['address']}, {site['city']}, {site['state']}",
                            confidence=0.95,
                        ))
        except Exception as e:
            logging.warning(f"EPA environmental lookup failed: {e}")
            return {"data": {"epa_environmental": epa_data}, "unknowns": [], "errors": [str(e)], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

        total_hazards = sum(len(epa_data[k]) for k in ["superfund_sites", "brownfields", "toxic_releases", "hazardous_waste"])
        if total_hazards == 0:
            epa_data["risk_summary"] = "No EPA environmental hazards found within 5 miles"
        else:
            parts = []
            if epa_data["superfund_sites"]:
                parts.append(f"{len(epa_data['superfund_sites'])} Superfund sites")
            if epa_data["brownfields"]:
                parts.append(f"{len(epa_data['brownfields'])} brownfields")
            if epa_data["toxic_releases"]:
                parts.append(f"{len(epa_data['toxic_releases'])} toxic release facilities")
            if epa_data["hazardous_waste"]:
                parts.append(f"{len(epa_data['hazardous_waste'])} hazardous waste handlers")
            epa_data["risk_summary"] = f"WARNING: {', '.join(parts)} within 5 miles"

        return {"data": {"epa_environmental": epa_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

    async def _worker_wildfire_hazard(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        """Check USFS wildfire hazard potential (2023 dataset)."""
        profile = context.get("normalize_geocode", {}).get("property_profile", {})
        geo = profile.get("geo", {})
        lat, lng = geo.get("lat"), geo.get("lng")
        evidence: list[EvidenceDraft] = []

        wildfire_data: dict[str, Any] = {"hazard_level": None, "hazard_value": None, "description": None}

        if not lat or not lng:
            return {"data": {"wildfire_hazard": wildfire_data}, "unknowns": [{"field": "wildfire", "reason": "No geocode"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # USFS raster layer — use identify operation
                resp = await client.get(
                    "https://apps.fs.usda.gov/arcx/rest/services/RDW_Wildfire/RMRS_WildfireHazardPotential_2023/MapServer/identify",
                    params={
                        "geometry": f"{lng},{lat}",
                        "geometryType": "esriGeometryPoint",
                        "sr": "4326",
                        "tolerance": "1",
                        "mapExtent": f"{lng-1},{lat-1},{lng+1},{lat+1}",
                        "imageDisplay": "600,550,96",
                        "returnGeometry": "false",
                        "f": "json",
                    },
                )
                resp.raise_for_status()
                results = resp.json().get("results", [])
                if results:
                    attrs = results[0].get("attributes", {})
                    class_desc = attrs.get("class_desc", attrs.get("Classname", ""))
                    value = attrs.get("VALUE", attrs.get("Pixel Value", ""))

                    level_map = {"1": "Very Low", "2": "Low", "3": "Moderate", "4": "High", "5": "Very High", "6": "Non-burnable"}
                    level = level_map.get(str(value), class_desc.split(":")[-1].strip() if ":" in str(class_desc) else str(class_desc))

                    wildfire_data["hazard_level"] = level
                    wildfire_data["hazard_value"] = int(value) if str(value).isdigit() else None

                    is_high = level in ("High", "Very High")
                    wildfire_data["description"] = f"Wildfire hazard: {level}" + (" — may affect insurance availability" if is_high else "")

                    evidence.append(EvidenceDraft(
                        category="wildfire",
                        claim=f"USFS wildfire hazard potential: {level}",
                        source_url="https://www.firelab.org/project/wildfire-hazard-potential",
                        raw_excerpt=f"class_desc={class_desc}, VALUE={value}",
                        confidence=0.90,
                    ))
                else:
                    wildfire_data["hazard_level"] = "Unknown"
                    wildfire_data["description"] = "No USFS wildfire data available for this location"

        except Exception as e:
            logging.warning(f"Wildfire hazard lookup failed: {e}")
            return {"data": {"wildfire_hazard": wildfire_data}, "unknowns": [], "errors": [str(e)], "evidence": [], "web_calls": 1, "cost_usd": 0.0}

        return {"data": {"wildfire_hazard": wildfire_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": 1, "cost_usd": 0.0}

    async def _worker_hud_opportunity(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        """Get HUD Opportunity Indices: school proficiency, jobs, poverty, transit, labor, env health."""
        profile = context.get("normalize_geocode", {}).get("property_profile", {})
        geo = profile.get("geo", {})
        lat, lng = geo.get("lat"), geo.get("lng")
        evidence: list[EvidenceDraft] = []
        web_calls = 0

        hud_data: dict[str, Any] = {
            "school_proficiency_index": None,
            "jobs_proximity_index": None,
            "poverty_index": None,
            "transit_index": None,
            "labor_market_index": None,
            "environmental_health_index": None,
            "transportation_cost_index": None,
        }

        if not lat or not lng:
            return {"data": {"hud_opportunity": hud_data}, "unknowns": [{"field": "hud", "reason": "No geocode"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

        base_params = {
            "geometry": f"{lng},{lat}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "returnGeometry": "false",
            "f": "json",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Layer 13: Block group level (school + jobs)
                resp1 = await client.get(
                    "https://egis.hud.gov/arcgis/rest/services/affht/AffhtMapService/MapServer/13/query",
                    params={**base_params, "outFields": "SCHL_IDX,JOBS_IDX"},
                )
                web_calls += 1
                resp1.raise_for_status()
                feats1 = resp1.json().get("features", [])
                if feats1:
                    attrs = feats1[0].get("attributes", {})
                    hud_data["school_proficiency_index"] = attrs.get("SCHL_IDX")
                    hud_data["jobs_proximity_index"] = attrs.get("JOBS_IDX")

                # Layer 23: Tract level (poverty, transit, labor, env, transport cost)
                resp2 = await client.get(
                    "https://egis.hud.gov/arcgis/rest/services/affht/AffhtMapService/MapServer/23/query",
                    params={**base_params, "outFields": "POV_IDX,LBR_IDX,HAZ_IDX,TCOST_IDX,TRANS_IDX"},
                )
                web_calls += 1
                resp2.raise_for_status()
                feats2 = resp2.json().get("features", [])
                if feats2:
                    attrs = feats2[0].get("attributes", {})
                    hud_data["poverty_index"] = attrs.get("POV_IDX")
                    hud_data["labor_market_index"] = attrs.get("LBR_IDX")
                    hud_data["environmental_health_index"] = attrs.get("HAZ_IDX")
                    hud_data["transportation_cost_index"] = attrs.get("TCOST_IDX")
                    hud_data["transit_index"] = attrs.get("TRANS_IDX")

                # Build evidence
                scored = {k: v for k, v in hud_data.items() if v is not None}
                if scored:
                    summary = ", ".join(f"{k.replace('_', ' ').title()}: {v}/100" for k, v in scored.items())
                    evidence.append(EvidenceDraft(
                        category="opportunity_index",
                        claim=f"HUD Opportunity Indices: {summary}",
                        source_url="https://egis.hud.gov/affht/",
                        raw_excerpt=str(scored),
                        confidence=0.95,
                    ))

        except Exception as e:
            logging.warning(f"HUD opportunity index lookup failed: {e}")
            return {"data": {"hud_opportunity": hud_data}, "unknowns": [], "errors": [str(e)], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

        return {"data": {"hud_opportunity": hud_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

    async def _worker_wetlands(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        """Check USFWS National Wetlands Inventory."""
        profile = context.get("normalize_geocode", {}).get("property_profile", {})
        geo = profile.get("geo", {})
        lat, lng = geo.get("lat"), geo.get("lng")
        evidence: list[EvidenceDraft] = []

        wetlands_data: dict[str, Any] = {"wetlands_found": False, "wetlands": [], "development_restricted": False}

        if not lat or not lng:
            return {"data": {"wetlands": wetlands_data}, "unknowns": [{"field": "wetlands", "reason": "No geocode"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest/services/Wetlands/MapServer/identify",
                    params={
                        "geometry": f"{lng},{lat}",
                        "geometryType": "esriGeometryPoint",
                        "sr": "4326",
                        "tolerance": "10",
                        "mapExtent": f"{lng-0.01},{lat-0.01},{lng+0.01},{lat+0.01}",
                        "imageDisplay": "600,550,96",
                        "returnGeometry": "false",
                        "f": "json",
                    },
                )
                resp.raise_for_status()
                results = resp.json().get("results", [])
                for r in results[:5]:
                    attrs = r.get("attributes", {})
                    wetland = {
                        "type": attrs.get("WETLAND_TYPE", "Unknown"),
                        "acres": attrs.get("ACRES"),
                        "classification": attrs.get("ATTRIBUTE", ""),
                        "system": attrs.get("SYSTEM_NAME", ""),
                        "water_regime": attrs.get("WATER_REGIME_NAME", ""),
                    }
                    wetlands_data["wetlands"].append(wetland)
                    evidence.append(EvidenceDraft(
                        category="wetlands",
                        claim=f"Wetland present: {wetland['type']} ({wetland['acres']} acres, {wetland['system']})",
                        source_url="https://www.fws.gov/program/national-wetlands-inventory",
                        raw_excerpt=f"ATTRIBUTE={wetland['classification']}, WATER_REGIME={wetland['water_regime']}",
                        confidence=0.90,
                    ))

                if wetlands_data["wetlands"]:
                    wetlands_data["wetlands_found"] = True
                    wetlands_data["development_restricted"] = True

        except Exception as e:
            logging.warning(f"Wetlands lookup failed: {e}")
            return {"data": {"wetlands": wetlands_data}, "unknowns": [], "errors": [str(e)], "evidence": [], "web_calls": 1, "cost_usd": 0.0}

        return {"data": {"wetlands": wetlands_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": 1, "cost_usd": 0.0}

    async def _worker_historic_places(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        """Check National Register of Historic Places within 1 mile."""
        profile = context.get("normalize_geocode", {}).get("property_profile", {})
        geo = profile.get("geo", {})
        lat, lng = geo.get("lat"), geo.get("lng")
        evidence: list[EvidenceDraft] = []

        historic_data: dict[str, Any] = {"in_historic_district": False, "nearby_places": [], "renovation_restricted": False, "tax_credit_eligible": False}

        if not lat or not lng:
            return {"data": {"historic_places": historic_data}, "unknowns": [{"field": "historic", "reason": "No geocode"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://mapservices.nps.gov/arcgis/rest/services/cultural_resources/nrhp_locations/MapServer/0/query",
                    params={
                        "geometry": f"{lng},{lat}",
                        "geometryType": "esriGeometryPoint",
                        "inSR": "4326",
                        "spatialRel": "esriSpatialRelIntersects",
                        "distance": "1609",
                        "units": "esriSRUnit_Meter",
                        "outFields": "RESNAME,ResType,Address,City,State,County,Is_NHL",
                        "returnGeometry": "false",
                        "f": "json",
                    },
                )
                resp.raise_for_status()
                features = resp.json().get("features", [])
                for feat in features[:10]:
                    attrs = feat.get("attributes", {})
                    place = {
                        "name": attrs.get("RESNAME", "Unknown"),
                        "type": attrs.get("ResType", ""),
                        "address": attrs.get("Address", ""),
                        "city": attrs.get("City", ""),
                        "state": attrs.get("State", ""),
                        "is_landmark": attrs.get("Is_NHL") == "Y",
                    }
                    historic_data["nearby_places"].append(place)

                    if place["type"] == "district":
                        historic_data["in_historic_district"] = True
                        historic_data["renovation_restricted"] = True
                        historic_data["tax_credit_eligible"] = True

                    evidence.append(EvidenceDraft(
                        category="historic",
                        claim=f"National Register: {place['name']} ({place['type']}) within 1 mile" + (" — National Historic Landmark" if place["is_landmark"] else ""),
                        source_url="https://www.nps.gov/subjects/nationalregister/database-research.htm",
                        raw_excerpt=f"{place['name']} at {place['address']}, {place['city']}, {place['state']}",
                        confidence=0.95,
                    ))

        except Exception as e:
            logging.warning(f"Historic places lookup failed: {e}")
            return {"data": {"historic_places": historic_data}, "unknowns": [], "errors": [str(e)], "evidence": [], "web_calls": 1, "cost_usd": 0.0}

        return {"data": {"historic_places": historic_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": 1, "cost_usd": 0.0}

    async def _worker_seismic_hazard(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        """Check USGS seismic hazard (peak ground acceleration) and nearby quaternary faults."""
        profile = context.get("normalize_geocode", {}).get("property_profile", {})
        geo = profile.get("geo", {})
        lat, lng = geo.get("lat"), geo.get("lng")
        evidence: list[EvidenceDraft] = []
        web_calls = 0

        seismic_data: dict[str, Any] = {"peak_ground_acceleration": None, "seismic_risk_level": None, "nearby_faults": [], "description": None}

        if not lat or not lng:
            return {"data": {"seismic_hazard": seismic_data}, "unknowns": [{"field": "seismic", "reason": "No geocode"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # 1. Peak ground acceleration (raster identify)
                resp1 = await client.get(
                    "https://earthquake.usgs.gov/arcgis/rest/services/haz/USpga250_2014/MapServer/identify",
                    params={
                        "geometry": f"{lng},{lat}",
                        "geometryType": "esriGeometryPoint",
                        "sr": "4326",
                        "tolerance": "1",
                        "mapExtent": f"{lng-5},{lat-5},{lng+5},{lat+5}",
                        "imageDisplay": "600,550,96",
                        "returnGeometry": "false",
                        "f": "json",
                    },
                )
                web_calls += 1
                resp1.raise_for_status()
                pga_results = resp1.json().get("results", [])
                if pga_results:
                    attrs = pga_results[0].get("attributes", {})
                    pga_val = attrs.get("ACC_VAL", attrs.get("Pixel Value"))
                    if pga_val is not None:
                        pga = float(pga_val) if str(pga_val).replace(".", "").isdigit() else None
                        seismic_data["peak_ground_acceleration"] = pga
                        if pga is not None:
                            if pga >= 60:
                                seismic_data["seismic_risk_level"] = "High"
                            elif pga >= 20:
                                seismic_data["seismic_risk_level"] = "Moderate"
                            else:
                                seismic_data["seismic_risk_level"] = "Low"
                            seismic_data["description"] = f"Peak ground acceleration: {pga}%g ({seismic_data['seismic_risk_level']} risk)"

                            evidence.append(EvidenceDraft(
                                category="seismic",
                                claim=f"USGS seismic hazard: PGA={pga}%g — {seismic_data['seismic_risk_level']} risk",
                                source_url="https://earthquake.usgs.gov/hazards/hazmaps/",
                                raw_excerpt=f"ACC_VAL={pga_val}",
                                confidence=0.90,
                            ))

                # 2. Nearby quaternary faults (10km buffer)
                resp2 = await client.get(
                    "https://earthquake.usgs.gov/arcgis/rest/services/haz/Qfaults/MapServer/21/query",
                    params={
                        "geometry": f"{lng},{lat}",
                        "geometryType": "esriGeometryPoint",
                        "inSR": "4326",
                        "spatialRel": "esriSpatialRelIntersects",
                        "distance": "16093",
                        "units": "esriSRUnit_Meter",
                        "outFields": "fault_name,section_name,age,slip_rate,slip_sense",
                        "returnGeometry": "false",
                        "f": "json",
                    },
                )
                web_calls += 1
                resp2.raise_for_status()
                faults = resp2.json().get("features", [])
                for feat in faults[:5]:
                    attrs = feat.get("attributes", {})
                    fault = {
                        "name": attrs.get("fault_name", "Unknown"),
                        "section": attrs.get("section_name", ""),
                        "age": attrs.get("age", ""),
                        "slip_rate": attrs.get("slip_rate", ""),
                    }
                    seismic_data["nearby_faults"].append(fault)
                    evidence.append(EvidenceDraft(
                        category="seismic",
                        claim=f"Quaternary fault within 10 miles: {fault['name']}",
                        source_url="https://earthquake.usgs.gov/hazards/qfaults/",
                        raw_excerpt=f"fault={fault['name']}, age={fault['age']}, slip_rate={fault['slip_rate']}",
                        confidence=0.90,
                    ))

        except Exception as e:
            logging.warning(f"Seismic hazard lookup failed: {e}")
            return {"data": {"seismic_hazard": seismic_data}, "unknowns": [], "errors": [str(e)], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

        return {"data": {"seismic_hazard": seismic_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

    async def _worker_school_district(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        """Look up Census school district and tract GEOID."""
        profile = context.get("normalize_geocode", {}).get("property_profile", {})
        geo = profile.get("geo", {})
        lat, lng = geo.get("lat"), geo.get("lng")
        evidence: list[EvidenceDraft] = []
        web_calls = 0

        district_data: dict[str, Any] = {"school_district": None, "district_geoid": None, "census_tract_geoid": None}

        if not lat or not lng:
            return {"data": {"school_district": district_data}, "unknowns": [{"field": "school_district", "reason": "No geocode"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

        base_params = {
            "geometry": f"{lng},{lat}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "returnGeometry": "false",
            "f": "json",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Unified school district
                resp1 = await client.get(
                    "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/School/MapServer/0/query",
                    params={**base_params, "outFields": "NAME,BASENAME,GEOID,LOGRADE,HIGRADE"},
                )
                web_calls += 1
                resp1.raise_for_status()
                feats1 = resp1.json().get("features", [])
                if feats1:
                    attrs = feats1[0].get("attributes", {})
                    district_data["school_district"] = attrs.get("NAME") or attrs.get("BASENAME")
                    district_data["district_geoid"] = attrs.get("GEOID")

                    evidence.append(EvidenceDraft(
                        category="school_district",
                        claim=f"School district: {district_data['school_district']} (GEOID: {district_data['district_geoid']})",
                        source_url="https://www.census.gov/programs-surveys/school-districts.html",
                        raw_excerpt=f"NAME={attrs.get('NAME')}, GEOID={attrs.get('GEOID')}, grades={attrs.get('LOGRADE')}-{attrs.get('HIGRADE')}",
                        confidence=0.95,
                    ))

                # Census tract GEOID
                resp2 = await client.get(
                    "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2021/MapServer/14/query",
                    params={**base_params, "outFields": "GEOID,NAME,STATE,COUNTY,TRACT"},
                )
                web_calls += 1
                resp2.raise_for_status()
                feats2 = resp2.json().get("features", [])
                if feats2:
                    attrs = feats2[0].get("attributes", {})
                    district_data["census_tract_geoid"] = attrs.get("GEOID")

        except Exception as e:
            logging.warning(f"School district lookup failed: {e}")
            return {"data": {"school_district": district_data}, "unknowns": [], "errors": [str(e)], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

        return {"data": {"school_district": district_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

    # ── RapidAPI Tier 1 Workers (opt-in via extensive) ──

    async def _worker_us_real_estate(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        """US Real Estate API: noise score, recently sold homes, and mortgage rates."""
        profile = context.get("normalize_geocode", {}).get("property_profile", {})
        geo = profile.get("geo", {})
        lat, lng = geo.get("lat"), geo.get("lng")
        address = profile.get("normalized_address", "")
        evidence: list[EvidenceDraft] = []
        web_calls = 0

        us_re_data: dict[str, Any] = {
            "noise_score": None,
            "noise_categories": {},
            "sold_homes": [],
            "mortgage_rates": {},
        }

        if not settings.rapidapi_key:
            return {"data": {"us_real_estate": us_re_data}, "unknowns": [{"field": "us_real_estate", "reason": "No RapidAPI key"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

        headers = {
            "x-rapidapi-key": settings.rapidapi_key,
            "x-rapidapi-host": "us-real-estate.p.rapidapi.com",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # 1) Noise score (lat/lng based)
                if lat and lng:
                    try:
                        resp = await client.get(
                            "https://us-real-estate.p.rapidapi.com/location/noise-score",
                            params={"lat": str(lat), "lng": str(lng)},
                            headers=headers,
                        )
                        web_calls += 1
                        if resp.status_code == 200:
                            noise_data = resp.json()
                            data_node = noise_data.get("data", noise_data)
                            us_re_data["noise_score"] = data_node.get("noise_score") or data_node.get("score")
                            categories = data_node.get("noise_categories") or data_node.get("categories") or {}
                            if isinstance(categories, dict):
                                us_re_data["noise_categories"] = categories
                            elif isinstance(categories, list):
                                for cat in categories:
                                    if isinstance(cat, dict):
                                        us_re_data["noise_categories"][cat.get("name", "unknown")] = cat.get("score")
                            if us_re_data["noise_score"] is not None:
                                evidence.append(EvidenceDraft(
                                    category="noise",
                                    claim=f"Noise score: {us_re_data['noise_score']}/100",
                                    source_url="https://www.realtor.com/",
                                    raw_excerpt=f"Noise categories: {us_re_data['noise_categories']}",
                                    confidence=0.85,
                                ))
                    except Exception as e:
                        logging.warning(f"US Real Estate noise score failed: {e}")

                # 2) Recently sold homes (by zip or city/state)
                zip_code = profile.get("parcel_facts", {}).get("zip") or ""
                # Try to extract zip from address
                if not zip_code and address:
                    zip_match = re.search(r"\b(\d{5})\b", address)
                    if zip_match:
                        zip_code = zip_match.group(1)

                if zip_code:
                    try:
                        resp = await client.get(
                            "https://us-real-estate.p.rapidapi.com/sold-homes",
                            params={"postal_code": zip_code, "offset": "0", "limit": "10", "sort": "sold_date"},
                            headers=headers,
                        )
                        web_calls += 1
                        if resp.status_code == 200:
                            sold_data = resp.json()
                            results = sold_data.get("data", {}).get("results", sold_data.get("results", []))
                            if isinstance(results, list):
                                for item in results[:10]:
                                    loc = item.get("location", {})
                                    addr = loc.get("address", {}) if isinstance(loc, dict) else {}
                                    desc = item.get("description", {})
                                    sold_home = {
                                        "address": addr.get("line", item.get("address", "Unknown")),
                                        "city": addr.get("city", ""),
                                        "price": item.get("last_sold_price") or item.get("price") or desc.get("sold_price"),
                                        "date": item.get("last_sold_date") or item.get("sold_date"),
                                        "beds": desc.get("beds") or item.get("beds"),
                                        "baths": desc.get("baths") or item.get("baths"),
                                        "sqft": desc.get("sqft") or item.get("sqft"),
                                    }
                                    us_re_data["sold_homes"].append(sold_home)
                            if us_re_data["sold_homes"]:
                                evidence.append(EvidenceDraft(
                                    category="sold_homes",
                                    claim=f"{len(us_re_data['sold_homes'])} recently sold homes in ZIP {zip_code}",
                                    source_url="https://www.realtor.com/",
                                    raw_excerpt=f"Top sold: {us_re_data['sold_homes'][0].get('address', '')} at ${us_re_data['sold_homes'][0].get('price', '?')}",
                                    confidence=0.85,
                                ))
                    except Exception as e:
                        logging.warning(f"US Real Estate sold homes failed: {e}")

                # 3) Mortgage rates
                try:
                    resp = await client.get(
                        "https://us-real-estate.p.rapidapi.com/finance/average-rate",
                        headers=headers,
                    )
                    web_calls += 1
                    if resp.status_code == 200:
                        rate_data = resp.json()
                        data_node = rate_data.get("data", rate_data)
                        # Extract common rate fields
                        if isinstance(data_node, dict):
                            for key in ["thirty_year_fixed", "fifteen_year_fixed", "five_one_arm",
                                        "rate_30", "rate_15", "rate_51_arm",
                                        "30_year_fixed", "15_year_fixed"]:
                                if key in data_node:
                                    us_re_data["mortgage_rates"][key] = data_node[key]
                            # Try nested rates
                            rates = data_node.get("rates") or data_node.get("mortgage_rates")
                            if isinstance(rates, (dict, list)):
                                us_re_data["mortgage_rates"]["raw"] = rates
                        if us_re_data["mortgage_rates"]:
                            evidence.append(EvidenceDraft(
                                category="finance",
                                claim=f"Current mortgage rates retrieved",
                                source_url="https://www.realtor.com/mortgage/rates/",
                                raw_excerpt=str(us_re_data["mortgage_rates"])[:200],
                                confidence=0.90,
                            ))
                except Exception as e:
                    logging.warning(f"US Real Estate mortgage rates failed: {e}")

        except Exception as e:
            logging.warning(f"US Real Estate worker failed: {e}")
            return {"data": {"us_real_estate": us_re_data}, "unknowns": [], "errors": [str(e)], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

        return {"data": {"us_real_estate": us_re_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

    async def _worker_walk_score(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        """Walk Score API: walk, transit, and bike scores."""
        profile = context.get("normalize_geocode", {}).get("property_profile", {})
        geo = profile.get("geo", {})
        lat, lng = geo.get("lat"), geo.get("lng")
        address = profile.get("normalized_address", "")
        evidence: list[EvidenceDraft] = []

        walk_data: dict[str, Any] = {
            "walk_score": None,
            "walk_description": None,
            "transit_score": None,
            "transit_description": None,
            "bike_score": None,
            "bike_description": None,
        }

        if not settings.rapidapi_key:
            return {"data": {"walk_score": walk_data}, "unknowns": [{"field": "walk_score", "reason": "No RapidAPI key"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}
        if not lat or not lng:
            return {"data": {"walk_score": walk_data}, "unknowns": [{"field": "walk_score", "reason": "No geocode"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

        headers = {
            "x-rapidapi-key": settings.rapidapi_key,
            "x-rapidapi-host": "walk-score.p.rapidapi.com",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://walk-score.p.rapidapi.com/score",
                    params={
                        "lat": str(lat),
                        "lon": str(lng),
                        "address": address,
                        "transit": "1",
                        "bike": "1",
                    },
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()

                walk_data["walk_score"] = data.get("walkscore")
                walk_data["walk_description"] = data.get("description")

                transit = data.get("transit", {})
                if isinstance(transit, dict):
                    walk_data["transit_score"] = transit.get("score")
                    walk_data["transit_description"] = transit.get("description")

                bike = data.get("bike", {})
                if isinstance(bike, dict):
                    walk_data["bike_score"] = bike.get("score")
                    walk_data["bike_description"] = bike.get("description")

                parts = []
                if walk_data["walk_score"] is not None:
                    parts.append(f"Walk: {walk_data['walk_score']}/100 ({walk_data['walk_description'] or ''})")
                if walk_data["transit_score"] is not None:
                    parts.append(f"Transit: {walk_data['transit_score']}/100 ({walk_data['transit_description'] or ''})")
                if walk_data["bike_score"] is not None:
                    parts.append(f"Bike: {walk_data['bike_score']}/100 ({walk_data['bike_description'] or ''})")

                if parts:
                    evidence.append(EvidenceDraft(
                        category="walkability",
                        claim=f"Walkability scores — {'; '.join(parts)}",
                        source_url=data.get("ws_link", "https://www.walkscore.com/"),
                        raw_excerpt=f"Walk={walk_data['walk_score']}, Transit={walk_data['transit_score']}, Bike={walk_data['bike_score']}",
                        confidence=0.95,
                    ))

        except Exception as e:
            logging.warning(f"Walk Score lookup failed: {e}")
            return {"data": {"walk_score": walk_data}, "unknowns": [], "errors": [str(e)], "evidence": evidence, "web_calls": 1, "cost_usd": 0.0}

        return {"data": {"walk_score": walk_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": 1, "cost_usd": 0.0}

    async def _worker_redfin(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        """Redfin API: property estimate, market data, and walk score from Redfin."""
        profile = context.get("normalize_geocode", {}).get("property_profile", {})
        address = profile.get("normalized_address", "")
        evidence: list[EvidenceDraft] = []
        web_calls = 0

        redfin_data: dict[str, Any] = {
            "redfin_estimate": None,
            "property_url": None,
            "property_type": None,
            "year_built": None,
            "lot_size": None,
            "hoa_fee": None,
            "listing_status": None,
            "last_sold_price": None,
            "last_sold_date": None,
            "walk_score": None,
            "transit_score": None,
            "bike_score": None,
        }

        if not settings.rapidapi_key:
            return {"data": {"redfin": redfin_data}, "unknowns": [{"field": "redfin", "reason": "No RapidAPI key"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}
        if not address:
            return {"data": {"redfin": redfin_data}, "unknowns": [{"field": "redfin", "reason": "No address"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

        headers = {
            "x-rapidapi-key": settings.rapidapi_key,
            "x-rapidapi-host": "redfin-com-data.p.rapidapi.com",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Step 1: Auto-complete to find property URL
                resp = await client.get(
                    "https://redfin-com-data.p.rapidapi.com/auto-complete",
                    params={"query": address},
                    headers=headers,
                )
                web_calls += 1
                if resp.status_code != 200:
                    return {"data": {"redfin": redfin_data}, "unknowns": [{"field": "redfin", "reason": f"Auto-complete returned {resp.status_code}"}], "errors": [], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

                ac_data = resp.json()
                # Find best match from auto-complete results
                property_url = None
                results = ac_data.get("data", ac_data.get("results", []))
                if isinstance(results, list):
                    for item in results:
                        if isinstance(item, dict):
                            url = item.get("url") or item.get("link")
                            if url:
                                property_url = url
                                break
                elif isinstance(results, dict):
                    # Sometimes nested: data.sections[].rows[]
                    sections = results.get("sections", [])
                    for section in sections:
                        rows = section.get("rows", [])
                        for row in rows:
                            url = row.get("url") or row.get("link")
                            if url:
                                property_url = url
                                break
                        if property_url:
                            break

                if not property_url:
                    return {"data": {"redfin": redfin_data}, "unknowns": [{"field": "redfin", "reason": "No property match found"}], "errors": [], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

                redfin_data["property_url"] = property_url

                # Step 2: Get property info
                resp2 = await client.get(
                    "https://redfin-com-data.p.rapidapi.com/properties/get-info",
                    params={"url": property_url},
                    headers=headers,
                )
                web_calls += 1
                if resp2.status_code == 200:
                    info = resp2.json()
                    data_node = info.get("data", info)
                    if isinstance(data_node, dict):
                        # Basic info
                        basic = data_node.get("basicInfo", data_node)
                        redfin_data["redfin_estimate"] = basic.get("price") or data_node.get("predictedValue") or data_node.get("avm", {}).get("predictedValue")
                        redfin_data["property_type"] = basic.get("propertyType") or data_node.get("propertyType")
                        redfin_data["year_built"] = basic.get("yearBuilt") or data_node.get("yearBuilt")
                        redfin_data["lot_size"] = basic.get("lotSize") or data_node.get("lotSize")
                        redfin_data["listing_status"] = basic.get("listingStatus") or data_node.get("status")

                        # Financial
                        redfin_data["hoa_fee"] = data_node.get("hoaFee") or data_node.get("hoa", {}).get("fee") if isinstance(data_node.get("hoa"), dict) else None
                        redfin_data["last_sold_price"] = data_node.get("lastSoldPrice") or data_node.get("salePrice")
                        redfin_data["last_sold_date"] = data_node.get("lastSoldDate") or data_node.get("saleDate")

                        if redfin_data["redfin_estimate"]:
                            evidence.append(EvidenceDraft(
                                category="valuation",
                                claim=f"Redfin estimate: ${redfin_data['redfin_estimate']:,.0f}" if isinstance(redfin_data["redfin_estimate"], (int, float)) else f"Redfin estimate: {redfin_data['redfin_estimate']}",
                                source_url=f"https://www.redfin.com{property_url}" if property_url.startswith("/") else property_url,
                                raw_excerpt=f"Type: {redfin_data['property_type']}, Year: {redfin_data['year_built']}, Last sold: {redfin_data['last_sold_price']}",
                                confidence=0.85,
                            ))

                # Step 3: Walk score from Redfin
                try:
                    resp3 = await client.get(
                        "https://redfin-com-data.p.rapidapi.com/properties/get-walk-score",
                        params={"url": property_url},
                        headers=headers,
                    )
                    web_calls += 1
                    if resp3.status_code == 200:
                        ws_data = resp3.json()
                        data_node = ws_data.get("data", ws_data)
                        if isinstance(data_node, dict):
                            for ws_item in data_node.get("walkScoreData", data_node.get("scores", [data_node])):
                                if isinstance(ws_item, dict):
                                    if ws_item.get("walkScore") is not None or ws_item.get("walk_score") is not None:
                                        redfin_data["walk_score"] = ws_item.get("walkScore") or ws_item.get("walk_score")
                                    if ws_item.get("transitScore") is not None or ws_item.get("transit_score") is not None:
                                        redfin_data["transit_score"] = ws_item.get("transitScore") or ws_item.get("transit_score")
                                    if ws_item.get("bikeScore") is not None or ws_item.get("bike_score") is not None:
                                        redfin_data["bike_score"] = ws_item.get("bikeScore") or ws_item.get("bike_score")
                                    break
                except Exception as e:
                    logging.warning(f"Redfin walk score failed: {e}")

        except Exception as e:
            logging.warning(f"Redfin worker failed: {e}")
            return {"data": {"redfin": redfin_data}, "unknowns": [], "errors": [str(e)], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

        return {"data": {"redfin": redfin_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": web_calls, "cost_usd": 0.0}

    async def _worker_rentcast(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        """RentCast API: independent rent estimate with comparable rentals."""
        profile = context.get("normalize_geocode", {}).get("property_profile", {})
        address = profile.get("normalized_address", "")
        facts = profile.get("parcel_facts", {})
        evidence: list[EvidenceDraft] = []

        rentcast_data: dict[str, Any] = {
            "rent_estimate": None,
            "rent_range_low": None,
            "rent_range_high": None,
            "comparables": [],
        }

        if not settings.rentcast_api_key:
            return {"data": {"rentcast": rentcast_data}, "unknowns": [{"field": "rentcast", "reason": "No RentCast API key"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}
        if not address:
            return {"data": {"rentcast": rentcast_data}, "unknowns": [{"field": "rentcast", "reason": "No address"}], "errors": [], "evidence": [], "web_calls": 0, "cost_usd": 0.0}

        headers = {"X-Api-Key": settings.rentcast_api_key}
        params: dict[str, Any] = {"address": address}
        if facts.get("beds"):
            params["bedrooms"] = facts["beds"]
        if facts.get("baths"):
            params["bathrooms"] = facts["baths"]
        if facts.get("sqft"):
            params["squareFootage"] = facts["sqft"]

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://api.rentcast.io/v1/avm/rent/long-term",
                    params=params,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()

                rentcast_data["rent_estimate"] = data.get("rent")
                rentcast_data["rent_range_low"] = data.get("rentRangeLow")
                rentcast_data["rent_range_high"] = data.get("rentRangeHigh")

                comps = data.get("comparables", [])
                for comp in comps[:10]:
                    rentcast_data["comparables"].append({
                        "address": comp.get("formattedAddress", "Unknown"),
                        "rent": comp.get("price"),
                        "distance_mi": comp.get("distance"),
                        "correlation": comp.get("correlation"),
                        "beds": comp.get("bedrooms"),
                        "baths": comp.get("bathrooms"),
                        "sqft": comp.get("squareFootage"),
                    })

                if rentcast_data["rent_estimate"]:
                    evidence.append(EvidenceDraft(
                        category="rent_estimate",
                        claim=f"RentCast rent estimate: ${rentcast_data['rent_estimate']:,.0f}/mo (range: ${rentcast_data['rent_range_low'] or '?'}-${rentcast_data['rent_range_high'] or '?'})",
                        source_url="https://www.rentcast.io/",
                        raw_excerpt=f"{len(rentcast_data['comparables'])} comparable rentals used",
                        confidence=0.90,
                    ))

        except Exception as e:
            logging.warning(f"RentCast lookup failed: {e}")
            return {"data": {"rentcast": rentcast_data}, "unknowns": [], "errors": [str(e)], "evidence": evidence, "web_calls": 1, "cost_usd": 0.0}

        return {"data": {"rentcast": rentcast_data}, "unknowns": [], "errors": [], "evidence": evidence, "web_calls": 1, "cost_usd": 0.0}

    # ── UPGRADED: AI-Powered Dossier Writer ──
    async def _worker_dossier_writer(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        profile = context.get("normalize_geocode", {}).get("property_profile", {})
        underwrite = context.get("underwriting", {}).get("underwrite", {})
        risk_score = context.get("underwriting", {}).get("risk_score", {})
        sales = context.get("comps_sales", {}).get("comps_sales", [])
        rentals = context.get("comps_rentals", {}).get("comps_rentals", [])
        neighborhood = context.get("neighborhood_intel", {}).get("neighborhood_intel", {})
        flood = context.get("flood_zone", {}).get("flood_zone", {})
        public_records = context.get("public_records", {}).get("public_records_hits", [])
        permits = context.get("permits_violations", {}).get("permit_violation_hits", [])

        evidences = (
            db.query(EvidenceItem)
            .filter(EvidenceItem.job_id == job.id)
            .order_by(EvidenceItem.id.asc())
            .all()
        )

        strategy = (job.assumptions or {}).get("strategy", job.strategy or "wholesale")
        cost_usd = 0.0

        # ── Build structured data summary for Claude ──
        data_summary = []

        # Property profile
        facts = profile.get("parcel_facts", {})
        geo = profile.get("geo", {})
        data_summary.append(f"PROPERTY: {profile.get('normalized_address', 'unknown')}")
        parts = []
        if facts.get("beds"):
            parts.append(f"{facts['beds']} bed")
        if facts.get("baths"):
            parts.append(f"{facts['baths']} bath")
        if facts.get("sqft"):
            parts.append(f"{facts['sqft']:,} sqft")
        if facts.get("year"):
            parts.append(f"built {facts['year']}")
        if parts:
            data_summary.append(f"Details: {' / '.join(parts)}")
        if profile.get("owner_names"):
            data_summary.append(f"Owner: {', '.join(profile['owner_names'])}")
        assessed = profile.get("assessed_values", {})
        if assessed.get("zestimate"):
            data_summary.append(f"Zestimate: ${assessed['zestimate']:,.0f}")
        if assessed.get("rent_zestimate"):
            data_summary.append(f"Rent Zestimate: ${assessed['rent_zestimate']:,.0f}/mo")

        # Comps
        if sales:
            data_summary.append(f"\nCOMPARABLE SALES ({len(sales)} found):")
            for c in sales[:8]:
                price = f"${c['sale_price']:,.0f}" if c.get("sale_price") else "N/A"
                data_summary.append(f"  - {c['address']}: {price} (score: {c['similarity_score']:.2f}, dist: {c.get('distance_mi', '?')} mi)")
        else:
            data_summary.append("\nCOMPARABLE SALES: None found")

        if rentals:
            data_summary.append(f"\nCOMPARABLE RENTALS ({len(rentals)} found):")
            for c in rentals[:8]:
                rent = f"${c['rent']:,.0f}/mo" if c.get("rent") else "N/A"
                data_summary.append(f"  - {c['address']}: {rent} (score: {c['similarity_score']:.2f})")
        else:
            data_summary.append("\nCOMPARABLE RENTALS: None found")

        # Underwriting
        if underwrite:
            data_summary.append(f"\nUNDERWRITING (strategy: {strategy}):")
            arv = underwrite.get("arv_estimate", {})
            if arv.get("base"):
                data_summary.append(f"  ARV: ${arv['base']:,.0f} (low: ${arv.get('low', 0):,.0f}, high: ${arv.get('high', 0):,.0f})")
            rent_est = underwrite.get("rent_estimate", {})
            if rent_est.get("base"):
                data_summary.append(f"  Rent estimate: ${rent_est['base']:,.0f}/mo")
            data_summary.append(f"  Rehab tier: {underwrite.get('rehab_tier', 'unknown')}")
            rehab = underwrite.get("rehab_estimated_range", {})
            if rehab.get("low"):
                data_summary.append(f"  Rehab cost: ${rehab['low']:,.0f} - ${rehab.get('high', 0):,.0f}")
            offer = underwrite.get("offer_price_recommendation", {})
            if offer.get("base"):
                data_summary.append(f"  OFFER RECOMMENDATION: ${offer['base']:,.0f} (low: ${offer.get('low', 0):,.0f}, high: ${offer.get('high', 0):,.0f})")

        # Risk
        if risk_score:
            data_summary.append(f"\nRISK ASSESSMENT:")
            if risk_score.get("title_risk") is not None:
                data_summary.append(f"  Title risk: {risk_score['title_risk']:.0%}")
            if risk_score.get("data_confidence") is not None:
                data_summary.append(f"  Data confidence: {risk_score['data_confidence']:.0%}")
            flags = risk_score.get("compliance_flags", [])
            if flags:
                data_summary.append(f"  Compliance flags: {', '.join(flags)}")

        # Flood zone
        if flood:
            data_summary.append(f"\nFLOOD ZONE:")
            data_summary.append(f"  Zone: {flood.get('flood_zone', 'unknown')}")
            data_summary.append(f"  Description: {flood.get('flood_zone_description', 'unknown')}")
            data_summary.append(f"  In floodplain: {flood.get('in_floodplain', 'unknown')}")
            data_summary.append(f"  Insurance required: {flood.get('insurance_required', 'unknown')}")

        # Neighborhood
        if neighborhood:
            ai_neighborhood = neighborhood.get("ai_summary")
            if ai_neighborhood:
                data_summary.append(f"\nNEIGHBORHOOD ANALYSIS:\n{ai_neighborhood}")
            else:
                for cat in ["crime", "schools", "market_trends"]:
                    items = neighborhood.get(cat, [])
                    if items:
                        data_summary.append(f"\n{cat.upper()} DATA:")
                        for item in items[:3]:
                            data_summary.append(f"  - {item.get('title', '')}: {item.get('snippet', '')[:150]}")

        # Public records & permits
        if public_records:
            data_summary.append(f"\nPUBLIC RECORDS ({len(public_records)} sources found):")
            for r in public_records[:5]:
                data_summary.append(f"  - {r.get('title', '')}: {r.get('snippet', '')[:100]}")
        if permits:
            data_summary.append(f"\nPERMITS/VIOLATIONS ({len(permits)} sources found):")
            for r in permits[:5]:
                data_summary.append(f"  - {r.get('title', '')}: {r.get('snippet', '')[:100]}")

        # Extensive research data (opt-in)
        epa = context.get("epa_environmental", {}).get("epa_environmental", {})
        if epa and epa.get("risk_summary"):
            data_summary.append(f"\nEPA ENVIRONMENTAL:")
            data_summary.append(f"  {epa['risk_summary']}")
            for cat in ["superfund_sites", "brownfields", "toxic_releases", "hazardous_waste"]:
                sites = epa.get(cat, [])
                if sites:
                    data_summary.append(f"  {cat.replace('_', ' ').title()} ({len(sites)}):")
                    for s in sites[:3]:
                        data_summary.append(f"    - {s.get('name', 'Unknown')} at {s.get('address', '')}")

        wildfire = context.get("wildfire_hazard", {}).get("wildfire_hazard", {})
        if wildfire and wildfire.get("hazard_level"):
            data_summary.append(f"\nWILDFIRE HAZARD: {wildfire['hazard_level']}")
            if wildfire.get("description"):
                data_summary.append(f"  {wildfire['description']}")

        hud = context.get("hud_opportunity", {}).get("hud_opportunity", {})
        if hud and any(v is not None for v in hud.values()):
            data_summary.append(f"\nHUD OPPORTUNITY INDICES (0-100 scale, higher=better):")
            for k, v in hud.items():
                if v is not None:
                    data_summary.append(f"  {k.replace('_', ' ').title()}: {v}/100")

        wetland = context.get("wetlands", {}).get("wetlands", {})
        if wetland and wetland.get("wetlands_found"):
            data_summary.append(f"\nWETLANDS: {len(wetland.get('wetlands', []))} wetland(s) found — development may be restricted")
            for w in wetland.get("wetlands", [])[:3]:
                data_summary.append(f"  - {w.get('type', 'Unknown')}, {w.get('acres', '?')} acres, {w.get('system', '')}")

        historic = context.get("historic_places", {}).get("historic_places", {})
        if historic and historic.get("nearby_places"):
            data_summary.append(f"\nHISTORIC PLACES ({len(historic['nearby_places'])} within 1 mile):")
            if historic.get("in_historic_district"):
                data_summary.append("  WARNING: Property in historic district — renovation restrictions apply, 20% federal tax credit available")
            for p in historic["nearby_places"][:5]:
                data_summary.append(f"  - {p.get('name', 'Unknown')} ({p.get('type', '')})" + (" — National Historic Landmark" if p.get("is_landmark") else ""))

        seismic = context.get("seismic_hazard", {}).get("seismic_hazard", {})
        if seismic and seismic.get("peak_ground_acceleration") is not None:
            data_summary.append(f"\nSEISMIC HAZARD: {seismic.get('description', '')}")
            faults = seismic.get("nearby_faults", [])
            if faults:
                data_summary.append(f"  Nearby faults ({len(faults)}):")
                for f in faults[:3]:
                    data_summary.append(f"    - {f.get('name', 'Unknown')} (age: {f.get('age', '?')})")

        school = context.get("school_district", {}).get("school_district", {})
        if school and school.get("school_district"):
            data_summary.append(f"\nSCHOOL DISTRICT: {school['school_district']}")
            if school.get("census_tract_geoid"):
                data_summary.append(f"  Census tract GEOID: {school['census_tract_geoid']}")

        # RapidAPI Tier 1 data
        us_re = context.get("us_real_estate", {}).get("us_real_estate", {})
        if us_re:
            if us_re.get("noise_score") is not None:
                data_summary.append(f"\nNOISE SCORE: {us_re['noise_score']}/100")
                cats = us_re.get("noise_categories", {})
                if cats:
                    for k, v in cats.items():
                        if v is not None:
                            data_summary.append(f"  {k}: {v}")
            if us_re.get("sold_homes"):
                data_summary.append(f"\nRECENTLY SOLD HOMES ({len(us_re['sold_homes'])} in area):")
                for h in us_re["sold_homes"][:5]:
                    price = f"${h['price']:,.0f}" if isinstance(h.get("price"), (int, float)) else str(h.get("price", "?"))
                    data_summary.append(f"  - {h.get('address', 'Unknown')}: {price} ({h.get('date', '?')})")
            if us_re.get("mortgage_rates"):
                data_summary.append(f"\nCURRENT MORTGAGE RATES:")
                for k, v in us_re["mortgage_rates"].items():
                    if k != "raw" and v is not None:
                        data_summary.append(f"  {k.replace('_', ' ').title()}: {v}%")

        ws = context.get("walk_score", {}).get("walk_score", {})
        if ws and ws.get("walk_score") is not None:
            data_summary.append(f"\nWALKABILITY:")
            data_summary.append(f"  Walk Score: {ws['walk_score']}/100 ({ws.get('walk_description', '')})")
            if ws.get("transit_score") is not None:
                data_summary.append(f"  Transit Score: {ws['transit_score']}/100 ({ws.get('transit_description', '')})")
            if ws.get("bike_score") is not None:
                data_summary.append(f"  Bike Score: {ws['bike_score']}/100 ({ws.get('bike_description', '')})")

        redfin = context.get("redfin", {}).get("redfin", {})
        if redfin and redfin.get("redfin_estimate"):
            est = redfin["redfin_estimate"]
            est_str = f"${est:,.0f}" if isinstance(est, (int, float)) else str(est)
            data_summary.append(f"\nREDFIN DATA:")
            data_summary.append(f"  Redfin Estimate: {est_str}")
            if redfin.get("last_sold_price"):
                data_summary.append(f"  Last sold: ${redfin['last_sold_price']:,.0f}" if isinstance(redfin["last_sold_price"], (int, float)) else f"  Last sold: {redfin['last_sold_price']}")
            if redfin.get("hoa_fee"):
                data_summary.append(f"  HOA fee: ${redfin['hoa_fee']}/mo")

        rc = context.get("rentcast", {}).get("rentcast", {})
        if rc and rc.get("rent_estimate"):
            data_summary.append(f"\nRENTCAST RENT ESTIMATE:")
            data_summary.append(f"  Rent: ${rc['rent_estimate']:,.0f}/mo (range: ${rc.get('rent_range_low', '?')}-${rc.get('rent_range_high', '?')})")
            if rc.get("comparables"):
                data_summary.append(f"  Based on {len(rc['comparables'])} comparable rentals")

        structured_data = "\n".join(data_summary)

        # ── Try Claude AI narrative ──
        ai_narrative = None
        if settings.anthropic_api_key:
            try:
                from app.services.llm_service import llm_service as _llm

                ai_narrative = _llm.generate(
                    f"""You are a senior real estate investment analyst writing an investment memo. Based on the data below, write a comprehensive property dossier in markdown format.

STRATEGY: {strategy}

{structured_data}

Write the dossier with these sections:
1. **Executive Summary** (2-3 sentences: is this a good deal? key numbers, go/no-go recommendation)
2. **Property Overview** (address, details, owner, condition indicators)
3. **Market Analysis** (comps analysis — are they strong? price trends, rental demand)
4. **Environmental & Natural Hazards** (flood zone, EPA sites, wildfire risk, seismic risk, wetlands — whatever data is available)
5. **Neighborhood Profile** (safety, schools, HUD opportunity indices, demographics, historic district impacts, market outlook)
6. **Financial Analysis** (ARV, rent estimate, rehab costs, offer recommendation with reasoning)
7. **Risk Factors** (title risk, data confidence, compliance flags, insurance implications, what's missing)
8. **Recommendation** (clear buy/pass/investigate-further with specific next steps)

Be specific with numbers. If data is missing, say so clearly and explain the impact. Write for an experienced investor who needs actionable intelligence, not fluff.""",
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=1500,
                )
                cost_usd = 0.02  # Approximate Sonnet cost for 1500 tokens
            except Exception as e:
                logging.warning(f"Claude dossier generation failed: {e}")
                ai_narrative = None

        # ── Build final markdown ──
        if ai_narrative:
            # AI-generated dossier with data appendix
            markdown_text = ai_narrative
            markdown_text += "\n\n---\n\n## Raw Data Appendix\n\n"
            markdown_text += self._build_data_appendix(profile, sales, rentals, underwrite, risk_score, flood, evidences)
        else:
            # Fallback: structured markdown (original approach, enhanced)
            markdown_text = self._build_structured_dossier(
                profile, sales, rentals, underwrite, risk_score, flood, neighborhood, evidences, context
            )

        # Persist
        db.query(Dossier).filter(Dossier.job_id == job.id).delete()
        new_dossier = Dossier(
            research_property_id=job.research_property_id,
            job_id=job.id,
            markdown=markdown_text,
            citations=[{"evidence_id": ev.id, "source_url": ev.source_url} for ev in evidences],
        )
        db.add(new_dossier)
        db.commit()

        # Auto-embed dossier for vector search
        try:
            from app.services.embedding_service import embedding_service
            db.refresh(new_dossier)
            embedding_service.embed_dossier(db, new_dossier.id)
        except Exception:
            pass  # best-effort, don't break pipeline

        return {
            "data": {"dossier": {"markdown": markdown_text}},
            "unknowns": [],
            "errors": [],
            "evidence": [
                EvidenceDraft(
                    category="dossier",
                    claim=f"Dossier generated {'with AI narrative' if ai_narrative else 'from structured data'}.",
                    source_url=f"internal://agentic_jobs/{job.id}/dossier",
                    raw_excerpt=None,
                    confidence=1.0,
                )
            ],
            "web_calls": 0,
            "cost_usd": cost_usd,
        }

    def _build_data_appendix(self, profile, sales, rentals, underwrite, risk_score, flood, evidences) -> str:
        """Build a raw data appendix for the AI dossier."""
        lines = []
        # Comps table
        if sales:
            lines.append("### Comparable Sales")
            lines.append("| Address | Price | Distance | Score |")
            lines.append("|---------|-------|----------|-------|")
            for c in sales[:8]:
                price = f"${c['sale_price']:,.0f}" if c.get("sale_price") else "N/A"
                lines.append(f"| {c['address']} | {price} | {c.get('distance_mi', '?')} mi | {c['similarity_score']:.2f} |")
            lines.append("")

        if rentals:
            lines.append("### Comparable Rentals")
            lines.append("| Address | Rent | Score |")
            lines.append("|---------|------|-------|")
            for c in rentals[:8]:
                rent = f"${c['rent']:,.0f}/mo" if c.get("rent") else "N/A"
                lines.append(f"| {c['address']} | {rent} | {c['similarity_score']:.2f} |")
            lines.append("")

        # Evidence trail
        if evidences:
            lines.append("### Evidence Trail")
            for ev in evidences:
                lines.append(f"- [{ev.category}] {ev.claim} — {ev.source_url}")
            lines.append("")

        return "\n".join(lines)

    def _build_structured_dossier(self, profile, sales, rentals, underwrite, risk_score, flood, neighborhood, evidences, context=None) -> str:
        """Fallback structured dossier when Claude is unavailable."""
        context = context or {}
        citation_refs = " ".join([f"[^e{ev.id}]" for ev in evidences[:6]])
        markdown = []
        markdown.append(f"# Property Dossier: {profile.get('normalized_address', 'unknown')}")
        markdown.append("")

        # Property profile
        markdown.append("## Property Profile")
        markdown.append(f"- Address: {profile.get('normalized_address', 'unknown')} {citation_refs}".strip())
        markdown.append(f"- APN: {profile.get('apn') or 'unknown'}")
        geo = profile.get("geo") or {}
        markdown.append(f"- Geo: {geo.get('lat', 'unknown')}, {geo.get('lng', 'unknown')}")
        facts = profile.get("parcel_facts") or {}
        markdown.append(f"- Beds/Baths/Sqft: {facts.get('beds') or '?'} / {facts.get('baths') or '?'} / {facts.get('sqft') or '?'}")
        if profile.get("owner_names"):
            markdown.append(f"- Owner: {', '.join(profile['owner_names'])}")
        markdown.append("")

        # Flood zone
        if flood and flood.get("flood_zone"):
            markdown.append("## Flood Zone")
            markdown.append(f"- Zone: {flood['flood_zone']} — {flood.get('description', '')}")
            markdown.append(f"- In floodplain: {'Yes' if flood.get('in_floodplain') else 'No'}")
            markdown.append(f"- Insurance required: {'Yes' if flood.get('insurance_required') else 'No'}")
            markdown.append("")

        # Neighborhood
        if neighborhood:
            ai_summary = neighborhood.get("ai_summary")
            if ai_summary:
                markdown.append("## Neighborhood Analysis")
                markdown.append(ai_summary)
                markdown.append("")

        # Extensive research data
        epa = context.get("epa_environmental", {}).get("epa_environmental", {})
        if epa and epa.get("risk_summary"):
            markdown.append("## EPA Environmental")
            markdown.append(f"- {epa['risk_summary']}")
            markdown.append("")

        wildfire = context.get("wildfire_hazard", {}).get("wildfire_hazard", {})
        if wildfire and wildfire.get("hazard_level"):
            markdown.append("## Wildfire Hazard")
            markdown.append(f"- Level: {wildfire['hazard_level']}")
            if wildfire.get("description"):
                markdown.append(f"- {wildfire['description']}")
            markdown.append("")

        hud = context.get("hud_opportunity", {}).get("hud_opportunity", {})
        if hud and any(v is not None for v in hud.values()):
            markdown.append("## HUD Opportunity Indices")
            for k, v in hud.items():
                if v is not None:
                    markdown.append(f"- {k.replace('_', ' ').title()}: {v}/100")
            markdown.append("")

        wetland = context.get("wetlands", {}).get("wetlands", {})
        if wetland and wetland.get("wetlands_found"):
            markdown.append("## Wetlands")
            markdown.append(f"- {len(wetland.get('wetlands', []))} wetland(s) found — development restricted")
            markdown.append("")

        historic = context.get("historic_places", {}).get("historic_places", {})
        if historic and historic.get("nearby_places"):
            markdown.append("## Historic Places")
            if historic.get("in_historic_district"):
                markdown.append("- WARNING: In historic district — renovation restrictions, 20% federal tax credit eligible")
            for p in historic["nearby_places"][:5]:
                markdown.append(f"- {p.get('name', 'Unknown')} ({p.get('type', '')})")
            markdown.append("")

        seismic = context.get("seismic_hazard", {}).get("seismic_hazard", {})
        if seismic and seismic.get("seismic_risk_level"):
            markdown.append("## Seismic Hazard")
            markdown.append(f"- {seismic.get('description', '')}")
            faults = seismic.get("nearby_faults", [])
            if faults:
                markdown.append(f"- {len(faults)} fault(s) within 10 miles")
            markdown.append("")

        school = context.get("school_district", {}).get("school_district", {})
        if school and school.get("school_district"):
            markdown.append("## School District")
            markdown.append(f"- District: {school['school_district']}")
            markdown.append("")

        # RapidAPI Tier 1 data
        us_re = context.get("us_real_estate", {}).get("us_real_estate", {})
        if us_re and us_re.get("noise_score") is not None:
            markdown.append("## Noise Score")
            markdown.append(f"- Score: {us_re['noise_score']}/100")
            cats = us_re.get("noise_categories", {})
            for k, v in cats.items():
                if v is not None:
                    markdown.append(f"- {k}: {v}")
            markdown.append("")

        if us_re and us_re.get("sold_homes"):
            markdown.append(f"## Recently Sold Homes ({len(us_re['sold_homes'])} in area)")
            for h in us_re["sold_homes"][:5]:
                price = f"${h['price']:,.0f}" if isinstance(h.get("price"), (int, float)) else str(h.get("price", "?"))
                markdown.append(f"- {h.get('address', 'Unknown')}: {price} ({h.get('date', '?')})")
            markdown.append("")

        ws = context.get("walk_score", {}).get("walk_score", {})
        if ws and ws.get("walk_score") is not None:
            markdown.append("## Walkability")
            markdown.append(f"- Walk Score: {ws['walk_score']}/100 ({ws.get('walk_description', '')})")
            if ws.get("transit_score") is not None:
                markdown.append(f"- Transit Score: {ws['transit_score']}/100 ({ws.get('transit_description', '')})")
            if ws.get("bike_score") is not None:
                markdown.append(f"- Bike Score: {ws['bike_score']}/100 ({ws.get('bike_description', '')})")
            markdown.append("")

        redfin = context.get("redfin", {}).get("redfin", {})
        if redfin and redfin.get("redfin_estimate"):
            est = redfin["redfin_estimate"]
            est_str = f"${est:,.0f}" if isinstance(est, (int, float)) else str(est)
            markdown.append("## Redfin Data")
            markdown.append(f"- Redfin Estimate: {est_str}")
            if redfin.get("last_sold_price"):
                price_str = f"${redfin['last_sold_price']:,.0f}" if isinstance(redfin["last_sold_price"], (int, float)) else str(redfin["last_sold_price"])
                markdown.append(f"- Last Sold: {price_str}")
            if redfin.get("hoa_fee"):
                markdown.append(f"- HOA Fee: ${redfin['hoa_fee']}/mo")
            markdown.append("")

        rc = context.get("rentcast", {}).get("rentcast", {})
        if rc and rc.get("rent_estimate"):
            markdown.append("## RentCast Rent Estimate")
            markdown.append(f"- Rent: ${rc['rent_estimate']:,.0f}/mo")
            markdown.append(f"- Range: ${rc.get('rent_range_low', '?')}-${rc.get('rent_range_high', '?')}")
            if rc.get("comparables"):
                markdown.append(f"- Based on {len(rc['comparables'])} comparable rentals")
            markdown.append("")

        # Comps
        markdown.append("## Comparable Sales (Top 8)")
        if sales:
            for comp in sales[:8]:
                markdown.append(f"- {comp['address']} | ${comp.get('sale_price') or '?'} | score={comp['similarity_score']:.3f}")
        else:
            markdown.append("- No qualified comps found")
        markdown.append("")

        markdown.append("## Comparable Rentals (Top 8)")
        if rentals:
            for comp in rentals[:8]:
                markdown.append(f"- {comp['address']} | rent=${comp.get('rent') or '?'} | score={comp['similarity_score']:.3f}")
        else:
            markdown.append("- No qualified rental comps found")
        markdown.append("")

        # Underwriting
        markdown.append("## Underwriting")
        offer = underwrite.get("offer_price_recommendation") or {}
        markdown.append(f"- Offer (low/base/high): {offer.get('low') or '?'} / {offer.get('base') or '?'} / {offer.get('high') or '?'}")
        markdown.append(f"- Rehab tier: {underwrite.get('rehab_tier') or '?'}")
        markdown.append("")

        # Risk
        markdown.append("## Risk")
        markdown.append(f"- Title risk: {risk_score.get('title_risk', '?')}")
        markdown.append(f"- Data confidence: {risk_score.get('data_confidence', '?')}")
        markdown.append(f"- Flags: {', '.join(risk_score.get('compliance_flags', [])) or 'none'}")
        markdown.append("")

        # Evidence
        markdown.append("## Evidence")
        if evidences:
            for ev in evidences:
                markdown.append(f"[^e{ev.id}]: {ev.source_url} (captured_at={ev.captured_at.isoformat()})")
        else:
            markdown.append("- No evidence records found.")

        return "\n".join(markdown)

    def _find_matching_crm_property(self, db: Session, research_property: ResearchProperty) -> Property | None:
        query = db.query(Property)

        if research_property.state:
            query = query.filter(Property.state.ilike(research_property.state))
        if research_property.city:
            query = query.filter(Property.city.ilike(research_property.city))

        exact = query.filter(Property.address.ilike(research_property.raw_address)).first()
        if exact:
            return exact

        return query.filter(Property.address.ilike(f"%{research_property.raw_address}%")).first()

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
        sales_rows = db.query(CompSale).filter(CompSale.job_id == job_id).order_by(CompSale.similarity_score.desc()).all()
        rental_rows = db.query(CompRental).filter(CompRental.job_id == job_id).order_by(CompRental.similarity_score.desc()).all()
        underwrite_row = db.query(Underwriting).filter(Underwriting.job_id == job_id).order_by(Underwriting.id.desc()).first()
        risk_row = db.query(RiskScore).filter(RiskScore.job_id == job_id).order_by(RiskScore.id.desc()).first()
        dossier_row = db.query(Dossier).filter(Dossier.job_id == job_id).order_by(Dossier.id.desc()).first()
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
