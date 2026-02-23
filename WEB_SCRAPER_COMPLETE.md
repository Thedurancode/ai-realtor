# 🌐 Web Scraper Feature — Complete Implementation

## Overview

Automated property data extraction from any website. Point the AI at a URL and automatically extract structured property data or create properties directly from the listing.

---

## Files Created (3 Files)

### Service Layer
- ✅ `app/services/web_scraper_service.py` (~650 lines)
  - `WebScraperService` — Main service with async HTTP client
  - `ZillowScraper` — Specialized Zillow parser
  - `RedfinScraper` — Redfin with JSON-LD extraction
  - `RealtorComScraper` — Realtor.com parser
  - `ZillowSearchScraper` — Multiple properties from search results
  - `GenericScraper` — AI-powered fallback using Claude Sonnet 4

### API Router
- ✅ `app/routers/web_scraper.py` (~250 lines)
  - 8 API endpoints for scraping operations
  - Single URL scraping and preview
  - Multiple concurrent scraping
  - Scrape-and-create with property creation
  - Platform-specific endpoints (Zillow, Redfin, Realtor)
  - Batch import with auto-enrichment

### MCP Tools
- ✅ `mcp_server/tools/web_scraper.py` (~400 lines)
  - 6 MCP tools for voice-controlled scraping
  - `scrape_url` — Preview scraping without creating
  - `scrape_and_create` — Create property from URL
  - `scrape_zillow_search` — Extract multiple properties
  - `scrape_and_create_batch` — Bulk import with enrichment
  - `scrape_redfin` — Convenience for Redfin URLs
  - `scrape_realtor` — Convenience for Realtor.com URLs

---

## Integration Points

### Updated Files (4 files)
- ✅ `app/routers/__init__.py` — Added web_scraper export
- ✅ `app/main.py` — Registered web_scraper router
- ✅ `mcp_server/tools/__init__.py` — Imported web_scraper tools
- ✅ `CLAUDE.md` — Added feature documentation + voice examples

---

## API Endpoints (8 endpoints)

### Single URL Operations
```
POST /scrape/url
```
Scrape a URL and return extracted data (preview only).

**Request:**
```json
{
  "url": "https://www.zillow.com/homedetails/123-st-street/12345678_zpid/",
  "use_ai": true
}
```

**Response:**
```json
{
  "url": "...",
  "data": {
    "address": "123 St Street",
    "city": "Miami",
    "state": "FL",
    "zip_code": "33101",
    "price": 450000,
    "bedrooms": 3,
    "bathrooms": 2.0,
    "square_feet": 1850,
    "year_built": 2015,
    "property_type": "house",
    "description": "...",
    "photos": []
  },
  "is_valid": true,
  "source": "zillow"
}
```

### Scrape and Create
```
POST /scrape/scrape-and-create
```
Scrape URL and create property in database.

**Request:**
```json
{
  "url": "https://www.zillow.com/...",
  "agent_id": 1,
  "use_ai": true,
  "auto_enrich": false
}
```

**Response:**
```json
{
  "property_id": 42,
  "address": "123 St Street",
  "city": "Miami",
  "price": 450000,
  "message": "Property created successfully",
  "auto_enriched": false
}
```

### Platform-Specific Endpoints
```
POST /scrape/zillow-listing
POST /scrape/redfin-listing
POST /scrape/realtor-listing
```
Convenience endpoints for specific platforms.

### Multiple URLs
```
POST /scrape/multiple
```
Scrape multiple URLs concurrently without creating.

**Request:**
```json
{
  "urls": ["https://zillow.com/...", "https://redfin.com/..."],
  "use_ai": true,
  "concurrent": 3
}
```

### Zillow Search Results
```
POST /scrape/zillow-search
```
Extract multiple properties from Zillow search results page.

**Request:**
```json
{
  "search_url": "https://www.zillow.com/miami-fl/",
  "max_properties": 20
}
```

### Batch Import
```
POST /scrape/scrape-and-enrich-batch
```
The most powerful endpoint — scrape, create, and enrich in one operation.

**Request:**
```json
{
  "urls": ["https://zillow.com/1", "https://zillow.com/2"],
  "agent_id": 1,
  "concurrent": 3,
  "auto_enrich": true
}
```

**Response:**
```json
{
  "total_urls": 2,
  "successfully_scraped": 2,
  "properties_created": 2,
  "properties_enriched": 2,
  "errors": [],
  "created_properties": [...]
}
```

---

## MCP Tools (6 tools)

### 1. `scrape_url`
**Voice:**
- "Scrape this Zillow listing URL"
- "What data can we get from this URL?"
- "Preview data from this Redfin page"

**Purpose:** Preview extracted data without creating a property.

