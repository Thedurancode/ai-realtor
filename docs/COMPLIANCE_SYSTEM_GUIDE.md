# Compliance Knowledge Management System

## 🎉 Implementation Complete!

Your AI Realtor platform now has a comprehensive **Compliance Knowledge Management System** with full CRUD operations, AI-powered rule generation, bulk import/export, and voice integration.

---

## 📁 Files Created

### Database Models
- **`app/models/compliance_rule.py`** - Database models for compliance rules, checks, violations, and templates

### Schemas
- **`app/schemas/compliance.py`** - Pydantic models for API request/response validation

### Services
- **`app/services/compliance_knowledge_service.py`** - AI-powered rule validation and generation service

### API Router
- **`app/routers/compliance_knowledge.py`** - Complete CRUD API with 30+ endpoints

### Seed Data
- **`scripts/seeds/seed_compliance_rules.py`** - Script to populate database with example rules for NY, CA, FL, TX

### Updated Files
- **`app/main.py`** - Added compliance_knowledge_router
- **`app/routers/__init__.py`** - Exported compliance_knowledge_router

---

## 🚀 Deployment Instructions

### 1. Deploy to Fly.io

The new compliance endpoints are **not yet live** on your production server. You need to redeploy:

```bash
# From your project root
fly deploy
```

This will:
- Build the new Docker image with compliance code
- Create database tables for compliance rules
- Make endpoints available at `https://ai-realtor.fly.dev/compliance/knowledge/*`

### 2. Seed the Database

After deployment, populate with example compliance rules:

**Option A: Via API (recommended)**
```bash
curl -X POST "https://ai-realtor.fly.dev/compliance/knowledge/rules/bulk" \
  -H "Content-Type: application/json" \
  -d @compliance_rules_seed.json
```

**Option B: Run seed script on Fly.io**
```bash
fly ssh console
cd /app
python3 scripts/seeds/seed_compliance_rules.py
exit
```

**Option C: Import CSV**
```bash
curl -X POST "https://ai-realtor.fly.dev/compliance/knowledge/rules/import-csv" \
  -F "file=@compliance_rules.csv"
```

---

## 📚 API Endpoints

### Create Operations

#### Create Single Rule
```bash
POST /compliance/knowledge/rules
```

**Example:**
```bash
curl -X POST "https://ai-realtor.fly.dev/compliance/knowledge/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "state": "NY",
    "rule_code": "NY-LEAD-001",
    "category": "disclosure",
    "title": "Lead Paint Disclosure",
    "description": "Properties built before 1978 require lead paint disclosure",
    "rule_type": "threshold",
    "field_to_check": "year_built",
    "condition": "< 1978",
    "severity": "critical",
    "requires_document": true,
    "document_type": "lead_paint_disclosure"
  }'
```

#### Bulk Create Rules
```bash
POST /compliance/knowledge/rules/bulk
```

#### Import from CSV
```bash
POST /compliance/knowledge/rules/import-csv
```

#### AI-Generate Rule from Natural Language
```bash
POST /compliance/knowledge/rules/ai-generate
```

**Example:**
```bash
curl -X POST "https://ai-realtor.fly.dev/compliance/knowledge/rules/ai-generate" \
  -H "Content-Type: application/json" \
  -d '{
    "state": "CA",
    "natural_language_rule": "All homes in California earthquake zones must have seismic retrofit disclosure",
    "category": "safety"
  }'
```

---

### Read Operations

#### List All Rules (with filters)
```bash
GET /compliance/knowledge/rules
```

**Query Parameters:**
- `state` - Filter by state (e.g., `NY`, `CA`)
- `city` - Filter by city
- `category` - Filter by category (`disclosure`, `safety`, etc.)
- `severity` - Filter by severity (`critical`, `high`, `medium`, `low`)
- `is_active` - Show only active rules (default: `true`)
- `is_draft` - Filter draft rules
- `rule_type` - Filter by rule type
- `search` - Search in title, description, rule_code
- `tags` - Filter by tags (can specify multiple)
- `skip` - Pagination offset
- `limit` - Results per page (default: 100)

**Examples:**
```bash
# Get all NY disclosure rules
curl "https://ai-realtor.fly.dev/compliance/knowledge/rules?state=NY&category=disclosure"

# Search for lead paint rules
curl "https://ai-realtor.fly.dev/compliance/knowledge/rules?search=lead"

# Get critical severity rules
curl "https://ai-realtor.fly.dev/compliance/knowledge/rules?severity=critical"

# Get draft rules for review
curl "https://ai-realtor.fly.dev/compliance/knowledge/rules?is_draft=true"
```

