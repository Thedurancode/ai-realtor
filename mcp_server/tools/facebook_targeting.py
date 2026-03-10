"""Facebook Ad Targeting MCP Tools

Voice-controlled tools for AI-powered Facebook ad targeting.
"""
from mcp.types import Tool, TextContent

from ..server import register_tool
from ..utils.http_client import api_get, api_post


async def handle_get_facebook_targeting(arguments: dict) -> list[TextContent]:
    """Get AI-powered Facebook ad targeting recommendations for a property."""
    property_id = arguments.get("property_id")
    if not property_id:
        return [TextContent(type="text", text="Error: property_id is required")]

    response = api_post("/facebook-targeting/analyze", json={"property_id": property_id})
    response.raise_for_status()
    result = response.json()

    if result.get("error"):
        return [TextContent(type="text", text=f"Error: {result['error']}")]

    text = format_targeting_for_voice(result)
    return [TextContent(type="text", text=text)]


async def handle_list_targeting_personas(arguments: dict) -> list[TextContent]:
    """List all available Facebook targeting personas."""
    response = api_get("/facebook-targeting/personas")
    response.raise_for_status()
    result = response.json()

    if result.get("error"):
        return [TextContent(type="text", text=f"Error: {result['error']}")]

    text = format_personas_for_voice(result)
    return [TextContent(type="text", text=text)]


async def handle_suggest_facebook_audiences(arguments: dict) -> list[TextContent]:
    """Get Facebook audience suggestions based on property characteristics."""
    property_id = arguments.get("property_id")
    if not property_id:
        return [TextContent(type="text", text="Error: property_id is required")]

    response = api_post("/facebook-targeting/analyze", json={"property_id": property_id})
    response.raise_for_status()
    result = response.json()

    if result.get("error"):
        return [TextContent(type="text", text=f"Error: {result['error']}")]

    text = format_audiences_for_voice(result)
    return [TextContent(type="text", text=text)]


def format_targeting_for_voice(result: dict) -> str:
    """Format targeting analysis for voice output."""
    property_analysis = result.get("property_analysis", {})
    primary = result.get("primary_audience", {})
    secondary = result.get("secondary_audience", {})
    location = result.get("location_targeting", {})
    budget = result.get("budget_recommendations", {})
    creative = result.get("creative_recommendations", {})

    voice = f"""Facebook Ad Targeting for {property_analysis.get('address', 'Property')}

Property Analysis:
- Price: ${property_analysis.get('price', 0):,.0f}
- Type: {property_analysis.get('property_type', 'N/A').title()}
- Bedrooms: {property_analysis.get('bedrooms', 'N/A')}
- Bathrooms: {property_analysis.get('bathrooms', 'N/A')}

Primary Audience: {primary.get('name', 'N/A')}
- Ages: {primary.get('age_min', 0)}-{primary.get('age_max', 0)}
- Income: {primary.get('income_level', 'N/A').title()}
- Key Interests: {', '.join(primary.get('interests', [])[:5])}
- Behaviors: {', '.join(primary.get('behaviors', []))}

Secondary Audience: {secondary.get('name', 'N/A')}
- Ages: {secondary.get('age_min', 0)}-{secondary.get('age_max', 0)}
- Key Interests: {', '.join(secondary.get('interests', [])[:5])}

Location Strategy:
- Area: {location.get('location', 'N/A')}
- Radius: {location.get('radius_km', 0)}km
- Type: {location.get('location_type', 'N/A').title()}
- Description: {location.get('description', 'N/A')}

Budget Recommendations:
- Daily Budget: ${budget.get('daily_budget_min', 0)}-${budget.get('daily_budget_max', 0)}
- Projected CPL: ${budget.get('projected_cpl', {}).get('avg_cpl', 0):.2f}
- Duration: {budget.get('recommended_duration_days', 30)} days

Creative Angles:"""

    for angle in creative.get('angles', []):
        voice += f"\n- {angle.get('angle', 'N/A').title()}: {angle.get('headline', 'N/A')}"

    voice += f"\n\nCustomer Pain Points:"
    for pain_point in creative.get('pain_points', []):
        voice += f"\n- {pain_point}"

    testing = result.get("testing_strategy", {})
    voice += f"""

Testing Strategy:
- {testing.get('recommendation', 'N/A')}
- Test Duration: {testing.get('test_duration_days', 14)} days
- Budget Per Variant: {testing.get('budget_per_variant', 'N/A')}
- Success Metrics: {', '.join(testing.get('success_metrics', []))}

Ready to launch in Meta Ads Manager!"""

    return voice


def format_personas_for_voice(result: dict) -> str:
    """Format personas list for voice output."""
    personas = result.get("personas", [])

    voice = f"Available Facebook Targeting Personas ({len(personas)} total)\n"

    for persona in personas:
        voice += f"""
- {persona['name']}
  Age Range: {persona['age_range'][0]}-{persona['age_range'][1]}
  Income: {persona['income_level'].title()}
  Education: {persona['education'].title().replace('_', ' ')}
  Top Interests: {', '.join(persona['interests'][:4])}
  Behaviors: {', '.join(persona['behaviors'][:2]) if persona['behaviors'] else 'None'}
"""

    return voice


def format_audiences_for_voice(result: dict) -> str:
    """Format audience suggestions for voice output."""
    property_analysis = result.get("property_analysis", {})
    primary = result.get("primary_audience", {})
    location = result.get("location_targeting", {})

    voice = f"""Suggested Facebook Audiences for {property_analysis.get('address', 'Property')}

Based on property analysis, I recommend targeting:

PRIMARY AUDIENCE: {primary.get('name', 'N/A')}
- Age: {primary.get('age_min', 0)}-{primary.get('age_max', 0)}
- Location: {location.get('location', 'N/A')} ({location.get('radius_km', 0)}km radius)
- Income: {primary.get('income_level', 'N/A').title()}

Top 10 Interests to Target:"""

    for i, interest in enumerate(primary.get('interests', [])[:10], 1):
        voice += f"\n  {i}. {interest}"

    voice += f"""

Behaviors to Target:"""

    for behavior in primary.get('behaviors', []):
        voice += f"\n  - {behavior}"

    voice += f"""

Why This Audience Works:
- Property type ({property_analysis.get('property_type', 'N/A')}) attracts {primary.get('name', 'N/A').lower()}s
- Price tier (${property_analysis.get('price', 0):,.0f}) matches {primary.get('income_level', 'N/A')} income levels
- Location type ({location.get('location_type', 'N/A')}) suggests {location.get('description', 'N/A').lower()}

Ready to create your ad campaign with this targeting!"""

    return voice


# ============================================================================
# Tool Registrations
# ============================================================================

register_tool(
    Tool(
        name="get_facebook_targeting",
        description="Get AI-powered Facebook ad targeting recommendations for a property. Returns comprehensive targeting including primary/secondary audiences, location strategy, budget recommendations, creative angles, and testing strategy.",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "Property ID to analyze for targeting"
                }
            },
            "required": ["property_id"]
        }
    ),
    handle_get_facebook_targeting
)

register_tool(
    Tool(
        name="list_targeting_personas",
        description="List all available Facebook targeting personas with details including age ranges, interests, behaviors, and income levels.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    handle_list_targeting_personas
)

register_tool(
    Tool(
        name="suggest_facebook_audiences",
        description="Get Facebook audience suggestions based on property characteristics. AI analyzes property type, price, location, and features to recommend optimal audience segments.",
        inputSchema={
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "number",
                    "description": "Property ID to analyze"
                }
            },
            "required": ["property_id"]
        }
    ),
    handle_suggest_facebook_audiences
)
