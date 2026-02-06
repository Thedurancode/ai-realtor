import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from statistics import mean
from time import perf_counter
from typing import Any, Awaitable, Callable

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
    def __init__(self, search_provider: SearchProvider | None = None):
        self.search_provider = search_provider or build_search_provider_from_settings()
        self.portal_fetcher = PortalFetcher()
        self.logger = logging.getLogger("agentic_research")

    async def create_job(self, db: Session, payload: ResearchInput) -> AgenticJob:
        stable_key = build_stable_property_key(
            address=payload.address,
            city=payload.city,
            state=payload.state,
            zip_code=payload.zip,
            apn=payload.apn,
        )
        normalized = normalize_address(
            address=payload.address,
            city=payload.city,
            state=payload.state,
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
                state=payload.state,
                zip_code=payload.zip,
                apn=payload.apn,
            )
            db.add(research_property)
            db.flush()
        else:
            research_property.raw_address = payload.address
            research_property.normalized_address = normalized
            research_property.city = payload.city or research_property.city
            research_property.state = payload.state or research_property.state
            research_property.zip_code = payload.zip or research_property.zip_code
            research_property.apn = payload.apn or research_property.apn

        job = AgenticJob(
            trace_id=new_trace_id(),
            research_property_id=research_property.id,
            status=AgenticJobStatus.PENDING,
            strategy=payload.strategy,
            assumptions=payload.assumptions,
            limits=payload.limits.model_dump(),
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
        max_steps = int(limits.get("max_steps", 7))
        max_web_calls = int(limits.get("max_web_calls", 20))
        timeout_seconds = int(limits.get("timeout_seconds_per_step", 20))

        context: dict[str, Any] = {}
        total_web_calls = 0

        workers: list[tuple[str, Callable[[], Awaitable[dict[str, Any]]]]] = [
            ("normalize_geocode", lambda: self._worker_normalize_geocode(db, job, context)),
            ("public_records", lambda: self._worker_public_records(db, job, context)),
            ("permits_violations", lambda: self._worker_permits_violations(db, job, context)),
            ("comps_sales", lambda: self._worker_comps_sales(db, job, context)),
            ("comps_rentals", lambda: self._worker_comps_rentals(db, job, context)),
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
                self._persist_evidence(
                    db=db,
                    job=job,
                    evidence_drafts=execution.evidence,
                )

            context[worker_name] = execution.data

            if total_web_calls > max_web_calls:
                raise RuntimeError(
                    f"Job exceeded web call limit ({total_web_calls} > {max_web_calls})"
                )

        return self.get_full_output(db=db, property_id=job.research_property_id, job_id=job.id)

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
                        rp.city = rp.city or details.get("city")
                        rp.state = rp.state or details.get("state")
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
            if zillow:
                profile["assessed_values"] = {
                    "annual_tax_amount": zillow.annual_tax_amount,
                    "zestimate": zillow.zestimate,
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
            evidence.append(
                EvidenceDraft(
                    category="public_records",
                    claim=f"Public records candidate found: {result.get('title', 'unknown')}.",
                    source_url=result.get("url", "internal://search/no-url"),
                    raw_excerpt=result.get("snippet"),
                    confidence=0.5,
                )
            )

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
            evidence.append(
                EvidenceDraft(
                    category="permits",
                    claim=f"Permit/violation source candidate found: {result.get('title', 'unknown')}.",
                    source_url=result.get("url", "internal://search/no-url"),
                    raw_excerpt=result.get("snippet"),
                    confidence=0.5,
                )
            )

        return {
            "data": {"permit_violation_hits": results},
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

        radius = float(
            (job.assumptions or {}).get(
                "sales_radius_mi",
                1.0 if profile.get("geo", {}).get("lat") else 3.0,
            )
        )
        target_sqft = profile.get("parcel_facts", {}).get("sqft")
        target_beds = profile.get("parcel_facts", {}).get("beds")
        target_baths = profile.get("parcel_facts", {}).get("baths")

        rp = db.query(ResearchProperty).filter(ResearchProperty.id == job.research_property_id).first()
        if rp is None:
            raise ValueError("Research property not found")

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
                    "details": {"property_id": candidate.id},
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
                confidence=0.9,
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

        radius = float(
            (job.assumptions or {}).get(
                "rental_radius_mi",
                1.0 if profile.get("geo", {}).get("lat") else 3.0,
            )
        )
        target_sqft = profile.get("parcel_facts", {}).get("sqft")
        target_beds = profile.get("parcel_facts", {}).get("beds")
        target_baths = profile.get("parcel_facts", {}).get("baths")

        rp = db.query(ResearchProperty).filter(ResearchProperty.id == job.research_property_id).first()
        if rp is None:
            raise ValueError("Research property not found")

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
                    "details": {"property_id": candidate.id},
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
                confidence=0.9,
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
            deduped.append(item)

        return sorted(
            deduped,
            key=lambda item: (
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
                            "details": {"origin": "external_exa"},
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
                            "details": {"origin": "external_exa"},
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

        # Risk score derived from evidence coverage and unknowns.
        evidence_count = db.query(EvidenceItem).filter(EvidenceItem.job_id == job.id).count()
        coverage = min(1.0, evidence_count / 12.0)
        unknown_penalty = min(0.6, len(unknowns) * 0.1)
        data_confidence = max(0.0, min(1.0, coverage - unknown_penalty + 0.25))
        title_risk = 0.75 if not profile.get("owner_names") else 0.35

        compliance_flags = []
        if not profile.get("owner_names"):
            compliance_flags.append("owner_not_verified")
        if not sales:
            compliance_flags.append("insufficient_sales_comps")
        if not rentals:
            compliance_flags.append("insufficient_rental_comps")

        risk_score = {
            "title_risk": round(title_risk, 3),
            "data_confidence": round(data_confidence, 3),
            "compliance_flags": compliance_flags,
            "notes": "Risk score is computed from deterministic evidence coverage and missing-field penalties.",
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

    async def _worker_dossier_writer(self, db: Session, job: AgenticJob, context: dict[str, Any]) -> dict[str, Any]:
        profile = context.get("normalize_geocode", {}).get("property_profile", {})
        underwrite = context.get("underwriting", {}).get("underwrite", {})
        risk_score = context.get("underwriting", {}).get("risk_score", {})
        sales = context.get("comps_sales", {}).get("comps_sales", [])
        rentals = context.get("comps_rentals", {}).get("comps_rentals", [])

        evidences = (
            db.query(EvidenceItem)
            .filter(EvidenceItem.job_id == job.id)
            .order_by(EvidenceItem.id.asc())
            .all()
        )

        citation_refs = " ".join([f"[^e{ev.id}]" for ev in evidences[:6]])

        markdown = []
        markdown.append(f"# Property Dossier: {profile.get('normalized_address', 'unknown')}")
        markdown.append("")
        markdown.append("## Property Profile")
        markdown.append(f"- Normalized Address: {profile.get('normalized_address', 'unknown')} {citation_refs}".strip())
        markdown.append(f"- APN: {profile.get('apn') or 'unknown'}")
        geo = profile.get("geo") or {}
        markdown.append(f"- Geo: {geo.get('lat') if geo.get('lat') is not None else 'unknown'}, {geo.get('lng') if geo.get('lng') is not None else 'unknown'}")
        facts = profile.get("parcel_facts") or {}
        markdown.append(f"- Beds/Baths/Sqft: {facts.get('beds') or 'unknown'} / {facts.get('baths') or 'unknown'} / {facts.get('sqft') or 'unknown'}")
        markdown.append("")

        markdown.append("## Comparable Sales (Top 8)")
        if sales:
            for comp in sales[:8]:
                markdown.append(
                    f"- {comp['address']} | ${comp.get('sale_price') or 'unknown'} | score={comp['similarity_score']:.3f}"
                )
        else:
            markdown.append("- unknown (no qualified comps)")
        markdown.append("")

        markdown.append("## Comparable Rentals (Top 8)")
        if rentals:
            for comp in rentals[:8]:
                markdown.append(
                    f"- {comp['address']} | rent=${comp.get('rent') or 'unknown'} | score={comp['similarity_score']:.3f}"
                )
        else:
            markdown.append("- unknown (no qualified rental comps)")
        markdown.append("")

        markdown.append("## Underwriting")
        offer = underwrite.get("offer_price_recommendation") or {}
        markdown.append(
            f"- Offer Recommendation (low/base/high): {offer.get('low') or 'unknown'} / {offer.get('base') or 'unknown'} / {offer.get('high') or 'unknown'}"
        )
        markdown.append(f"- Rehab Tier: {underwrite.get('rehab_tier') or 'unknown'}")
        markdown.append("")

        markdown.append("## Risk")
        markdown.append(f"- Title Risk: {risk_score.get('title_risk', 'unknown')}")
        markdown.append(f"- Data Confidence: {risk_score.get('data_confidence', 'unknown')}")
        markdown.append(f"- Compliance Flags: {', '.join(risk_score.get('compliance_flags', [])) or 'none'}")
        markdown.append("")

        markdown.append("## Evidence")
        if evidences:
            for ev in evidences:
                markdown.append(f"[^e{ev.id}]: {ev.source_url} (captured_at={ev.captured_at.isoformat()})")
        else:
            markdown.append("- No evidence records found.")

        markdown_text = "\n".join(markdown)

        db.query(Dossier).filter(Dossier.job_id == job.id).delete()
        db.add(
            Dossier(
                research_property_id=job.research_property_id,
                job_id=job.id,
                markdown=markdown_text,
                citations=[{"evidence_id": ev.id, "source_url": ev.source_url} for ev in evidences],
            )
        )
        db.commit()

        return {
            "data": {"dossier": {"markdown": markdown_text}},
            "unknowns": [],
            "errors": [],
            "evidence": [
                EvidenceDraft(
                    category="dossier",
                    claim="Dossier generated from structured data and evidence records only.",
                    source_url=f"internal://agentic_jobs/{job.id}/dossier",
                    raw_excerpt=None,
                    confidence=1.0,
                )
            ],
            "web_calls": 0,
            "cost_usd": 0.0,
        }

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
