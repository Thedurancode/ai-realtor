"""Facebook Ad Targeting Router

AI-powered targeting recommendations for Facebook real estate ads.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict
from pydantic import BaseModel

from app.database import get_db
from app.services.facebook_targeting_service import FacebookTargetingService

router = APIRouter(prefix="/facebook-targeting", tags=["facebook-targeting"])


# ============================================================================
# Request/Response Models
# ============================================================================

class TargetingRequest(BaseModel):
    property_id: int


# ============================================================================
# Targeting Endpoints
# ============================================================================

@router.post("/analyze")
async def analyze_targeting(request: TargetingRequest, db: Session = Depends(get_db)):
    """Get AI-powered Facebook ad targeting for a property

    Returns comprehensive targeting including:
    - Primary and secondary audience personas
    - Location targeting strategy
    - Budget recommendations
    - Creative angle suggestions
    - Testing strategy

    Example request:
    {
        "property_id": 5
    }
    """
    try:
        service = FacebookTargetingService(db)
        targeting = service.analyze_property_for_targeting(request.property_id)
        return targeting
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/personas")
async def list_personas():
    """List all available targeting personas

    Returns detailed information about each persona:
    - Name and description
    - Age ranges
    - Recommended interests
    - Behaviors to target
    - Income and education levels
    """
    from app.services.facebook_targeting_service import FacebookTargetingService

    personas = []
    for persona_key, persona_data in FacebookTargetingService.PERSONAS.items():
        personas.append({
            "key": persona_key,
            "name": persona_data["name"],
            "age_range": persona_data["age_range"],
            "interests": persona_data["interests"],
            "behaviors": persona_data.get("behaviors", []),
            "income_level": persona_data["income_level"],
            "education": persona_data.get("education", "all")
        })

    return {
        "personas": personas,
        "total": len(personas)
    }


@router.get("/location-strategies")
async def list_location_strategies():
    """List all location targeting strategies

    Returns strategies for:
    - Urban (city center targeting)
    - Suburban (family-oriented targeting)
    - Resort (vacation home targeting)
    - Beachfront (coastal property targeting)
    """
    from app.services.facebook_targeting_service import FacebookTargetingService

    strategies = []
    for strategy_key, strategy_data in FacebookTargetingService.LOCATION_STRATEGIES.items():
        strategies.append({
            "type": strategy_key,
            "radius_km": strategy_data["radius_km"],
            "additional_interests": strategy_data["interests_addition"],
            "description": strategy_data["description"]
        })

    return {
        "strategies": strategies,
        "total": len(strategies)
    }


@router.get("/property-types")
async def list_property_type_targeting():
    """List property type targeting recommendations

    Returns targeting personas and interests for each property type:
    - House
    - Condo
    - Townhouse
    - Land
    - Commercial
    """
    from app.services.facebook_targeting_service import FacebookTargetingService

    types = []
    for type_key, type_data in FacebookTargetingService.PROPERTY_TYPE_TARGETING.items():
        types.append({
            "property_type": type_key,
            "primary_persona": type_data["primary_persona"],
            "secondary_persona": type_data["secondary_persona"],
            "recommended_interests": type_data["interests"]
        })

    return {
        "property_types": types,
        "total": len(types)
    }
