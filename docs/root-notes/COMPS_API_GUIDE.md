# 📊 Comparable Sales (Comps) API - Complete Guide

## Overview

Your AI Realtor platform has a **powerful Comparable Sales system** that aggregates comp data from **3 different sources** and provides market metrics, pricing recommendations, and rental analysis.

---

## 🎯 What It Does

**The Comps API:**
1. **Aggregates comps from 3 sources:**
   - Agentic Research (deep property research)
   - Zillow Price History (historical sales)
   - Internal Portfolio (your other properties)

2. **Calculates market metrics:**
   - Median/average sale price
   - Price per square foot
   - Price trend (rising/falling)
   - Subject property vs market comparison

3. **Provides AI recommendations:**
   - Pricing recommendations (under/over/at market)
   - Rental yield estimates
   - Market position analysis

---

## 📡 API Endpoints

### 1. **Full Dashboard** (All Data)

```bash
GET /comps/{property_id}
```

**Returns:**
- Sale comps (up to 20)
- Rental comps (up to 20)
- Internal portfolio comps (up to 10)
- Market metrics
- Pricing recommendation
- Data sources summary
- Voice summary

**Example:**
```bash
curl "http://localhost:8000/comps/1" \
  -H "X-API-Key: nanobot-perm-key-2024"
```

---

### 2. **Sales Comps Only**

```bash
GET /comps/{property_id}/sales
```

**Returns:**
- Comparable sales only
- Market metrics
- Pricing recommendation
- Voice summary

**Example:**
```bash
curl "http://localhost:8000/comps/1/sales" \
  -H "X-API-Key: nanobot-perm-key-2024"
```

---

### 3. **Rental Comps Only**

```bash
GET /comps/{property_id}/rentals
```

**Returns:**
- Comparable rentals only
- Rental metrics
- Voice summary

**Example:**
```bash
curl "http://localhost:8000/comps/1/rentals" \
  -H "X-API-Key: nanobot-perm-key-2024"
```

---

## 🤖 Voice Commands (MCP Tools)

### Full Dashboard
```
"Show me comps for property 5"
"What are the comparables?"
"Compare property 5 to nearby sales"
"Market analysis for property 5"
```

### Sales Comps
```
"What have similar properties sold for?"
"Nearby sales for property 5"
"Sales comps for property 5"
```

### Rental Comps
```
"What are similar properties renting for?"
"Rental comps for property 5"
"What's the rental market like?"
```

---

## 📊 Response Structure

### Full Dashboard Response

```json
{
  "property_id": 1,
  "subject": {
    "address": "123 Main St",
    "price": 850000,
    "bedrooms": 3,
    "bathrooms": 2,
    "square_feet": 1800,
    "city": "New York",
    "state": "NY",
    "zestimate": 875000
  },
  "comp_sales": [
    {
      "address": "125 Main St",
      "sale_price": 860000,
      "sqft": 1850,
      "beds": 3,
      "baths": 2,
      "distance_mi": 0.1,
      "sale_date": "2025-01-15",
      "similarity_score": 0.92,
      "source": "research"
    }
  ],
  "comp_rentals": [
    {
      "address": "130 Oak Ave",
      "rent": 2800,
      "sqft": 1800,
      "beds": 3,
      "baths": 2,
      "distance_mi": 0.2,
      "similarity_score": 0.88
    }
  ],
  "internal_portfolio_comps": [
    {
      "property_id": 5,
      "address": "456 Oak Ave",
      "price": 875000,
      "status": "complete"
    }
  ],
  "market_metrics": {
    "comp_count": 15,
    "median_sale_price": 850000,
    "avg_price_per_sqft": 472,
    "price_trend": "rising",
    "trend_pct": 5.2,
    "subject_vs_market": "at_market",
    "subject_difference_pct": 0.0
  },
  "rental_metrics": {
    "comp_count": 8,
    "median_rent": 2750,
    "avg_rent_per_sqft": 1.53
  },
  "pricing_recommendation": "Property is priced at market value based on 15 comparable sales.",
  "data_sources": {
    "comp_sales_from_research": 10,
    "comp_sales_from_zillow": 5,
    "comp_rentals": 8,
    "internal_portfolio": 3,
    "has_zillow_enrichment": true,
    "has_agentic_research": true
  },
  "voice_summary": "Property #1 at 123 Main St has 15 comparable sales. Median comp price: $850,000. Listed at_market."
}
```

---

## 🎯 How It Works

### Step 1: Find Subject Property

```python
# Get property details
prop = db.query(Property).filter(Property.id == property_id).first()

# Get Zillow enrichment (for Zestimate)
enrichment = db.query(ZillowEnrichment).filter(
    ZillowEnrichment.property_id == property_id
).first()
```

### Step 2: Load Comps from 3 Sources

**A. Agentic Research (if available):**
```python
# Check if property has deep research
research = db.query(ResearchProperty).filter(
    ResearchProperty.property_id == property_id
).first()

if research:
    # Load comp sales and rentals from research
    comp_sales = _load_comp_sales(db, research.id)
    comp_rentals = _load_comp_rentals(db, research.id)
```

**B. Zillow Price History:**
```python
# Get sold properties from Zillow enrichment
if enrichment:
    zillow_sales = _load_zillow_sold_history(enrichment)
```

**C. Internal Portfolio:**
```python
# Find similar properties in your portfolio
internal_comps = db.query(Property).filter(
    Property.city == prop.city,
    Property.state == prop.state,
    Property.price.between(prop.price * 0.8, prop.price * 1.2),
    Property.id != property_id
    ).all()
```

### Step 3: Calculate Similarity Scores

Each comp gets a **similarity score** (0-1) based on:
- Distance from subject property
- Price difference
- Square footage difference
- Bedroom/bathroom match

