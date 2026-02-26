# 📊 Property Data - Complete Reference

## Overview

Each property in AI Realtor contains **26+ top-level data fields** plus **8 related data tables** with hundreds of individual data points.

---

## 🏠 Basic Property Information (17 fields)

### Core Details
- **id** - Unique property identifier
- **title** - Property display name (e.g., "123 Main St")
- **description** - Freeform property description
- **address** - Full street address
- **city** - City name
- **state** - 2-letter state code
- **zip_code** - ZIP/postal code

### Property Specs
- **price** - Listing price (float)
- **bedrooms** - Number of bedrooms (integer)
- **bathrooms** - Number of bathrooms (float, supports half baths)
- **square_feet** - Living area in sqft (integer)
- **lot_size** - Lot size (float, various units)
- **year_built** - Year built (integer)

### Classification
- **property_type** - Type: `HOUSE`, `CONDO`, `TOWNHOUSE`, `APARTMENT`, `LAND`, `COMMERCIAL`, `MULTI_FAMILY`
- **status** - Pipeline stage: `new_property`, `enriched`, `researched`, `waiting_for_contracts`, `complete`
- **deal_type** - Deal classification (optional)

### Metadata
- **agent_id** - Assigned agent ID
- **created_at** - Creation timestamp
- **updated_at** - Last update timestamp

---

## 📈 Zillow Enrichment Data (20+ fields)

### Valuation
- **zpid** - Zillow Property ID
- **zestimate** - Zillow home value estimate
- **zestimate_low** - Zestimate low range
- **zestimate_high** - Zestimate high range
- **rent_zestimate** - Monthly rental estimate

### Property Details
- **living_area** - Interior square footage
- **lot_size** - Lot size
- **lot_area_units** - Unit of measure (sqft/acres)
- **year_built** - Year constructed
- **home_type** - Property type classification
- **home_status** - Current status (For Sale, Pending, etc.)
- **days_on_zillow** - Days listed on Zillow

### Engagement Metrics
- **page_view_count** - Zillow page views
- **favorite_count** - Zillow saves/favorites

### Financial
- **property_tax_rate** - Annual tax rate (%)
- **annual_tax_amount** - Yearly property tax

### Media & Links
- **photos** - JSON array of photo URLs (up to 10)
- **zillow_url** - Full Zillow listing URL
- **hdp_url** - Zillow details page path
- **description** - Property description from Zillow

### Rich Data Arrays (JSON)
- **schools** - Array of nearby schools with:
  - Name, rating (1-10), distance, grades, link
- **tax_history** - Array of tax assessments with:
  - Tax amount, assessment year
- **price_history** - Array of price changes with:
  - Price, date, event type (sold, listed, etc.)
- **reso_facts** - 100+ property attributes including:
  - Room dimensions, features, parking, basement, HVAC, flooring, etc.

---

## 🔍 Skip Trace Data (8 fields per record)

### Owner Information
- **owner_name** - Full owner name
- **owner_first_name** - First name
- **owner_last_name** - Last name

### Contact Methods (JSON arrays)
- **phone_numbers** - Array with:
  - Number, type (mobile/landline), status, link
- **emails** - Array with:
  - Email address, type, info

### Mailing Address
- **mailing_address** - Street address
- **mailing_city** - City
- **mailing_state** - State
- **mailing_zip** - ZIP code

### Raw Data
- **raw_response** - Full API response JSON

---

## 👥 Contacts (8 fields per contact)

- **id** - Contact ID
- **property_id** - Linked property
- **name** - Full name
- **first_name** - First name
- **last_name** - Last name
- **role** - Contact type:
  - `buyer`, `seller`, `lawyer`, `attorney`, `contractor`, `inspector`, `appraiser`, `lender`, `mortgage_broker`, `title_company`, `tenant`, `landlord`, `property_manager`, `handyman`, `plumber`, `electrician`, `photographer`, `stager`, `other`
- **phone** - Phone number
- **email** - Email address
- **company** - Company name
- **notes** - Freeform notes
- **created_at** - Creation timestamp
- **updated_at** - Last update

---

## 📄 Contracts (13 fields per contract)

