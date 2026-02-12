"""PDF Report Service — orchestrates data gathering, PDF generation, and emailing."""
import logging
from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.agent import Agent
from app.models.zillow_enrichment import ZillowEnrichment
from app.services.property_recap_service import property_recap_service
from app.services.resend_service import resend_service
from app.services.reports import get_report, list_report_types

logger = logging.getLogger(__name__)


def generate_and_send(
    db: Session,
    property_id: int,
    report_type: str,
    agent_id: int,
) -> dict:
    """
    Build context, generate PDF, and email it to the agent.

    Returns dict with success status, email result, and filename.
    """
    # 1. Load property
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise ValueError(f"Property {property_id} not found")

    # 2. Load agent
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise ValueError(f"Agent {agent_id} not found")
    if not agent.email:
        raise ValueError(f"Agent {agent_id} has no email address")

    # 3. Gather context (reuse recap service helper)
    context = property_recap_service._gather_property_context(db, prop)

    # 4. Augment context with extra data the PDF needs
    enrichment = db.query(ZillowEnrichment).filter(
        ZillowEnrichment.property_id == property_id
    ).first()

    if enrichment and enrichment.photos:
        photos = enrichment.photos
        if isinstance(photos, str):
            import json
            photos = json.loads(photos)
        context["photos"] = photos[:5]  # first 5 photos

    context["agent_name"] = agent.name
    context["deal_score"] = prop.deal_score
    context["score_grade"] = prop.score_grade

    # 5. Generate PDF
    report = get_report(report_type)
    pdf_buf = report.generate(context)
    pdf_bytes = pdf_buf.read()
    filename = report.get_filename(context)

    # 6. Email to agent
    address = context["property"]["address"]
    email_result = resend_service.send_report_email(
        to_email=agent.email,
        to_name=agent.name,
        report_name=report.display_name,
        property_address=address,
        pdf_content=pdf_bytes,
        pdf_filename=filename,
    )

    return {
        "success": email_result.get("success", False),
        "email": email_result,
        "filename": filename,
        "report_type": report_type,
        "property_id": property_id,
        "property_address": address,
        "agent_email": agent.email,
    }
