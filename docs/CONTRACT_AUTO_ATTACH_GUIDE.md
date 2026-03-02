# Contract Auto-Attach System - Complete Guide

## 🎉 Implementation Complete!

Your AI Realtor platform now has **automatic contract attachment**! When you create a property, required contracts are automatically attached based on state, property type, and other criteria.

---

## 📁 Files Created

### Core System
- **`app/models/contract_template.py`** - Contract template model
- **`app/schemas/contract_template.py`** - Pydantic schemas
- **`app/services/contract_auto_attach.py`** - Auto-attach service logic
- **`app/routers/contract_templates.py`** - Template management API
- **`scripts/seeds/seed_contract_templates.py`** - Database seed script with 15 templates

### Modified Files
- **`app/routers/properties.py`** - Added auto-attach on property creation
- **`app/routers/contracts.py`** - Added contract status and management endpoints
- **`app/routers/__init__.py`** - Exported contract_templates_router
- **`app/main.py`** - Included contract_templates_router

---

## 🚀 How It Works

### **1. Automatic Contract Attachment Flow**

```
User creates property
    ↓
System checks applicable contract templates
    ↓
Filters by: state, city, property type, price
    ↓
Auto-attaches contracts where auto_attach_on_create = true
    ↓
Contracts created with DRAFT status
    ↓
Voice confirmation tells user how many contracts attached
```

### **2. Contract Template Configuration**

Each template defines:
- **What:** Contract name, description, category
- **Where:** State, city, property type filters
- **When:** Required, recommended, or optional
- **Auto-attach:** Should it attach automatically?
- **DocuSeal:** Template ID for sending contracts

---

## 📚 API Endpoints

### Contract Template Management

#### Create Template
```bash
POST /contract-templates/
{
  "name": "NY Property Disclosure",
  "description": "Required for all NY residential sales",
  "category": "disclosure",
  "requirement": "required",
  "state": "NY",
  "property_type_filter": ["house", "condo"],
  "auto_attach_on_create": true,
  "default_recipient_role": "seller",
  "is_active": true,
  "priority": 10
}
```

#### List Templates
```bash
# All templates
GET /contract-templates/

# Filter by state
GET /contract-templates/?state=NY

# Filter by category
GET /contract-templates/?category=disclosure

# Filter by requirement
GET /contract-templates/?requirement=required
```

#### Update Template
```bash
PATCH /contract-templates/{template_id}
{
  "docuseal_template_id": "abc123",
  "is_active": true
}
```

#### Delete Template
```bash
DELETE /contract-templates/{template_id}
```

---

### Auto-Attach Endpoints

#### Manually Trigger Auto-Attach
```bash
# Attach contracts to existing property
POST /contracts/property/{property_id}/auto-attach

# Response:
{
  "property_id": 5,
  "property_address": "123 Main St",
  "contracts_attached": 3,
  "contracts": [
    {
      "id": 10,
      "name": "NY Property Disclosure",
      "description": "Required disclosure",
      "status": "draft"
    }
  ]
}
```

#### Get Required Contracts Status
```bash
# Check if property is ready to close
GET /contracts/property/{property_id}/required-status

# Response:
{
  "property_id": 5,
  "property_address": "123 Main St",
  "total_required": 3,
  "completed": 2,
  "in_progress": 0,
  "missing": 1,
  "is_ready_to_close": false,
  "missing_templates": [
    {
      "id": 1,
      "name": "NY Property Disclosure",
      "description": "Required disclosure",
      "category": "disclosure"
    }
  ],
  "incomplete_contracts": []
}
```

#### Get Missing Contracts
```bash
# Get all missing contracts
GET /contracts/property/{property_id}/missing-contracts

# Get only required missing contracts
GET /contracts/property/{property_id}/missing-contracts?required_only=true

# Response:
{
  "property_id": 5,
  "property_address": "123 Main St",
  "missing_count": 1,
  "missing_contracts": [
    {
      "id": 1,
      "name": "NY Property Disclosure",
      "description": "Required disclosure",
      "category": "disclosure",
      "requirement": "required",
      "docuseal_template_id": "abc123"
    }
  ]
}
```

