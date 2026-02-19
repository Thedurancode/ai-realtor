import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.activity_event import ActivityEvent, ActivityEventStatus, ActivityEventType
from app.models.offer import FinancingType, Offer, OfferStatus
from app.models.property import Property, PropertyStatus
from app.schemas.offer import (
    CounterOfferCreate,
    MAOResponse,
    OfferCreate,
    OfferResponse,
    OfferSummary,
    TriRangeOut,
)

logger = logging.getLogger(__name__)


def _log_offer_activity(db: Session, tool_name: str, offer: Offer, extra: dict | None = None) -> None:
    data = {
        "offer_id": offer.id,
        "property_id": offer.property_id,
        "offer_price": offer.offer_price,
        "status": offer.status.value,
    }
    if extra:
        data.update(extra)
    event = ActivityEvent(
        tool_name=tool_name,
        event_type=ActivityEventType.SYSTEM_EVENT,
        status=ActivityEventStatus.SUCCESS,
        data=json.dumps(data),
    )
    db.add(event)


def create_offer(db: Session, payload: OfferCreate) -> Offer:
    prop = db.query(Property).filter(Property.id == payload.property_id).first()
    if not prop:
        raise ValueError(f"Property {payload.property_id} not found")

    # Validate financing type
    try:
        fin_type = FinancingType(payload.financing_type.lower())
    except ValueError:
        fin_type = FinancingType.OTHER

    now = datetime.now(timezone.utc)
    expires_at = None
    if payload.expires_in_hours:
        expires_at = now + timedelta(hours=payload.expires_in_hours)

    # Snapshot MAO if underwriting data exists
    mao_low, mao_base, mao_high = _get_mao_snapshot(db, payload.property_id)

    offer = Offer(
        property_id=payload.property_id,
        buyer_contact_id=payload.buyer_contact_id,
        offer_price=payload.offer_price,
        earnest_money=payload.earnest_money,
        financing_type=fin_type,
        closing_days=payload.closing_days,
        contingencies=payload.contingencies or [],
        notes=payload.notes,
        is_our_offer=payload.is_our_offer,
        status=OfferStatus.SUBMITTED,
        submitted_at=now,
        expires_at=expires_at,
        mao_low=mao_low,
        mao_base=mao_base,
        mao_high=mao_high,
    )
    db.add(offer)
    db.flush()

    _log_offer_activity(db, "offer_created", offer)
    db.commit()
    db.refresh(offer)
    return offer


def counter_offer(db: Session, offer_id: int, payload: CounterOfferCreate) -> Offer:
    parent = db.query(Offer).filter(Offer.id == offer_id).first()
    if not parent:
        raise ValueError(f"Offer {offer_id} not found")
    if parent.status not in (OfferStatus.SUBMITTED, OfferStatus.COUNTERED):
        raise ValueError(f"Cannot counter an offer with status '{parent.status.value}'. Must be submitted or countered.")

    now = datetime.now(timezone.utc)

    # Mark parent as countered
    parent.status = OfferStatus.COUNTERED
    parent.responded_at = now

    expires_at = None
    if payload.expires_in_hours:
        expires_at = now + timedelta(hours=payload.expires_in_hours)

    child = Offer(
        property_id=parent.property_id,
        buyer_contact_id=parent.buyer_contact_id,
        parent_offer_id=parent.id,
        offer_price=payload.offer_price,
        earnest_money=payload.earnest_money if payload.earnest_money is not None else parent.earnest_money,
        financing_type=parent.financing_type,
        closing_days=payload.closing_days if payload.closing_days is not None else parent.closing_days,
        contingencies=payload.contingencies if payload.contingencies is not None else parent.contingencies,
        notes=payload.notes,
        is_our_offer=not parent.is_our_offer,
        status=OfferStatus.SUBMITTED,
        submitted_at=now,
        expires_at=expires_at,
        mao_low=parent.mao_low,
        mao_base=parent.mao_base,
        mao_high=parent.mao_high,
    )
    db.add(child)
    db.flush()

    _log_offer_activity(db, "offer_countered", child, {"parent_offer_id": parent.id})
    db.commit()
    db.refresh(child)
    return child


def accept_offer(db: Session, offer_id: int) -> Offer:
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise ValueError(f"Offer {offer_id} not found")
    if offer.status not in (OfferStatus.SUBMITTED, OfferStatus.COUNTERED):
        raise ValueError(f"Cannot accept offer with status '{offer.status.value}'")

    now = datetime.now(timezone.utc)
    offer.status = OfferStatus.ACCEPTED
    offer.responded_at = now

    # Side effect 1: Property → waiting_for_contracts
    prop = db.query(Property).filter(Property.id == offer.property_id).first()
    if prop and prop.status != PropertyStatus.COMPLETE:
        prop.status = PropertyStatus.WAITING_FOR_CONTRACTS

    # Side effect 2: Auto-reject other active offers on same property
    other_offers = (
        db.query(Offer)
        .filter(
            Offer.property_id == offer.property_id,
            Offer.id != offer.id,
            Offer.status.in_([OfferStatus.SUBMITTED, OfferStatus.COUNTERED, OfferStatus.DRAFT]),
        )
        .all()
    )
    for other in other_offers:
        other.status = OfferStatus.REJECTED
        other.responded_at = now

    _log_offer_activity(db, "offer_accepted", offer, {"rejected_count": len(other_offers)})
    db.commit()
    db.refresh(offer)

    # Side effect 3: Auto-attach contracts (best effort)
    try:
        from app.services.contract_auto_attach import ContractAutoAttachService

        if prop:
            service = ContractAutoAttachService()
            service.auto_attach_contracts(db=db, property=prop)
    except Exception as e:
        logger.warning(f"Failed to auto-attach contracts after offer acceptance: {e}")

    return offer


