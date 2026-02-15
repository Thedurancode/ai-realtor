"""
Auto-enrich pipeline and deal quality scoring service.

Runs Zillow enrichment + skip trace in parallel as background tasks
after property creation, then computes a deal quality score (0-100).
"""
import asyncio
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.property import Property
from app.models.zillow_enrichment import ZillowEnrichment
from app.models.skip_trace import SkipTrace
from app.services.zillow_enrichment import zillow_enrichment_service
from app.services.skip_trace import skip_trace_service
from app.services.property_recap_service import property_recap_service

logger = logging.getLogger(__name__)


async def run_auto_enrich_pipeline(property_id: int) -> None:
    """
    Background task: enrich a property with Zillow data and skip trace in parallel,
    then compute a deal quality score.
    """
    db = SessionLocal()
    try:
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            logger.error(f"Pipeline: property {property_id} not found")
            return

        # Mark pipeline as running
        prop.pipeline_status = "running"
        prop.pipeline_started_at = datetime.utcnow()
        db.commit()

        full_address = f"{prop.address}, {prop.city}, {prop.state} {prop.zip_code}"

        # Run enrichment and skip trace in parallel
        enrich_result, skip_result = await asyncio.gather(
            zillow_enrichment_service.enrich_by_address(full_address),
            skip_trace_service.skip_trace(prop.address, prop.city, prop.state, prop.zip_code),
            return_exceptions=True,
        )

        # Save enrichment (if successful)
        if isinstance(enrich_result, Exception):
            logger.warning(f"Pipeline: enrichment failed for property {property_id}: {enrich_result}")
        else:
            _save_enrichment(db, prop.id, enrich_result)

        # Save skip trace (if successful)
        if isinstance(skip_result, Exception):
            logger.warning(f"Pipeline: skip trace failed for property {property_id}: {skip_result}")
        else:
            _save_skip_trace(db, prop.id, skip_result)

        db.commit()

        # Re-fetch property to get fresh relationships
        db.refresh(prop)

        # Calculate score
        calculate_property_score(db, prop)

        # Generate AI recap with all the fresh data
        try:
            await property_recap_service.generate_recap(db, prop, trigger="pipeline_completed")
        except Exception as recap_exc:
            logger.warning(f"Pipeline: recap generation failed for property {property_id}: {recap_exc}")

        # Mark pipeline completed
        prop.pipeline_status = "completed"
        prop.pipeline_completed_at = datetime.utcnow()
        db.commit()

        logger.info(
            f"Pipeline completed for property {property_id}: "
            f"score={prop.deal_score}, grade={prop.score_grade}"
        )

    except Exception as exc:
        logger.exception(f"Pipeline failed for property {property_id}: {exc}")
        try:
            prop = db.query(Property).filter(Property.id == property_id).first()
            if prop:
                prop.pipeline_status = "failed"
                prop.pipeline_completed_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def _save_enrichment(db: Session, property_id: int, data: dict[str, Any]) -> None:
    """Save Zillow enrichment data, updating existing record or creating new one."""
    existing = db.query(ZillowEnrichment).filter(ZillowEnrichment.property_id == property_id).first()

    if existing:
        for key, value in data.items():
            if key != "raw_response":
                setattr(existing, key.replace("-", "_"), value)
        existing.raw_response = data.get("raw_response")
    else:
        enrichment = ZillowEnrichment(
            property_id=property_id,
            zpid=data.get("zpid"),
            zestimate=data.get("zestimate"),
            zestimate_low=None,
            zestimate_high=None,
            rent_zestimate=data.get("rent_zestimate"),
            living_area=data.get("living_area"),
            lot_size=data.get("lot_area_value"),
            lot_area_units=data.get("lot_area_units"),
            year_built=data.get("year_built"),
            home_type=data.get("home_type"),
            home_status=data.get("home_status"),
            days_on_zillow=data.get("days_on_zillow"),
            page_view_count=data.get("page_view_count"),
            favorite_count=data.get("favorite_count"),
            property_tax_rate=data.get("property_tax_rate"),
            annual_tax_amount=data.get("annual_tax_amount"),
            hdp_url=data.get("hdp_url"),
            zillow_url=data.get("zillow_url"),
            photos=data.get("photos"),
            description=data.get("description"),
            schools=data.get("schools"),
            tax_history=data.get("tax_history"),
            price_history=data.get("price_history"),
            reso_facts=data.get("reso_facts"),
            raw_response=data.get("raw_response"),
        )
        db.add(enrichment)


def _save_skip_trace(db: Session, property_id: int, data: dict[str, Any]) -> None:
    """Save skip trace result as a new record."""
    skip_trace = SkipTrace(
        property_id=property_id,
        owner_name=data["owner_name"],
        owner_first_name=data["owner_first_name"],
        owner_last_name=data["owner_last_name"],
        phone_numbers=data["phone_numbers"],
        emails=data["emails"],
        mailing_address=data["mailing_address"],
        mailing_city=data["mailing_city"],
        mailing_state=data["mailing_state"],
        mailing_zip=data["mailing_zip"],
        raw_response=data.get("raw_response"),
    )
    db.add(skip_trace)


def calculate_property_score(db: Session, prop: Property) -> dict[str, Any]:
    """
    Compute a deal quality score (0-100) using the 4-dimension scoring engine.

    Delegates to PropertyScoringService which scores across:
      - Market (30%): Zestimate spread, DOM, price trend, schools, tax gap
      - Financial (25%): Upside potential, rental yield, price per sqft
      - Readiness (25%): Contracts, contacts, skip trace reachability
      - Engagement (20%): Recent activity, notes, tasks, notifications

    Returns dict with score, grade, and breakdown. Also saves to property.
    """
    from app.services.property_scoring_service import property_scoring_service

    result = property_scoring_service.score_property(db, prop.id, save=True)
    if result.get("error"):
        return {"score": 0, "grade": "F", "breakdown": {}}

    return {
        "score": result["score"],
        "grade": result["grade"],
        "breakdown": result.get("breakdown", {}),
    }