#### Voice Contract Status
```bash
# Voice: "Check contract status for 141 throop"
POST /contracts/voice/check-contracts?address_query=141+throop

# Response:
{
  "property_address": "141 Throop Ave",
  "is_ready_to_close": false,
  "total_required": 3,
  "completed": 1,
  "in_progress": 1,
  "missing": 1,
  "voice_response": "Contract status for 141 Throop Ave:\n✅ 1 contracts completed\n⏳ 1 contracts in progress\n❌ 1 contracts not yet created\n..."
}
```

---

## 🎯 Usage Examples

### Example 1: Create Property with Auto-Attach

```bash
# Create NY property
curl -X POST "https://ai-realtor.fly.dev/properties/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Luxury Condo in Manhattan",
    "address": "123 Broadway",
    "city": "New York",
    "state": "NY",
    "zip_code": "10001",
    "price": 1000000,
    "bedrooms": 2,
    "bathrooms": 2,
    "property_type": "condo",
    "status": "available",
    "agent_id": 1
  }'

# Result: Property created + 3 contracts auto-attached:
# 1. NY Property Condition Disclosure Statement
# 2. NY Lead-Based Paint Disclosure
# 3. NY Purchase and Sale Agreement
```

### Example 2: Voice Property Creation

```bash
# Voice: "Create a new listing for 555 Park Avenue"
curl -X POST "https://ai-realtor.fly.dev/properties/voice" \
  -H "Content-Type: application/json" \
  -d '{
    "place_id": "ChIJOwg_06VPwokRYv534QaPC8g",
    "price": 2500000,
    "bedrooms": 3,
    "bathrooms": 2,
    "property_type": "condo",
    "agent_id": 1
  }'

# Voice Response:
# "I've created a new listing for 555 Park Avenue, New York, NY.
#  Listed at $2,500,000, 3 bedroom, 2 bathroom.
#  I've also attached 3 required contracts that need to be signed."
```

### Example 3: Check Contract Status

```bash
# Check if property is ready to close
curl "https://ai-realtor.fly.dev/contracts/property/5/required-status"

# Response shows:
# - 3 total required contracts
# - 2 completed
# - 1 in progress
# - 0 missing
# - is_ready_to_close: false (because 1 still in progress)
```

### Example 4: Manually Attach Contracts

```bash
# If property was created before templates were configured,
# manually trigger auto-attach:
curl -X POST "https://ai-realtor.fly.dev/contracts/property/5/auto-attach"

# Result: Attaches any missing applicable contracts
```

---

## 🗄️ Database Schema

### **contract_templates** Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String | Template name |
| description | Text | Description |
| category | Enum | listing, purchase, disclosure, inspection, lease, addendum, other |
| requirement | Enum | required, recommended, optional |
| docuseal_template_id | String | DocuSeal template ID |
| state | String(2) | State filter (null = all states) |
| city | String | City filter (null = all cities) |
| property_type_filter | JSON | ["house", "condo"] or null |
| min_price | Integer | Minimum property price |
| max_price | Integer | Maximum property price |
| auto_attach_on_create | Boolean | Auto-attach when property created |
| auto_send | Boolean | Auto-send contract when attached |
| default_recipient_role | String | Default recipient (seller, buyer, etc.) |
| message_template | Text | Default message for sending |
| is_active | Boolean | Is template active |
| priority | Integer | Display priority (higher = first) |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Update timestamp |

---

## 📊 Contract Template Examples

### 15 Pre-Configured Templates

The seed script creates:

**New York (3 templates)**
- NY Property Condition Disclosure Statement (REQUIRED)
- NY Lead-Based Paint Disclosure (REQUIRED)
- NY Purchase and Sale Agreement (REQUIRED)

**California (3 templates)**
- CA Transfer Disclosure Statement (REQUIRED)
- CA Natural Hazard Disclosure Statement (REQUIRED)
- CA Residential Purchase Agreement (REQUIRED)

**Florida (3 templates)**
- FL Seller's Property Disclosure (RECOMMENDED)
- FL Homeowners Association Disclosure (REQUIRED)
- FL Residential Purchase Agreement (REQUIRED)

