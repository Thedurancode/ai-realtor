"""
AI Agent Tools

Tools that AI agents can use to interact with the system.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from anthropic.types import ToolParam

from app.models.property import Property
from app.models.contact import Contact
from app.models.contract import Contract
from app.services.zillow_enrichment import zillow_enrichment_service
from app.services.compliance_engine import ComplianceEngine
from app.services.exa_research_service import exa_research_service


class AgentTools:
    """
    Tools available to AI agents for property research and analysis.

    Each tool is defined with:
    1. A schema (for Claude's tool use API)
    2. An implementation function
    """

    def __init__(self, db: Session):
        self.db = db
        self.compliance_engine = ComplianceEngine()

    def get_tool_schemas(self) -> List[ToolParam]:
        """Get all available tool schemas for Claude API"""
        return [
            {
                "name": "get_property_details",
                "description": "Get detailed information about a property including address, price, specs, and current status. Use this when you need property information.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "property_id": {
                            "type": "integer",
                            "description": "The ID of the property to retrieve"
                        }
                    },
                    "required": ["property_id"]
                }
            },
            {
                "name": "get_comparable_properties",
                "description": "Find comparable properties (comps) in the same area with similar characteristics. Use this for market analysis and pricing.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "property_id": {
                            "type": "integer",
                            "description": "The property to find comps for"
                        },
                        "radius_miles": {
                            "type": "number",
                            "description": "Search radius in miles (default: 1.0)",
                            "default": 1.0
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of comps to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["property_id"]
                }
            },
            {
                "name": "get_zillow_data",
                "description": "Get enriched market data from Zillow including zestimate, rental estimate, and market trends. Use this for valuation and market insights.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "property_id": {
                            "type": "integer",
                            "description": "The property ID to get Zillow data for"
                        }
                    },
                    "required": ["property_id"]
                }
            },
            {
                "name": "check_compliance",
                "description": "Run comprehensive compliance checks on a property including legal, regulatory, and contract requirements. Use this for due diligence.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "property_id": {
                            "type": "integer",
                            "description": "The property ID to check compliance for"
                        }
                    },
                    "required": ["property_id"]
                }
            },
            {
                "name": "get_property_contracts",
                "description": "Get all contracts associated with a property including their status and requirements. Use this to check contract readiness.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "property_id": {
                            "type": "integer",
                            "description": "The property ID to get contracts for"
                        }
                    },
                    "required": ["property_id"]
                }
            },
            {
                "name": "search_properties",
                "description": "Search for properties by various criteria like city, state, price range, property type. Use this for market research.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "Filter by city"
                        },
                        "state": {
                            "type": "string",
                            "description": "Filter by state (2-letter code)"
                        },
                        "min_price": {
                            "type": "integer",
                            "description": "Minimum price"
                        },
                        "max_price": {
                            "type": "integer",
                            "description": "Maximum price"
                        },
                        "property_type": {
                            "type": "string",
                            "description": "Property type: house, condo, townhouse, land, multi_family, commercial"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results (default: 10)",
                            "default": 10
                        }
                    }
                }
            },
            {
                "name": "calculate_roi",
                "description": "Calculate investment ROI metrics including cash flow, cap rate, and cash-on-cash return. Requires property details and assumptions.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "property_id": {
                            "type": "integer",
                            "description": "The property to analyze"
                        },
                        "down_payment_percent": {
                            "type": "number",
                            "description": "Down payment as percentage (e.g., 20)",
                            "default": 20
                        },
                        "interest_rate": {
                            "type": "number",
                            "description": "Annual interest rate as percentage (e.g., 7.5)",
                            "default": 7.5
                        },
                        "monthly_rent": {
                            "type": "number",
                            "description": "Expected monthly rent (if not provided, will estimate)"
                        },
                        "vacancy_rate": {
                            "type": "number",
                            "description": "Vacancy rate as percentage (default: 5)",
                            "default": 5
                        },
                        "management_fee_percent": {
                            "type": "number",
                            "description": "Property management fee as percentage (default: 10)",
                            "default": 10
                        }
                    },
                    "required": ["property_id"]
                }
            },
            {
                "name": "exa_create_research_task",
                "description": "Create an Exa Research task for deep web research. Use this for open-web investigations beyond internal property records.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "instructions": {
                            "type": "string",
                            "description": "Research instructions for Exa"
                        },
                        "model": {
                            "type": "string",
                            "description": "Exa research model name (default: exa-research-fast)",
                            "default": "exa-research-fast"
                        }
                    },
                    "required": ["instructions"]
                }
            },
            {
                "name": "exa_get_research_task",
                "description": "Fetch Exa Research task status/results by task_id after creating a task.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "The task ID returned by exa_create_research_task"
                        }
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "exa_create_subdivision_research_task",
                "description": "Create a subdivision-feasibility Exa Research task for a property address.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "address": {
                            "type": "string",
                            "description": "Full property address"
                        },
                        "county": {
                            "type": "string",
                            "description": "Optional county name"
                        },
                        "target_strategy": {
                            "type": "string",
                            "description": "Subdivision strategy (default: subdivide and build)",
                            "default": "subdivide and build"
                        },
                        "target_lot_count": {
                            "type": "integer",
                            "description": "Optional target number of lots"
                        },
                        "model": {
                            "type": "string",
                            "description": "Exa research model name (default: exa-research-fast)",
                            "default": "exa-research-fast"
                        }
                    },
                    "required": ["address"]
                }
            }
        ]

    async def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return results"""

        if tool_name == "get_property_details":
            return await self._get_property_details(tool_input["property_id"])

        elif tool_name == "get_comparable_properties":
            return await self._get_comparable_properties(
                tool_input["property_id"],
                tool_input.get("radius_miles", 1.0),
                tool_input.get("limit", 5)
            )

        elif tool_name == "get_zillow_data":
            return await self._get_zillow_data(tool_input["property_id"])

        elif tool_name == "check_compliance":
            return await self._check_compliance(tool_input["property_id"])

        elif tool_name == "get_property_contracts":
            return await self._get_property_contracts(tool_input["property_id"])

        elif tool_name == "search_properties":
            return await self._search_properties(tool_input)

        elif tool_name == "calculate_roi":
            return await self._calculate_roi(tool_input)

        elif tool_name == "exa_create_research_task":
            return await self._exa_create_research_task(tool_input)

        elif tool_name == "exa_get_research_task":
            return await self._exa_get_research_task(tool_input)

        elif tool_name == "exa_create_subdivision_research_task":
            return await self._exa_create_subdivision_research_task(tool_input)

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    # Tool Implementations

    async def _get_property_details(self, property_id: int) -> Dict:
        """Get detailed property information"""
        property = self.db.query(Property).filter(Property.id == property_id).first()

        if not property:
            return {"error": f"Property {property_id} not found"}

        return {
            "id": property.id,
            "address": property.address,
            "city": property.city,
            "state": property.state,
            "zip_code": property.zip_code,
            "price": property.price,
            "bedrooms": property.bedrooms,
            "bathrooms": property.bathrooms,
            "square_feet": property.square_feet,
            "lot_size": property.lot_size,
            "year_built": property.year_built,
            "property_type": property.property_type.value if property.property_type else None,
            "status": property.status.value if property.status else None,
            "deal_type": property.deal_type.value if property.deal_type else None,
            "price_per_sqft": round(property.price / property.square_feet, 2) if property.square_feet else None
        }

    async def _get_comparable_properties(self, property_id: int, radius_miles: float, limit: int) -> Dict:
        """Find comparable properties"""
        property = self.db.query(Property).filter(Property.id == property_id).first()

        if not property:
            return {"error": f"Property {property_id} not found"}

        # Simple comparable search (same city, similar bedrooms)
        comps = self.db.query(Property).filter(
            Property.id != property_id,
            Property.city == property.city,
            Property.state == property.state,
            Property.bedrooms == property.bedrooms
        ).limit(limit).all()

        return {
            "target_property": {
                "address": property.address,
                "price": property.price,
                "price_per_sqft": round(property.price / property.square_feet, 2) if property.square_feet else None
            },
            "comparables": [
                {
                    "id": p.id,
                    "address": p.address,
                    "price": p.price,
                    "bedrooms": p.bedrooms,
                    "bathrooms": p.bathrooms,
                    "square_feet": p.square_feet,
                    "price_per_sqft": round(p.price / p.square_feet, 2) if p.square_feet else None,
                    "year_built": p.year_built
                }
                for p in comps
            ],
            "market_insights": {
                "average_price": sum(p.price for p in comps) / len(comps) if comps else 0,
                "average_price_per_sqft": sum(p.price / p.square_feet for p in comps if p.square_feet) / len([p for p in comps if p.square_feet]) if comps else 0,
                "target_vs_market": f"{((property.price / (sum(p.price for p in comps) / len(comps)) - 1) * 100):.1f}%" if comps else "N/A"
            }
        }

    async def _get_zillow_data(self, property_id: int) -> Dict:
        """Get Zillow enrichment data"""
        try:
            zillow_data = await zillow_enrichment_service.enrich_property(self.db, property_id)
            return zillow_data
        except Exception as e:
            return {"error": str(e), "note": "Zillow data not available"}

    async def _check_compliance(self, property_id: int) -> Dict:
        """Run compliance checks"""
        property = self.db.query(Property).filter(Property.id == property_id).first()

        if not property:
            return {"error": f"Property {property_id} not found"}

        try:
            compliance_results = await self.compliance_engine.run_compliance_check(self.db, property)
            return compliance_results
        except Exception as e:
            return {"error": str(e)}

    async def _get_property_contracts(self, property_id: int) -> Dict:
        """Get property contracts"""
        contracts = self.db.query(Contract).filter(Contract.property_id == property_id).all()

        return {
            "property_id": property_id,
            "total_contracts": len(contracts),
            "contracts": [
                {
                    "id": c.id,
                    "name": c.name,
                    "status": c.status.value,
                    "sent_at": c.sent_at.isoformat() if c.sent_at else None,
                    "completed_at": c.completed_at.isoformat() if c.completed_at else None
                }
                for c in contracts
            ],
            "summary": {
                "completed": len([c for c in contracts if c.status.value == "completed"]),
                "pending": len([c for c in contracts if c.status.value in ["sent", "in_progress", "pending_signature"]]),
                "draft": len([c for c in contracts if c.status.value == "draft"])
            }
        }

    async def _search_properties(self, filters: Dict) -> Dict:
        """Search properties by criteria"""
        query = self.db.query(Property)

        if "city" in filters:
            query = query.filter(Property.city == filters["city"])
        if "state" in filters:
            query = query.filter(Property.state == filters["state"])
        if "min_price" in filters:
            query = query.filter(Property.price >= filters["min_price"])
        if "max_price" in filters:
            query = query.filter(Property.price <= filters["max_price"])
        if "property_type" in filters:
            query = query.filter(Property.property_type == filters["property_type"])

        limit = filters.get("limit", 10)
        properties = query.limit(limit).all()

        return {
            "total_found": len(properties),
            "filters_applied": filters,
            "properties": [
                {
                    "id": p.id,
                    "address": p.address,
                    "city": p.city,
                    "state": p.state,
                    "price": p.price,
                    "bedrooms": p.bedrooms,
                    "bathrooms": p.bathrooms,
                    "square_feet": p.square_feet,
                    "property_type": p.property_type.value if p.property_type else None
                }
                for p in properties
            ]
        }

    async def _calculate_roi(self, params: Dict) -> Dict:
        """Calculate investment ROI metrics"""
        property_id = params["property_id"]
        property = self.db.query(Property).filter(Property.id == property_id).first()

        if not property:
            return {"error": f"Property {property_id} not found"}

        price = property.price
        down_payment_pct = params.get("down_payment_percent", 20)
        interest_rate = params.get("interest_rate", 7.5)
        vacancy_rate = params.get("vacancy_rate", 5)
        mgmt_fee_pct = params.get("management_fee_percent", 10)

        # Calculate monthly rent (estimate if not provided)
        monthly_rent = params.get("monthly_rent")
        if not monthly_rent:
            # Rough estimate: 1% of property value per month
            monthly_rent = price * 0.01

        # Loan calculations
        down_payment = price * (down_payment_pct / 100)
        loan_amount = price - down_payment
        monthly_rate = (interest_rate / 100) / 12
        num_payments = 30 * 12  # 30-year mortgage

        # Monthly mortgage payment
        if monthly_rate > 0:
            monthly_mortgage = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
        else:
            monthly_mortgage = loan_amount / num_payments

        # Monthly expenses
        annual_property_tax = price * 0.012  # Rough 1.2% estimate
        annual_insurance = price * 0.005  # Rough 0.5% estimate
        monthly_property_tax = annual_property_tax / 12
        monthly_insurance = annual_insurance / 12
        monthly_hoa = 0  # Could add if property has HOA
        monthly_maintenance = monthly_rent * 0.05  # 5% of rent for maintenance
        monthly_vacancy = monthly_rent * (vacancy_rate / 100)
        monthly_mgmt = monthly_rent * (mgmt_fee_pct / 100)

        total_monthly_expenses = monthly_mortgage + monthly_property_tax + monthly_insurance + monthly_hoa + monthly_maintenance + monthly_vacancy + monthly_mgmt

        # Net cash flow
        monthly_cash_flow = monthly_rent - total_monthly_expenses
        annual_cash_flow = monthly_cash_flow * 12

        # ROI metrics
        cash_on_cash_return = (annual_cash_flow / down_payment * 100) if down_payment > 0 else 0
        annual_noi = (monthly_rent * 12) - (annual_property_tax + annual_insurance + (monthly_maintenance * 12) + (monthly_vacancy * 12) + (monthly_mgmt * 12))
        cap_rate = (annual_noi / price * 100) if price > 0 else 0

        return {
            "property_id": property_id,
            "purchase_price": price,
            "financing": {
                "down_payment": down_payment,
                "down_payment_percent": down_payment_pct,
                "loan_amount": loan_amount,
                "interest_rate": interest_rate,
                "monthly_mortgage": round(monthly_mortgage, 2)
            },
            "monthly_income": {
                "gross_rent": monthly_rent
            },
            "monthly_expenses": {
                "mortgage": round(monthly_mortgage, 2),
                "property_tax": round(monthly_property_tax, 2),
                "insurance": round(monthly_insurance, 2),
                "hoa": monthly_hoa,
                "maintenance": round(monthly_maintenance, 2),
                "vacancy": round(monthly_vacancy, 2),
                "property_management": round(monthly_mgmt, 2),
                "total": round(total_monthly_expenses, 2)
            },
            "cash_flow": {
                "monthly": round(monthly_cash_flow, 2),
                "annual": round(annual_cash_flow, 2)
            },
            "roi_metrics": {
                "cash_on_cash_return": f"{round(cash_on_cash_return, 2)}%",
                "cap_rate": f"{round(cap_rate, 2)}%",
                "noi": round(annual_noi, 2)
            },
            "assessment": {
                "cash_flows_positive": monthly_cash_flow > 0,
                "estimated_monthly_profit": round(monthly_cash_flow, 2),
                "breakeven_rent": round(total_monthly_expenses, 2)
            }
        }

    async def _exa_create_research_task(self, params: Dict) -> Dict:
        """Create Exa research task"""
        instructions = str(params.get("instructions", "")).strip()
        if not instructions:
            return {"error": "instructions is required"}

        model = str(params.get("model", "exa-research-fast")).strip() or "exa-research-fast"
        try:
            raw = await exa_research_service.create_research_task(
                instructions=instructions,
                model=model,
            )
            return {
                "task_id": exa_research_service.extract_task_id(raw),
                "status": exa_research_service.extract_status(raw),
                "raw": raw,
            }
        except Exception as exc:
            return {"error": f"Exa create task failed: {exc}"}

    async def _exa_get_research_task(self, params: Dict) -> Dict:
        """Fetch Exa research task"""
        task_id = str(params.get("task_id", "")).strip()
        if not task_id:
            return {"error": "task_id is required"}

        try:
            raw = await exa_research_service.get_research_task(task_id=task_id)
            return {
                "task_id": exa_research_service.extract_task_id(raw) or task_id,
                "status": exa_research_service.extract_status(raw),
                "raw": raw,
            }
        except Exception as exc:
            return {"error": f"Exa get task failed: {exc}"}

    async def _exa_create_subdivision_research_task(self, params: Dict) -> Dict:
        """Create Exa subdivision-feasibility research task"""
        address = str(params.get("address", "")).strip()
        if not address:
            return {"error": "address is required"}

        county = params.get("county")
        county_value = str(county).strip() if county is not None else None
        target_strategy = str(params.get("target_strategy", "subdivide and build")).strip() or "subdivide and build"

        target_lot_count = params.get("target_lot_count")
        if target_lot_count is not None:
            try:
                target_lot_count = int(target_lot_count)
            except Exception:
                return {"error": "target_lot_count must be an integer"}

        model = str(params.get("model", "exa-research-fast")).strip() or "exa-research-fast"
        instructions = exa_research_service.build_subdivision_dossier_instructions(
            address=address,
            county=county_value,
            target_strategy=target_strategy,
            target_lot_count=target_lot_count,
        )

        try:
            raw = await exa_research_service.create_research_task(
                instructions=instructions,
                model=model,
            )
            return {
                "task_id": exa_research_service.extract_task_id(raw),
                "status": exa_research_service.extract_status(raw),
                "instructions": instructions,
                "raw": raw,
            }
        except Exception as exc:
            return {"error": f"Exa subdivision task failed: {exc}"}
