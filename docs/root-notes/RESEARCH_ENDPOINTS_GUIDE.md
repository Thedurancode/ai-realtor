# 🔬 Research Endpoints - Complete Technical Guide

## Overview

Your AI Realtor platform has **TWO separate research systems**:

1. **Agentic Research** - Deep AI-powered property research with worker agents (NEW)
2. **Legacy Research** - Orchestrated multi-endpoint research (ORIGINAL)

Both systems serve different use cases and can be used independently or together.

---

## 📊 System Comparison

| Feature | Agentic Research | Legacy Research |
|---------|------------------|-----------------|
| **Purpose** | Deep property analysis with autonomous agents | Orchestrated API calls to multiple services |
| **Speed** | 1-3 minutes (extensive) | 30-60 seconds |
| **Data Sources** | 20+ external APIs | Internal services (Zillow, Compliance, Contracts) |
| **Output** | Investment dossier with ARV, underwriting, comps | Structured research results |
| **Database** | `research_properties`, `agentic_jobs` | `research` table |
| **MCP Tools** | 4 tools | 0 tools (API only) |
| **Best For** | Investment decisions, deal analysis | Compliance checks, contract analysis |

---

# 🤖 System 1: Agentic Research (NEW)

## What It Does

Agentic Research uses **autonomous worker agents** to deep research a property from 20+ external data sources:

### Data Sources Accessed:

**Property Data:**
- County assessor/parcel data
- Property tax records
- Building permits
- Zillow (photos, Zestimate, price history)
- Redfin estimates

**Comps:**
- Comparable sales (recently sold)
- Comparable rentals
- Price per square foot analysis

**Underwriting:**
- ARV (After Repair Value) calculation
- Rehab cost estimates (light/medium/heavy tier)
- Rental estimates
- Maximum allowable offer (MAO)
- Cash flow projections

**Risk Analysis:**
- Flood zone data (FEMA)
- EPA environmental hazards
- Wildfire risk
- Seismic risk
- Wetlands
- Historic places
- Compliance flags

**Neighborhood:**
- Walk Score, Transit Score, Bike Score
- Noise scores
- School district ratings
- HUD indices
- Crime statistics
- Demographics

**Financial:**
- Current mortgage rates
- RentCast rent estimates
- Market trends

---

## API Endpoints

### 1. Create Async Job (Background)
```python
POST /agentic/jobs
```

**Request:**
```json
{
  "address": "123 Main St",
  "city": "New York",
  "state": "NY",
  "zip": "10001",
  "strategy": "wholesale",
  "assumptions": {
    "rehab_tier": "medium"
  }
}
```

**Response:**
```json
{
  "job_id": 42,
  "property_id": 15,
  "trace_id": "uuid-here",
  "status": "pending"
}
```

**Research Strategies:**
- `flip` - Buy, renovate, sell (fix-and-flip)
- `rental` - Buy for long-term rental income
- `wholesale` - Buy below market, assign contract

**Rehab Tiers:**
- `light` - $15/sqft (cosmetic updates)
- `medium` - $35/sqft (standard renovation)
- `heavy` - $60/sqft (full gut renovation)

**How It Works:**
1. Creates `AgenticJob` record with status `pending`
2. Starts background task to run research
3. Returns immediately with `job_id`
4. Poll `/agentic/jobs/{job_id}` for progress

---

### 2. Get Job Status
```python
GET /agentic/jobs/{job_id}
```

**Response:**
```json
{
  "id": 42,
  "property_id": 15,
  "trace_id": "uuid-here",
  "status": "in_progress",
  "progress": 65,
  "current_step": "Fetching comparable sales...",
  "error_message": null,
  "created_at": "2026-02-24T10:00:00Z",
  "started_at": "2026-02-24T10:00:05Z",
  "completed_at": null
}
```

**Status Values:**
- `pending` - Job queued, not started
- `in_progress` - Research running (progress 0-99)
- `completed` - Research complete
- `failed` - Error occurred (check `error_message`)

---

### 3. Get Property with Research Output
```python
GET /agentic/properties/{property_id}
```