def reject_offer(db: Session, offer_id: int) -> Offer:
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise ValueError(f"Offer {offer_id} not found")
    if offer.status not in (OfferStatus.SUBMITTED, OfferStatus.COUNTERED):
        raise ValueError(f"Cannot reject offer with status '{offer.status.value}'")

    offer.status = OfferStatus.REJECTED
    offer.responded_at = datetime.now(timezone.utc)

    _log_offer_activity(db, "offer_rejected", offer)
    db.commit()
    db.refresh(offer)
    return offer


def withdraw_offer(db: Session, offer_id: int) -> Offer:
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        raise ValueError(f"Offer {offer_id} not found")
    if offer.status in (OfferStatus.ACCEPTED, OfferStatus.REJECTED):
        raise ValueError(f"Cannot withdraw offer with status '{offer.status.value}'")

    offer.status = OfferStatus.WITHDRAWN
    offer.responded_at = datetime.now(timezone.utc)

    _log_offer_activity(db, "offer_withdrawn", offer)
    db.commit()
    db.refresh(offer)
    return offer


def get_offer(db: Session, offer_id: int) -> Offer | None:
    return db.query(Offer).filter(Offer.id == offer_id).first()


def list_offers(
    db: Session,
    property_id: int | None = None,
    status: str | None = None,
) -> list[Offer]:
    q = db.query(Offer)
    if property_id is not None:
        q = q.filter(Offer.property_id == property_id)
    if status:
        try:
            status_enum = OfferStatus(status.lower())
            q = q.filter(Offer.status == status_enum)
        except ValueError:
            pass
    return q.order_by(Offer.created_at.desc()).all()


def get_negotiation_chain(db: Session, offer_id: int) -> list[Offer]:
    """Walk up to root, then collect all descendants in order."""
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if not offer:
        return []

    # Walk to root
    root = offer
    while root.parent_offer_id is not None:
        parent = db.query(Offer).filter(Offer.id == root.parent_offer_id).first()
        if not parent:
            break
        root = parent

    # Collect chain from root
    chain = [root]
    current = root
    while True:
        child = (
            db.query(Offer)
            .filter(Offer.parent_offer_id == current.id)
            .order_by(Offer.created_at.asc())
            .first()
        )
        if not child:
            break
        chain.append(child)
        current = child

    return chain


def get_offer_summary(db: Session, property_id: int) -> OfferSummary:
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise ValueError(f"Property {property_id} not found")

    offers = list_offers(db, property_id=property_id)
    active = [o for o in offers if o.status in (OfferStatus.SUBMITTED, OfferStatus.COUNTERED)]
    prices = [o.offer_price for o in active if o.offer_price]

    address = f"{prop.address}, {prop.city or ''}, {prop.state or ''}"

    # Build voice summary
    if not offers:
        voice = f"No offers on {address}."
    elif not active:
        voice = f"{len(offers)} total offer(s) on {address}, but none currently active. Latest status: {offers[0].status.value}."
    else:
        highest = max(prices) if prices else 0
        voice = (
            f"{len(active)} active offer(s) on {address}. "
            f"Highest: ${highest:,.0f}. "
            f"Total offers: {len(offers)}."
        )

    return OfferSummary(
        property_id=property_id,
        property_address=address,
        total_offers=len(offers),
        active_offers=len(active),
        highest_offer=max(prices) if prices else None,
        lowest_offer=min(prices) if prices else None,
        latest_status=offers[0].status.value if offers else None,
        offers=[OfferResponse.model_validate(o) for o in offers[:10]],
        voice_summary=voice,
    )


