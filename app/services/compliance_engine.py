"""
Compliance Engine - Evaluates properties against compliance rules

This service runs compliance checks on properties and generates violations.
"""
import json
import os
import time
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.compliance_rule import (
    ComplianceRule,
    ComplianceCheck,
    ComplianceViolation,
    ComplianceStatus,
    ViolationStatus,
    Severity,
    RuleType
)
from app.services.llm_service import llm_service


class ComplianceEngine:
    """
    AI-powered compliance checking engine.
    Uses Claude to interpret complex rules and property data.
    """

    async def run_compliance_check(
        self,
        db: Session,
        property: Property,
        check_type: str = "full",
        agent_id: Optional[int] = None
    ) -> ComplianceCheck:
        """
        Main compliance check workflow:
        1. Load rules for property's state/city
        2. Evaluate each rule (simple + AI-powered)
        3. Generate violations
        4. Create AI summary
        """

        # Create check record
        check = ComplianceCheck(
            property_id=property.id,
            agent_id=agent_id,
            check_type=check_type,
            status=ComplianceStatus.PENDING.value
        )
        db.add(check)
        db.commit()
        db.refresh(check)

        start_time = time.time()

        try:
            # 1. Load applicable rules
            rules = self._get_rules_for_property(db, property, check_type)
            check.total_rules_checked = len(rules)

            violations = []

            # 2. Evaluate each rule
            for rule in rules:
                # Update rule statistics
                rule.times_checked += 1

                violation = await self._evaluate_rule(db, property, rule)
                if violation:
                    violations.append(violation)
                    violation.check_id = check.id
                    db.add(violation)

                    # Update rule violation count
                    rule.times_violated += 1

            # 3. Calculate results
            check.failed_count = len([v for v in violations if v.status == ViolationStatus.FAILED.value])
            check.warning_count = len([v for v in violations if v.status == ViolationStatus.WARNING.value])
            check.passed_count = check.total_rules_checked - check.failed_count - check.warning_count

            # 4. Determine overall status
            if check.failed_count > 0:
                check.status = ComplianceStatus.FAILED.value
            elif check.warning_count > 0:
                check.status = ComplianceStatus.NEEDS_REVIEW.value
            else:
                check.status = ComplianceStatus.PASSED.value

            # 5. Generate AI summary
            check.ai_summary = await self._generate_summary(property, violations, rules)

            check.completion_time_seconds = time.time() - start_time
            check.completed_at = datetime.utcnow()

            db.commit()
            db.refresh(check)

            return check

        except Exception as e:
            check.status = ComplianceStatus.FAILED.value
            check.ai_summary = f"Error during compliance check: {str(e)}"
            check.completed_at = datetime.utcnow()
            db.commit()
            raise

    def _get_rules_for_property(
        self,
        db: Session,
        property: Property,
        check_type: str
    ) -> List[ComplianceRule]:
        """Load applicable rules for property's location"""

        query = db.query(ComplianceRule).filter(
            ComplianceRule.is_active == True,
            ComplianceRule.is_draft == False,
            ComplianceRule.state == property.state
        )

        # Add city-specific rules
        rules = query.filter(
            (ComplianceRule.city == None) |
            (ComplianceRule.city == property.city)
        ).all()

        # Filter by property type
        filtered_rules = []
        for rule in rules:
            # Check if rule applies to this property type
            if rule.property_type_filter:
                if property.property_type and property.property_type.value not in rule.property_type_filter:
                    continue

            # Check price filters
            if rule.min_price and property.price < rule.min_price:
                continue
            if rule.max_price and property.price > rule.max_price:
                continue

            # Check year built filters
            if property.year_built:
                if rule.min_year_built and property.year_built < rule.min_year_built:
                    continue
                if rule.max_year_built and property.year_built > rule.max_year_built:
                    continue

            filtered_rules.append(rule)

        # Filter by check type
        if check_type != "full":
            category_map = {
                "disclosure_only": ["disclosure"],
                "safety_only": ["safety", "building_code"],
                "zoning_only": ["zoning"],
                "environmental_only": ["environmental"]
            }
            if check_type in category_map:
                filtered_rules = [r for r in filtered_rules if r.category in category_map[check_type]]

        return filtered_rules

    async def _evaluate_rule(
        self,
        db: Session,
        property: Property,
        rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Evaluate single rule against property.
        Supports multiple rule types:
        - REQUIRED_FIELD: Check if field exists
        - THRESHOLD: Compare numeric values
        - DOCUMENT: Check if document uploaded
        - AI_REVIEW: Use Claude to interpret complex rules
        """

        if rule.rule_type == RuleType.REQUIRED_FIELD.value:
            return self._check_required_field(property, rule)

        elif rule.rule_type == RuleType.THRESHOLD.value:
            return self._check_threshold(property, rule)

        elif rule.rule_type == RuleType.DOCUMENT.value:
            return self._check_document(db, property, rule)

        elif rule.rule_type == RuleType.AI_REVIEW.value:
            return await self._check_with_ai(property, rule)

        elif rule.rule_type == RuleType.BOOLEAN.value:
            return self._check_boolean(property, rule)

        elif rule.rule_type == RuleType.LIST_CHECK.value:
            return self._check_list(property, rule)

        return None

    def _check_required_field(
        self,
        property: Property,
        rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """Check if required field is present"""

        field_value = getattr(property, rule.field_to_check, None)

        if not field_value:
            return ComplianceViolation(
                rule_id=rule.id,
                status=ViolationStatus.FAILED.value,
                severity=rule.severity,
                violation_message=f"Missing required field: {rule.field_to_check}",
                ai_explanation=f"{rule.title}: {rule.description}",
                recommendation=rule.how_to_fix or f"Please provide the {rule.field_to_check} information.",
                expected_value="Not null",
                actual_value="null"
            )

        return None

    def _check_threshold(
        self,
        property: Property,
        rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """Check numeric threshold (e.g., year_built < 1978)"""

        field_value = getattr(property, rule.field_to_check, None)

        if field_value is None:
            return None  # Skip if field not present

        # Parse condition
        try:
            operator, threshold = rule.condition.split()
            threshold = float(threshold)
        except:
            return None  # Invalid condition format

        operators = {
            "<": lambda x, y: x < y,
            ">": lambda x, y: x > y,
            "<=": lambda x, y: x <= y,
            ">=": lambda x, y: x >= y,
            "==": lambda x, y: x == y,
            "!=": lambda x, y: x != y,
        }

        if operator in operators and operators[operator](float(field_value), threshold):
            return ComplianceViolation(
                rule_id=rule.id,
                status=ViolationStatus.WARNING.value if rule.severity in [Severity.LOW.value, Severity.INFO.value] else ViolationStatus.FAILED.value,
                severity=rule.severity,
                violation_message=f"{rule.title} violated",
                ai_explanation=rule.description,
                recommendation=rule.how_to_fix or rule.penalty_description or "Please review this requirement",
                expected_value=f"NOT {rule.condition}",
                actual_value=str(field_value)
            )

        return None

    def _check_boolean(
        self,
        property: Property,
        rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """Check boolean field"""

        field_value = getattr(property, rule.field_to_check, None)

        # If condition is "== true" or "== false"
        if rule.condition:
            expected = "true" in rule.condition.lower()
            if field_value != expected:
                return ComplianceViolation(
                    rule_id=rule.id,
                    status=ViolationStatus.FAILED.value,
                    severity=rule.severity,
                    violation_message=f"{rule.title} violated",
                    ai_explanation=rule.description,
                    recommendation=rule.how_to_fix,
                    expected_value=str(expected),
                    actual_value=str(field_value)
                )

        return None

    def _check_list(
        self,
        property: Property,
        rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """Check if value is in allowed list"""

        field_value = getattr(property, rule.field_to_check, None)

        if field_value and rule.allowed_values:
            # Convert to string for comparison
            field_str = str(field_value).lower() if hasattr(field_value, 'value') else str(field_value).lower()
            allowed = [str(v).lower() for v in rule.allowed_values]

            if field_str not in allowed:
                return ComplianceViolation(
                    rule_id=rule.id,
                    status=ViolationStatus.FAILED.value,
                    severity=rule.severity,
                    violation_message=f"{rule.title} violated",
                    ai_explanation=rule.description,
                    recommendation=rule.how_to_fix,
                    expected_value=f"One of: {', '.join(rule.allowed_values)}",
                    actual_value=str(field_value)
                )

        return None

    def _check_document(
        self,
        db: Session,
        property: Property,
        rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """Check if document uploaded (placeholder - extend with document storage)"""

        # TODO: Integrate with document storage system
        # For now, we'll create a warning that document needs verification

        return ComplianceViolation(
            rule_id=rule.id,
            status=ViolationStatus.NEEDS_REVIEW.value,
            severity=rule.severity,
            violation_message=f"{rule.title} requires document verification",
            ai_explanation=f"Document required: {rule.document_type}. {rule.description}",
            recommendation=rule.how_to_fix or f"Upload {rule.document_type} document",
            expected_value=f"{rule.document_type} document",
            actual_value="Not verified"
        )

    async def _check_with_ai(
        self,
        property: Property,
        rule: ComplianceRule
    ) -> Optional[ComplianceViolation]:
        """
        Use Claude to evaluate complex rules.
        This is the most powerful feature - AI interprets natural language rules.
        """

        if not os.getenv("ANTHROPIC_API_KEY"):
            # If no AI client, create a needs_review violation
            return ComplianceViolation(
                rule_id=rule.id,
                status=ViolationStatus.NEEDS_REVIEW.value,
                severity=rule.severity,
                violation_message=f"{rule.title} requires manual review",
                ai_explanation=rule.description,
                recommendation=rule.how_to_fix or "Manual review required",
                expected_value="Compliant",
                actual_value="Requires AI review (API key not configured)"
            )

        # Build property context
        property_data = {
            "address": property.address,
            "city": property.city,
            "state": property.state,
            "zip_code": property.zip_code,
            "price": property.price,
            "bedrooms": property.bedrooms,
            "bathrooms": property.bathrooms,
            "square_feet": property.square_feet,
            "year_built": property.year_built,
            "property_type": property.property_type.value if property.property_type else None,
            "status": property.status.value if property.status else None,
        }

        # Add Zillow enrichment if available
        if property.zillow_enrichment:
            property_data["zestimate"] = property.zillow_enrichment.zestimate
            property_data["home_type"] = property.zillow_enrichment.home_type
            if property.zillow_enrichment.reso_facts:
                property_data["zoning"] = property.zillow_enrichment.reso_facts.get("zoning")

        prompt = f"""You are a real estate compliance expert evaluating properties against state regulations.

COMPLIANCE RULE:
Code: {rule.rule_code}
State: {rule.state}
Category: {rule.category}
Title: {rule.title}
Description: {rule.description}

RULE TO EVALUATE:
{rule.ai_prompt}

PROPERTY DATA:
{json.dumps(property_data, indent=2)}

TASK:
1. Determine if this property violates the compliance rule
2. If it does violate, explain why in simple terms
3. Provide a recommendation to fix the issue
4. Rate severity: CRITICAL, HIGH, MEDIUM, LOW

Respond in JSON format:
{{
    "violates": true/false,
    "explanation": "why it violates or passes",
    "recommendation": "how to fix (if violates)",
    "severity": "CRITICAL/HIGH/MEDIUM/LOW"
}}"""

        try:
            response_text = llm_service.generate(prompt, max_tokens=1000)

            # Extract JSON
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
            else:
                result = json.loads(response_text)

            if result.get("violates"):
                return ComplianceViolation(
                    rule_id=rule.id,
                    status=ViolationStatus.FAILED.value if result["severity"] in ["CRITICAL", "HIGH"] else ViolationStatus.WARNING.value,
                    severity=result["severity"].lower(),
                    violation_message=f"{rule.title} violated",
                    ai_explanation=result["explanation"],
                    recommendation=result["recommendation"],
                    expected_value="Compliant",
                    actual_value="Non-compliant (AI evaluated)"
                )

            return None

        except Exception as e:
            # If AI check fails, create needs_review violation
            return ComplianceViolation(
                rule_id=rule.id,
                status=ViolationStatus.NEEDS_REVIEW.value,
                severity=rule.severity,
                violation_message=f"{rule.title} requires manual review",
                ai_explanation=f"AI evaluation failed: {str(e)}",
                recommendation=rule.how_to_fix or "Manual review required",
                expected_value="Compliant",
                actual_value="AI check failed"
            )

    async def _generate_summary(
        self,
        property: Property,
        violations: List[ComplianceViolation],
        rules: List[ComplianceRule]
    ) -> str:
        """Generate executive summary of compliance check"""

        if not violations:
            return f"✅ Property at {property.address} is fully compliant with all {len(rules)} {property.state} regulations."

        critical = len([v for v in violations if v.severity == Severity.CRITICAL.value])
        high = len([v for v in violations if v.severity == Severity.HIGH.value])
        medium = len([v for v in violations if v.severity == Severity.MEDIUM.value])
        low = len([v for v in violations if v.severity == Severity.LOW.value])

        summary = f"⚠️ Found {len(violations)} compliance issue{'s' if len(violations) != 1 else ''} for {property.address}:\n\n"

        if critical > 0:
            summary += f"🔴 {critical} CRITICAL issue(s) - must fix before listing\n"
        if high > 0:
            summary += f"🟡 {high} HIGH priority issue(s) - fix recommended\n"
        if medium > 0:
            summary += f"🟠 {medium} MEDIUM issue(s) - should address\n"
        if low > 0:
            summary += f"🔵 {low} LOW priority issue(s)\n"

        summary += "\nTop Issues:\n"
        # Sort by severity
        severity_order = {Severity.CRITICAL.value: 0, Severity.HIGH.value: 1, Severity.MEDIUM.value: 2, Severity.LOW.value: 3}
        sorted_violations = sorted(violations, key=lambda x: severity_order.get(x.severity, 999))

        for i, v in enumerate(sorted_violations[:5], 1):
            summary += f"{i}. {v.violation_message}\n"

        if len(violations) > 5:
            summary += f"\n... and {len(violations) - 5} more issues"

        return summary


# Singleton instance
compliance_engine = ComplianceEngine()