**Response:**
```json
{
  "property_id": 15,
  "latest_job_id": 42,
  "output": {
    "property_profile": {
      "normalized_address": "123 Main St, New York, NY 10001",
      "parcel_facts": {
        "beds": 3,
        "baths": 2,
        "sqft": 1800,
        "year": 1985,
        "lot_size": 5000
      },
      "owner_names": ["John Smith", "Jane Smith"]
    },
    "underwrite": {
      "arv_estimate": {
        "base": 450000,
        "low": 425000,
        "high": 475000
      },
      "rent_estimate": {
        "base": 2750,
        "low": 2500,
        "high": 3000
      },
      "rehab_estimated_range": {
        "low": 27000,
        "high": 63000
      },
      "offer_price_recommendation": {
        "base": 315000
      }
    },
    "comps_sales": [
      {
        "address": "125 Main St",
        "sale_price": 440000,
        "sqft": 1850,
        "beds": 3,
        "baths": 2,
        "distance_mi": 0.1,
        "sale_date": "2025-01-15"
      }
    ],
    "comps_rentals": [
      {
        "address": "130 Oak Ave",
        "rent": 2800,
        "sqft": 1800,
        "beds": 3,
        "baths": 2,
        "distance_mi": 0.2
      }
    ],
    "risk_score": {
      "data_confidence": 0.85,
      "compliance_flags": ["flood_zone_required"]
    },
    "flood_zone": {
      "flood_zone": "AE",
      "in_floodplain": true,
      "insurance_required": true
    },
    "neighborhood_intel": {
      "ai_summary": "Safe family neighborhood with good schools..."
    },
    "dossier": {
      "markdown": "# Investment Dossier\n\n..."
    },
    "worker_runs": [...]
  }
}
```

---

### 4. Get Enrichment Status
```python
GET /agentic/properties/{property_id}/enrichment-status?max_age_hours=24
```

**Response:**
```json
{
  "property_id": 15,
  "enrichment_status": {
    "has_research": true,
    "latest_job_id": 42,
    "completed_at": "2026-02-24T10:02:30Z",
    "is_fresh": true,
    "age_hours": 2.5
  }
}
```

**Query Params:**
- `max_age_hours` - Optional freshness threshold (returns `is_fresh=false` if older)

---

### 5. Get Investment Dossier (Markdown)
```python
GET /agentic/properties/{property_id}/dossier
```

**Response:**
```json
{
  "property_id": 15,
  "latest_job_id": 42,
  "markdown": "# Investment Dossier: 123 Main St\n\n## Property Overview\n\n**Address:** 123 Main St, New York, NY 10001\n**Beds/Baths/Sqft:** 3/2/1,800\n**Year Built:** 1985\n\n## Investment Analysis\n\n### After Repair Value (ARV)\n- **Base Estimate:** $450,000\n- **Range:** $425,000 - $475,000\n\n### Rental Estimate\n- **Base:** $2,750/month\n- **Range:** $2,500 - $3,000/month\n\n### Rehab Costs (Medium Tier)\n- **Estimate:** $27,000 - $63,000\n- **Per Sqft:** $35\n\n### Maximum Allowable Offer (MAO)\n- **Recommended:** $315,000\n\n..."
}
```

---

### 6. Run Synchronous Research (Wait for Result)
```python
POST /agentic/research
```

**Same request as `/agentic/jobs`, but WAITS for completion (1-3 minutes)**

**Response:** Full property output (same as `/agentic/properties/{property_id}`)

**Use when:** You need immediate results and don't mind waiting

---

## MCP Tools (Voice Commands)

### 1. Research Property (Synchronous)
```bash
research_property
```

**Voice Examples:**
- "Do extensive research on 123 Main St in New York"
- "Research 456 Oak Ave Dallas Texas for a flip strategy"
- "Analyze 789 Pine Road with heavy rehab estimate"

**Parameters:**
```python
{
  "address": "123 Main St",  # Required
  "city": "New York",        # Optional
  "state": "NY",             # Optional
  "zip": "10001",            # Optional
  "strategy": "wholesale",   # flip|rental|wholesale (default: wholesale)
  "rehab_tier": "medium",    # light|medium|heavy (default: medium)
  "extensive": true          # Boolean - deep research with 20+ data sources
}
```

**What It Returns:**
```
Research complete for 123 Main St, New York, NY 10001 (3-bed, 2-bath, 1,800 sqft, built 1985).
Owner: John Smith, Jane Smith.

Underwriting: ARV $450,000, rent $2,750/mo, rehab $27,000-$63,000, recommended offer $315,000.
Comparables: 15 sale comps (avg $435,000), 8 rental comps (avg $2,700/mo).

Data confidence: 85%. Flags: flood_zone_required.
Flood zone: AE. WARNING: in floodplain. Insurance required.

Neighborhood: Safe family neighborhood with good schools and low crime rate.

Extended research: EPA: minimal risk; wildfire: low; walkability 75/100; Redfin estimate $445,000; RentCast $2,650/mo.

Research used 18 workers in 112.3s.
```