**Formula:**
```python
similarity = (
    (1 - distance_weight) * 0.3 +
    (1 - price_diff_weight) * 0.3 +
    (1 - sqft_diff_weight) * 0.2 +
    room_match_score * 0.2
)
```

### Step 4: Compute Market Metrics

**Sales Metrics:**
```python
{
  "comp_count": 15,
  "median_sale_price": 850000,
  "avg_price_per_sqft": 472,
  "min_price": 720000,
  "max_price": 950000,
  "price_trend": "rising",
  "trend_pct": 5.2
}
```

**Rental Metrics:**
```python
{
  "comp_count": 8,
  "median_rent": 2750,
  "avg_rent_per_sqft": 1.53,
  "rental_yield": 0.039
}
```

### Step 5: Build Pricing Recommendation

**Logic:**
```python
if subject_price < median * 0.95:
    recommendation = "Property is under market value. Consider increasing price."
elif subject_price > median * 1.05:
    recommendation = "Property is over market value. Consider reducing price."
else:
    recommendation = "Property is priced at market value."
```

---

## 🎨 Real Example

### Property
- **123 Main St, New York, NY**
- **Price:** $850,000
- **3 bed, 2 bath, 1,800 sqft**

### Comps Found
- **15 sales comps** (median: $850,000)
- **8 rental comps** (median: $2,750/mo)
- **3 internal portfolio comps**

### Market Analysis
```
Market: median $850,000, avg $472/sqft, trend rising (+5.2%), vs market: at_market

Sale comps (15):
  1. 125 Main St — $860,000 (1,850 sqft, 3bd/2ba, 0.1mi, 92% match)
  2. 130 Oak Ave — $845,000 (1,750 sqft, 3bd/2ba, 0.2mi, 88% match)
  ...

Rental comps (8):
  1. 130 Oak Ave — $2,800/mo (1,800 sqft, 3bd/2ba, 0.2mi, 88% match)
  2. 135 Pine Rd — $2,700/mo (1,750 sqft, 3bd/2ba, 0.3mi, 85% match)
  ...

Recommendation: Property is priced at market value based on 15 comparable sales.
```

---

## 📈 Data Sources

### 1. Agentic Research (Primary)
**Table:** `research_property_comps`
**Fields:**
- Sale price, sale date
- Distance from subject
- Property details
- Similarity score

**When available:** After deep property research

### 2. Zillow Price History (Secondary)
**Table:** `zillow_enrichments.price_history`
**Fields:**
- Sold price
- Sale date
- From Zillow enrichment

**When available:** After Zillow enrichment

### 3. Internal Portfolio (Tertiary)
**Table:** `properties`
**Fields:**
- Your other properties
- Filtered by city/state/price
- Similarity calculated

**When available:** Always (if you have similar properties)

---

## 🎯 Use Cases

### 1. Pricing Strategy
**Agent asks:** "What should I list this property for?"

**System:**
- Pulls comps for property
- Calculates median market price
- Compares to list price
- Recommends pricing strategy

**Voice response:**
```
"Based on 15 comparable sales in the area, the median price is $850,000.
Your property is priced at market value. Comparable properties are selling
within 5% of this price."
```

---

### 2. Market Analysis
**Agent asks:** "How's the market performing?"

**System:**
- Aggregates all comps
- Calculates price trend
- Shows market velocity
- Provides recommendations

**Voice response:**
```
"The market is rising with prices up 5.2% recently. Properties are selling
at a median of $850,000, averaging $472 per square foot."
```

---

### 3. Rental Analysis
**Agent asks:** "What are similar properties renting for?"

**System:**
- Pulls rental comps
- Calculates median rent
- Shows rental yield
- Compares to subject

**Voice response:**
```
"Similar properties are renting for $2,750 per month (median). With your
price of $850,000, that's a 3.9% annual rental yield."
```

---

## 🔍 Advanced Features

### Similarity Scoring

Each comp is scored on:
- **Distance** (closer = higher score)
- **Price** (similar price = higher score)
- **Square footage** (similar size = higher score)
- **Rooms** (bed/bath match = higher score)

**Score range:** 0 to 1 (higher = better match)

### Market Position

**At Market:** Price within ±5% of median
```json
{
  "subject_vs_market": "at_market",
  "subject_difference_pct": 0.0
}
```

**Under Market:** Price >5% below median
```json
{
  "subject_vs_market": "under_market",
  "subject_difference_pct": -8.5
}
```

**Over Market:** Price >5% above median
```json
{
  "subject_vs_market": "over_market",
  "subject_difference_pct": 12.3
}
```

---

## 📚 Related Features

### Property Research
- **Deep property research** generates comp data
- Run: `research_property` → comps auto-generated

### Zillow Enrichment
- **Price history** includes sold properties
- Run: `enrich_property` → price history captured

### Internal Portfolio
- **Your other properties** become comps
- Automatically included if similar location/price

---

## 🎯 Summary

**Your Comps API:**

✅ **3 data sources** (research, Zillow, portfolio)
✅ **Market metrics** (median, average, trend)
✅ **Pricing recommendations** (under/over/at market)
✅ **Similarity scoring** (finds best matches)
✅ **Voice summaries** (TTS-optimized)
✅ **MCP tools** (3 voice commands)

**Total:**
- 3 API endpoints
- 3 MCP tools
- 2 database tables
- 1 comprehensive service

**Your AI Realtor platform has world-class comparable sales analysis!** 📊🏠

---

## 🚀 Try It Now

```bash
# Get full dashboard
curl "http://localhost:8000/comps/1" \
  -H "X-API-Key: nanobot-perm-key-2024" | python3 -m json.tool

# Or use voice command in Nanobot:
# "Show me comps for property 1"
```

---

**Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)**