### 2. `scrape_and_create`
**Voice:**
- "Add this property from the URL"
- "Create property from this Redfin link"
- "Import this Zillow listing to my portfolio"

**Purpose:** Scrape URL and create property in database.

### 3. `scrape_zillow_search`
**Voice:**
- "Show me properties from this Zillow search"
- "What listings are on this Zillow search page?"

**Purpose:** Extract multiple properties from Zillow search results.

### 4. `scrape_and_create_batch`
**Voice:**
- "Import these 10 Zillow listings and enrich them all"
- "Bulk import these URLs into my portfolio"
- "Add all these properties and enrich with Zillow data"

**Purpose:** Bulk import with auto-enrichment.

### 5. `scrape_redfin`
**Voice:**
- "Add this Redfin property to my portfolio"
- "Create property from this Redfin URL"

**Purpose:** Convenience tool for Redfin URLs.

### 6. `scrape_realtor`
**Voice:**
- "Import this Realtor.com listing"
- "Add this Realtor property"

**Purpose:** Convenience tool for Realtor.com URLs.

---

## Data Extraction

### ScrapedPropertyData Structure
```python
@dataclass
class ScrapedPropertyData:
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    price: Optional[float]
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    square_feet: Optional[int]
    lot_size: Optional[float]
    year_built: Optional[int]
    property_type: Optional[str]
    description: Optional[str]
    url: Optional[str]
    source: Optional[str]
    raw_data: dict
    photos: List[str]

    def is_valid(self) -> bool:
        return bool(self.address and self.city and self.price)
```

### Extraction Methods

**Zillow:**
- CSS selector-based extraction
- Price, beds, baths, sqft from structured HTML classes
- Address from H1
- City/state from meta tags (og:locality, og:region)

**Redfin:**
- JSON-LD structured data extraction
- SingleFamilyResidence schema parsing
- Address object parsing
- Floor size extraction

**Realtor.com:**
- Price span extraction
- Address from H1.page-title
- Specs from list items

**Generic (AI-powered):**
- Extract page text (first 5000 chars)
- Send to Claude Sonnet 4 with extraction prompt
- JSON response parsing with regex fallback
- Fills missing fields from specialized scrapers

---

## Features

### 1. Automatic Source Detection
```python
def _detect_source(url: str, soup: BeautifulSoup) -> str:
    domain = urlparse(url).netloc.lower()

    if "zillow" in domain:
        return "zillow"
    elif "redfin" in domain:
        return "redfin"
    elif "realtor.com" in domain:
        return "realtor"
    else:
        # Check meta tags
        site_name = soup.find("meta", {"property": "og:site_name"})
        if site_name:
            # Parse site name and return appropriate source
        return "generic"
```

### 2. Concurrent Scraping with Rate Limiting
```python
semaphore = asyncio.Semaphore(concurrent)  # Limit concurrent requests

async def scrape_with_semaphore(url: str):
    async with semaphore:
        await asyncio.sleep(1)  # Be polite
        return await self.scrape_url(url, use_ai=use_ai)

tasks = [scrape_with_semaphore(url) for url in urls]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

### 3. Duplicate Detection
```python
existing = db.query(Property).filter(
    Property.address == scraped_data.address,
    Property.city == scraped_data.city
).first()

if existing:
    return {
        "error": f"Property already exists: ID {existing.id}"
    }
```

### 4. Auto-Enrichment
```python
if auto_enrich:
    await zillow_enrichment_service.enrich_property(
        db, prop.id, force=True
    )
```

### 5. Property Type Mapping
```python
mapping = {
    "house": PropertyType.HOUSE,
    "single family": PropertyType.HOUSE,
    "condo": PropertyType.CONDO,
    "townhouse": PropertyType.TOWNHOUSE,
    "apartment": PropertyType.APARTMENT,
    "land": PropertyType.LAND,
    "commercial": PropertyType.COMMERCIAL,
}
```

---

## Voice Examples

```
# Preview Scraping
"Scrape this Zillow listing URL"
"What data can we extract from this Redfin page?"
"Show me what data we'd get from this URL"

# Property Creation
"Add this property from the URL"
"Create property from this Realtor.com link"
"Import this Zillow listing to my portfolio"
"Add this Redfin property and enrich it"

# Batch Operations
"Import these 10 Zillow listings"
"Scrape and create properties from these URLs"
"Bulk import these listings and enrich them all"
"Add all properties from this Zillow search page"

# Platform-Specific
"Scrape this Redfin listing"
"Add this Realtor.com property"
"Import from this Zillow URL"
```

---

## Usage Examples

### Python API Usage
```python
from app.services.web_scraper_service import web_scraper_service
from app.database import SessionLocal