---

### 2. Research Property (Async - Background)
```bash
research_property_async
```

**Voice Examples:**
- "Start researching 456 Oak St in the background"
- "Run deep research on 789 Pine Road asynchronously"

**Parameters:** Same as `research_property`, but without `extensive` option

**What It Returns:**
```
Research job #42 started for 456 Oak St. Running in the background — use get_research_status with job ID 42 to check progress.
```

---

### 3. Get Research Status
```bash
get_research_status
```

**Voice Examples:**
- "What's the status of research job 42?"
- "Check the progress of job 5"

**Parameters:**
```python
{
  "job_id": 42  # Required
}
```

**What It Returns:**
```
Research job #42: in_progress (65% complete). Current step: Fetching comparable sales...
```

---

### 4. Get Research Dossier
```bash
get_research_dossier
```

**Voice Examples:**
- "Get the research dossier for property 15"
- "Show me the investment report for property 8"

**Parameters:**
```python
{
  "property_id": 15  # Required - Agentic research property ID
}
```

**What It Returns:**
```
Investment dossier for property 15:

# Investment Dossier: 123 Main St

## Property Overview

**Address:** 123 Main St, New York, NY 10001
**Beds/Baths/Sqft:** 3/2/1,800
**Year Built:** 1985
**Owner:** John Smith, Jane Smith

...
```

---

## How Agentic Research Works Internally

### Step 1: Job Creation
```python
# POST /agentic/jobs
job = await agentic_research_service.create_job(db, payload)

# Creates AgenticJob record:
{
  "id": 42,
  "research_property_id": 15,
  "status": "pending",
  "progress": 0,
  "current_step": null,
  "trace_id": "uuid-for-tracing",
  "created_at": "2026-02-24T10:00:00Z"
}
```

### Step 2: Background Task
```python
# Background task starts immediately
background_tasks.add_task(agentic_research_service.run_job, job.id)

# Updates job status:
# - status: "in_progress"
# - started_at: now()
# - current_step: "Initializing research workers..."
```

### Step 3: Worker Execution

The service spawns **multiple autonomous worker agents** that run in parallel:

| Worker | Data Source | Output |
|--------|-------------|--------|
| **Parcel Worker** | County assessor | Property facts (beds, baths, sqft, year) |
| **Tax Worker** | Tax records | Tax assessment, owner names |
| **Zillow Worker** | Zillow API | Photos, Zestimate, price history |
| **Comps Sales Worker** | MLS/Redfin | Comparable sold properties |
| **Comps Rentals Worker** | Rental listings | Comparable rentals |
| **Underwriting Worker** | Internal calculation | ARV, MAO, cash flow |
| **Flood Worker** | FEMA | Flood zone, insurance reqs |
| **EPA Worker** | EPA database | Environmental hazards |
| **Wildfire Worker** | Wildfire database | Fire risk |
| **Schools Worker** | School district | Ratings, district info |
| **Walk Score Worker** | Walk Score API | Walk/Transit/Bike scores |
| **Redfin Worker** | Redfin API | Redfin estimate |
| **RentCast Worker** | RentCast API | Rent estimate |
| **Mortgage Worker** | Mortgage rates | Current rates |
| **Neighborhood Worker** | Census/crime APIs | Demographics, safety |

**Parallel Execution:**
- Workers run concurrently (up to 4 at a time)
- Each worker updates job progress
- Failed workers don't stop other workers
- Results aggregated into final output

### Step 4: Result Aggregation
```python
# All worker outputs combined:
output = {
  "property_profile": {...},      # Parcel + Tax workers
  "underwrite": {...},             # Underwriting worker
  "comps_sales": [...],            # Comps Sales worker
  "comps_rentals": [...],          # Comps Rentals worker
  "risk_score": {...},             # Aggregated from all workers
  "flood_zone": {...},             # Flood worker
  "neighborhood_intel": {...},     # Neighborhood worker
  "dossier": {...},                # Generated from all outputs
  "worker_runs": [...]             # Execution log
}
```

### Step 5: Completion
```python
# Job marked complete:
{
  "status": "completed",
  "progress": 100,
  "current_step": "Research complete",
  "completed_at": "2026-02-24T10:02:17Z"
}
```

---

## Database Schema

