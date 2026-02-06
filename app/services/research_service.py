"""
Research Service

Orchestrates multiple API calls to perform comprehensive research.
"""
import asyncio
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import httpx
import os
from anthropic import Anthropic

from app.models.property import Property
from app.models.research import Research, ResearchStatus, ResearchType
from app.services.zillow_enrichment import zillow_enrichment_service
from app.services.contract_ai_service import contract_ai_service
from app.services.contract_auto_attach import contract_auto_attach_service
from app.services.compliance_engine import ComplianceEngine


class ResearchService:
    """Service for orchestrating multi-endpoint research"""

    def __init__(self):
        self.compliance_engine = ComplianceEngine()
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def perform_research(
        self,
        db: Session,
        research: Research
    ) -> Dict:
        """
        Execute research job by calling multiple endpoints and aggregating results.
        """
        try:
            # Update status
            research.status = ResearchStatus.IN_PROGRESS
            research.started_at = datetime.utcnow()
            db.commit()

            # Route to appropriate research handler
            if research.research_type == ResearchType.PROPERTY_ANALYSIS:
                results = await self._property_analysis(db, research)
            elif research.research_type == ResearchType.MARKET_ANALYSIS:
                results = await self._market_analysis(db, research)
            elif research.research_type == ResearchType.COMPLIANCE_CHECK:
                results = await self._compliance_check(db, research)
            elif research.research_type == ResearchType.CONTRACT_ANALYSIS:
                results = await self._contract_analysis(db, research)
            elif research.research_type == ResearchType.OWNER_RESEARCH:
                results = await self._owner_research(db, research)
            elif research.research_type == ResearchType.NEIGHBORHOOD_ANALYSIS:
                results = await self._neighborhood_analysis(db, research)
            elif research.research_type == ResearchType.CUSTOM:
                results = await self._custom_research(db, research)
            elif research.research_type == ResearchType.AI_RESEARCH:
                results = await self._ai_research(db, research)
            elif research.research_type == ResearchType.API_RESEARCH:
                results = await self._api_research(db, research)
            else:
                raise ValueError(f"Unknown research type: {research.research_type}")

            # Mark complete
            research.status = ResearchStatus.COMPLETED
            research.progress = 100
            research.completed_at = datetime.utcnow()
            research.results = results
            db.commit()

            return results

        except Exception as e:
            research.status = ResearchStatus.FAILED
            research.error_message = str(e)
            db.commit()
            raise

    async def _property_analysis(self, db: Session, research: Research) -> Dict:
        """
        Complete property deep dive:
        1. Get property details
        2. Enrich with Zillow data
        3. Skip trace owner info
        4. Check compliance
        5. Analyze contract requirements
        6. AI recommendations
        """
        property = db.query(Property).filter(Property.id == research.property_id).first()
        if not property:
            raise ValueError("Property not found")

        results = {
            "research_type": "property_analysis",
            "property_id": research.property_id,
            "timestamp": datetime.utcnow().isoformat(),
            "steps": {}
        }

        # Step 1: Get property details (10%)
        research.current_step = "Fetching property details"
        research.progress = 10
        db.commit()

        results["steps"]["property_details"] = {
            "address": property.address,
            "city": property.city,
            "state": property.state,
            "price": property.price,
            "bedrooms": property.bedrooms,
            "bathrooms": property.bathrooms,
            "square_feet": property.square_feet,
            "year_built": property.year_built,
            "property_type": property.property_type.value if property.property_type else None
        }

        # Step 2: Zillow enrichment (30%)
        research.current_step = "Enriching with Zillow data"
        research.progress = 30
        db.commit()

        try:
            zillow_data = await zillow_enrichment_service.enrich_property(db, property.id)
            results["steps"]["zillow_enrichment"] = zillow_data
        except Exception as e:
            results["steps"]["zillow_enrichment"] = {"error": str(e)}

        # Step 3: Skip trace (50%)
        research.current_step = "Skip tracing owner information"
        research.progress = 50
        db.commit()

        # Note: Skip trace would be called here if needed
        results["steps"]["skip_trace"] = {
            "status": "not_implemented",
            "note": "Skip trace service integration pending"
        }

        # Step 4: Compliance check (70%)
        research.current_step = "Checking compliance requirements"
        research.progress = 70
        db.commit()

        try:
            compliance = await self.compliance_engine.run_compliance_check(db, property)
            results["steps"]["compliance"] = compliance
        except Exception as e:
            results["steps"]["compliance"] = {"error": str(e)}

        # Step 5: Contract analysis (85%)
        research.current_step = "Analyzing contract requirements"
        research.progress = 85
        db.commit()

        try:
            contract_suggestions = await contract_ai_service.suggest_required_contracts(db, property)
            readiness = contract_auto_attach_service.get_required_contracts_status(db, property)

            results["steps"]["contract_analysis"] = {
                "ai_suggestions": contract_suggestions,
                "readiness": readiness
            }
        except Exception as e:
            results["steps"]["contract_analysis"] = {"error": str(e)}

        # Step 6: AI recommendations (95%)
        research.current_step = "Generating AI recommendations"
        research.progress = 95
        db.commit()

        # Generate overall recommendations
        recommendations = self._generate_property_recommendations(results)
        results["recommendations"] = recommendations

        research.current_step = "Complete"
        research.progress = 100

        return results

    async def _market_analysis(self, db: Session, research: Research) -> Dict:
        """
        Market analysis:
        1. Compare similar properties
        2. Market trends
        3. Neighborhood data
        4. Price analysis
        """
        property = db.query(Property).filter(Property.id == research.property_id).first()
        if not property:
            raise ValueError("Property not found")

        results = {
            "research_type": "market_analysis",
            "property_id": research.property_id,
            "timestamp": datetime.utcnow().isoformat(),
            "steps": {}
        }

        # Step 1: Find comparable properties (25%)
        research.current_step = "Finding comparable properties"
        research.progress = 25
        db.commit()

        comparables = db.query(Property).filter(
            Property.id != property.id,
            Property.city == property.city,
            Property.state == property.state,
            Property.bedrooms == property.bedrooms
        ).limit(5).all()

        results["steps"]["comparables"] = [
            {
                "address": p.address,
                "price": p.price,
                "square_feet": p.square_feet,
                "price_per_sqft": p.price / p.square_feet if p.square_feet else None
            }
            for p in comparables
        ]

        # Step 2: Price analysis (50%)
        research.current_step = "Analyzing price trends"
        research.progress = 50
        db.commit()

        if comparables:
            avg_price = sum(p.price for p in comparables) / len(comparables)
            avg_price_per_sqft = sum(
                p.price / p.square_feet for p in comparables if p.square_feet
            ) / len([p for p in comparables if p.square_feet])

            results["steps"]["price_analysis"] = {
                "target_property_price": property.price,
                "average_comparable_price": avg_price,
                "price_difference": property.price - avg_price,
                "price_difference_percent": ((property.price - avg_price) / avg_price * 100) if avg_price else 0,
                "target_price_per_sqft": property.price / property.square_feet if property.square_feet else None,
                "average_price_per_sqft": avg_price_per_sqft
            }

        # Step 3: Zillow market data (75%)
        research.current_step = "Fetching Zillow market data"
        research.progress = 75
        db.commit()

        try:
            zillow_data = await zillow_enrichment_service.enrich_property(db, property.id)
            results["steps"]["zillow_market_data"] = zillow_data
        except Exception as e:
            results["steps"]["zillow_market_data"] = {"error": str(e)}

        # Step 4: Market recommendations (95%)
        research.current_step = "Generating market insights"
        research.progress = 95
        db.commit()

        recommendations = self._generate_market_recommendations(results)
        results["recommendations"] = recommendations

        return results

    async def _compliance_check(self, db: Session, research: Research) -> Dict:
        """
        Comprehensive compliance research:
        1. Run compliance engine
        2. Check contract requirements
        3. Identify violations
        4. Provide remediation steps
        """
        property = db.query(Property).filter(Property.id == research.property_id).first()
        if not property:
            raise ValueError("Property not found")

        results = {
            "research_type": "compliance_check",
            "property_id": research.property_id,
            "timestamp": datetime.utcnow().isoformat(),
            "steps": {}
        }

        # Step 1: Run compliance engine (50%)
        research.current_step = "Running compliance checks"
        research.progress = 50
        db.commit()

        compliance_results = await self.compliance_engine.run_compliance_check(db, property)
        results["steps"]["compliance_engine"] = compliance_results

        # Step 2: Contract compliance (80%)
        research.current_step = "Checking contract compliance"
        research.progress = 80
        db.commit()

        readiness = contract_auto_attach_service.get_required_contracts_status(db, property)
        results["steps"]["contract_compliance"] = readiness

        # Step 3: Generate remediation plan (95%)
        research.current_step = "Generating remediation plan"
        research.progress = 95
        db.commit()

        remediation = self._generate_remediation_plan(compliance_results, readiness)
        results["remediation_plan"] = remediation

        return results

    async def _contract_analysis(self, db: Session, research: Research) -> Dict:
        """
        Contract requirements analysis:
        1. AI contract suggestions
        2. Template analysis
        3. Gap analysis
        4. Readiness check
        """
        property = db.query(Property).filter(Property.id == research.property_id).first()
        if not property:
            raise ValueError("Property not found")

        results = {
            "research_type": "contract_analysis",
            "property_id": research.property_id,
            "timestamp": datetime.utcnow().isoformat(),
            "steps": {}
        }

        # Step 1: AI suggestions (33%)
        research.current_step = "Getting AI contract suggestions"
        research.progress = 33
        db.commit()

        ai_suggestions = await contract_ai_service.suggest_required_contracts(db, property)
        results["steps"]["ai_suggestions"] = ai_suggestions

        # Step 2: Gap analysis (66%)
        research.current_step = "Analyzing contract gaps"
        research.progress = 66
        db.commit()

        gap_analysis = await contract_ai_service.analyze_contract_gaps(db, property)
        results["steps"]["gap_analysis"] = gap_analysis

        # Step 3: Readiness check (95%)
        research.current_step = "Checking readiness to close"
        research.progress = 95
        db.commit()

        readiness = contract_auto_attach_service.get_required_contracts_status(db, property)
        results["steps"]["readiness"] = readiness

        return results

    async def _owner_research(self, db: Session, research: Research) -> Dict:
        """
        Owner research:
        1. Skip trace
        2. Public records
        3. Contact information
        """
        results = {
            "research_type": "owner_research",
            "property_id": research.property_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "not_implemented",
            "note": "Skip trace and owner research pending integration"
        }
        return results

    async def _neighborhood_analysis(self, db: Session, research: Research) -> Dict:
        """
        Neighborhood analysis:
        1. Schools
        2. Crime data
        3. Demographics
        4. Amenities
        """
        results = {
            "research_type": "neighborhood_analysis",
            "property_id": research.property_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "not_implemented",
            "note": "Neighborhood analysis pending integration"
        }
        return results

    async def _custom_research(self, db: Session, research: Research) -> Dict:
        """
        Custom research with specified endpoints.
        """
        results = {
            "research_type": "custom",
            "property_id": research.property_id,
            "timestamp": datetime.utcnow().isoformat(),
            "steps": {}
        }

        endpoints = research.endpoints_to_call or []
        total_steps = len(endpoints)

        for idx, endpoint_config in enumerate(endpoints):
            step_progress = int((idx + 1) / total_steps * 100)
            research.current_step = f"Calling {endpoint_config.get('name', 'endpoint')}"
            research.progress = step_progress
            db.commit()

            # Call endpoint (implementation depends on endpoint format)
            # This is a placeholder for custom endpoint calling
            results["steps"][endpoint_config.get('name', f'step_{idx}')] = {
                "status": "not_implemented",
                "config": endpoint_config
            }

        return results

    async def _ai_research(self, db: Session, research: Research) -> Dict:
        """
        Custom AI research with configurable prompts and models.

        Expected parameters:
        - prompt: str (required) - The question or research prompt
        - model: str (optional) - Model to use (default: claude-sonnet-4-20250514)
        - max_tokens: int (optional) - Max tokens in response (default: 4096)
        - temperature: float (optional) - Temperature 0-1 (default: 1.0)
        - system_prompt: str (optional) - System prompt for context
        - property_context: bool (optional) - Include property details in context (default: True)
        """
        results = {
            "research_type": "ai_research",
            "property_id": research.property_id,
            "timestamp": datetime.utcnow().isoformat(),
            "steps": {}
        }

        params = research.parameters or {}
        prompt = params.get("prompt")

        if not prompt:
            raise ValueError("AI research requires 'prompt' parameter")

        # Step 1: Prepare context (10%)
        research.current_step = "Preparing AI context"
        research.progress = 10
        db.commit()

        # Get property context if requested
        property_context = ""
        if params.get("property_context", True) and research.property_id:
            property = db.query(Property).filter(Property.id == research.property_id).first()
            if property:
                property_context = f"""
Property Context:
- Address: {property.address}, {property.city}, {property.state} {property.zip_code}
- Price: ${property.price:,.2f}
- Type: {property.property_type.value if property.property_type else 'N/A'}
- Beds/Baths: {property.bedrooms}/{property.bathrooms}
- Square Feet: {property.square_feet}
- Year Built: {property.year_built}
- Status: {property.status.value if property.status else 'N/A'}
"""

        # Step 2: Call AI model (50%)
        research.current_step = "Calling AI model"
        research.progress = 50
        db.commit()

        try:
            # Build messages
            messages = []

            # Add property context if available
            if property_context:
                messages.append({
                    "role": "user",
                    "content": property_context
                })

            # Add main prompt
            messages.append({
                "role": "user",
                "content": prompt
            })

            # Call Anthropic API
            response = self.anthropic_client.messages.create(
                model=params.get("model", "claude-sonnet-4-20250514"),
                max_tokens=params.get("max_tokens", 4096),
                temperature=params.get("temperature", 1.0),
                system=params.get("system_prompt", "You are a helpful AI assistant specializing in real estate research and analysis."),
                messages=messages
            )

            results["steps"]["ai_response"] = {
                "model": params.get("model", "claude-sonnet-4-20250514"),
                "prompt": prompt,
                "response": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }

        except Exception as e:
            results["steps"]["ai_response"] = {
                "error": str(e)
            }
            raise

        # Step 3: Complete (100%)
        research.current_step = "AI research complete"
        research.progress = 100
        db.commit()

        return results

    async def _api_research(self, db: Session, research: Research) -> Dict:
        """
        Custom API calls to external services.

        Expected parameters:
        - endpoints: List[Dict] (required) - List of API endpoints to call
          Each endpoint should have:
          - name: str (optional) - Descriptive name
          - url: str (required) - API endpoint URL
          - method: str (optional) - HTTP method (default: GET)
          - headers: Dict (optional) - Request headers
          - params: Dict (optional) - Query parameters
          - json: Dict (optional) - JSON body for POST/PUT
          - timeout: int (optional) - Request timeout in seconds (default: 30)
        """
        results = {
            "research_type": "api_research",
            "property_id": research.property_id,
            "timestamp": datetime.utcnow().isoformat(),
            "steps": {}
        }

        params = research.parameters or {}
        endpoints = params.get("endpoints", [])

        if not endpoints:
            raise ValueError("API research requires 'endpoints' parameter")

        total_steps = len(endpoints)

        async with httpx.AsyncClient() as client:
            for idx, endpoint_config in enumerate(endpoints):
                step_progress = int((idx + 1) / total_steps * 90)  # Reserve 10% for final step
                endpoint_name = endpoint_config.get('name', f'api_call_{idx}')

                research.current_step = f"Calling {endpoint_name}"
                research.progress = step_progress
                db.commit()

                # Validate required fields
                url = endpoint_config.get('url')
                if not url:
                    results["steps"][endpoint_name] = {
                        "error": "Missing required 'url' field"
                    }
                    continue

                try:
                    # Prepare request
                    method = endpoint_config.get('method', 'GET').upper()
                    headers = endpoint_config.get('headers', {})
                    params_dict = endpoint_config.get('params', {})
                    json_body = endpoint_config.get('json')
                    timeout = endpoint_config.get('timeout', 30)

                    # Make request
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params_dict,
                        json=json_body,
                        timeout=timeout
                    )

                    # Store results
                    results["steps"][endpoint_name] = {
                        "url": url,
                        "method": method,
                        "status_code": response.status_code,
                        "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                        "headers": dict(response.headers)
                    }

                except httpx.TimeoutException:
                    results["steps"][endpoint_name] = {
                        "url": url,
                        "error": f"Request timed out after {timeout} seconds"
                    }
                except Exception as e:
                    results["steps"][endpoint_name] = {
                        "url": url,
                        "error": str(e)
                    }

        # Complete (100%)
        research.current_step = "API research complete"
        research.progress = 100
        db.commit()

        return results

    def _generate_property_recommendations(self, results: Dict) -> List[str]:
        """Generate actionable recommendations from property analysis"""
        recommendations = []

        # Compliance recommendations
        compliance = results.get("steps", {}).get("compliance", {})
        if not compliance.get("passes_compliance"):
            recommendations.append("⚠️ Property has compliance violations that must be addressed before closing")

        # Contract recommendations
        contract_analysis = results.get("steps", {}).get("contract_analysis", {})
        readiness = contract_analysis.get("readiness", {})
        if not readiness.get("is_ready_to_close"):
            missing = readiness.get("missing", 0)
            in_progress = readiness.get("in_progress", 0)
            if missing > 0:
                recommendations.append(f"📄 {missing} required contract(s) need to be attached")
            if in_progress > 0:
                recommendations.append(f"✍️ {in_progress} contract(s) awaiting signature")

        # Market recommendations
        zillow = results.get("steps", {}).get("zillow_enrichment", {})
        if zillow and not zillow.get("error"):
            recommendations.append("✅ Property data enriched with Zillow market information")

        return recommendations

    def _generate_market_recommendations(self, results: Dict) -> List[str]:
        """Generate market insights"""
        recommendations = []

        price_analysis = results.get("steps", {}).get("price_analysis", {})
        if price_analysis:
            diff_percent = price_analysis.get("price_difference_percent", 0)
            if diff_percent > 10:
                recommendations.append(f"⬆️ Property is priced {diff_percent:.1f}% above comparable properties")
            elif diff_percent < -10:
                recommendations.append(f"⬇️ Property is priced {diff_percent:.1f}% below comparable properties")
            else:
                recommendations.append(f"✅ Property price is competitive with market ({diff_percent:+.1f}%)")

        return recommendations

    def _generate_remediation_plan(self, compliance: Dict, readiness: Dict) -> List[Dict]:
        """Generate step-by-step remediation plan"""
        plan = []

        # Compliance violations
        violations = compliance.get("violations", [])
        for violation in violations:
            plan.append({
                "priority": "high",
                "category": "compliance",
                "issue": violation.get("rule"),
                "action": violation.get("reason")
            })

        # Missing contracts
        missing = readiness.get("missing_templates", [])
        for template in missing:
            plan.append({
                "priority": "high",
                "category": "contracts",
                "issue": f"Missing required contract: {template.name}",
                "action": f"Attach and send {template.name} for signature"
            })

        # Incomplete contracts
        incomplete = readiness.get("incomplete_contracts", [])
        for contract in incomplete:
            plan.append({
                "priority": "medium",
                "category": "contracts",
                "issue": f"Contract pending: {contract.name}",
                "action": f"Follow up for signature on {contract.name}"
            })

        return plan


# Singleton instance
research_service = ResearchService()