### Basic Info
- **id** - Contract ID
- **property_id** - Linked property
- **contact_id** - Linked contact (optional)
- **name** - Contract name
- **description** - Contract description

### DocuSeal Integration
- **docuseal_template_id** - Template ID
- **docuseal_submission_id** - Submission ID
- **docuseal_url** - Signing URL

### Status & Requirements
- **status** - Contract status:
  - `DRAFT`, `SENT`, `IN_PROGRESS`, `PENDING_SIGNATURE`, `COMPLETED`, `CANCELLED`, `EXPIRED`, `ARCHIVED`
- **is_required** - Whether contract is required
- **required_by_date** - Deadline date
- **requirement_source** - How requirement was determined:
  - `AUTOMATIC`, `AI_SUGGESTED`, `MANUAL`
- **requirement_reason** - Why it's required

### Timestamps
- **sent_at** - When sent for signing
- **completed_at** - When completed
- **created_at** - Creation timestamp
- **updated_at** - Last update

---

## 📝 Property Notes (5 fields per note)

- **id** - Note ID
- **property_id** - Linked property
- **content** - Note text content
- **source** - How note was added:
  - `voice`, `manual`, `ai`, `phone_call`, `system`
- **created_by** - Creator (optional)
- **created_at** - Creation timestamp

---

## 💰 Offers (14 fields per offer)

### Offer Details
- **id** - Offer ID
- **property_id** - Linked property
- **buyer_contact_id** - Buyer contact
- **parent_offer_id** - Parent offer (for counter-offers)
- **offer_price** - Offered price
- **earnest_money** - Earnest money deposit
- **financing_type** - Financing:
  - `CASH`, `CONVENTIONAL`, `FHA`, `VA`, `OTHER`
- **closing_days** - Days to closing

### Terms (JSON)
- **contingencies** - Array of contingencies:
  - Inspection, financing, appraisal, sale of current home, etc.

### Status
- **status** - Offer status:
  - `DRAFT`, `SUBMITTED`, `ACCEPTED`, `REJECTED`, `COUNTERED`, `EXPIRED`, `WITHDRAWN`, `NULLIFIED`
- **is_our_offer** - True if this is our offer to seller
- **notes** - Freeform notes

### MAO Analysis
- **mao_low** - Maximum allowable offer (low)
- **mao_base** - Maximum allowable offer (base)
- **mao_high** - Maximum allowable offer (high)

### Timestamps
- **submitted_at** - When submitted
- **expires_at** - Expiration deadline
- **responded_at** - When responded to
- **created_at** - Creation timestamp
- **updated_at** - Last update

---

## 📊 Scoring Data (3 fields)

### Overall Score
- **deal_score** - Overall score (0-100)
- **score_grade** - Letter grade: `A`, `B`, `C`, `D`, `F`

### Score Breakdown (JSON)
- **dimensions** - 4 scoring dimensions:
  - **market** (30% weight) - Zestimate spread, days on market, school quality
  - **financial** (25% weight) - Zestimate upside, rental yield, price per sqft
  - **readiness** (25% weight) - Contracts, contacts, skip trace
  - **engagement** (20% weight) - Recent activity, notes, tasks, notifications
- **components** - 15+ individual metrics:
  - Market: School quality, tax gap, price trend
  - Financial: Rental yield, gross yield, price per sqft
  - Readiness: Contact coverage, skip trace reachability, contract completion
  - Engagement: Activity count (7d), notes count, tasks count, notifications

---

## ⏳ Pipeline Status (3 fields)

- **pipeline_status** - Automation status:
  - `not_started`, `in_progress`, `completed`, `blocked`
- **pipeline_started_at** - When automation started
- **pipeline_completed_at** - When automation completed

---

## 💓 Heartbeat (12 fields)

### Stage Info
- **stage** - Current stage: `new_property`, `enriched`, `researched`, `waiting_for_contracts`, `complete`
- **stage_label** - Human-readable stage name
- **stage_index** - Stage number (0-4)
- **total_stages** - Total stages (5)

### Checklist (4 items)
- **enriched** - Zillow enrichment done
- **researched** - Skip trace done
- **contracts_attached** - Contracts attached
- **contracts_completed** - Required contracts completed