#### Get Single Rule
```bash
GET /compliance/knowledge/rules/{rule_id}
```

#### Get Rule by Code
```bash
GET /compliance/knowledge/rules/code/{rule_code}
```

**Example:**
```bash
curl "https://ai-realtor.fly.dev/compliance/knowledge/rules/code/NY-LEAD-001"
```

#### Get Rule History (versions)
```bash
GET /compliance/knowledge/rules/{rule_id}/history
```

#### Get Available States
```bash
GET /compliance/knowledge/states
```

Returns list of states with rule counts.

#### Get Categories
```bash
GET /compliance/knowledge/categories?state=NY
```

#### Export to CSV
```bash
GET /compliance/knowledge/export/csv?state=NY&category=disclosure
```

**Example:**
```bash
# Export all NY rules
curl "https://ai-realtor.fly.dev/compliance/knowledge/export/csv?state=NY" > ny_rules.csv

# Export all disclosure rules
curl "https://ai-realtor.fly.dev/compliance/knowledge/export/csv?category=disclosure" > disclosure_rules.csv
```

---

### Update Operations

#### Update Rule
```bash
PATCH /compliance/knowledge/rules/{rule_id}
```

**Example:**
```bash
curl -X PATCH "https://ai-realtor.fly.dev/compliance/knowledge/rules/5" \
  -H "Content-Type: application/json" \
  -d '{
    "severity": "high",
    "description": "Updated description with more details"
  }'
```

**Create New Version:**
```bash
curl -X PATCH "https://ai-realtor.fly.dev/compliance/knowledge/rules/5?create_new_version=true" \
  -H "Content-Type: application/json" \
  -d '{"severity": "critical"}'
```

#### Activate Rule
```bash
POST /compliance/knowledge/rules/{rule_id}/activate
```

#### Deactivate Rule (soft delete)
```bash
POST /compliance/knowledge/rules/{rule_id}/deactivate
```

#### Publish Draft Rule
```bash
POST /compliance/knowledge/rules/{rule_id}/publish
```

---

### Delete Operations

#### Delete Single Rule
```bash
DELETE /compliance/knowledge/rules/{rule_id}
```

**Soft delete (default):**
```bash
curl -X DELETE "https://ai-realtor.fly.dev/compliance/knowledge/rules/5"
```

**Hard delete (permanent):**
```bash
curl -X DELETE "https://ai-realtor.fly.dev/compliance/knowledge/rules/5?hard_delete=true"
```

#### Bulk Delete
```bash
DELETE /compliance/knowledge/rules/bulk
```

**Example:**
```bash
curl -X DELETE "https://ai-realtor.fly.dev/compliance/knowledge/rules/bulk" \
  -H "Content-Type: application/json" \
  -d '{"rule_ids": [1, 2, 3], "hard_delete": false}'
```

---

### Clone Operations

#### Clone Single Rule
```bash
POST /compliance/knowledge/rules/{rule_id}/clone
```

**Example - Clone NY rule to CA:**
```bash
curl -X POST "https://ai-realtor.fly.dev/compliance/knowledge/rules/5/clone?new_state=CA&new_rule_code=CA-LEAD-001"
```

#### Clone All State Rules
```bash
POST /compliance/knowledge/rules/clone-state-rules
```

**Example - Copy all NY rules to NJ:**
```bash
curl -X POST "https://ai-realtor.fly.dev/compliance/knowledge/rules/clone-state-rules?source_state=NY&target_state=NJ"
```

---

### Voice-Optimized Endpoints

#### Add Rule via Voice
```bash
POST /compliance/knowledge/voice/add-rule
```

**Example:**
```bash
curl -X POST "https://ai-realtor.fly.dev/compliance/knowledge/voice/add-rule" \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language": "All properties in Florida built in flood zones must have flood insurance disclosure",
    "state": "FL",
    "category": "environmental"
  }'
```

#### Search Rules via Voice
```bash
GET /compliance/knowledge/voice/search-rules?query=lead&state=NY
```

**Response includes:**
```json
{
  "rules": [...],
  "count": 5,
  "voice_summary": "Found 5 rules matching 'lead' for NY: Lead-Based Paint Disclosure Required, Lead Testing Requirements, and 3 more"
}
```

---

## 🎯 Usage Examples

### Example 1: Create Lead Paint Rule