### research_properties Table
```python
{
  "id": 15,
  "normalized_address": "123 Main St, New York, NY 10001",
  "raw_address": "123 Main St",
  "city": "New York",
  "state": "NY",
  "zip": "10001",
  "created_at": "2026-02-24T10:00:00Z"
}
```

### agentic_jobs Table
```python
{
  "id": 42,
  "research_property_id": 15,
  "status": "completed",
  "progress": 100,
  "current_step": "Research complete",
  "trace_id": "uuid-for-tracing",
  "error_message": null,
  "created_at": "2026-02-24T10:00:00Z",
  "started_at": "2026-02-24T10:00:05Z",
  "completed_at": "2026-02-24T10:02:17Z"
}
```

### Output Storage
Output is stored as JSONB in `agentic_jobs.output` column (not shown in schema)

---

## Extensive Research Mode

When `extensive=true` (or using voice "Do extensive research..."), additional workers are spawned:

| Additional Worker | Data Source | Output |
|-------------------|-------------|--------|
| **EPA Environmental** | EPA EJScreen | Air quality, toxins, hazardous waste |
| **Seismic Worker** | USGS | Earthquake risk |
| **Wetlands Worker** | USFWS | Wetlands proximity |
| **Historic Worker** | National Register | Historic property status |
| **HUD Worker** | HUD datasets | Housing indices |
| **School Districts** | Department of Education | School boundaries, ratings |
| **Redfin Estimate** | Redfin API | Redfin valuation |
| **Walk/Transit/Bike** | Walk Score API | Three scores |
| **Noise Scores** | Noise monitoring | Traffic/airport noise |
| **Recently Sold** | MLS | Recently sold nearby homes |
| **Mortgage Rates** | Freddie Mac | Current 30-yr, 15-yr rates |
| **RentCast** | RentCast API | Rent estimate |

**Trade-off:**
- **Standard research:** ~60-90 seconds, 10-12 workers
- **Extensive research:** ~2-3 minutes, 18-20 workers

---

# 📚 System 2: Legacy Research (ORIGINAL)

## What It Does

Legacy Research **orchestrates multiple internal API calls** to perform comprehensive property analysis:

**Research Types:**
1. `property_analysis` - Complete property deep dive
2. `market_analysis` - Market trends and comparables
3. `compliance_check` - Legal and contract compliance
4. `contract_analysis` - Contract requirements and gaps
5. `owner_research` - Skip trace and owner info (not implemented)
6. `neighborhood_analysis` - Area research (not implemented)
7. `custom` - Custom endpoint orchestration
8. `ai_research` - Custom AI analysis with Claude
9. `api_research` - Custom external API calls

---

## API Endpoints

### 1. Create Research Job
```python
POST /research/
```

**Request (Property Analysis):**
```json
{
  "research_type": "property_analysis",
  "property_id": 1,
  "agent_id": 5,
  "parameters": {},
  "endpoints_to_call": null
}
```

**Request (AI Research):**
```json
{
  "research_type": "ai_research",
  "property_id": 1,
  "parameters": {
    "prompt": "What are the top 5 risks for this property?",
    "model": "claude-3-5-sonnet-20241022",
    "temperature": 0.7,
    "property_context": true
  }
}
```

**Request (API Research):**
```json
{
  "research_type": "api_research",
  "property_id": 1,
  "parameters": {
    "endpoints": [
      {
        "name": "Get weather data",
        "url": "https://api.weather.com/data",
        "method": "GET",
        "headers": {"Authorization": "Bearer token"},
        "params": {"location": "Dallas, TX"}
      }
    ]
  }
}
```

**Response:**
```json
{
  "id": 10,
  "research_type": "property_analysis",
  "property_id": 1,
  "agent_id": 5,
  "status": "pending",
  "progress": 0,
  "current_step": null,
  "created_at": "2026-02-24T10:00:00Z"
}
```

---

### 2. Get Research Status/Results
```python
GET /research/{research_id}
```

**Response:**
```json
{
  "id": 10,
  "research_type": "property_analysis",
  "property_id": 1,
  "status": "completed",
  "progress": 100,
  "current_step": "Complete",
  "results": {
    "research_type": "property_analysis",
    "property_id": 1,
    "timestamp": "2026-02-24T10:01:30Z",
    "steps": {
      "property_details": {...},
      "zillow_enrichment": {...},
      "skip_trace": {...},
      "compliance": {...},
      "contract_analysis": {...}
    },
    "recommendations": [...]
  },
  "created_at": "2026-02-24T10:00:00Z",
  "started_at": "2026-02-24T10:00:05Z",
  "completed_at": "2026-02-24T10:01:30Z"
}
```

