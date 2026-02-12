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
    Compute a deal quality score (0-100) from enrichment and skip trace data.

    Components (weights re-normalized when data is missing):
      - Zestimate vs Price: 30  (higher spread = better deal)
      - Days on Market:     20  (longer DOM = more motivated seller)
      - Price Trend:        20  (declining history = negotiation opportunity)
      - Tax vs Price:       10  (tax assessment below price = potential overpricing)
      - School Quality:     10  (higher avg rating = better resale)
      - Skip Trace Reach:   10  (has phone/email = easier to contact)

    Returns dict with score, grade, and breakdown. Also saves to property.
    """
    enrichment = (
        db.query(ZillowEnrichment)
        .filter(ZillowEnrichment.property_id == prop.id)
        .first()
    )
    skip_trace = (
        db.query(SkipTrace)
        .filter(SkipTrace.property_id == prop.id)
        .order_by(SkipTrace.created_at.desc())
        .first()
    )

    components: list[tuple[str, float, float]] = []  # (name, weight, score 0-100)

    # 1. Zestimate vs Price
    if enrichment and enrichment.zestimate and prop.price and prop.price > 0:
        spread = (enrichment.zestimate - prop.price) / prop.price
        # spread of +20% or more → 100, 0% → 50, -20% or worse → 0
        score = max(0.0, min(100.0, 50 + spread * 250))
        components.append(("zestimate_vs_price", 30, score))

    # 2. Days on Market
    if enrichment and enrichment.days_on_zillow is not None:
        dom = enrichment.days_on_zillow
        # 0 days → 0, 90+ days → 100 (more motivated seller)
        score = max(0.0, min(100.0, dom / 90 * 100))
        components.append(("days_on_market", 20, score))

    # 3. Price Trend (declining = opportunity)
    if enrichment and enrichment.price_history:
        prices = [
            p["price"] for p in enrichment.price_history
            if p.get("price") and p.get("event") in ("Listed for sale", "Price change", None)
        ]
        if len(prices) >= 2:
            # Compare most recent to oldest in history
            newest, oldest = prices[0], prices[-1]
            if oldest > 0:
                change = (newest - oldest) / oldest
                # -20% drop → 100, 0% → 50, +20% rise → 0
                score = max(0.0, min(100.0, 50 - change * 250))
                components.append(("price_trend", 20, score))

    # 4. Tax Assessment vs Price
    if enrichment and enrichment.tax_history and prop.price and prop.price > 0:
        latest_tax = enrichment.tax_history[0] if enrichment.tax_history else None
        if latest_tax and latest_tax.get("value") and latest_tax["value"] > 0:
            tax_val = latest_tax["value"]
            gap = (prop.price - tax_val) / prop.price
            # If price is 30%+ above tax assessment → 100 (overpriced, room to negotiate)
            # If price equals assessment → 50, below assessment → 0
            score = max(0.0, min(100.0, gap * 333))
            components.append(("tax_vs_price", 10, score))

    # 5. School Quality
    if enrichment and enrichment.schools:
        ratings = [s["rating"] for s in enrichment.schools if s.get("rating")]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            # Rating 1-10 scale → 0-100
            score = max(0.0, min(100.0, avg_rating * 10))
            components.append(("school_quality", 10, score))

    # 6. Skip Trace Reachability
    if skip_trace:
        has_phones = bool(skip_trace.phone_numbers and len(skip_trace.phone_numbers) > 0)
        has_emails = bool(skip_trace.emails and len(skip_trace.emails) > 0)
        has_name = bool(skip_trace.owner_name and skip_trace.owner_name != "Unknown Owner")
        score = 0.0
        if has_name:
            score += 40
        if has_phones:
            score += 30
        if has_emails:
            score += 30
        components.append(("skip_trace_reachability", 10, score))

    # Compute weighted score (re-normalize weights when data is missing)
    if not components:
        result = {"score": 0, "grade": "F", "breakdown": {}}
        prop.deal_score = 0
        prop.score_grade = "F"
        prop.score_breakdown = result["breakdown"]
        db.commit()
        return result

    total_weight = sum(w for _, w, _ in components)
    weighted_sum = sum(w * s for _, w, s in components)
    final_score = round(weighted_sum / total_weight, 1)

    # Grade scale
    if final_score >= 80:
        grade = "A"
    elif final_score >= 60:
        grade = "B"
    elif final_score >= 40:
        grade = "C"
    elif final_score >= 20:
        grade = "D"
    else:
        grade = "F"

    breakdown = {name: round(score, 1) for name, _, score in components}

    # Save to property
    prop.deal_score = final_score
    prop.score_grade = grade
    prop.score_breakdown = breakdown
    db.commit()

    return {"score": final_score, "grade": grade, "breakdown": breakdown}
