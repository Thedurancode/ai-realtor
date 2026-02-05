"""
Contract AI Service

AI-powered contract suggestion and analysis using Claude.
"""
import os
from typing import List, Dict
from sqlalchemy.orm import Session
from anthropic import Anthropic

from app.models.property import Property
from app.models.contract_template import ContractTemplate
from app.models.contract import Contract, RequirementSource


class ContractAIService:
    """AI service for contract suggestions and analysis"""

    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def suggest_required_contracts(
        self,
        db: Session,
        property: Property
    ) -> Dict:
        """
        Use AI to analyze property and suggest which contracts are required.

        Returns:
        {
            "required_contracts": [...],
            "optional_contracts": [...],
            "ai_reasoning": "...",
            "total_suggested": 5
        }
        """
        # Get all available contract templates
        all_templates = db.query(ContractTemplate).filter(
            ContractTemplate.is_active == True
        ).all()

        # Build property context for AI
        property_context = self._build_property_context(property)

        # Build templates list for AI
        templates_list = self._build_templates_list(all_templates)

        # Create AI prompt
        prompt = f"""You are a real estate contract expert. Analyze this property and determine which contracts are REQUIRED vs OPTIONAL.

PROPERTY DETAILS:
{property_context}

AVAILABLE CONTRACT TEMPLATES:
{templates_list}

Please analyze this property and categorize each contract as REQUIRED or OPTIONAL.

Consider:
1. State/local regulations and requirements
2. Property type and characteristics
3. Price range and transaction complexity
4. Standard real estate practices
5. Risk mitigation

Return your analysis as JSON in this exact format:
{{
    "required_contracts": [
        {{
            "template_id": 1,
            "name": "Contract Name",
            "reason": "Why this is required (1-2 sentences)"
        }}
    ],
    "optional_contracts": [
        {{
            "template_id": 2,
            "name": "Contract Name",
            "reason": "Why this is optional (1-2 sentences)"
        }}
    ],
    "summary": "Brief overall assessment (2-3 sentences)"
}}

Be thorough and consider all applicable regulations for {property.state} state."""

        # Call Claude
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Parse response
        response_text = response.content[0].text

        # Extract JSON from response
        import json
        import re

        # Try to find JSON in response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            # Fallback: assume entire response is JSON
            result = json.loads(response_text)

        # Add metadata
        result["total_suggested"] = len(result.get("required_contracts", [])) + len(result.get("optional_contracts", []))
        result["property_id"] = property.id
        result["property_address"] = property.address

        return result

    async def analyze_contract_gaps(
        self,
        db: Session,
        property: Property
    ) -> Dict:
        """
        Analyze what contracts are missing for a property.

        Returns:
        {
            "has_all_required": false,
            "missing_critical": [...],
            "missing_recommended": [...],
            "ai_recommendation": "..."
        }
        """
        # Get existing contracts
        existing_contracts = db.query(Contract).filter(
            Contract.property_id == property.id
        ).all()

        existing_names = {c.name.lower() for c in existing_contracts}

        # Get AI suggestions
        suggestions = await self.suggest_required_contracts(db, property)

        # Find what's missing
        missing_critical = []
        for contract in suggestions.get("required_contracts", []):
            if contract["name"].lower() not in existing_names:
                missing_critical.append(contract)

        missing_recommended = []
        for contract in suggestions.get("optional_contracts", []):
            if contract["name"].lower() not in existing_names:
                missing_recommended.append(contract)

        # Build AI recommendation
        if not missing_critical:
            ai_recommendation = f"All critical contracts are in place for {property.address}. Property has {len(existing_contracts)} contracts attached."
        else:
            ai_recommendation = f"Missing {len(missing_critical)} critical contract(s) for {property.address}. These should be added before proceeding."

        return {
            "property_id": property.id,
            "property_address": property.address,
            "has_all_required": len(missing_critical) == 0,
            "existing_contracts_count": len(existing_contracts),
            "missing_critical": missing_critical,
            "missing_recommended": missing_recommended,
            "ai_recommendation": ai_recommendation,
            "summary": suggestions.get("summary", "")
        }

    def _build_property_context(self, property: Property) -> str:
        """Build property context for AI analysis"""
        context = f"""
- Address: {property.address}, {property.city}, {property.state} {property.zip_code}
- Property Type: {property.property_type.value if property.property_type else 'Unknown'}
- Price: ${property.price:,.2f}
- Bedrooms: {property.bedrooms or 'N/A'}
- Bathrooms: {property.bathrooms or 'N/A'}
- Square Feet: {property.square_feet or 'N/A'}
- Year Built: {property.year_built or 'N/A'}
- Status: {property.status.value if property.status else 'Unknown'}
"""
        return context.strip()

    def _build_templates_list(self, templates: List[ContractTemplate]) -> str:
        """Build formatted list of available templates"""
        lines = []
        for t in templates:
            state_filter = f" ({t.state} only)" if t.state else " (All states)"
            lines.append(
                f"ID {t.id}: {t.name}{state_filter} - {t.description} "
                f"[{t.category.value}, {t.requirement.value}]"
            )
        return "\n".join(lines)


# Singleton instance
contract_ai_service = ContractAIService()