```bash
curl -X POST "https://ai-realtor.fly.dev/compliance/knowledge/rules" \
  -H "Content-Type: application/json" \
  -d '{
    "state": "NY",
    "rule_code": "NY-LEAD-001",
    "category": "disclosure",
    "title": "Lead-Based Paint Disclosure",
    "description": "Properties built before 1978 must have lead paint disclosure",
    "legal_citation": "42 U.S.C. § 4852d",
    "rule_type": "threshold",
    "field_to_check": "year_built",
    "condition": "< 1978",
    "severity": "critical",
    "requires_document": true,
    "document_type": "lead_paint_disclosure",
    "ai_prompt": "If property was built before 1978, it MUST have lead paint disclosure",
    "how_to_fix": "Complete EPA Lead-Based Paint Disclosure Form",
    "penalty_description": "Up to $10,000 fine per violation",
    "tags": ["lead", "pre-1978", "disclosure"]
  }'
```

### Example 2: AI-Generate Rule

```bash
curl -X POST "https://ai-realtor.fly.dev/compliance/knowledge/rules/ai-generate" \
  -H "Content-Type: application/json" \
  -d '{
    "state": "CA",
    "natural_language_rule": "California properties built before 1960 in earthquake zones must disclose seismic retrofit status",
    "category": "safety",
    "legal_citation": "CA Civil Code § 1102.6"
  }'
```

### Example 3: Search and Filter

```bash
# Find all critical rules for NY
curl "https://ai-realtor.fly.dev/compliance/knowledge/rules?state=NY&severity=critical"

# Find all disclosure requirements
curl "https://ai-realtor.fly.dev/compliance/knowledge/rules?category=disclosure"

# Search for earthquake-related rules
curl "https://ai-realtor.fly.dev/compliance/knowledge/rules?search=earthquake"
```

### Example 4: Update and Version Control

```bash
# Update rule (in-place)
curl -X PATCH "https://ai-realtor.fly.dev/compliance/knowledge/rules/5" \
  -H "Content-Type: application/json" \
  -d '{"severity": "high"}'

# Create new version
curl -X PATCH "https://ai-realtor.fly.dev/compliance/knowledge/rules/5?create_new_version=true" \
  -H "Content-Type: application/json" \
  -d '{"severity": "critical"}'

# View version history
curl "https://ai-realtor.fly.dev/compliance/knowledge/rules/5/history"
```

### Example 5: Bulk Operations

```bash
# Import from CSV
curl -X POST "https://ai-realtor.fly.dev/compliance/knowledge/rules/import-csv" \
  -F "file=@compliance_rules.csv"

# Export to CSV
curl "https://ai-realtor.fly.dev/compliance/knowledge/export/csv?state=NY" > ny_rules.csv

# Clone all NY rules to NJ
curl -X POST "https://ai-realtor.fly.dev/compliance/knowledge/rules/clone-state-rules?source_state=NY&target_state=NJ"
```

---

## 🗂️ Database Schema

### ComplianceRule Table

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| state | String(2) | 2-letter state code (NY, CA, etc.) |
| rule_code | String(50) | Unique code (NY-LEAD-001) |
| category | String(50) | Category (disclosure, safety, etc.) |
| title | String(255) | Rule title |
| description | Text | Detailed description |
| rule_type | String(50) | Type (threshold, document, ai_review, etc.) |
| severity | String(20) | Severity (critical, high, medium, low) |
| is_active | Boolean | Active status |
| is_draft | Boolean | Draft status |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

### Rule Types

- **threshold** - Numeric comparison (e.g., `year_built < 1978`)
- **required_field** - Check if field exists
- **document** - Document must be uploaded
- **ai_review** - AI interprets complex rule
- **boolean** - True/false check
- **list_check** - Value must be in allowed list
- **date_range** - Date must be within range
- **conditional** - If X then Y logic

### Categories

- `disclosure` - Legal disclosure requirements
- `safety` - Safety requirements (smoke detectors, etc.)
- `building_code` - Building code compliance
- `zoning` - Zoning regulations
- `environmental` - Environmental disclosures
- `accessibility` - ADA and accessibility
- `licensing` - Licensing requirements
- `fair_housing` - Fair housing compliance
- `tax` - Tax-related requirements
- `hoa` - HOA/condo requirements
- `other` - Miscellaneous

### Severity Levels

- `critical` - Blocks listing, must fix immediately
- `high` - Must fix before listing
- `medium` - Should fix
- `low` - Nice to have
- `info` - Informational only

---

## 🤖 AI Features

### AI-Powered Rule Generation

The system uses **Claude Sonnet 4** to generate structured compliance rules from natural language:

```bash
POST /compliance/knowledge/rules/ai-generate
{
  "state": "CA",
  "natural_language_rule": "All California properties must disclose proximity to airports",
  "category": "disclosure"
}
```

**AI generates:**
- Rule code (CA-DISC-###)
- Structured fields
- AI evaluation prompt
- How-to-fix instructions
- Relevant tags

### AI Rule Validation

Before saving, the service validates:
- Required fields present
- Rule type has necessary fields
- State code format
- Rule code format
- Category/severity valid

---

## 📊 Seed Data Included

The seed script creates **14 example rules** for:

### New York (6 rules)
- Lead paint disclosure (pre-1978)
- Smoke detector requirements
- Property condition disclosure
- High-value property documentation

### California (4 rules)
- Natural hazard disclosure
- Earthquake retrofit disclosure
- Water-conserving fixtures
- Lead paint disclosure

### Florida (3 rules)
- Radon gas disclosure
- Property tax disclosure
- HOA/condo association disclosure

### Texas (3 rules)
- Seller's disclosure notice
- Lead paint disclosure
- Flood zone disclosure

---

## 🎙️ Voice Integration Examples

### MCP Tool Example

```python
@mcp.tool()
async def add_compliance_rule(
    state: str,
    rule_description: str,
    category: str = None
) -> str:
    """
    Add a compliance rule using natural language.

    Example: "Add rule for NY: All properties need CO detectors"
    """

    response = await http_client.post(
        f"{API_URL}/compliance/knowledge/voice/add-rule",
        json={
            "natural_language": rule_description,
            "state": state,
            "category": category
        }
    )

    data = response.json()
    return data["voice_confirmation"]


@mcp.tool()
async def search_compliance_rules(
    query: str,
    state: str = None
) -> str:
    """
    Search compliance rules.

    Example: "Show me all lead paint rules for New York"
    """

    params = {"query": query}
    if state:
        params["state"] = state

    response = await http_client.get(
        f"{API_URL}/compliance/knowledge/voice/search-rules",
        params=params
    )

    data = response.json()
    return data["voice_summary"]
```

### Voice Commands

- *"Add a compliance rule for New York: All properties built before 1978 must have lead paint disclosure"*
- *"Show me all disclosure rules for California"*
- *"What are the critical compliance rules for NY?"*
- *"Search for earthquake-related compliance rules"*
- *"Clone all New York rules to New Jersey"*

---

## ✅ Testing Checklist

After deployment, test these endpoints:

- [ ] **Create rule** - `POST /compliance/knowledge/rules`
- [ ] **List rules** - `GET /compliance/knowledge/rules?state=NY`
- [ ] **Get rule by ID** - `GET /compliance/knowledge/rules/1`
- [ ] **Get rule by code** - `GET /compliance/knowledge/rules/code/NY-LEAD-001`
- [ ] **Update rule** - `PATCH /compliance/knowledge/rules/1`
- [ ] **AI generate** - `POST /compliance/knowledge/rules/ai-generate`
- [ ] **Search rules** - `GET /compliance/knowledge/rules?search=lead`
- [ ] **Export CSV** - `GET /compliance/knowledge/export/csv?state=NY`
- [ ] **Delete rule** - `DELETE /compliance/knowledge/rules/1`
- [ ] **Clone rule** - `POST /compliance/knowledge/rules/1/clone?new_state=CA`
- [ ] **Voice add** - `POST /compliance/knowledge/voice/add-rule`
- [ ] **Voice search** - `GET /compliance/knowledge/voice/search-rules?query=lead`

---

## 🔗 Next Steps

1. **Deploy to Fly.io**: `fly deploy`
2. **Seed database**: Run seed script or bulk import
3. **Test API endpoints**: Use curl or Postman
4. **Integrate with voice agent**: Add MCP tools
5. **Build compliance checker**: Create compliance engine service (next phase)

---

## 📖 Documentation

Interactive API docs will be available at:
- **Swagger UI**: `https://ai-realtor.fly.dev/docs`
- **ReDoc**: `https://ai-realtor.fly.dev/redoc`

Look for the **"compliance-knowledge"** tag in the API documentation.

---

## 🎉 Success!

Your compliance knowledge management system is ready! You now have:

✅ Full CRUD operations for compliance rules
✅ AI-powered rule generation from natural language
✅ Bulk import/export (CSV)
✅ Version control and rule history
✅ Clone rules between states
✅ Voice-optimized endpoints
✅ Advanced search and filtering
✅ 14 pre-built example rules

**What's next?** Build the Compliance Engine to actually run checks on properties using these rules!