def calculate_mao(db: Session, property_id: int) -> MAOResponse:
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise ValueError(f"Property {property_id} not found")

    address = f"{prop.address}, {prop.city or ''}, {prop.state or ''}"

    # Try to find agentic research underwriting data
    arv_range = None
    offer_range = None
    strategy = "wholesale"
    explanation_parts = []

    try:
        from app.models.agentic_property import ResearchProperty
        from app.models.underwriting import Underwriting
        from app.models.agentic_job import AgenticJob, AgenticJobStatus

        # Find matching research property
        rp = (
            db.query(ResearchProperty)
            .filter(
                or_(
                    ResearchProperty.normalized_address.ilike(f"%{prop.address}%"),
                    ResearchProperty.raw_address.ilike(f"%{prop.address}%"),
                )
            )
            .first()
        )

        if rp:
            # Get latest completed job
            latest_job = (
                db.query(AgenticJob)
                .filter(
                    AgenticJob.research_property_id == rp.id,
                    AgenticJob.status == AgenticJobStatus.COMPLETED,
                )
                .order_by(AgenticJob.completed_at.desc())
                .first()
            )

            if latest_job:
                uw = (
                    db.query(Underwriting)
                    .filter(Underwriting.job_id == latest_job.id)
                    .order_by(Underwriting.id.desc())
                    .first()
                )
                if uw:
                    strategy = latest_job.strategy or "wholesale"
                    if uw.arv_low or uw.arv_base or uw.arv_high:
                        arv_range = TriRangeOut(low=uw.arv_low, base=uw.arv_base, high=uw.arv_high)
                        explanation_parts.append(f"ARV: ${uw.arv_base:,.0f}" if uw.arv_base else "ARV data available")
                    if uw.offer_low or uw.offer_base or uw.offer_high:
                        offer_range = TriRangeOut(low=uw.offer_low, base=uw.offer_base, high=uw.offer_high)
                        explanation_parts.append(
                            f"Recommended offer: ${uw.offer_low:,.0f}-${uw.offer_high:,.0f}"
                            if uw.offer_low and uw.offer_high
                            else f"Offer base: ${uw.offer_base:,.0f}" if uw.offer_base else ""
                        )
    except Exception as e:
        logger.warning(f"Failed to lookup underwriting for MAO: {e}")

    # Fallback: Zestimate × 0.7 rule
    zestimate = None
    if not offer_range:
        try:
            from app.models.zillow_enrichment import ZillowEnrichment

            ze = db.query(ZillowEnrichment).filter(ZillowEnrichment.property_id == property_id).first()
            if ze and ze.zestimate:
                zestimate = ze.zestimate
                fallback_offer = zestimate * 0.7
                offer_range = TriRangeOut(
                    low=round(fallback_offer * 0.9),
                    base=round(fallback_offer),
                    high=round(fallback_offer * 1.1),
                )
                explanation_parts.append(f"Zestimate: ${zestimate:,.0f} × 70% rule = ${fallback_offer:,.0f}")
        except Exception as e:
            logger.warning(f"Failed to lookup Zestimate for MAO: {e}")

    if not explanation_parts:
        explanation_parts.append("No underwriting or Zestimate data available. Run agentic research first for accurate MAO.")

    explanation = ". ".join(explanation_parts)

    # Voice summary
    if offer_range and offer_range.base:
        voice = f"For {address}, the maximum allowable offer is ${offer_range.base:,.0f} (range: ${offer_range.low:,.0f} to ${offer_range.high:,.0f}). {explanation}"
    else:
        voice = f"No MAO data available for {address}. {explanation}"

    return MAOResponse(
        property_id=property_id,
        address=address,
        arv=arv_range,
        offer_recommendation=offer_range,
        strategy=strategy,
        list_price=prop.price,
        zestimate=zestimate,
        explanation=explanation,
        voice_summary=voice,
    )


def expire_stale_offers(db: Session) -> int:
    now = datetime.now(timezone.utc)
    count = (
        db.query(Offer)
        .filter(
            Offer.status.in_([OfferStatus.SUBMITTED, OfferStatus.COUNTERED]),
            Offer.expires_at.isnot(None),
            Offer.expires_at < now,
        )
        .update({"status": OfferStatus.EXPIRED}, synchronize_session="fetch")
    )
    db.commit()
    return count


def _get_mao_snapshot(db: Session, property_id: int) -> tuple[float | None, float | None, float | None]:
    """Get MAO values from latest underwriting for snapshot."""
    try:
        from app.models.agentic_property import ResearchProperty
        from app.models.underwriting import Underwriting
        from app.models.agentic_job import AgenticJob, AgenticJobStatus

        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return None, None, None

        rp = (
            db.query(ResearchProperty)
            .filter(
                or_(
                    ResearchProperty.normalized_address.ilike(f"%{prop.address}%"),
                    ResearchProperty.raw_address.ilike(f"%{prop.address}%"),
                )
            )
            .first()
        )
        if not rp:
            return None, None, None

        latest_job = (
            db.query(AgenticJob)
            .filter(
                AgenticJob.research_property_id == rp.id,
                AgenticJob.status == AgenticJobStatus.COMPLETED,
            )
            .order_by(AgenticJob.completed_at.desc())
            .first()
        )
        if not latest_job:
            return None, None, None

        uw = db.query(Underwriting).filter(Underwriting.job_id == latest_job.id).order_by(Underwriting.id.desc()).first()
        if uw:
            return uw.offer_low, uw.offer_base, uw.offer_high
    except Exception:
        pass
    return None, None, None