# Preview scrape
data = await web_scraper_service.scrape_url(
    url="https://www.zillow.com/homedetails/...",
    use_ai=True
)
print(f"Address: {data.address}, Price: ${data.price}")

# Create property
db = SessionLocal()
result = await web_scraper_service.scrape_and_create_property(
    db=db,
    url="https://www.zillow.com/homedetails/...",
    agent_id=1,
    use_ai=True,
    auto_enrich=True
)
print(f"Created property {result['property_id']}")
db.close()

# Batch import
results = await web_scraper_service.scrape_multiple_urls(
    urls=[
        "https://www.zillow.com/1",
        "https://www.zillow.com/2",
        "https://www.redfin.com/3"
    ],
    use_ai=True,
    concurrent=3
)
print(f"Scraped {len(results)} properties")
```

### HTTP API Usage
```bash
# Preview scrape
curl -X POST "http://localhost:8000/scrape/url" \
  -H "x-api-key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.zillow.com/...", "use_ai": true}'

# Create property
curl -X POST "http://localhost:8000/scrape/scrape-and-create" \
  -H "x-api-key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.zillow.com/...",
    "agent_id": 1,
    "auto_enrich": true
  }'

# Batch import
curl -X POST "http://localhost:8000/scrape/scrape-and-enrich-batch" \
  -H "x-api-key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://zillow.com/1", "https://zillow.com/2"],
    "agent_id": 1,
    "auto_enrich": true
  }'
```

---

## Testing

### Test Single URL Scraping
```bash
curl -X POST "http://localhost:8000/scrape/url" \
  -H "x-api-key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.zillow.com/homedetails/123-Main-St-Miami-FL-33101/12345678_zpid/",
    "use_ai": true
  }'
```

### Test Property Creation
```bash
curl -X POST "http://localhost:8000/scrape/scrape-and-create" \
  -H "x-api-key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.zillow.com/homedetails/123-Main-St/12345678_zpid/",
    "agent_id": 1,
    "use_ai": true,
    "auto_enrich": false
  }'
```

### Test Zillow Search Scraping
```bash
curl -X POST "http://localhost:8000/scrape/zillow-search" \
  -H "x-api-key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "search_url": "https://www.zillow.com/miami-fl/",
    "max_properties": 10
  }'
```

---

## Error Handling

### HTTP Errors
```python
except httpx.HTTPError as e:
    logger.error(f"HTTP error scraping {url}: {e}")
    return ScrapedPropertyData(url=url, raw_data={"error": str(e)})
```

### Validation Errors
```python
if not scraped_data.is_valid():
    return {
        "error": f"Invalid scraped data: missing address ({scraped_data.address}), city ({scraped_data.city}), or price ({scraped_data.price})"
    }
```

### Duplicate Detection
```python
if existing:
    return {
        "error": f"Property already exists: {existing.address}, {existing.city}",
        "existing_property_id": existing.id
    }
```

---

## Performance Considerations

### Rate Limiting
- Default: 3 concurrent requests
- 1 second delay between requests
- Configurable via `concurrent` parameter
- Respects server resources

### AI Extraction
- Uses Claude Sonnet 4 (fast, cost-effective)
- Max 1000 tokens for extraction
- Regex fallback if JSON parsing fails
- Can be disabled with `use_ai=False`

### Batch Operations
- Capped at 50 URLs per batch
- Individual commits per property
- Error isolation (one failure doesn't crash batch)
- Progress tracking via response summary

---

## Deployment

### 1. No Database Migration Required
Uses existing `properties` table — no new tables needed.

### 2. Dependencies Already Installed
- httpx (HTTP client)
- beautifulsoup4 (HTML parsing)
- No new dependencies required

### 3. Deploy to Fly.io
```bash
git add .
git commit -m "feat: Add web scraper with 6 MCP tools and 8 API endpoints"
git push
fly deploy
```

### 4. Verify Deployment
```bash
curl https://ai-realtor.fly.dev/docs
# Look for /scrape/* endpoints
```

---

## MCP Tool Count

**Previous Total:** 129 tools
**New Tools:** 6 tools
**New Total:** **135 tools** (+4.7%)

---

## Summary

✅ **Service:** `web_scraper_service.py` (650 lines)
✅ **Router:** `web_scraper.py` (250 lines, 8 endpoints)
✅ **MCP Tools:** `web_scraper.py` (400 lines, 6 tools)
✅ **Integration:** All routers registered, tools imported
✅ **Documentation:** CLAUDE.md updated with feature docs + voice examples

**Total Implementation:**
- 3 new files
- ~1,300 lines of production code
- 8 new API endpoints
- 6 new MCP tools (135 total)
- 3 specialized scrapers + 1 AI-powered generic scraper
- Full voice control with natural language commands

---

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
