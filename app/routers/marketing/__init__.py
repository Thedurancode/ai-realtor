"""Marketing domain routers — campaigns, social, ads, mail, etc."""

from app.routers.marketing.campaigns import router as campaigns_router
from app.routers.marketing.postiz import router as postiz_router
from app.routers.marketing.zuckerbot import router as zuckerbot_router
from app.routers.marketing.facebook_ads import router as facebook_ads_router
from app.routers.marketing.facebook_targeting import router as facebook_targeting_router
from app.routers.marketing.contact_lists import router as contact_lists_router
from app.routers.marketing.direct_mail import router as direct_mail_router
from app.routers.marketing.listing_presentation import router as listing_presentation_router
from app.routers.marketing.cma_report import router as cma_report_router

__all__ = [
    "campaigns_router", "postiz_router", "zuckerbot_router",
    "facebook_ads_router", "facebook_targeting_router",
    "contact_lists_router", "direct_mail_router",
    "listing_presentation_router", "cma_report_router",
]
