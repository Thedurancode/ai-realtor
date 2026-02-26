"""Facebook Ad Targeting AI Service

AI-powered targeting recommendations for Facebook real estate ads.
Analyzes property details to suggest optimal audiences, demographics, and interests.
"""
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.property import Property

logger = logging.getLogger(__name__)


class FacebookTargetingService:
    """AI-powered Facebook ad targeting recommendations"""

    # Real estate targeting personas
    PERSONAS = {
        "luxury_buyer": {
            "name": "Luxury Home Buyer",
            "age_range": (35, 65),
            "interests": [
                "Luxury goods", "High-end real estate", "Private jet",
                "Yachting", "Fine dining", "Art collection",
                "Wealth management", "Investment properties"
            ],
            "behaviors": ["Facebook Page Admins", "Engaged Shoppers (High)"],
            "income_level": "high",
            "education": "graduate_degree"
        },
        "first_time_buyer": {
            "name": "First-Time Home Buyer",
            "age_range": (25, 40),
            "interests": [
                "Home buying", "Mortgage calculator", "Interior design",
                "Home improvement", "Real estate investing",
                "Apartment hunting", "Moving and relocation"
            ],
            "behaviors": ["Facebook Page Admins", "Recent home purchasers"],
            "income_level": "medium",
            "education": "college"
        },
        "investor": {
            "name": "Real Estate Investor",
            "age_range": (30, 65),
            "interests": [
                "Real estate investing", "Rental properties",
                "Property management", "House flipping",
                "Real estate crowdfunding", "REIT",
                "Passive income", "Investment strategy"
            ],
            "behaviors": ["Facebook Page Admins", "Business decision-makers"],
            "income_level": "high",
            "education": "graduate_degree"
        },
        "vacation_home": {
            "name": "Vacation/Second Home Buyer",
            "age_range": (40, 65),
            "interests": [
                "Vacation homes", "Beach houses", "Mountain properties",
                "Resort living", "Seasonal rental", "Luxury travel",
                "Timeshare", "Second home"
            ],
            "behaviors": ["Facebook Page Admins", "Frequent travelers"],
            "income_level": "high",
            "education": "college"
        },
        "downsizer": {
            "name": "Empty Nester/Downsizer",
            "age_range": (55, 75),
            "interests": [
                "Condominium", "Retirement communities", "Active adult living",
                "Low maintenance homes", "Senior living", "Gated community",
                "Interior design", "Home organization"
            ],
            "behaviors": ["Facebook Page Admins", "Retirement planning"],
            "income_level": "medium_high",
            "education": "college"
        },
        "family_home": {
            "name": "Family Home Buyer",
            "age_range": (30, 50),
            "interests": [
                "Family home", "Suburban living", "School district",
                "Child care", "Parenting", "Family activities",
                "Backyard design", "Home safety"
            ],
            "behaviors": ["Facebook Page Admins", "Parents"],
            "income_level": "medium_high",
            "education": "college"
        }
    }

    # Location-based targeting strategies
    LOCATION_STRATEGIES = {
        "urban": {
            "radius_km": 10,
            "interests_addition": ["Urban living", "City life", "Public transportation", "Walkability"],
            "description": "Target urban professionals and city dwellers"
        },
        "suburban": {
            "radius_km": 25,
            "interests_addition": ["Suburban living", "Family-friendly", "School ratings", "Community events"],
            "description": "Target families and suburban home seekers"
        },
        "resort": {
            "radius_km": 50,
            "interests_addition": ["Luxury travel", "Vacation destinations", "Resort amenities", "Golf courses"],
            "description": "Target vacation home buyers and luxury seekers"
        },
        "beachfront": {
            "radius_km": 40,
            "interests_addition": ["Beach houses", "Oceanfront living", "Water sports", "Coastal living"],
            "description": "Target oceanfront property seekers"
        }
    }

    # Property type targeting
    PROPERTY_TYPE_TARGETING = {
        "house": {
            "primary_persona": "family_home",
            "secondary_persona": "first_time_buyer",
            "interests": ["Single-family home", "Backyard", "Garage", "Homeownership"]
        },
        "condo": {
            "primary_persona": "luxury_buyer",
            "secondary_persona": "downsizer",
            "interests": ["Condominium", "Low maintenance living", "Amenities", "HOA"]
        },
        "townhouse": {
            "primary_persona": "family_home",
            "secondary_persona": "first_time_buyer",
            "interests": ["Townhouse", "Multi-level living", "Urban community"]
        },
        "land": {
            "primary_persona": "investor",
            "secondary_persona": "luxury_buyer",
            "interests": ["Land development", "Custom homes", "Building lots", "Acreage"]
        },
        "commercial": {
            "primary_persona": "investor",
            "secondary_persona": "investor",
            "interests": ["Commercial real estate", "Business location", "Retail space", "Office space"]
        }
    }

    def __init__(self, db: Session):
        self.db = db

    def analyze_property_for_targeting(self, property_id: int) -> Dict:
        """Analyze property and generate targeting recommendations

        Args:
            property_id: Property ID to analyze

        Returns:
            Comprehensive targeting recommendations
        """
        property = self.db.query(Property).filter(Property.id == property_id).first()
        if not property:
            raise ValueError(f"Property {property_id} not found")

        # Determine property characteristics
        price_tier = self._get_price_tier(property.price)
        location_type = self._detect_location_type(property.city, property.state)
        property_type = property.property_type or "house"

        # Get base personas
        property_targeting = self.PROPERTY_TYPE_TARGETING.get(property_type, self.PROPERTY_TYPE_TARGETING["house"])
        primary_persona = self.PERSONAS[property_targeting["primary_persona"]]
        secondary_persona = self.PERSONAS[property_targeting["secondary_persona"]]

        # Build location strategy
        location_strategy = self.LOCATION_STRATEGIES.get(location_type, self.LOCATION_STRATEGIES["suburban"])

        # Compile comprehensive targeting
        targeting = {
            "property_analysis": {
                "property_id": property.id,
                "address": f"{property.address}, {property.city}, {property.state}",
                "price": property.price,
                "price_tier": price_tier,
                "property_type": property_type,
                "bedrooms": property.bedrooms,
                "bathrooms": property.bathrooms
            },
            "primary_audience": {
                "name": primary_persona["name"],
                "description": f"Primary target: {primary_persona['name']}s in {property.city} area",
                "age_min": primary_persona["age_range"][0],
                "age_max": primary_persona["age_range"][1],
                "interests": primary_persona["interests"] + property_targeting["interests"],
                "behaviors": primary_persona.get("behaviors", []),
                "income_level": primary_persona["income_level"],
                "education": primary_persona.get("education", "all")
            },
            "secondary_audience": {
                "name": secondary_persona["name"],
                "description": f"Secondary target: {secondary_persona['name']}s",
                "age_min": secondary_persona["age_range"][0],
                "age_max": secondary_persona["age_range"][1],
                "interests": secondary_persona["interests"][:5],  # Fewer interests for secondary
                "behaviors": secondary_persona.get("behaviors", []),
                "income_level": secondary_persona["income_level"]
            },
            "location_targeting": {
                "location_type": location_type,
                "radius_km": location_strategy["radius_km"],
                "location": f"{property.city}, {property.state}",
                "description": location_strategy["description"],
                "additional_interests": location_strategy["interests_addition"]
            },
            "budget_recommendations": {
                "daily_budget_min": self._calculate_min_budget(price_tier),
                "daily_budget_max": self._calculate_max_budget(price_tier),
                "recommended_duration_days": 30,
                "projected_cpl": self._project_cpl(price_tier, location_type)
            },
            "creative_recommendations": {
                "angles": self._suggest_creative_angles(property, price_tier),
                "headline_keywords": self._get_headline_keywords(property, location_type),
                "pain_points": self._identify_pain_points(property, primary_persona["name"])
            },
            "testing_strategy": {
                "recommendation": "Test all 3 angles simultaneously",
                "test_duration_days": 14,
                "budget_per_variant": "33% of total budget",
                "success_metrics": ["Click-through rate", "Cost per lead", "Conversion rate"]
            }
        }

        return targeting

    def _get_price_tier(self, price: Optional[int]) -> str:
        """Determine price tier from property price"""
        if not price:
            return "medium"

        if price < 300000:
            return "budget"
        elif price < 500000:
            return "medium"
        elif price < 1000000:
            return "high"
        else:
            return "luxury"

    def _detect_location_type(self, city: str, state: str) -> str:
        """Detect location type based on city characteristics"""
        city_lower = city.lower()

        # Beachfront locations
        beach_keywords = ["miami beach", "malibu", "santa monica", "hamptons", "cape cod"]
        if any(kw in city_lower for kw in beach_keywords):
            return "beachfront"

        # Resort locations
        resort_keywords = ["aspen", "vail", "park city", "scottsdale", "naples"]
        if any(kw in city_lower for kw in resort_keywords):
            return "resort"

        # Urban locations
        urban_cities = ["new york", "manhattan", "san francisco", "boston", "chicago", "washington"]
        if any(kw in city_lower for kw in urban_cities):
            return "urban"

        # Default to suburban
        return "suburban"

    def _calculate_min_budget(self, price_tier: str) -> int:
        """Calculate minimum daily budget based on price tier"""
        budgets = {
            "budget": 10,
            "medium": 20,
            "high": 50,
            "luxury": 100
        }
        return budgets.get(price_tier, 20)

    def _calculate_max_budget(self, price_tier: str) -> int:
        """Calculate maximum daily budget based on price tier"""
        budgets = {
            "budget": 30,
            "medium": 50,
            "high": 100,
            "luxury": 200
        }
        return budgets.get(price_tier, 50)

    def _project_cpl(self, price_tier: str, location_type: str) -> Dict[str, float]:
        """Project cost per lead based on price tier and location"""
        base_cpl = {
            "budget": 15,
            "medium": 30,
            "high": 50,
            "luxury": 100
        }

        location_multipliers = {
            "urban": 1.5,
            "suburban": 1.0,
            "beachfront": 1.3,
            "resort": 1.4
        }

        base = base_cpl.get(price_tier, 30)
        multiplier = location_multipliers.get(location_type, 1.0)

        return {
            "min_cpl": round(base * multiplier * 0.7, 2),
            "avg_cpl": round(base * multiplier, 2),
            "max_cpl": round(base * multiplier * 1.3, 2)
        }

    def _suggest_creative_angles(self, property: Property, price_tier: str) -> List[Dict]:
        """Suggest creative angles based on property analysis"""
        angles = []

        # Always include value angle
        angles.append({
            "angle": "value",
            "headline": f"Premium {property.city} Property at Market Price",
            "rationale": "Emphasizes value proposition and fair pricing"
        })

        # Luxury angle for high-end properties
        if price_tier in ["high", "luxury"]:
            angles.append({
                "angle": "luxury",
                "headline": f"Exclusive {property.city} Living",
                "rationale": "Highlights luxury features and exclusivity"
            })

        # Urgency angle
        angles.append({
            "angle": "urgency",
            "headline": f"Limited Opportunity in {property.city}",
            "rationale": "Creates scarcity and urgency"
        })

        return angles

    def _get_headline_keywords(self, property: Property, location_type: str) -> List[str]:
        """Get effective headline keywords"""
        keywords = [property.city, property.state]

        if property.bedrooms and property.bedrooms >= 3:
            keywords.extend(["Spacious", "Family Home"])

        if property.bathrooms and property.bathrooms >= 2:
            keywords.append("Luxurious Bath")

        if location_type == "beachfront":
            keywords.extend(["Ocean Views", "Beach Access", "Coastal Living"])

        if location_type == "urban":
            keywords.extend(["City Views", "Urban Living", "Prime Location"])

        return keywords

    def _identify_pain_points(self, property: Property, persona: str) -> List[str]:
        """Identify customer pain points to address"""
        pain_points = {
            "luxury_buyer": [
                "Hard to find true luxury properties",
                "Concerns about privacy and exclusivity",
                "Need for premium amenities"
            ],
            "first_time_buyer": [
                "Worried about affordability",
                "Need guidance through buying process",
                "Want a home that will grow in value"
            ],
            "investor": [
                "Need strong ROI potential",
                "Want low-maintenance properties",
                "Concerned about market timing"
            ],
            "vacation_home": [
                "Want the perfect getaway",
                "Need easy rental management",
                "Looking for lifestyle investment"
            ],
            "downsizer": [
                "Want low maintenance",
                "Need single-level living",
                "Seek community and security"
            ],
            "family_home": [
                "Need good school district",
                "Want safe neighborhood",
                "Need room to grow"
            ]
        }

        return pain_points.get(persona, ["Finding the right property", "Getting fair value"])


# Helper function for MCP tool integration
async def get_facebook_targeting(property_id: int) -> Dict:
    """Get Facebook targeting recommendations for a property

    Args:
        property_id: Property ID to analyze

    Returns:
        Targeting recommendations with audiences, budgets, and creative suggestions
    """
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        service = FacebookTargetingService(db)
        return service.analyze_property_for_targeting(property_id)
    finally:
        db.close()
