"""
Property Recap Service

Generates and maintains AI-powered property summaries that automatically
update when property data changes. Used for phone calls and voice interactions.
"""
import os
import logging
from typing import Optional
from sqlalchemy.orm import Session
from anthropic import Anthropic
import json

logger = logging.getLogger(__name__)

from app.models.property import Property
from app.models.property_recap import PropertyRecap
from app.models.contract import Contract, ContractStatus
from app.models.zillow_enrichment import ZillowEnrichment
from app.models.contact import Contact
from app.models.property_note import PropertyNote
from app.services.contract_auto_attach import contract_auto_attach_service
from app.services.deal_type_service import get_deal_type_summary


class PropertyRecapService:
    """Generate and manage AI property recaps"""

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def generate_recap(
        self,
        db: Session,
        property: Property,
        trigger: str = "manual"
    ) -> PropertyRecap:
        """
        Generate or update AI recap for a property.

        Args:
            db: Database session
            property: Property to recap
            trigger: What triggered this update (e.g., "property_created", "contract_signed")

        Returns:
            PropertyRecap with AI-generated content
        """
        # Gather all property data
        context = self._gather_property_context(db, property)

        # Generate AI recap
        recap_text, voice_summary, structured_context = await self._generate_ai_recap(context)

        # Get or create recap record
        recap = db.query(PropertyRecap).filter(
            PropertyRecap.property_id == property.id
        ).first()

        if recap:
            # Update existing
            recap.recap_text = recap_text
            recap.voice_summary = voice_summary
            recap.recap_context = structured_context
            recap.last_trigger = trigger
            recap.version += 1
        else:
            # Create new
            recap = PropertyRecap(
                property_id=property.id,
                recap_text=recap_text,
                voice_summary=voice_summary,
                recap_context=structured_context,
                last_trigger=trigger,
                version=1
            )
            db.add(recap)

        db.commit()
        db.refresh(recap)

        # Auto-embed the recap for vector search
        try:
            from app.services.embedding_service import embedding_service
            embedding_service.embed_recap(db, recap.id)
        except Exception as e:
            logger.warning(f"Failed to auto-embed recap {recap.id}: {e}")

        return recap

    def _gather_property_context(self, db: Session, property: Property) -> dict:
        """Gather all relevant property data for recap generation"""

        # Get contracts
        contracts = db.query(Contract).filter(
            Contract.property_id == property.id
        ).all()

        # Get enrichment data
        enrichment = db.query(ZillowEnrichment).filter(
            ZillowEnrichment.property_id == property.id
        ).first()

        # Get contacts
        contacts = db.query(Contact).filter(
            Contact.property_id == property.id
        ).all()

        # Get notes
        notes = (
            db.query(PropertyNote)
            .filter(PropertyNote.property_id == property.id)
            .order_by(PropertyNote.created_at.desc())
            .limit(20)
            .all()
        )

        # Get contract readiness
        readiness = contract_auto_attach_service.get_required_contracts_status(db, property)

        # Get deal type info
        deal_type_info = None
        if property.deal_type:
            deal_summary = get_deal_type_summary(db, property)
            deal_type_info = {
                "deal_type": deal_summary.get("deal_type"),
                "deal_type_name": deal_summary.get("deal_type_name"),
                "contracts_completed": deal_summary.get("contracts", {}).get("completed", 0),
                "contracts_total": deal_summary.get("contracts", {}).get("total", 0),
                "contracts_pending": deal_summary.get("contracts", {}).get("pending_names", []),
                "checklist_completed": deal_summary.get("checklist", {}).get("completed", 0),
                "checklist_total": deal_summary.get("checklist", {}).get("total", 0),
                "checklist_pending": [
                    item["title"] for item in deal_summary.get("checklist", {}).get("pending_items", [])
                ],
                "missing_contacts": deal_summary.get("contacts", {}).get("missing_roles", []),
                "ready_to_close": deal_summary.get("ready_to_close", False),
            }

        return {
            "property": {
                "id": property.id,
                "address": f"{property.address}, {property.city}, {property.state} {property.zip_code}",
                "price": property.price,
                "bedrooms": property.bedrooms,
                "bathrooms": property.bathrooms,
                "square_feet": property.square_feet,
                "property_type": property.property_type.value if property.property_type else None,
                "status": property.status.value if property.status else None,
                "year_built": property.year_built,
                "deal_type": property.deal_type.value if property.deal_type else None,
            },
            "deal_type": deal_type_info,
            "contracts": [
                {
                    "id": c.id,
                    "name": c.name,
                    "status": c.status.value,
                    "is_required": c.is_required,
                    "requirement_source": c.requirement_source.value if c.requirement_source else None,
                }
                for c in contracts
            ],
            "contract_readiness": {
                "is_ready_to_close": readiness.get("is_ready_to_close", False),
                "total_required": readiness.get("total_required", 0),
                "completed": readiness.get("completed", 0),
                "in_progress": readiness.get("in_progress", 0),
                "missing": readiness.get("missing", 0),
            },
            "enrichment": {
                "zestimate": enrichment.zestimate if enrichment else None,
                "rent_zestimate": enrichment.rent_zestimate if enrichment else None,
                "schools": enrichment.schools[:3] if enrichment and enrichment.schools else [],
            } if enrichment else None,
            "contacts": [
                {
                    "name": c.name,
                    "role": c.role,
                    "email": c.email,
                    "phone": c.phone,
                }
                for c in contacts
            ],
            "notes": [
                {
                    "content": n.content,
                    "source": n.source.value if n.source else "manual",
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in notes
            ],
        }

    async def _generate_ai_recap(self, context: dict) -> tuple[str, str, dict]:
        """
        Generate AI recap from property context.

        Returns:
            (recap_text, voice_summary, structured_context)
        """
        property_info = context["property"]
        contracts_info = context["contracts"]
        readiness_info = context["contract_readiness"]
        enrichment_info = context.get("enrichment")
        contacts_info = context["contacts"]
        deal_type_info = context.get("deal_type")
        notes_info = context.get("notes", [])

        # Build prompt
        prompt = f"""You are a real estate assistant generating a comprehensive property summary for phone calls and voice interactions.

PROPERTY DETAILS:
Address: {property_info['address']}
Price: ${property_info['price']:,.0f}
Type: {property_info['property_type']}
Status: {property_info['status']}
Deal Type: {property_info.get('deal_type') or 'Not set'}
Bedrooms: {property_info['bedrooms'] or 'N/A'}
Bathrooms: {property_info['bathrooms'] or 'N/A'}
Square Feet: {property_info['square_feet'] or 'N/A'}
Year Built: {property_info['year_built'] or 'N/A'}

{self._format_deal_type_for_prompt(deal_type_info)}

CONTRACT STATUS:
Ready to Close: {'YES' if readiness_info['is_ready_to_close'] else 'NO'}
Total Required Contracts: {readiness_info['total_required']}
Completed: {readiness_info['completed']}
In Progress: {readiness_info['in_progress']}
Missing: {readiness_info['missing']}

Contracts:
{self._format_contracts_for_prompt(contracts_info)}

{"ENRICHMENT DATA:" if enrichment_info else ""}
{self._format_enrichment_for_prompt(enrichment_info) if enrichment_info else ""}

CONTACTS ({len(contacts_info)}):
{self._format_contacts_for_prompt(contacts_info)}

{self._format_notes_for_prompt(notes_info)}

Generate TWO summaries:

1. DETAILED RECAP (3-4 paragraphs):
   - Comprehensive property overview
   - Current status and transaction readiness
   - Contract status and what's needed
   - Key highlights, concerns, and any relevant notes from the agent
   - Next steps

2. VOICE SUMMARY (2-3 sentences):
   - Ultra-concise for phone/TTS
   - Focus on most critical info
   - Natural conversational tone
   - Perfect for "Tell me about this property"

Return as JSON:
{{
    "detailed_recap": "...",
    "voice_summary": "...",
    "key_facts": [
        "3 bed, 2 bath condo",
        "Ready to close",
        "All contracts signed"
    ],
    "concerns": [
        "Missing lead paint disclosure"
    ],
    "next_steps": [
        "Schedule final walkthrough",
        "Review closing documents"
    ]
}}"""

        # Call Claude
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        response_text = response.content[0].text

        # Extract JSON
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(response_text)

        # Build structured context for VAPI
        structured_context = {
            "property": property_info,
            "deal_type": deal_type_info,
            "contracts": contracts_info,
            "readiness": readiness_info,
            "enrichment": enrichment_info,
            "contacts": contacts_info,
            "notes": notes_info,
            "ai_summary": {
                "detailed": result.get("detailed_recap", ""),
                "voice": result.get("voice_summary", ""),
                "key_facts": result.get("key_facts", []),
                "concerns": result.get("concerns", []),
                "next_steps": result.get("next_steps", []),
            }
        }

        recap_text = result.get("detailed_recap", "")
        voice_summary = result.get("voice_summary", "")

        return recap_text, voice_summary, structured_context

    def _format_deal_type_for_prompt(self, deal_type_info: dict) -> str:
        """Format deal type info for AI prompt"""
        if not deal_type_info:
            return ""

        lines = [f"DEAL TYPE: {deal_type_info['deal_type']}"]
        lines.append(f"Contracts: {deal_type_info['contracts_completed']}/{deal_type_info['contracts_total']} completed")
        if deal_type_info.get('contracts_pending'):
            lines.append(f"Pending contracts: {', '.join(deal_type_info['contracts_pending'])}")
        lines.append(f"Checklist: {deal_type_info['checklist_completed']}/{deal_type_info['checklist_total']} completed")
        if deal_type_info.get('checklist_pending'):
            lines.append(f"Pending checklist items: {', '.join(deal_type_info['checklist_pending'])}")
        if deal_type_info.get('missing_contacts'):
            lines.append(f"Missing required contacts: {', '.join(deal_type_info['missing_contacts'])}")
        lines.append(f"Ready to close: {'YES' if deal_type_info['ready_to_close'] else 'NO'}")
        return "\n".join(lines)

    def _format_contracts_for_prompt(self, contracts: list) -> str:
        """Format contracts for AI prompt"""
        if not contracts:
            return "  None"

        lines = []
        for c in contracts:
            req_status = "REQUIRED" if c.get("is_required") else "OPTIONAL"
            lines.append(
                f"  - {c['name']}: {c['status'].upper()} ({req_status}, source: {c.get('requirement_source', 'unknown')})"
            )
        return "\n".join(lines)

    def _format_enrichment_for_prompt(self, enrichment: dict) -> str:
        """Format enrichment data for AI prompt"""
        if not enrichment:
            return ""

        lines = []
        if enrichment.get("zestimate"):
            lines.append(f"Zestimate: ${enrichment['zestimate']:,.0f}")
        if enrichment.get("rent_zestimate"):
            lines.append(f"Rent Zestimate: ${enrichment['rent_zestimate']:,.0f}/month")
        if enrichment.get("schools"):
            lines.append(f"Nearby Schools: {len(enrichment['schools'])} (top rated)")

        return "\n".join(lines)

    def _format_contacts_for_prompt(self, contacts: list) -> str:
        """Format contacts for AI prompt"""
        if not contacts:
            return "  None"

        lines = []
        for c in contacts:
            lines.append(f"  - {c['name']} ({c['role']})")
        return "\n".join(lines)

    def _format_notes_for_prompt(self, notes: list) -> str:
        """Format property notes for AI prompt"""
        if not notes:
            return ""

        lines = [f"AGENT NOTES ({len(notes)}):"]
        for n in notes:
            source = n.get("source", "manual")
            lines.append(f"  - [{source}] {n['content']}")
        return "\n".join(lines)

    def get_recap(self, db: Session, property_id: int) -> Optional[PropertyRecap]:
        """Get existing recap for a property"""
        return db.query(PropertyRecap).filter(
            PropertyRecap.property_id == property_id
        ).first()

    async def ensure_recap_exists(
        self,
        db: Session,
        property: Property,
        trigger: str = "auto"
    ) -> PropertyRecap:
        """
        Ensure a recap exists for a property, creating if needed.
        Used for lazy generation.
        """
        recap = self.get_recap(db, property.id)

        if not recap:
            # Generate for first time
            recap = await self.generate_recap(db, property, trigger)

        return recap


# Singleton instance
property_recap_service = PropertyRecapService()


async def regenerate_recap_background(property_id: int, trigger: str) -> None:
    """Background-safe recap regeneration with its own DB session.

    Use this with FastAPI BackgroundTasks so the recap runs after the
    request's DB session is closed.
    """
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        prop = db.query(Property).filter(Property.id == property_id).first()
        if prop:
            await property_recap_service.generate_recap(db, prop, trigger=trigger)
    except Exception as exc:
        logger.warning("Background recap failed for property %s: %s", property_id, exc)
    finally:
        db.close()
