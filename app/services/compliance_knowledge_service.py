"""
Compliance Knowledge Service - Manage compliance rules knowledge base
"""
import json
import os
import re
from typing import Dict, Optional

from app.services.llm_service import llm_service


class ComplianceKnowledgeService:
    """Service for managing compliance knowledge base"""

    def validate_rule(self, rule_data: dict) -> Optional[str]:
        """
        Validate rule data before saving.
        Returns error message if invalid, None if valid.
        """

        errors = []

        # Required fields
        required = ['state', 'rule_code', 'category', 'title', 'description', 'rule_type', 'severity']
        for field in required:
            if not rule_data.get(field):
                errors.append(f"Missing required field: {field}")

        # Validate rule_type specific fields
        rule_type = rule_data.get('rule_type')

        if rule_type == 'threshold':
            if not rule_data.get('field_to_check'):
                errors.append("threshold rule requires 'field_to_check'")
            if not rule_data.get('condition'):
                errors.append("threshold rule requires 'condition'")

        elif rule_type == 'required_field':
            if not rule_data.get('field_to_check'):
                errors.append("required_field rule requires 'field_to_check'")

        elif rule_type == 'document':
            if not rule_data.get('document_type'):
                errors.append("document rule requires 'document_type'")

        elif rule_type == 'ai_review':
            if not rule_data.get('ai_prompt'):
                errors.append("ai_review rule requires 'ai_prompt'")

        elif rule_type == 'list_check':
            if not rule_data.get('allowed_values'):
                errors.append("list_check rule requires 'allowed_values'")

        # Validate state code (2 letters)
        if rule_data.get('state') and len(rule_data['state']) != 2:
            errors.append("state must be 2-letter code (e.g., 'NY', 'CA')")

        # Validate rule_code format
        rule_code = rule_data.get('rule_code', '')
        if rule_code and not re.match(r'^[A-Z]{2}-[A-Z0-9]+-\d+$', rule_code):
            errors.append("rule_code should follow format: STATE-CATEGORY-NUMBER (e.g., 'NY-LEAD-001')")

        # Validate severity
        valid_severities = ['critical', 'high', 'medium', 'low', 'info']
        if rule_data.get('severity') and rule_data['severity'].lower() not in valid_severities:
            errors.append(f"severity must be one of: {', '.join(valid_severities)}")

        # Validate category
        valid_categories = [
            'disclosure', 'safety', 'building_code', 'zoning', 'environmental',
            'accessibility', 'licensing', 'fair_housing', 'tax', 'hoa', 'other'
        ]
        if rule_data.get('category') and rule_data['category'].lower() not in valid_categories:
            errors.append(f"category must be one of: {', '.join(valid_categories)}")

        return "; ".join(errors) if errors else None

    async def generate_rule_with_ai(
        self,
        state: str,
        natural_language: str,
        category: Optional[str] = None,
        legal_citation: Optional[str] = None
    ) -> Dict:
        """
        Use Claude to generate a structured rule from natural language description
        """

        if not os.getenv("ANTHROPIC_API_KEY"):
            raise Exception("ANTHROPIC_API_KEY not configured. Cannot use AI features.")

        prompt = f"""You are a real estate compliance expert creating structured compliance rules.

TASK: Convert this natural language compliance requirement into a structured rule.

STATE: {state}
NATURAL LANGUAGE RULE: {natural_language}
{"LEGAL CITATION: " + legal_citation if legal_citation else ""}
{"CATEGORY: " + category if category else ""}

Please create a structured compliance rule with these fields:
1. rule_code: Generate a code like "STATE-CATEGORY-###" (e.g., "NY-LEAD-001")
2. category: One of: disclosure, safety, building_code, zoning, environmental, accessibility, licensing, fair_housing, tax, hoa, other
3. title: Short, clear title (under 100 chars)
4. description: Detailed explanation
5. rule_type: One of: required_field, threshold, document, ai_review, boolean, list_check, date_range, conditional
6. severity: One of: critical, high, medium, low, info
7. field_to_check: Property field to check (if applicable): year_built, price, bedrooms, bathrooms, square_feet, property_type, etc.
8. condition: Comparison condition if threshold type (e.g., "< 1978", ">= 2000")
9. ai_prompt: Natural language instruction for AI to evaluate this rule
10. requires_document: true/false if document needed
11. document_type: Type of document if required
12. how_to_fix: Instructions to fix violation
13. tags: Array of relevant keywords for search

Respond in JSON format with all applicable fields.

Example:
{{
    "rule_code": "CA-EARTH-001",
    "category": "disclosure",
    "title": "Earthquake Hazard Disclosure",
    "description": "Properties in California earthquake zones must include Natural Hazard Disclosure Statement",
    "rule_type": "document",
    "severity": "high",
    "requires_document": true,
    "document_type": "natural_hazard_disclosure",
    "ai_prompt": "Check if property has earthquake hazard disclosure document on file",
    "how_to_fix": "Obtain and complete Natural Hazard Disclosure Statement (NHD) form",
    "tags": ["earthquake", "disclosure", "natural_hazard"]
}}"""

        response_text = await llm_service.agenerate(prompt, max_tokens=2000)

        # Try to parse JSON from response
        try:
            # Look for JSON block
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                rule_data = json.loads(json_str)
            else:
                rule_data = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback: create basic rule structure
            rule_data = {
                "rule_code": f"{state.upper()}-AUTO-{hash(natural_language) % 1000}",
                "category": category or "other",
                "title": natural_language[:100],
                "description": natural_language,
                "rule_type": "ai_review",
                "severity": "medium",
                "ai_prompt": natural_language,
                "tags": []
            }

        rule_data['state'] = state.upper()

        return rule_data

    def csv_row_to_rule(self, row: dict) -> dict:
        """Convert CSV row to rule dictionary"""

        return {
            "state": row.get('state', '').upper(),
            "rule_code": row.get('rule_code', ''),
            "category": row.get('category', 'other'),
            "title": row.get('title', ''),
            "description": row.get('description', ''),
            "rule_type": row.get('rule_type', 'ai_review'),
            "field_to_check": row.get('field_to_check') or None,
            "condition": row.get('condition') or None,
            "severity": row.get('severity', 'medium'),
            "requires_document": row.get('requires_document', '').lower() in ['true', '1', 'yes'],
            "document_type": row.get('document_type') or None,
            "ai_prompt": row.get('ai_prompt') or None,
            "legal_citation": row.get('legal_citation') or None,
            "how_to_fix": row.get('how_to_fix') or None,
            "tags": row.get('tags', '').split(',') if row.get('tags') else [],
        }


# Singleton instance
compliance_knowledge_service = ComplianceKnowledgeService()
