"""Bulk Operations Engine — execute operations across multiple properties."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.property import Property, PropertyStatus, PropertyType
from app.models.zillow_enrichment import ZillowEnrichment
from app.models.skip_trace import SkipTrace
from app.services.contract_auto_attach import contract_auto_attach_service
from app.services.property_recap_service import property_recap_service

logger = logging.getLogger(__name__)

# Lazy imports to avoid circular imports at module load.
def _get_zillow_service():
    from app.services.zillow_enrichment import zillow_enrichment_service
    return zillow_enrichment_service


def _get_skip_trace_service():
    from app.services.skip_trace import skip_trace_service
    return skip_trace_service


def _get_compliance_engine():
    from app.services.compliance_engine import compliance_engine
    return compliance_engine


_OPERATION_META = [
    {
        "name": "enrich",
        "description": "Enrich properties with Zillow data (Zestimate, photos, schools, features)",
        "params": {"force": "Re-enrich even if already enriched (default: false)"},
    },
    {
        "name": "skip_trace",
        "description": "Skip trace properties to find owner contact information",
        "params": {"force": "Re-trace even if already traced (default: false)"},
    },
    {
        "name": "attach_contracts",
        "description": "Auto-attach matching contract templates to properties",
        "params": {},
    },
    {
        "name": "generate_recaps",
        "description": "Generate AI-powered property recaps",
        "params": {},
    },
    {
        "name": "update_status",
        "description": "Update property status in bulk",
        "params": {"status": "Target status (available, pending, sold, rented, off_market)"},
    },
    {
        "name": "check_compliance",
        "description": "Run compliance checks on properties",
        "params": {},
    },
]


class BulkOperationsService:
    MAX_BATCH_SIZE = 50

    SUPPORTED_OPERATIONS = {m["name"] for m in _OPERATION_META}

    # ── Main entry point ──

    async def execute(
        self,
        db: Session,
        operation: str,
        property_ids: list[int] | None = None,
        filters: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict:
        """Execute *operation* on properties matching IDs/filters."""
        if operation not in self.SUPPORTED_OPERATIONS:
            raise ValueError(f"Unsupported operation: {operation}. Choose from: {sorted(self.SUPPORTED_OPERATIONS)}")

        params = params or {}
        properties = self._resolve_properties(db, property_ids, filters)

        if not properties:
            return {
                "operation": operation,
                "total": 0,
                "succeeded": 0,
                "failed": 0,
                "skipped": 0,
                "results": [],
                "voice_summary": "No properties matched your selection.",
            }

        handler = {
            "enrich": self._bulk_enrich,
            "skip_trace": self._bulk_skip_trace,
            "attach_contracts": self._bulk_attach_contracts,
            "generate_recaps": self._bulk_generate_recaps,
            "update_status": self._bulk_update_status,
            "check_compliance": self._bulk_check_compliance,
        }[operation]

        results = await handler(db, properties, params)

        succeeded = sum(1 for r in results if r["status"] == "success")
        failed = sum(1 for r in results if r["status"] == "error")
        skipped = sum(1 for r in results if r["status"] == "skipped")

        voice = self._build_voice_summary(operation, len(properties), succeeded, failed, skipped)

        return {
            "operation": operation,
            "total": len(properties),
            "succeeded": succeeded,
            "failed": failed,
            "skipped": skipped,
            "results": results,
            "voice_summary": voice,
        }

    # ── Property resolution ──

    def _resolve_properties(
        self,
        db: Session,
        property_ids: list[int] | None,
        filters: dict[str, Any] | None,
    ) -> list[Property]:
        """Build union of explicit IDs + filter matches, capped at MAX_BATCH_SIZE."""
        seen_ids: set[int] = set()
        properties: list[Property] = []

        # Explicit IDs
        if property_ids:
            explicit = db.query(Property).filter(Property.id.in_(property_ids)).all()
            for p in explicit:
                if p.id not in seen_ids:
                    seen_ids.add(p.id)
                    properties.append(p)

        # Dynamic filters
        if filters:
            query = db.query(Property)
            if filters.get("status"):
                try:
                    status_enum = PropertyStatus(filters["status"])
                    query = query.filter(Property.status == status_enum)
                except ValueError:
                    pass
            if filters.get("property_type"):
                try:
                    type_enum = PropertyType(filters["property_type"])
                    query = query.filter(Property.property_type == type_enum)
                except ValueError:
                    pass
            if filters.get("city"):
                query = query.filter(Property.city.ilike(f"%{filters['city']}%"))
            if filters.get("min_price") is not None:
                query = query.filter(Property.price >= filters["min_price"])
            if filters.get("max_price") is not None:
                query = query.filter(Property.price <= filters["max_price"])
            if filters.get("bedrooms") is not None:
                query = query.filter(Property.bedrooms >= filters["bedrooms"])

            for p in query.all():
                if p.id not in seen_ids:
                    seen_ids.add(p.id)
                    properties.append(p)

        return properties[: self.MAX_BATCH_SIZE]

    # ── Operation handlers ──

    async def _bulk_enrich(self, db: Session, properties: list[Property], params: dict) -> list[dict]:
        force = params.get("force", False)
        svc = _get_zillow_service()
        results: list[dict] = []

        for prop in properties:
            try:
                if not force:
                    existing = db.query(ZillowEnrichment).filter(ZillowEnrichment.property_id == prop.id).first()
                    if existing and existing.zestimate:
                        results.append({"property_id": prop.id, "address": prop.address, "status": "skipped", "detail": "Already enriched"})
                        continue

                full_address = f"{prop.address}, {prop.city}, {prop.state} {prop.zip_code or ''}".strip()
                data = await svc.enrich_by_address(full_address)

                zestimate = data.get("zestimate")
                rent_zestimate = data.get("rent_zestimate") or data.get("rentZestimate")
                zpid = data.get("zpid")

                existing = db.query(ZillowEnrichment).filter(ZillowEnrichment.property_id == prop.id).first()
                if existing:
                    existing.zestimate = zestimate
                    existing.rent_zestimate = rent_zestimate
                    if zpid:
                        existing.zpid = int(zpid)
                    existing.photos = data.get("photos")
                    existing.reso_facts = data.get("reso_facts") or data.get("resoFacts")
                    existing.schools = data.get("schools")
                    existing.tax_history = data.get("tax_history") or data.get("taxHistory")
                    existing.price_history = data.get("price_history") or data.get("priceHistory")
                else:
                    new_e = ZillowEnrichment(
                        property_id=prop.id,
                        zpid=int(zpid) if zpid else None,
                        zestimate=zestimate,
                        rent_zestimate=rent_zestimate,
                        photos=data.get("photos"),
                        reso_facts=data.get("reso_facts") or data.get("resoFacts"),
                        schools=data.get("schools"),
                        tax_history=data.get("tax_history") or data.get("taxHistory"),
                        price_history=data.get("price_history") or data.get("priceHistory"),
                    )
                    db.add(new_e)

                db.commit()
                detail = f"Zestimate: ${zestimate:,.0f}" if zestimate else "Enriched (no Zestimate)"
                results.append({"property_id": prop.id, "address": prop.address, "status": "success", "detail": detail})
            except Exception as exc:
                db.rollback()
                logger.warning("Bulk enrich failed for property %s: %s", prop.id, exc)
                results.append({"property_id": prop.id, "address": prop.address, "status": "error", "detail": str(exc)})

        return results

    async def _bulk_skip_trace(self, db: Session, properties: list[Property], params: dict) -> list[dict]:
        force = params.get("force", False)
        svc = _get_skip_trace_service()
        results: list[dict] = []

        for prop in properties:
            try:
                if not force:
                    existing = db.query(SkipTrace).filter(SkipTrace.property_id == prop.id).first()
                    if existing and existing.owner_name and existing.owner_name != "Unknown":
                        results.append({"property_id": prop.id, "address": prop.address, "status": "skipped", "detail": f"Already traced: {existing.owner_name}"})
                        continue

                data = await svc.skip_trace(
                    address=prop.address,
                    city=prop.city,
                    state=prop.state,
                    zip_code=prop.zip_code or "",
                )

                owner_name = data.get("owner_name", "Unknown")
                phones = data.get("phone_numbers", [])
                emails = data.get("email_addresses", data.get("emails", []))

                existing = db.query(SkipTrace).filter(SkipTrace.property_id == prop.id).first()
                if existing:
                    existing.owner_name = owner_name
                    existing.phone_numbers = phones
                    existing.emails = emails
                    existing.mailing_address = data.get("mailing_address")
                    existing.raw_response = data
                else:
                    new_st = SkipTrace(
                        property_id=prop.id,
                        owner_name=owner_name,
                        phone_numbers=phones,
                        emails=emails,
                        mailing_address=data.get("mailing_address"),
                        raw_response=data,
                    )
                    db.add(new_st)

                db.commit()
                phone_count = len(phones)
                results.append({"property_id": prop.id, "address": prop.address, "status": "success", "detail": f"Owner: {owner_name}, {phone_count} phone(s)"})
            except Exception as exc:
                db.rollback()
                logger.warning("Bulk skip trace failed for property %s: %s", prop.id, exc)
                results.append({"property_id": prop.id, "address": prop.address, "status": "error", "detail": str(exc)})

        return results

    async def _bulk_attach_contracts(self, db: Session, properties: list[Property], params: dict) -> list[dict]:
        results: list[dict] = []
        for prop in properties:
            try:
                attached = contract_auto_attach_service.auto_attach_contracts(db, prop)
                db.commit()
                count = len(attached)
                detail = f"{count} contract(s) attached" if count else "No matching templates"
                results.append({"property_id": prop.id, "address": prop.address, "status": "success", "detail": detail})
            except Exception as exc:
                db.rollback()
                logger.warning("Bulk attach contracts failed for property %s: %s", prop.id, exc)
                results.append({"property_id": prop.id, "address": prop.address, "status": "error", "detail": str(exc)})
        return results

    async def _bulk_generate_recaps(self, db: Session, properties: list[Property], params: dict) -> list[dict]:
        results: list[dict] = []
        for prop in properties:
            try:
                recap = await property_recap_service.generate_recap(db=db, property=prop, trigger="bulk_operation")
                db.commit()
                results.append({"property_id": prop.id, "address": prop.address, "status": "success", "detail": f"Recap v{recap.version}"})
            except Exception as exc:
                db.rollback()
                logger.warning("Bulk recap failed for property %s: %s", prop.id, exc)
                results.append({"property_id": prop.id, "address": prop.address, "status": "error", "detail": str(exc)})
        return results

    async def _bulk_update_status(self, db: Session, properties: list[Property], params: dict) -> list[dict]:
        target_status_str = params.get("status")
        if not target_status_str:
            return [{"property_id": p.id, "address": p.address, "status": "error", "detail": "Missing 'status' param"} for p in properties]

        try:
            target_status = PropertyStatus(target_status_str)
        except ValueError:
            return [{"property_id": p.id, "address": p.address, "status": "error", "detail": f"Invalid status: {target_status_str}"} for p in properties]

        results: list[dict] = []
        for prop in properties:
            try:
                if prop.status == target_status:
                    results.append({"property_id": prop.id, "address": prop.address, "status": "skipped", "detail": f"Already {target_status.value}"})
                    continue

                old_status = prop.status.value
                prop.status = target_status
                db.commit()
                results.append({"property_id": prop.id, "address": prop.address, "status": "success", "detail": f"{old_status} → {target_status.value}"})
            except Exception as exc:
                db.rollback()
                logger.warning("Bulk status update failed for property %s: %s", prop.id, exc)
                results.append({"property_id": prop.id, "address": prop.address, "status": "error", "detail": str(exc)})
        return results

    async def _bulk_check_compliance(self, db: Session, properties: list[Property], params: dict) -> list[dict]:
        engine = _get_compliance_engine()
        results: list[dict] = []
        for prop in properties:
            try:
                check = await engine.run_compliance_check(db, prop, check_type="full")
                db.commit()
                detail = f"Passed: {check.passed_count}, Failed: {check.failed_count}, Warnings: {check.warning_count}"
                results.append({"property_id": prop.id, "address": prop.address, "status": "success", "detail": detail})
            except Exception as exc:
                db.rollback()
                logger.warning("Bulk compliance check failed for property %s: %s", prop.id, exc)
                results.append({"property_id": prop.id, "address": prop.address, "status": "error", "detail": str(exc)})
        return results

    # ── Helpers ──

    def list_operations(self) -> list[dict]:
        """Return metadata about each supported operation."""
        return list(_OPERATION_META)

    @staticmethod
    def _build_voice_summary(operation: str, total: int, succeeded: int, failed: int, skipped: int) -> str:
        op_labels = {
            "enrich": "Enriched",
            "skip_trace": "Skip traced",
            "attach_contracts": "Attached contracts for",
            "generate_recaps": "Generated recaps for",
            "update_status": "Updated status for",
            "check_compliance": "Ran compliance on",
        }
        label = op_labels.get(operation, operation.replace("_", " ").title())
        parts = [f"{label} {succeeded} of {total} properties."]
        if failed:
            parts.append(f"{failed} failed.")
        if skipped:
            parts.append(f"{skipped} skipped.")
        return " ".join(parts)


bulk_operations_service = BulkOperationsService()
