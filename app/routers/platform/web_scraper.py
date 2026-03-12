"""Web Scraper API Router — automated property data extraction from websites."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, HttpUrl

from app.database import get_db
from app.services.web_scraper_service import web_scraper_service
from app.models import Agent


router = APIRouter(prefix="/scrape", tags=["Web Scraper"])


# Request schemas
class ScrapeUrlRequest(BaseModel):
    url: str
    use_ai: bool = True
    source: Optional[str] = None


class ScrapeMultipleRequest(BaseModel):
    urls: List[str]
    use_ai: bool = True
    concurrent: int = 3


class ScrapeAndCreateRequest(BaseModel):
    url: str
    agent_id: int
    use_ai: bool = True
    auto_enrich: bool = False


class ScrapeZillowSearchRequest(BaseModel):
    search_url: str
    agent_id: int
    max_properties: int = 20
    auto_enrich: bool = False


class ScrapeAndEnrichBatchRequest(BaseModel):
    urls: List[str]
    agent_id: int
    concurrent: int = 3
    auto_enrich: bool = True


# API Endpoints
@router.post("/url")
async def scrape_url(request: ScrapeUrlRequest):
    """Scrape a single URL and extract property data.

    Returns structured property data without saving to database.
    Use /scrape-and-create to automatically create a property.
    """
    result = await web_scraper_service.scrape_url(
        url=request.url,
        use_ai=request.use_ai,
        source=request.source
    )

    return {
        "url": request.url,
        "data": result.to_dict(),
        "is_valid": result.is_valid(),
        "source": result.source
    }


@router.post("/multiple")
async def scrape_multiple_urls(request: ScrapeMultipleRequest):
    """Scrape multiple URLs concurrently.

    Returns array of scraped property data without saving.
    """
    results = await web_scraper_service.scrape_multiple_urls(
        urls=request.urls,
        use_ai=request.use_ai,
        concurrent=request.concurrent
    )

    return {
        "total_urls": len(request.urls),
        "successful_scrapes": len(results),
        "results": [r.to_dict() for r in results]
    }


@router.post("/scrape-and-create")
async def scrape_and_create_property(
    request: ScrapeAndCreateRequest,
    db: Session = Depends(get_db)
):
    """Scrape URL and automatically create property in database.

    Validates scraped data and checks for duplicates before creating.
    Returns created property ID or error.
    """
    result = await web_scraper_service.scrape_and_create_property(
        db=db,
        url=request.url,
        agent_id=request.agent_id,
        use_ai=request.use_ai,
        auto_enrich=request.auto_enrich
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/zillow-listing")
async def scrape_zillow_listing(request: ScrapeAndCreateRequest, db: Session = Depends(get_db)):
    """Scrape a Zillow listing page and create property.

    Convenience endpoint for Zillow URLs.
    """
    result = await web_scraper_service.scrape_and_create_property(
        db=db,
        url=request.url,
        agent_id=request.agent_id,
        use_ai=request.use_ai,
        auto_enrich=request.auto_enrich
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/redfin-listing")
async def scrape_redfin_listing(request: ScrapeAndCreateRequest, db: Session = Depends(get_db)):
    """Scrape a Redfin listing page and create property.

    Convenience endpoint for Redfin URLs.
    """
    result = await web_scraper_service.scrape_and_create_property(
        db=db,
        url=request.url,
        agent_id=request.agent_id,
        use_ai=request.use_ai,
        auto_enrich=request.auto_enrich
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/realtor-listing")
async def scrape_realtor_listing(request: ScrapeAndCreateRequest, db: Session = Depends(get_db)):
    """Scrape a Realtor.com listing page and create property.

    Convenience endpoint for Realtor.com URLs.
    """
    result = await web_scraper_service.scrape_and_create_property(
        db=db,
        url=request.url,
        agent_id=request.agent_id,
        use_ai=request.use_ai,
        auto_enrich=request.auto_enrich
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/zillow-search")
async def scrape_zillow_search_results(request: ScrapeZillowSearchRequest):
    """Scrape Zillow search results page for multiple properties.

    Returns scraped data for all properties found (max 20).
    Does NOT create properties — use /scrape-and-enrich-batch for that.
    """
    from app.services.web_scraper_service import ZillowSearchScraper

    results = await ZillowSearchScraper.scrape_search_results(
        url=request.search_url,
        max_properties=request.max_properties
    )

    return {
        "search_url": request.search_url,
        "properties_found": len(results),
        "properties": [r.to_dict() for r in results]
    }


@router.post("/scrape-and-enrich-batch")
async def scrape_and_enrich_batch(
    request: ScrapeAndEnrichBatchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Scrape multiple URLs, create properties, and optionally auto-enrich.

    This is the most powerful endpoint for bulk property imports.

    Process:
    1. Scrape all URLs concurrently
    2. Create properties from valid results
    3. If auto_enrich=True, enrich each with Zillow data
    4. Return summary of created properties

    Voice example: "Import these 10 Zillow listings and enrich them all"
    """
    results = await web_scraper_service.scrape_multiple_urls(
        urls=request.urls,
        use_ai=True,
        concurrent=request.concurrent
    )

    created_properties = []
    errors = []

    for scraped_data in results:
        if not scraped_data.is_valid():
            errors.append({
                "url": scraped_data.url,
                "error": "Invalid data - missing address, city, or price"
            })
            continue

        # Check for duplicates
        from app.models import Property
        existing = db.query(Property).filter(
            Property.address == scraped_data.address,
            Property.city == scraped_data.city
        ).first()

        if existing:
            errors.append({
                "url": scraped_data.url,
                "error": f"Property already exists: ID {existing.id}"
            })
            continue

        # Create property
        try:
            from app.services.web_scraper_service import web_scraper_service
            result = await web_scraper_service.scrape_and_create_property(
                db=db,
                url=scraped_data.url or "",
                agent_id=request.agent_id,
                use_ai=False,  # Already used AI in scrape_multiple_urls
                auto_enrich=False  # Will enrich separately below
            )

            if "error" not in result:
                created_properties.append(result)
            else:
                errors.append({
                    "url": scraped_data.url,
                    "error": result.get("error", "Unknown error")
                })

        except Exception as e:
            errors.append({
                "url": scraped_data.url,
                "error": str(e)
            })

    # Auto-enrich if requested
    enriched_count = 0
    if request.auto_enrich and created_properties:
        from app.services.zillow_enrichment import zillow_enrichment_service

        for prop_result in created_properties:
            prop_id = prop_result.get("property_id")
            if prop_id:
                try:
                    await zillow_enrichment_service.enrich_property(
                        db, prop_id, force=True
                    )
                    enriched_count += 1
                except Exception as e:
                    errors.append({
                        "property_id": prop_id,
                        "error": f"Enrichment failed: {str(e)}"
                    })

    return {
        "total_urls": len(request.urls),
        "successfully_scraped": len(results),
        "properties_created": len(created_properties),
        "properties_enriched": enriched_count,
        "errors": errors,
        "created_properties": created_properties
    }
