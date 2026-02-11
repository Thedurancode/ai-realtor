"""
Offer Drafter Service

Generates professional AI-powered offer letters using Claude, incorporating
property data, deal score, enrichment data, MAO analysis, and negotiation strategy.
Stores result as a DRAFT Contract ready for DocuSeal signing.
"""
import json
import logging
import os
import re
from datetime import datetime, timezone

from anthropic import Anthropic
from sqlalchemy.orm import Session

from app.models.contract import Contract, ContractStatus, RequirementSource
from app.models.contract_template import ContractTemplate
from app.models.offer import Offer
from app.models.property import Property
from app.models.skip_trace import SkipTrace
from app.models.zillow_enrichment import ZillowEnrichment
from app.services import offer_service
from app.services.docuseal import docuseal_client

logger = logging.getLogger(__name__)


class OfferDrafterService:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def draft_from_offer(self, db: Session, offer_id: int) -> dict:
        """Draft an offer letter from an existing Offer record."""
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer:
            raise ValueError(f"Offer {offer_id} not found")

        prop = db.query(Property).filter(Property.id == offer.property_id).first()
        if not prop:
            raise ValueError(f"Property {offer.property_id} not found")

        offer_data = {
            "offer_price": offer.offer_price,
            "earnest_money": offer.earnest_money,
            "financing_type": offer.financing_type.value if offer.financing_type else "cash",
            "closing_days": offer.closing_days,
            "contingencies": offer.contingencies or [],
            "buyer_contact_id": offer.buyer_contact_id,
        }

        # Resolve buyer info from contact
        buyer_name = None
        buyer_email = None
        if offer.buyer_contact:
            buyer_name = offer.buyer_contact.name
            buyer_email = offer.buyer_contact.email
            offer_data["buyer_name"] = buyer_name
            offer_data["buyer_email"] = buyer_email

        context = self._gather_context(db, prop, offer_data)
        result = await self._generate_letter(context)
        contract, docuseal_template_id = self._create_contract(
            db, prop, result["letter_text"], offer.offer_price,
            offer.buyer_contact_id, result.get("template_fields"),
        )

        # Pre-fill DocuSeal submission when buyer email is available
        if docuseal_template_id and buyer_email and result.get("template_fields"):
            await self._prefill_docuseal(
                db, contract, result["template_fields"], buyer_email, buyer_name,
            )

        return {
            "letter_text": result["letter_text"],
            "contract_id": contract.id,
            "negotiation_strategy": result["negotiation_strategy"],
            "talking_points": result["talking_points"],
            "voice_summary": result["voice_summary"],
            "docuseal_template_id": docuseal_template_id,
        }

    async def draft_standalone(
        self,
        db: Session,
        property_id: int,
        offer_price: float,
        financing_type: str = "cash",
        closing_days: int = 30,
        contingencies: list[str] | None = None,
        earnest_money: float | None = None,
        buyer_name: str | None = None,
        buyer_email: str | None = None,
    ) -> dict:
        """Draft an offer letter without a pre-existing Offer record."""
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            raise ValueError(f"Property {property_id} not found")

        offer_data = {
            "offer_price": offer_price,
            "earnest_money": earnest_money,
            "financing_type": financing_type,
            "closing_days": closing_days,
            "contingencies": contingencies or [],
            "buyer_name": buyer_name,
            "buyer_email": buyer_email,
            "buyer_contact_id": None,
        }

        context = self._gather_context(db, prop, offer_data)
        result = await self._generate_letter(context)
        contract, docuseal_template_id = self._create_contract(
            db, prop, result["letter_text"], offer_price, None,
            result.get("template_fields"),
        )

        # Pre-fill DocuSeal submission when buyer email is available
        if docuseal_template_id and buyer_email and result.get("template_fields"):
            await self._prefill_docuseal(
                db, contract, result["template_fields"], buyer_email, buyer_name,
            )

        return {
            "letter_text": result["letter_text"],
            "contract_id": contract.id,
            "negotiation_strategy": result["negotiation_strategy"],
            "talking_points": result["talking_points"],
            "voice_summary": result["voice_summary"],
            "docuseal_template_id": docuseal_template_id,
        }

    def _gather_context(self, db: Session, property: Property, offer_data: dict) -> dict:
        """Assemble all available data for the AI prompt."""
        address = f"{property.address}, {property.city}, {property.state} {property.zip_code}"

        # Property details
        prop_ctx = {
            "address": address,
            "price": property.price,
            "bedrooms": property.bedrooms,
            "bathrooms": property.bathrooms,
            "square_feet": property.square_feet,
            "property_type": property.property_type.value if property.property_type else "Not available",
            "year_built": property.year_built,
            "status": property.status.value if property.status else "Not available",
        }

        # Deal score
        score_ctx = {
            "deal_score": property.deal_score,
            "score_grade": property.score_grade,
            "score_breakdown": property.score_breakdown,
        }

        # Zillow enrichment
        enrichment = db.query(ZillowEnrichment).filter(
            ZillowEnrichment.property_id == property.id
        ).first()
        enrich_ctx = None
        if enrichment:
            enrich_ctx = {
                "zestimate": enrichment.zestimate,
                "rent_zestimate": enrichment.rent_zestimate,
                "days_on_zillow": enrichment.days_on_zillow,
                "price_history": enrichment.price_history[:5] if enrichment.price_history else [],
                "tax_history": enrichment.tax_history[:3] if enrichment.tax_history else [],
                "schools": enrichment.schools[:3] if enrichment.schools else [],
            }

        # MAO analysis
        mao_ctx = None
        try:
            mao = offer_service.calculate_mao(db=db, property_id=property.id)
            mao_ctx = {
                "offer_recommendation": {
                    "low": mao.offer_recommendation.low if mao.offer_recommendation else None,
                    "base": mao.offer_recommendation.base if mao.offer_recommendation else None,
                    "high": mao.offer_recommendation.high if mao.offer_recommendation else None,
                },
                "arv": {
                    "low": mao.arv.low if mao.arv else None,
                    "base": mao.arv.base if mao.arv else None,
                    "high": mao.arv.high if mao.arv else None,
                },
                "strategy": mao.strategy,
                "explanation": mao.explanation,
            }
        except Exception as e:
            logger.warning(f"Failed to get MAO for offer letter: {e}")

        # Skip trace owner info
        skip = db.query(SkipTrace).filter(
            SkipTrace.property_id == property.id
        ).order_by(SkipTrace.created_at.desc()).first()
        owner_ctx = None
        if skip:
            owner_ctx = {
                "owner_name": skip.owner_name,
                "mailing_address": skip.mailing_address,
            }

        # Buyer info
        buyer_ctx = {
            "name": offer_data.get("buyer_name") or "Not specified",
            "email": offer_data.get("buyer_email") or "Not specified",
        }

        return {
            "property": prop_ctx,
            "deal_score": score_ctx,
            "enrichment": enrich_ctx,
            "mao": mao_ctx,
            "owner": owner_ctx,
            "buyer": buyer_ctx,
            "offer": {
                "price": offer_data["offer_price"],
                "earnest_money": offer_data.get("earnest_money"),
                "financing_type": offer_data.get("financing_type", "cash"),
                "closing_days": offer_data.get("closing_days", 30),
                "contingencies": offer_data.get("contingencies", []),
            },
        }

    async def _generate_letter(self, context: dict) -> dict:
        """Call Claude to generate the offer letter and supporting outputs."""
        prop = context["property"]
        offer = context["offer"]
        score = context["deal_score"]
        enrich = context.get("enrichment")
        mao = context.get("mao")
        owner = context.get("owner")
        buyer = context["buyer"]

        prompt = f"""You are a real estate professional drafting a formal offer letter.
Use the data below to produce a compelling, professional offer letter and negotiation guidance.

PROPERTY:
Address: {prop['address']}
List Price: ${prop['price']:,.0f}
Type: {prop['property_type']}
Bedrooms: {prop.get('bedrooms') or 'N/A'} | Bathrooms: {prop.get('bathrooms') or 'N/A'}
Square Feet: {prop.get('square_feet') or 'N/A'}
Year Built: {prop.get('year_built') or 'N/A'}

DEAL SCORE:
Score: {score.get('deal_score') or 'Not available'}
Grade: {score.get('score_grade') or 'Not available'}
Breakdown: {json.dumps(score.get('score_breakdown')) if score.get('score_breakdown') else 'Not available'}

ENRICHMENT DATA:
{self._fmt_enrichment(enrich)}

MAO ANALYSIS:
{self._fmt_mao(mao)}

OWNER INFO:
{f"Name: {owner['owner_name']}" if owner and owner.get('owner_name') else 'Not available'}
{f"Mailing address: {owner['mailing_address']}" if owner and owner.get('mailing_address') else ''}

OFFER TERMS:
Offer Price: ${offer['price']:,.0f}
Earnest Money: {f"${offer['earnest_money']:,.0f}" if offer.get('earnest_money') else 'To be determined'}
Financing: {offer['financing_type']}
Closing Days: {offer['closing_days']}
Contingencies: {', '.join(offer['contingencies']) if offer['contingencies'] else 'None'}

BUYER:
Name: {buyer['name']}
Email: {buyer['email']}

Generate a JSON object with these five fields:
1. "letter_text": A professional offer letter (plain text, properly formatted with line breaks). Include date, addresses, greeting, body paragraphs covering price, terms, financing, contingencies, closing timeline, and a professional closing.
2. "negotiation_strategy": A paragraph describing the recommended negotiation approach based on the deal score, MAO, and market data.
3. "talking_points": An array of 3-5 key bullet points the agent can reference during phone conversations.
4. "voice_summary": A 2-3 sentence summary suitable for text-to-speech, conveying the key offer details.
5. "template_fields": An object mapping DocuSeal template field names to their values. Use these exact keys:
   - "Property Address": full property address
   - "Offer Price": formatted price with $ sign (e.g. "$750,000")
   - "Earnest Money": formatted earnest money or "To be determined"
   - "Financing Type": financing type (e.g. "Cash", "Conventional", "FHA")
   - "Closing Date": estimated closing date as "Month Day, Year"
   - "Contingencies": comma-separated list or "None"
   - "Buyer Name": buyer's full name or "To be specified"
   - "Buyer Email": buyer's email or "To be specified"
   - "Seller/Owner Name": seller/owner name if known, else "Property Owner"
   - "Terms and Conditions": the main body of the offer letter
   - "Date": today's date as "Month Day, Year"

Return ONLY valid JSON, no markdown fences."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(text)

        return {
            "letter_text": result.get("letter_text", ""),
            "negotiation_strategy": result.get("negotiation_strategy", ""),
            "talking_points": result.get("talking_points", []),
            "voice_summary": result.get("voice_summary", ""),
            "template_fields": result.get("template_fields", {}),
        }

    def _create_contract(
        self,
        db: Session,
        property: Property,
        letter_text: str,
        offer_price: float,
        buyer_contact_id: int | None,
        template_fields: dict | None = None,
    ) -> tuple[Contract, str | None]:
        """Store the offer letter as a DRAFT contract, linking to a DocuSeal template if available.

        Returns (contract, docuseal_template_id).
        """
        address = f"{property.address}, {property.city}, {property.state}"
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Look up an active "Offer Letter" ContractTemplate with a docuseal_template_id
        docuseal_template_id = None
        tpl = (
            db.query(ContractTemplate)
            .filter(
                ContractTemplate.name.ilike("%offer letter%"),
                ContractTemplate.docuseal_template_id.isnot(None),
                ContractTemplate.is_active.is_(True),
            )
            .first()
        )
        if tpl:
            docuseal_template_id = tpl.docuseal_template_id
        else:
            # Fallback to env var
            docuseal_template_id = os.getenv("OFFER_LETTER_TEMPLATE_ID")

        # Build description: letter text + JSON template_fields section
        description = letter_text
        if template_fields:
            description += f"\n\n---TEMPLATE_FIELDS---\n{json.dumps(template_fields)}"

        contract = Contract(
            property_id=property.id,
            contact_id=buyer_contact_id,
            name=f"Offer Letter - {address} - {date_str}",
            description=description,
            status=ContractStatus.DRAFT,
            requirement_source=RequirementSource.AI_SUGGESTED,
            is_required=False,
            docuseal_template_id=docuseal_template_id,
        )
        db.add(contract)
        db.commit()
        db.refresh(contract)
        return contract, docuseal_template_id

    async def _prefill_docuseal(
        self,
        db: Session,
        contract: Contract,
        template_fields: dict,
        buyer_email: str,
        buyer_name: str | None = None,
    ) -> None:
        """Create a DocuSeal submission with pre-filled readonly fields.

        Only called when we have a docuseal_template_id and a buyer email.
        Updates the contract with submission_id and url.
        """
        if not contract.docuseal_template_id:
            return

        fields = [
            {"name": name, "default_value": str(value), "readonly": True}
            for name, value in template_fields.items()
            if value
        ]

        submitters = [
            {
                "email": buyer_email,
                "role": "Buyer",
                "fields": fields,
            }
        ]
        if buyer_name:
            submitters[0]["name"] = buyer_name

        try:
            result = await docuseal_client.create_submission(
                template_id=contract.docuseal_template_id,
                submitters=submitters,
                send_email=False,  # DRAFT — don't send yet
            )
            contract.docuseal_submission_id = str(result.get("id", ""))
            contract.docuseal_url = result.get("submission_url") or ""
            # Also capture per-submitter embed URL if available
            subs = result.get("submitters") or []
            if subs and subs[0].get("embed_src"):
                contract.docuseal_url = subs[0]["embed_src"]
            db.commit()
            db.refresh(contract)
            logger.info(
                f"Pre-filled DocuSeal submission {contract.docuseal_submission_id} "
                f"for contract {contract.id}"
            )
        except Exception as e:
            logger.warning(f"Failed to pre-fill DocuSeal for contract {contract.id}: {e}")

    @staticmethod
    def _fmt_enrichment(enrich: dict | None) -> str:
        if not enrich:
            return "Not available"
        lines = []
        if enrich.get("zestimate"):
            lines.append(f"Zestimate: ${enrich['zestimate']:,.0f}")
        if enrich.get("rent_zestimate"):
            lines.append(f"Rent Zestimate: ${enrich['rent_zestimate']:,.0f}/mo")
        if enrich.get("days_on_zillow") is not None:
            lines.append(f"Days on Zillow: {enrich['days_on_zillow']}")
        if enrich.get("price_history"):
            lines.append(f"Price history entries: {len(enrich['price_history'])}")
        if enrich.get("tax_history"):
            lines.append(f"Tax history entries: {len(enrich['tax_history'])}")
        if enrich.get("schools"):
            lines.append(f"Nearby schools: {len(enrich['schools'])}")
        return "\n".join(lines) if lines else "Not available"

    @staticmethod
    def _fmt_mao(mao: dict | None) -> str:
        if not mao:
            return "Not available"
        lines = []
        rec = mao.get("offer_recommendation", {})
        if rec.get("base"):
            lines.append(f"MAO: ${rec['base']:,.0f} (range: ${rec.get('low', 0):,.0f}-${rec.get('high', 0):,.0f})")
        arv = mao.get("arv", {})
        if arv.get("base"):
            lines.append(f"ARV: ${arv['base']:,.0f}")
        if mao.get("strategy"):
            lines.append(f"Strategy: {mao['strategy']}")
        if mao.get("explanation"):
            lines.append(f"Notes: {mao['explanation']}")
        return "\n".join(lines) if lines else "Not available"


# Singleton instance
offer_drafter_service = OfferDrafterService()