### Health Status
- **health** - Property health: `healthy`, `stale`, `blocked`
- **health_reason** - Why property is stale/blocked
- **days_in_stage** - Days in current stage
- **stale_threshold_days** - Days before becoming stale
- **days_since_activity** - Days since last activity

### Next Steps
- **next_action** - Recommended next action
- **deal_score** - Current deal score
- **score_grade** - Current grade
- **voice_summary** - 1-2 sentence text-to-speech summary

---

## 📋 Property Recap (AI-Generated)

### Recap Fields
- **id** - Recap ID
- **property_id** - Linked property
- **recap_text** - 3-4 paragraph AI summary
- **recap_context** - JSON with structured data
- **voice_summary** - 2-3 sentence TTS summary
- **version** - Recap version number
- **last_trigger** - What caused regeneration:
  - `manual`, `contract_signed`, `enrichment_updated`, `skip_trace_completed`, `note_added`, `contact_added`, `property_updated`
- **created_at** - Creation timestamp
- **updated_at** - Last update

---

## 🎯 Data Access Methods

### Via Telegram Bot
- "Show me property 1"
- "What data do you have on 123 Main St?"
- "Get details for property 1"

### Via API
```bash
# Get complete property data
curl http://localhost:8000/properties/1 \
  -H "X-API-Key: nanobot-perm-key-2024"

# Get specific sections
curl http://localhost:8000/properties/1/zillow-enrichment
curl http://localhost:8000/properties/1/skip-traces
curl http://localhost:8000/contracts/?property_id=1
curl http://localhost:8000/contacts/?property_id=1
curl http://localhost:8000/property-notes/?property_id=1
curl http://localhost:8000/offers/?property_id=1
```

---

## 📊 Data Counts per Property

Your **Property #1 (123 Main Street)** currently has:

| Data Type | Count | Status |
|-----------|-------|--------|
| Basic Fields | 17/17 | ✅ Complete |
| Zillow Enrichment | 20+ fields | ✅ Enriched |
| Skip Trace | 1 record | ✅ Found |
| Schools | 3 schools | ✅ With ratings |
| Photos | 1 photo | ✅ Available |
| Contacts | 0 | ❌ None |
| Contracts | 0 | ❌ None |
| Notes | 2 | ✅ Added |
| Offers | 0 | ❌ None |
| Scoring | 4 dimensions | ✅ Calculated |
| Heartbeat | 12 fields | ✅ Healthy |

**Total Data Points: 100+ individual fields per property!**

---

## 🔍 Data Relationships

```
Property (id=1)
├── Zillow Enrichment (1:1)
│   ├── Schools (0-10)
│   ├── Photos (0-10)
│   ├── Tax History (0+)
│   ├── Price History (0+)
│   └── RESO Facts (100+ attributes)
│
├── Skip Traces (1+)
│   ├── Phone Numbers (1+)
│   └── Emails (1+)
│
├── Contacts (0+)
│   └── Role-based organization
│
├── Contracts (0+)
│   └── DocuSeal integration
│
├── Notes (0+)
│   └── Multiple sources
│
├── Offers (0+)
│   ├── Contingencies (JSON array)
│   └── Counter-offer chain
│
├── Recap (1:1)
│   ├── AI summary
│   └── Voice summary
│
├── Scoring (1:1)
│   └── 4 dimensions, 15+ metrics
│
└── Heartbeat (computed)
    ├── Stage tracking
    ├── Health status
    └── Next actions
```

---

## 💡 Summary

Each property is a **comprehensive data repository** with:

- ✅ **100+ data fields** across 8 related tables
- ✅ **Rich enrichment** from Zillow (photos, schools, history)
- ✅ **Owner contact** discovery via skip tracing
- ✅ **Contract tracking** with DocuSeal integration
- ✅ **Knowledge base** via notes
- ✅ **Deal scoring** across 4 dimensions
- ✅ **Pipeline tracking** through 5 stages
- ✅ **AI summaries** for quick understanding
- ✅ **Real-time health** monitoring

All this data is **accessible via voice**, **Telegram bot**, or **API**! 🎉