---

### 3. List Research Jobs
```python
GET /research/?property_id=1&status=completed&limit=20
```

**Query Params:**
- `property_id` - Filter by property
- `agent_id` - Filter by agent
- `status` - Filter by status (pending/in_progress/completed/failed)
- `limit` - Max results (default 20)

---

### 4. Convenience Endpoints

#### Property Deep Dive
```python
POST /research/property/{property_id}/deep-dive
```
Shortcut for `research_type=property_analysis`

#### Market Analysis
```python
POST /research/property/{property_id}/market-analysis
```
Shortcut for `research_type=market_analysis`

#### Compliance Check
```python
POST /research/property/{property_id}/compliance
```
Shortcut for `research_type=compliance_check`

#### Get Latest Research
```python
GET /research/property/{property_id}/latest
```
Get most recent completed research for a property

---

## How Legacy Research Works Internally

### Property Analysis Flow (6 Steps)

```python
# Step 1: Get property details (10%)
research.progress = 10
results["steps"]["property_details"] = {
  "address": "123 Main St",
  "city": "New York",
  "price": 850000,
  "bedrooms": 3,
  "bathrooms": 2,
  "square_feet": 1800
}

# Step 2: Zillow enrichment (30%)
research.progress = 30
zillow_data = await zillow_enrichment_service.enrich_property(db, property.id)
results["steps"]["zillow_enrichment"] = zillow_data

# Step 3: Skip trace (50%)
research.progress = 50
results["steps"]["skip_trace"] = {"status": "not_implemented"}

# Step 4: Compliance check (70%)
research.progress = 70
compliance = await compliance_engine.run_compliance_check(db, property)
results["steps"]["compliance"] = compliance

# Step 5: Contract analysis (85%)
research.progress = 85
contract_suggestions = await contract_ai_service.suggest_required_contracts(db, property)
readiness = contract_auto_attach_service.get_required_contracts_status(db, property)
results["steps"]["contract_analysis"] = {
  "ai_suggestions": contract_suggestions,
  "readiness": readiness
}

# Step 6: AI recommendations (95%)
research.progress = 95
recommendations = generate_property_recommendations(results)
results["recommendations"] = recommendations

# Step 7: Complete (100%)
research.status = "completed"
research.progress = 100
```

---

## AI Research Feature

**Custom AI analysis using Claude with any prompt:**

```python
POST /research/ai-research
{
  "property_id": 1,
  "prompt": "What are the top 5 risks I should be aware of for this property?",
  "model": "claude-3-5-sonnet-20241022",
  "temperature": 0.7,
  "property_context": true
}
```

**How It Works:**
1. Gets property details from database
2. Builds context from property data (if `property_context=true`)
3. Calls Anthropic Claude API with prompt
4. Returns AI response with token usage

**Response:**
```json
{
  "id": 11,
  "research_type": "ai_research",
  "status": "completed",
  "results": {
    "research_type": "ai_research",
    "steps": {
      "ai_response": {
        "model": "claude-3-5-sonnet-20241022",
        "prompt": "What are the top 5 risks...",
        "response": "Based on the property analysis...\n\n1. Flood zone risk...\n2. Environmental...",
        "usage": {
          "input_tokens": 850,
          "output_tokens": 1200
        }
      }
    }
  }
}
```

---

## API Research Feature

**Orchestrate calls to external APIs:**

```python
POST /research/api-research
{
  "property_id": 1,
  "parameters": {
    "endpoints": [
      {
        "name": "Get weather data",
        "url": "https://api.weather.com/data",
        "method": "GET",
        "headers": {"Authorization": "Bearer token"},
        "params": {"location": "Dallas, TX"}
      },
      {
        "name": "Get crime stats",
        "url": "https://api.crime.com/stats",
        "method": "POST",
        "json": {"address": "123 Main St", "radius": 1}
      }
    ]
  }
}
```

**How It Works:**
1. Loops through each endpoint config
2. Makes HTTP request with provided parameters
3. Stores response (JSON or text)
4. Continues even if one endpoint fails
5. Returns all results

**Response:**
```json
{
  "id": 12,
  "research_type": "api_research",
  "status": "completed",
  "results": {
    "research_type": "api_research",
    "steps": {
      "Get weather data": {
        "url": "https://api.weather.com/data",
        "method": "GET",
        "status_code": 200,
        "response": {...}
      },
      "Get crime stats": {
        "url": "https://api.crime.com/stats",
        "method": "POST",
        "status_code": 200,
        "response": {...}
      }
    }
  }
}
```