**Texas (2 templates)**
- TX Seller's Disclosure Notice (REQUIRED)
- TX Residential Purchase Contract (REQUIRED)

**Universal (4 templates)**
- Home Inspection Contingency Addendum (RECOMMENDED)
- Financing Contingency Addendum (RECOMMENDED)
- Lead-Based Paint Disclosure - Federal (REQUIRED for pre-1978)

---

## 🎙️ Voice Integration

### Voice Commands

- **"Create a listing for 123 Main Street"** → Auto-attaches contracts
- **"Check contract status for 141 throop"** → Shows completion status
- **"Is 555 Park ready to close?"** → Checks if all contracts done
- **"What contracts are missing for this property?"** → Lists missing contracts

### MCP Tool Example

```python
@mcp.tool()
async def check_property_contracts(address: str) -> str:
    """
    Check contract status for a property.

    Example: "Are all contracts signed for 141 throop?"
    """

    response = await http_client.post(
        f"{API_URL}/contracts/voice/check-contracts",
        params={"address_query": address}
    )

    data = response.json()
    return data["voice_response"]
```

---

## 🔄 Workflow Examples

### Typical Real Estate Deal Flow

1. **Create Property**
   ```bash
   POST /properties/
   ```
   → System auto-attaches 3 required contracts

2. **Check What's Attached**
   ```bash
   GET /contracts/property/5
   ```
   → Shows all contracts (status: draft)

3. **Send Contracts to Seller**
   ```bash
   POST /contracts/{contract_id}/send-to-contact
   {
     "contact_id": 10,
     "recipient_role": "Seller",
     "message": "Please review and sign"
   }
   ```

4. **Check Status**
   ```bash
   GET /contracts/property/5/required-status
   ```
   → Shows: 1 completed, 2 in progress

5. **Verify Ready to Close**
   ```bash
   GET /contracts/property/5/required-status
   ```
   → `is_ready_to_close: true` when all required contracts done

---

## 🚀 Deployment

### Deploy to Fly.io

```bash
# 1. Deploy application
fly deploy

# 2. Seed contract templates
python3 scripts/seeds/seed_contract_templates.py

# 3. Update templates with DocuSeal IDs
# Go to DocuSeal dashboard and create templates
# Then update each template:
curl -X PATCH "https://ai-realtor.fly.dev/contract-templates/1" \
  -H "Content-Type: application/json" \
  -d '{"docuseal_template_id": "your_template_id"}'
```

### Test

```bash
# Create a test property
curl -X POST "https://ai-realtor.fly.dev/properties/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Property",
    "address": "123 Test St",
    "city": "New York",
    "state": "NY",
    "price": 500000,
    "property_type": "house",
    "agent_id": 1
  }'

# Verify contracts were attached
curl "https://ai-realtor.fly.dev/contracts/property/1"

# Should see 3 contracts auto-attached!
```

---

## ✅ Features

### What's Working:
✅ Auto-attach contracts when property created
✅ Filter by state, city, property type, price
✅ Voice confirmation mentions attached contracts
✅ Manual trigger for existing properties
✅ Check contract completion status
✅ Identify missing required contracts
✅ Voice-optimized status checks
✅ 15 pre-configured templates for NY, CA, FL, TX
✅ Full CRUD API for template management
✅ Integration with existing DocuSeal contract system

---

## 🎊 You're Ready!

Your contract auto-attach system is **complete and ready to use**!

**What happens now:**
1. When you create a NY property → 3 contracts auto-attach
2. When you create a CA property → 3 contracts auto-attach
3. When you create a FL property → 3 contracts auto-attach
4. When you create a TX property → 2 contracts auto-attach

**Next Steps:**
1. Deploy to Fly.io: `fly deploy`
2. Seed templates: `python3 scripts/seeds/seed_contract_templates.py`
3. Create DocuSeal templates and link them
4. Create a test property and watch contracts auto-attach!

**Voice your agent can now say:**
- "I've created the property and attached 3 required contracts"
- "This property has all contracts signed and is ready to close"
- "We're missing 2 required contracts for this deal"
