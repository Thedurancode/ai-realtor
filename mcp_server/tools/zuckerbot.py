"""Zuckerbot AI Facebook Ads MCP Tools

Voice commands for AI-powered Facebook ad campaign generation and management.
"""
import logging
from typing import Optional, List, Dict
from pathlib import Path

# Add parent directory to path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.services.zuckerbot_service import (
    ZuckerbotService,
    generate_campaign_from_property,
    get_market_intelligence
)

logger = logging.getLogger(__name__)


# ============================================================================
# MCP Tools
# ============================================================================

async def preview_facebook_campaign(
    url: str,
    campaign_type: str = "lead_generation"
) -> Dict:
    """Preview a Facebook ad campaign without creating it

    Args:
        url: Property or landing page URL
        campaign_type: Type of campaign (lead_generation, brand_awareness, traffic, conversions)

    Returns:
        Campaign preview with 2-3 ad variants including headlines, copy, and rationale
    """
    try:
        service = ZuckerbotService()
        result = await service.preview_campaign(url, campaign_type)

        preview_id = result.get("id", "unknown")
        business = result.get("business_name", "Unknown")
        ads = result.get("ads", [])

        return {
            "success": True,
            "preview_id": preview_id,
            "business_name": business,
            "description": result.get("description", ""),
            "ad_variants": len(ads),
            "ads": [
                {
                    "headline": ad.get("headline"),
                    "copy": ad.get("copy"),
                    "angle": ad.get("angle"),
                    "rationale": ad.get("rationale")
                }
                for ad in ads
            ]
        }
    except Exception as e:
        logger.error(f"Error previewing campaign: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def create_facebook_campaign(
    url: str,
    campaign_type: str = "lead_generation",
    budget: Optional[int] = None,
    duration_days: Optional[int] = None
) -> Dict:
    """Create a full AI-generated Facebook ad campaign

    Args:
        url: Property or landing page URL
        campaign_type: Type of campaign
        budget: Daily budget in dollars (optional)
        duration_days: Campaign duration in days (optional)

    Returns:
        Complete campaign with strategy, targeting, 3 ad variants, and 12-week roadmap
    """
    try:
        service = ZuckerbotService()
        result = await service.create_campaign(
            url=url,
            campaign_type=campaign_type,
            budget=budget,
            duration_days=duration_days
        )

        campaign_id = result.get("id", "unknown")
        business = result.get("business_name", "Unknown")
        strategy = result.get("strategy", {})
        targeting = result.get("targeting", {})
        variants = result.get("variants", [])

        return {
            "success": True,
            "campaign_id": campaign_id,
            "status": result.get("status", "draft"),
            "business_name": business,
            "objective": strategy.get("objective", "unknown"),
            "summary": strategy.get("summary", ""),
            "recommended_budget": strategy.get("recommended_daily_budget_cents"),
            "projected_leads": strategy.get("projected_monthly_leads"),
            "targeting": {
                "age_range": f"{targeting.get('age_min')}-{targeting.get('age_max')}",
                "platforms": targeting.get("publisher_platforms", []),
                "interests": targeting.get("interests", [])[:5]  # First 5
            },
            "ad_variants": len(variants),
            "ads": [
                {
                    "headline": v.get("headline"),
                    "copy": v.get("copy"),
                    "cta": v.get("cta"),
                    "angle": v.get("angle")
                }
                for v in variants
            ],
            "roadmap_included": bool(result.get("roadmap"))
        }
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def launch_facebook_campaign(
    campaign_id: str,
    meta_access_token: str,
    ad_account_id: str
) -> Dict:
    """Launch a campaign to Meta Ads Manager

    Args:
        campaign_id: Campaign ID from create_facebook_campaign
        meta_access_token: Meta API access token
        ad_account_id: Meta ad account ID (act_XXXXXXXXX)

    Returns:
        Launch status and Meta campaign IDs
    """
    try:
        service = ZuckerbotService()
        result = await service.launch_campaign(
            campaign_id=campaign_id,
            meta_access_token=meta_access_token,
            ad_account_id=ad_account_id
        )

        return {
            "success": True,
            "campaign_id": campaign_id,
            "status": result.get("status", "launched"),
            "meta_campaign_id": result.get("meta_campaign_id"),
            "message": "Campaign launched to Meta Ads Manager"
        }
    except Exception as e:
        logger.error(f"Error launching campaign: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_campaign_performance(campaign_id: str) -> Dict:
    """Get performance metrics for a campaign

    Args:
        campaign_id: Campaign ID

    Returns:
        Performance data including impressions, clicks, spend, conversions
    """
    try:
        service = ZuckerbotService()
        result = await service.get_campaign_performance(campaign_id)

        return {
            "success": True,
            "campaign_id": campaign_id,
            "metrics": result
        }
    except Exception as e:
        logger.error(f"Error getting performance: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def analyze_competitors(
    url: str,
    location: str,
    industry: str = "real_estate"
) -> Dict:
    """Analyze competitors in the market

    Args:
        url: Business URL
        location: City, State
        industry: Industry vertical

    Returns:
        Competitor analysis with strengths, weaknesses, gaps, and market saturation
    """
    try:
        service = ZuckerbotService()
        result = await service.research_competitors(url, location, industry)

        competitors = result.get("competitors", [])
        gaps = result.get("gaps", [])
        saturation = result.get("market_saturation", "unknown")

        return {
            "success": True,
            "location": location,
            "competitors_found": len(competitors),
            "market_saturation": saturation,
            "competitors": [
                {
                    "name": c.get("name"),
                    "strengths": c.get("strengths", [])[:2],
                    "weaknesses": c.get("weaknesses", [])[:2],
                    "has_ads": c.get("ad_presence", False)
                }
                for c in competitors[:5]  # Top 5
            ],
            "market_gaps": gaps[:5],  # Top 5 gaps
            "common_hooks": result.get("common_hooks", [])[:5]
        }
    except Exception as e:
        logger.error(f"Error analyzing competitors: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def analyze_market(
    business_type: str,
    location: str,
    industry: str = "real_estate"
) -> Dict:
    """Get market research and insights

    Args:
        business_type: Type of business (luxury_real_estate, commercial, etc.)
        location: City, State
        industry: Industry vertical

    Returns:
        Market analysis with size, growth trends, competition, budget recommendations
    """
    try:
        service = ZuckerbotService()
        result = await service.research_market(business_type, location, industry)

        return {
            "success": True,
            "location": location,
            "market_size": result.get("market_size_estimate", ""),
            "growth_trend": result.get("growth_trend", ""),
            "competition_level": result.get("advertising_landscape", {}).get("competition_level", "unknown"),
            "avg_cpc": result.get("advertising_landscape", {}).get("estimated_avg_cpc_cents"),
            "avg_cpl": result.get("advertising_landscape", {}).get("estimated_avg_cpl_cents"),
            "recommended_budget": result.get("budget_recommendation_daily_cents"),
            "opportunities": result.get("opportunities", [])[:3],
            "risks": result.get("risks", [])[:3],
            "positioning": result.get("recommended_positioning", "")
        }
    except Exception as e:
        logger.error(f"Error analyzing market: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def extract_reviews(
    business_name: str,
    location: str
) -> Dict:
    """Extract review insights from Google/Yelp

    Args:
        business_name: Business name
        location: City, State

    Returns:
        Review themes, sentiment analysis, best/worst quotes
    """
    try:
        service = ZuckerbotService()
        result = await service.research_reviews(business_name, location)

        return {
            "success": True,
            "business_name": business_name,
            "location": location,
            "rating": result.get("rating"),
            "review_count": result.get("review_count"),
            "sentiment_summary": result.get("sentiment_summary", ""),
            "themes": result.get("themes", []),
            "best_quotes": result.get("best_quotes", [])[:3],
            "worst_quotes": result.get("worst_quotes", [])[:3]
        }
    except Exception as e:
        logger.error(f"Error extracting reviews: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def generate_ad_creative(
    description: str,
    angle: str = "value",
    format: str = "image_ad"
) -> Dict:
    """Generate ad creative with AI

    Args:
        description: Product or property description
        angle: value, urgency, social_proof, luxury
        format: image_ad, video_ad, carousel

    Returns:
        Generated creative with headline, copy, CTA, and image prompt
    """
    try:
        service = ZuckerbotService()
        result = await service.generate_creatives(description, angle, format)

        # Handle error response
        if "error" in result:
            return {
                "success": False,
                "error": result.get("error")
            }

        return {
            "success": True,
            "headline": result.get("headline"),
            "copy": result.get("copy"),
            "cta": result.get("cta"),
            "angle": result.get("angle"),
            "image_prompt": result.get("image_prompt"),
            "rationale": result.get("rationale", "")
        }
    except Exception as e:
        logger.error(f"Error generating creative: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# Tool List for MCP Server
# ============================================================================

ZUCKERBOT_TOOLS = [
    {
        "name": "preview_facebook_campaign",
        "description": "Preview a Facebook ad campaign without creating it. Returns 2-3 ad variants with headlines, copy, and rationale.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Property or landing page URL"
                },
                "campaign_type": {
                    "type": "string",
                    "description": "Type of campaign (lead_generation, brand_awareness, traffic, conversions)",
                    "default": "lead_generation"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "create_facebook_campaign",
        "description": "Create a full AI-generated Facebook ad campaign with strategy, targeting, 3 ad variants, and 12-week roadmap.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Property or landing page URL"
                },
                "campaign_type": {
                    "type": "string",
                    "description": "Type of campaign",
                    "default": "lead_generation"
                },
                "budget": {
                    "type": "number",
                    "description": "Daily budget in dollars"
                },
                "duration_days": {
                    "type": "number",
                    "description": "Campaign duration in days"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "launch_facebook_campaign",
        "description": "Launch a campaign to Meta Ads Manager with live ads",
        "inputSchema": {
            "type": "object",
            "properties": {
                "campaign_id": {
                    "type": "string",
                    "description": "Campaign ID from create_facebook_campaign"
                },
                "meta_access_token": {
                    "type": "string",
                    "description": "Meta API access token"
                },
                "ad_account_id": {
                    "type": "string",
                    "description": "Meta ad account ID (act_XXXXXXXXX)"
                },
                "required": ["campaign_id", "meta_access_token", "ad_account_id"]
            }
        },
    },
    {
        "name": "get_campaign_performance",
        "description": "Get performance metrics for a campaign (impressions, clicks, spend, conversions)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "campaign_id": {
                    "type": "string",
                    "description": "Campaign ID"
                }
            },
            "required": ["campaign_id"]
        }
    },
    {
        "name": "analyze_competitors",
        "description": "Analyze competitors in the market with strengths, weaknesses, and gaps",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Business URL"
                },
                "location": {
                    "type": "string",
                    "description": "City, State"
                },
                "industry": {
                    "type": "string",
                    "description": "Industry vertical",
                    "default": "real_estate"
                }
            },
            "required": ["url", "location"]
        }
    },
    {
        "name": "analyze_market",
        "description": "Get market research with size, growth trends, competition, and budget recommendations",
        "inputSchema": {
            "type": "object",
            "properties": {
                "business_type": {
                    "type": "string",
                    "description": "Business type (luxury_real_estate, commercial, etc.)"
                },
                "location": {
                    "type": "string",
                    "description": "City, State"
                },
                "industry": {
                    "type": "string",
                    "description": "Industry vertical",
                    "default": "real_estate"
                }
            },
            "required": ["business_type", "location"]
        }
    },
    {
        "name": "extract_reviews",
        "description": "Extract review insights from Google/Yelp with sentiment analysis",
        "inputSchema": {
            "type": "object",
            "properties": {
                "business_name": {
                    "type": "string",
                    "description": "Business name"
                },
                "location": {
                    "type": "string",
                    "description": "City, State"
                }
            },
            "required": ["business_name", "location"]
        }
    },
    {
        "name": "generate_ad_creative",
        "description": "Generate ad creative with AI (headline, copy, CTA, image prompt)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Product or property description"
                },
                "angle": {
                    "type": "string",
                    "description": "value, urgency, social_proof, luxury",
                    "default": "value"
                },
                "format": {
                    "type": "string",
                    "description": "image_ad, video_ad, carousel",
                    "default": "image_ad"
                }
            },
            "required": ["description"]
        }
    }
]


# ============================================================================
# Voice Examples for Documentation
# ============================================================================

VOICE_EXAMPLES = [
    "Preview a Facebook ad for this property",
    "Create a Facebook ad campaign for property 5",
    "Generate a lead generation campaign for this listing",
    "Launch my Facebook campaign to Meta",
    "How is my Facebook campaign performing?",
    "Analyze competitors in Miami real estate",
    "What's the market like for luxury condos in NYC?",
    "Extract reviews for Emprezario in New York",
    "Generate an ad creative for this luxury condo",
    "Create an urgency-focused ad for this property"
]
