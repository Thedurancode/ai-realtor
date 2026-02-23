"""Document Analysis Service — extract insights from documents using vision AI."""

from __future__ import annotations

import logging
import re
from typing import Any, Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.property_note import PropertyNote, NoteSource
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class DocumentAnalyzerService:
    """Extract insights from contracts, inspection reports, appraisals using AI."""

    async def analyze_inspection_report(
        self,
        db: Session,
        property_id: int,
        document_text: str,
        create_note: bool = True,
    ) -> dict[str, Any]:
        """Extract key issues from inspection report using NLP.

        Args:
            property_id: Property to attach analysis to
            document_text: Text content of inspection report (from OCR)
            create_note: Whether to save analysis as a property note

        Returns:
            {
                "critical_issues": [...],
                "repair_estimate": float,
                "negotiation_leverage": [...],
                "deal_killers": [...],
                "summary": "...",
                "voice_summary": "..."
            }
        """
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return {"error": f"Property {property_id} not found"}

        # Use LLM to analyze the inspection report
        prompt = f"""Analyze this home inspection report and extract key information.

Property: {prop.address} in {prop.city}, {prop.state}

Inspection Report Text:
{document_text[:8000]}  # Limit to avoid token limits

Extract and return ONLY a JSON object with:
{{
    "critical_issues": [
        {{"category": "electrical | plumbing | structural | roof | HVAC | foundation | other",
         "severity": "safety_hazard | major | moderate | minor",
         "description": "brief description",
         "estimated_cost": 0}}
    ],
    "summary": "2-3 sentence overall assessment",
    "total_estimated_repair_cost": 0,
    "negotiation_points": ["issue1", "issue2"],  // Issues to use in price negotiation
    "deal_killers": ["issue1"]  // Issues that might kill the deal
}}

Return ONLY the JSON, no other text."""

        try:
            response = await llm_service.agenerate(prompt, max_tokens=2000)
            import json

            # Extract JSON from response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                analysis = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")

        except Exception as e:
            logger.error(f"Failed to analyze inspection report: {e}")
            # Fallback: basic keyword extraction
            analysis = self._fallback_inspection_analysis(document_text)

        # Categorize issues
        critical_issues = [
            issue for issue in analysis.get("critical_issues", [])
            if issue.get("severity") in ["safety_hazard", "major"]
        ]
        deal_killers = analysis.get("deal_killers", [])

        # Calculate total repair cost
        total_cost = sum(
            [issue.get("estimated_cost", 0) for issue in analysis.get("critical_issues", [])]
        )

        result = {
            "property_id": property_id,
            "address": prop.address,
            "critical_issues": critical_issues,
            "all_issues": analysis.get("critical_issues", []),
            "total_repair_estimate": total_cost,
            "negotiation_leverage": analysis.get("negotiation_points", []),
            "deal_killers": deal_killers,
            "summary": analysis.get("summary", "Analysis complete"),
            "voice_summary": self._build_inspection_voice_summary(
                prop, critical_issues, total_cost, deal_killers
            ),
        }

        # Save as note if requested
        if create_note:
            note_content = self._format_inspection_note(result)
            note = PropertyNote(
                property_id=property_id,
                content=note_content,
                source=NoteSource.AI,
            )
            db.add(note)
            db.commit()
            result["note_id"] = note.id

        return result

    async def compare_appraisals(
        self,
        db: Session,
        property_id: int,
        appraisal_docs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Compare multiple appraisals and flag discrepancies.

        Args:
            property_id: Property being appraised
            appraisal_docs: List of {"text": str, "source": str, "date": str}

        Returns:
            {
                "discrepancies": [...],
                "average_value": float,
                "recommendation": "...",
                "voice_summary": "..."
            }
        """
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return {"error": f"Property {property_id} not found"}

        # Extract values from each appraisal
        appraisals = []
        for doc in appraisal_docs:
            extracted = await self._extract_appraisal_data(doc["text"])
            appraisals.append({
                "source": doc.get("source", "unknown"),
                "date": doc.get("date"),
                **extracted,
            })

        if len(appraisals) < 2:
            return {
                "message": "Need at least 2 appraisals to compare",
                "appraisals": appraisals,
            }

        # Compare values
        discrepancies = []

        # Check estimated values
        values = [a.get("estimated_value") for a in appraisals if a.get("estimated_value")]
        if values:
            avg_value = sum(values) / len(values)
            max_diff = max(values) - min(values)

            if max_diff > avg_value * 0.10:  # More than 10% variance
                discrepancies.append({
                    "field": "estimated_value",
                    "values": values,
                    "variance_pct": round((max_diff / avg_value) * 100, 1),
                    "average": round(avg_value, 2),
                    "action": "request_reappraisal" if max_diff > avg_value * 0.20 else "investigate",
                })

        # Check other fields
        fields_to_compare = ["square_footage", "bedrooms", "bathrooms", "lot_size"]
        for field in fields_to_compare:
            field_values = [a.get(field) for a in appraisals if a.get(field)]
            if len(set(field_values)) > 1:
                discrepancies.append({
                    "field": field,
                    "values": field_values,
                    "variance": "inconsistent_values",
                    "action": "verify_measurements",
                })

        # Generate recommendation
        if discrepancies:
            if any(d.get("action") == "request_reappraisal" for d in discrepancies):
                recommendation = "Significant discrepancies found - consider requesting a new appraisal"
            else:
                recommendation = "Minor discrepancies found - verify measurements before proceeding"
        else:
            recommendation = "Appraisals are consistent - proceed with confidence"

        return {
            "property_id": property_id,
            "appraisals_compared": len(appraisals),
            "discrepancies": discrepancies,
            "average_estimated_value": round(values[0], 2) if values else None,
            "recommendation": recommendation,
            "voice_summary": self._build_appraisal_voice_summary(
                len(appraisals), discrepancies, recommendation
            ),
        }

    async def extract_contract_terms(
        self,
        db: Session,
        property_id: int,
        contract_text: str,
    ) -> dict[str, Any]:
        """Extract key terms from a contract document.

        Returns:
            {
                "parties": {...},
                "key_dates": {...},
                "financial_terms": {...},
                "contingencies": [...],
                "obligations": [...],
                "voice_summary": "..."
            }
        """
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return {"error": f"Property {property_id} not found"}

        prompt = f"""Extract key terms from this real estate contract.

Property: {prop.address}

Contract Text:
{contract_text[:8000]}

Return ONLY a JSON object with:
{{
    "parties": {{
        "buyer": "name",
        "seller": "name",
        "agent": "name"
    }},
    "key_dates": {{
        "offer_date": "YYYY-MM-DD",
        "closing_date": "YYYY-MM-DD",
        "contingency_deadline": "YYYY-MM-DD"
    }},
    "financial_terms": {{
        "purchase_price": 0,
        "earnest_money": 0,
        "down_payment": 0
    }},
    "contingencies": ["inspection", "financing", "appraisal"],
    "seller_obligations": ["repair1", "repair2"],
    "buyer_obligations": ["secure_financing"]
}}

Return ONLY the JSON, no other text."""

        try:
            response = await llm_service.agenerate(prompt, max_tokens=1500)
            import json

            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                terms = json.loads(json_str)
            else:
                raise ValueError("No JSON found")

        except Exception as e:
            logger.error(f"Failed to extract contract terms: {e}")
            # Fallback: regex extraction
            terms = self._fallback_contract_extraction(contract_text)

        return {
            "property_id": property_id,
            "extracted_terms": terms,
            "voice_summary": self._build_contract_voice_summary(terms),
        }

    # ── Private Methods ──

    async def _extract_appraisal_data(self, text: str) -> dict[str, Any]:
        """Extract key data from appraisal text."""
        # Look for estimated value patterns
        value_patterns = [
            r"estimated value[:\s]*\$?([\d,]+(?:\.\d{2})?)",
            r"appraised value[:\s]*\$?([\d,]+(?:\.\d{2})?)",
            r"fair market value[:\s]*\$?([\d,]+(?:\.\d{2})?)",
            r"\$([\d,]+(?:\.\d{2})?).*?appraisal",
        ]

        estimated_value = None
        for pattern in value_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace(",", "")
                try:
                    estimated_value = float(value_str)
                    break
                except ValueError:
                    continue

        # Extract square footage
        sqft_match = re.search(r"square feet[:\s]*([\d,]+)", text, re.IGNORECASE)
        sqft = int(sqft_match.group(1).replace(",", "")) if sqft_match else None

        # Extract bedrooms/bathrooms
        beds_match = re.search(r"bedroom[s]?:\s*(\d+)", text, re.IGNORECASE)
        baths_match = re.search(r"bathroom[s]?:\s*([\d.]+)", text, re.IGNORECASE)

        return {
            "estimated_value": estimated_value,
            "square_footage": sqft,
            "bedrooms": int(beds_match.group(1)) if beds_match else None,
            "bathrooms": float(baths_match.group(1)) if baths_match else None,
        }

    def _fallback_inspection_analysis(self, text: str) -> dict[str, Any]:
        """Fallback keyword-based inspection analysis."""
        # Define issue keywords
        issue_keywords = {
            "electrical": ["wiring", "electrical", "panel", "outlet", "breaker"],
            "plumbing": ["plumbing", "pipe", "leak", "sewer", "water heater", "faucet"],
            "structural": ["foundation", "structural", "crack", "settlement"],
            "roof": ["roof", "shingle", "leak", "flashing"],
            "HVAC": ["hvac", "furnace", "air conditioning", "heating", "ac"],
            "safety": ["safety", "hazard", "danger", "smoke detector", "carbon monoxide"],
        }

        issues = []
        text_lower = text.lower()

        for category, keywords in issue_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Find context around the keyword
                    idx = text_lower.find(keyword)
                    context = text[max(0, idx - 50):idx + 100]

                    issues.append({
                        "category": category,
                        "severity": "moderate",
                        "description": context.strip(),
                        "estimated_cost": 500,  # Default estimate
                    })
                    break  # One issue per category max

        return {
            "critical_issues": issues,
            "summary": f"Found {len(issues)} potential issues requiring attention",
            "total_estimated_repair_cost": len(issues) * 500,
            "negotiation_points": [],
            "deal_killers": [],
        }

    def _fallback_contract_extraction(self, text: str) -> dict[str, Any]:
        """Fallback regex-based contract extraction."""
        # Extract price
        price_match = re.search(r"purchase price[:\s]*\$?([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)

        # Extract dates
        closing_match = re.search(r"closing.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text, re.IGNORECASE)

        return {
            "parties": {"buyer": "Extracted from document", "seller": "Extracted from document"},
            "key_dates": {
                "closing_date": closing_match.group(1) if closing_match else "Not found",
            },
            "financial_terms": {
                "purchase_price": float(price_match.group(1).replace(",", "")) if price_match else None,
            },
            "contingencies": ["inspection", "financing"],
            "seller_obligations": [],
            "buyer_obligations": [],
        }

    def _format_inspection_note(self, analysis: dict) -> str:
        """Format inspection analysis as a property note."""
        lines = [
            "📋 Inspection Report Analysis",
            "",
            f"Critical Issues: {len(analysis['critical_issues'])}",
            f"Total Repair Estimate: ${analysis['total_repair_estimate']:,.0f}",
            "",
        ]

        if analysis["critical_issues"]:
            lines.append("Critical Issues:")
            for issue in analysis["critical_issues"][:5]:
                lines.append(f"  - [{issue['severity'].upper()}] {issue['description']}")

        if analysis["deal_killers"]:
            lines.append("")
            lines.append("⚠️ Deal Killers:")
            for killer in analysis["deal_killers"]:
                lines.append(f"  - {killer}")

        return "\n".join(lines)

    def _build_inspection_voice_summary(
        self, prop: Property, issues: list, cost: float, killers: list
    ) -> str:
        """Build voice summary for inspection analysis."""
        parts = [f"Inspection report for {prop.address} found {len(issues)} critical issues"]

        if cost > 0:
            parts.append(f"with an estimated ${cost:,.0f} in repairs")

        if killers:
            parts.append(f"and {len(killers)} potential deal killers")

        return ". ".join(parts) + "."

    def _build_appraisal_voice_summary(
        self, count: int, discrepancies: list, recommendation: str
    ) -> str:
        """Build voice summary for appraisal comparison."""
        if discrepancies:
            return (
                f"Compared {count} appraisals and found {len(discrepancies)} discrepancies. "
                f"{recommendation}."
            )
        return f"All {count} appraisals are consistent."

    def _build_contract_voice_summary(self, terms: dict) -> str:
        """Build voice summary for contract extraction."""
        price = terms.get("financial_terms", {}).get("purchase_price")
        closing = terms.get("key_dates", {}).get("closing_date")

        parts = ["Contract terms extracted"]
        if price:
            parts.append(f"for ${price:,.0f}")
        if closing:
            parts.append(f"with closing on {closing}")

        return ". ".join(parts) + "." if len(parts) > 1 else "Contract extracted."


document_analyzer_service = DocumentAnalyzerService()