---

# 🎯 Which Research System Should I Use?

## Use Agentic Research When:
✅ Analyzing potential investment deals
✅ Need ARV and underwriting analysis
✅ Want comparable sales and rentals
✅ Checking flood/environmental risks
✅ Evaluating neighborhood quality
✅ Making offer decisions
✅ Running flip/rental/wholesale strategies

**Voice:** "Do extensive research on 123 Main St"

---

## Use Legacy Research When:
✅ Checking compliance requirements
✅ Analyzing contract gaps
✅ Getting AI-powered insights
✅ Orchestrating multiple internal services
✅ Running custom API calls
✅ Need structured research job tracking

**API:** `POST /research/`

---

# 📊 Complete Endpoint List

## Agentic Research (6 endpoints)
```
POST   /agentic/jobs                              # Create async job
GET    /agentic/jobs/{job_id}                     # Get job status
GET    /agentic/properties/{property_id}          # Get property with output
GET    /agentic/properties/{property_id}/enrichment-status  # Check freshness
GET    /agentic/properties/{property_id}/dossier  # Get markdown dossier
POST   /agentic/research                          # Run sync research (wait)
```

## Legacy Research (9 endpoints)
```
POST   /research/                                 # Create research job
GET    /research/{research_id}                    # Get status/results
GET    /research/                                 # List research jobs
DELETE /research/{research_id}                    # Delete research
POST   /research/property/{property_id}/deep-dive  # Property analysis
POST   /research/property/{property_id}/market-analysis  # Market analysis
POST   /research/property/{property_id}/compliance  # Compliance check
GET    /research/property/{property_id}/latest    # Latest completed
POST   /research/ai-research                      # Custom AI analysis
POST   /research/api-research                     # Custom API calls
```

---

# 🔧 MCP Tools (Voice Commands)

## Agentic Research (4 tools)
```
research_property           # "Do extensive research on 123 Main St"
research_property_async     # "Start researching 456 Oak St in background"
get_research_status         # "What's the status of research job 42?"
get_research_dossier        # "Get the research dossier for property 15"
```

## Legacy Research
**No MCP tools** - API-only access

---

# 📝 Example Workflows

## Workflow 1: Investment Deal Analysis (Agentic)

```bash
# 1. Start extensive research
Voice: "Do extensive research on 123 Main St New York"

# 2. Wait 2-3 minutes for completion

# 3. Get full dossier
Voice: "Get the research dossier for property 15"

# Output: Full markdown report with ARV, comps, underwriting, risks
```

---

## Workflow 2: Background Research (Agentic)

```bash
# 1. Start async research
Voice: "Start researching 456 Oak St in the background"

# Output: "Research job #42 started"

# 2. Continue with other tasks...

# 3. Check progress later
Voice: "What's the status of research job 42?"

# Output: "Job #42: in_progress (65%) - Fetching comparable sales..."

# 4. Get results when complete
Voice: "Get the research dossier for property 16"
```

---

## Workflow 3: Compliance Check (Legacy)

```bash
# API call
POST /research/property/1/compliance

# Response after 30 seconds:
{
  "status": "completed",
  "results": {
    "steps": {
      "compliance_engine": {...},
      "contract_compliance": {...}
    },
    "remediation_plan": [...]
  }
}
```

---

## Workflow 4: Custom AI Analysis (Legacy)

```bash
# Ask any question about a property
POST /research/ai-research
{
  "property_id": 1,
  "prompt": "What are the top 5 risks for this property?"
}

# Response: AI-generated risk analysis
```

---

# 🎉 Summary

**You have TWO powerful research systems:**

## Agentic Research (NEW)
- **20+ external data sources**
- **Autonomous worker agents**
- **Investment-focused** (ARV, underwriting, MAO)
- **4 MCP tools** for voice control
- **6 API endpoints**
- **2-3 minutes** for extensive research
- **Best for:** Deal analysis, investment decisions

## Legacy Research (ORIGINAL)
- **Internal service orchestration**
- **Sequential execution**
- **Compliance-focused** (legal, contracts)
- **No MCP tools** (API only)
- **9+ API endpoints**
- **30-60 seconds** execution
- **Best for:** Compliance checks, custom AI analysis

---

**Both systems work independently and complement each other!**

---

**Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)**
