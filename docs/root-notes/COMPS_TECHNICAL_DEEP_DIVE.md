# 📊 Comps API - Technical Deep Dive

## How It Works - Step by Step

---

## 1. Main Dashboard Flow (`get_dashboard`)

### Step 1: Load Subject Property
```python
# Line 22-24: Get property from database
prop = db.query(Property).filter(Property.id == property_id).first()
if not prop:
    raise ValueError(f"Property {property_id} not found")
```

### Step 2: Get Zillow Enrichment
```python
# Line 26-28: Get Zillow data (zestimate, rent_zestimate)
enrichment = db.query(ZillowEnrichment).filter(
    ZillowEnrichment.property_id == property_id
).first()
zestimate = enrichment.zestimate if enrichment else None
rent_zestimate = enrichment.rent_zestimate if enrichment else None
```

### Step 3: Build Subject Object
```python
# Line 30: Create subject dict with all property details
subject = self._build_subject(prop, zestimate, rent_zestimate)
# Returns: {address, city, state, price, beds, baths, sqft, property_type, zestimate, rent_zestimate}
```

### Step 4: Load Comps from 3 Sources
```python
# Line 33-37: Load comps from multiple sources

# A. Agentic Research (if available)
rp = self._find_research_property(db, prop)  # Find research record by address
research_sales = self._load_comp_sales(db, rp.id) if rp else []  # From comp_sale table
research_rentals = self._load_comp_rentals(db, rp.id) if rp else []  # From comp_rental table

# B. Zillow Price History
zillow_sales = self._load_zillow_sold_history(enrichment)  # From enrichment.price_history JSON

# C. Internal Portfolio
internal_comps = self._load_internal_portfolio_comps(db, prop)  # From properties table
```

### Step 5: Merge and Sort Sales Comps
```python
# Line 39-40: Combine research + Zillow sales, sort by similarity
all_sales = research_sales + zillow_sales
all_sales.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
```

### Step 6: Calculate Metrics
```python
# Line 42-44: Compute market metrics and recommendations
metrics = self._compute_market_metrics(all_sales, prop.price, zestimate)
rental_metrics = self._compute_rental_metrics(research_rentals)
recommendation = self._build_pricing_recommendation(metrics, prop.price, zestimate)
```

### Step 7: Build Voice Summary
```python
# Line 45: TTS-optimized 1-2 sentence summary
voice = self._build_voice_summary(subject, metrics, len(all_sales), len(research_rentals))
```

### Step 8: Return Complete Dashboard
```python
# Line 47-64: Return full dashboard with all data
return {
    "property_id": property_id,
    "subject": subject,
    "comp_sales": all_sales[:20],  # Top 20 sales comps
    "comp_rentals": research_rentals[:20],  # Top 20 rental comps
    "internal_portfolio_comps": internal_comps[:10],  # Top 10 portfolio comps
    "market_metrics": {...},
    "pricing_recommendation": recommendation,
    "data_sources": {
        "comp_sales_from_research": len(research_sales),
        "comp_sales_from_zillow": len(zillow_sales),
        "comp_rentals": len(research_rentals),
        "internal_portfolio": len(internal_comps),
        "has_zillow_enrichment": enrichment is not None,
        "has_agentic_research": rp is not None,
    },
    "voice_summary": voice,
}
```

---

## 2. Data Source Loaders

### A. Load Comp Sales from Research (`_load_comp_sales`)
```python
# Lines 163-190: Query comp_sale table

from app.models.comp_sale import CompSale

rows = (
    db.query(CompSale)
    .filter(CompSale.research_property_id == rp_id)
    .order_by(CompSale.similarity_score.desc())
    .limit(20)
    .all()
)

# Transform to dict
return [
    {
        "address": r.address,
        "sale_price": r.sale_price,
        "sale_date": r.sale_date.isoformat() if r.sale_date else None,
        "distance_mi": r.distance_mi,
        "sqft": r.sqft,
        "beds": r.beds,
        "baths": r.baths,
        "year_built": r.year_built,
        "similarity_score": round(r.similarity_score, 2),
        "source": "agentic_research",
        "source_url": r.source_url,
    }
    for r in rows
]
```

**Table Structure:** `comp_sale`
- `research_property_id` - FK to research_property
- `address` - Comp property address
- `sale_price` - Sold price
- `sale_date` - Sale date
- `distance_mi` - Distance from subject
- `sqft`, `beds`, `baths`, `year_built` - Property details
- `similarity_score` - Pre-calculated similarity (0-1)
- `source_url` - Source URL

---

### B. Load Zillow Sold History (`_load_zillow_sold_history`)
```python
# Lines 219-250: Parse price_history JSON from enrichment

if not enrichment or not enrichment.price_history:
    return []

history = enrichment.price_history  # JSON array from Zillow
if not isinstance(history, list):
    return []

sales = []
for entry in history:
    if not isinstance(entry, dict):
        continue

    # Check if event was a sale
    event = str(entry.get("event", "")).lower()
    if "sold" not in event:
        continue

    price = entry.get("price")
    if not price:
        continue

    sales.append({
        "address": entry.get("address", "Subject property (historical)"),
        "sale_price": float(price),
        "sale_date": entry.get("date"),
        "distance_mi": 0.0,  # Historical sale of subject property
        "sqft": entry.get("sqft"),
        "beds": entry.get("beds"),
        "baths": entry.get("baths"),
        "year_built": None,
        "similarity_score": 0.5,  # Lower score for historical self-sales
        "source": "zillow_price_history",
        "source_url": None,
    })

return sales
```

**Zillow price_history JSON Structure:**
```json
[
    {
        "event": "Sold",
        "date": "2023-06-15",
        "price": 850000,
        "sqft": 1800,
        "beds": 3,
        "baths": 2
    },
    {
        "event": "Listed for sale",
        "date": "2023-05-01",
        "price": 875000
    }
]
```

---

### C. Load Internal Portfolio Comps (`_load_internal_portfolio_comps`)
```python
# Lines 252-282: Query properties table for similar properties

# Query candidates (same city/state, different property)
candidates = (
    db.query(Property)
    .filter(
        Property.id != prop.id,  # Not the subject property
        Property.city == prop.city,  # Same city
        Property.state == prop.state,  # Same state
        Property.status.in_([...])  # Any active status
    )
    .limit(50)  # Max 50 candidates
    .all()
)

# Score each candidate
scored = []
for c in candidates:
    score = self._simple_similarity(prop, c)  # Calculate similarity
    if score >= 0.3:  # Minimum 30% similarity threshold
        scored.append({
            "property_id": c.id,
            "address": f"{c.address}, {c.city}",
            "city": c.city,
            "price": c.price,
            "beds": c.bedrooms,
            "baths": c.bathrooms,
            "sqft": c.square_feet,
            "status": c.status.value if c.status else "unknown",
            "similarity_score": round(score, 2),
        })

# Sort by similarity and return top 10
scored.sort(key=lambda x: x["similarity_score"], reverse=True)
return scored[:10]
```

**Query Logic:**
1. Find properties in same city/state
2. Exclude subject property
3. Calculate similarity score for each
4. Filter by 30% minimum threshold
5. Sort by similarity (highest first)
6. Return top 10

---

## 3. Similarity Scoring Algorithm

### The Core Formula (`_simple_similarity`)
```python
# Lines 284-312: Calculate property similarity score (0-1)

def _simple_similarity(self, subject: Property, candidate: Property) -> float:
    score = 0.0
    total_weight = 0.0

    # 1. Price similarity (40% weight)
    if subject.price and candidate.price and subject.price > 0:
        price_ratio = min(subject.price, candidate.price) / max(subject.price, candidate.price)
        score += 0.4 * price_ratio
        total_weight += 0.4

    # 2. Bedroom match (20% weight)
    if subject.bedrooms is not None and candidate.bedrooms is not None:
        diff = abs(subject.bedrooms - candidate.bedrooms)
        score += 0.2 * max(0, 1 - diff / 3)  # -3 beds = 0 score, same = 1.0
        total_weight += 0.2

    # 3. Bathroom match (10% weight)
    if subject.bathrooms is not None and candidate.bathrooms is not None:
        diff = abs(subject.bathrooms - candidate.bathrooms)
        score += 0.1 * max(0, 1 - diff / 3)
        total_weight += 0.1

    # 4. Square footage match (30% weight)
    if subject.square_feet and candidate.square_feet and subject.square_feet > 0:
        sqft_ratio = min(subject.square_feet, candidate.square_feet) / max(subject.square_feet, candidate.square_feet)
        score += 0.3 * sqft_ratio
        total_weight += 0.3

    # Normalize by total weight (handles missing data)
    return score / total_weight if total_weight > 0 else 0.0
```

### Weight Breakdown

| Factor | Weight | Formula | Perfect Match | Completely Different |
|--------|--------|---------|---------------|---------------------|
| **Price** | 40% | `min/max` ratio | 1.0 | 0.0 (free) |
| **Bedrooms** | 20% | `1 - diff/3` | 1.0 (same) | 0.0 (3+ diff) |
| **Bathrooms** | 10% | `1 - diff/3` | 1.0 (same) | 0.0 (3+ diff) |
| **Sqft** | 30% | `min/max` ratio | 1.0 | 0.0 (free) |

**Total Range:** 0.0 to 1.0 (higher = better match)

### Example Calculation

**Subject:** $850k, 3bd, 2ba, 1800 sqft
**Candidate:** $820k, 4bd, 3ba, 1750 sqft

```
Price score:    0.4 * (820k/850k) = 0.4 * 0.965 = 0.386
Bedroom score:  0.2 * (1 - 1/3)    = 0.2 * 0.667 = 0.133
Bathroom score: 0.1 * (1 - 1/3)    = 0.1 * 0.667 = 0.067
Sqft score:     0.3 * (1750/1800)  = 0.3 * 0.972 = 0.292
───────────────────────────────────────────────────
Total score:    0.386 + 0.133 + 0.067 + 0.292 = 0.878
Similarity:     87.8%
```

**Interpretation:** 87.8% similarity = excellent match!

---

## 4. Market Metrics Calculation

### Compute Market Metrics (`_compute_market_metrics`)
```python
# Lines 316-373: Calculate comprehensive market statistics

def _compute_market_metrics(self, sales: list[dict], subject_price: float, zestimate: Optional[float]) -> dict:
    # Extract prices
    prices = [s["sale_price"] for s in sales if s.get("sale_price")]

    # Extract price per sqft
    ppsf_list = [
        s["sale_price"] / s["sqft"]
        for s in sales
        if s.get("sale_price") and s.get("sqft") and s["sqft"] > 0
    ]

    if not prices:
        return {"comp_count": 0, ...}  # All null values

    # Calculate averages and medians
    avg_price = mean(prices)
    med_price = median(prices)
    avg_ppsf = mean(ppsf_list) if ppsf_list else None
    med_ppsf = median(ppsf_list) if ppsf_list else None

    # Price trend
    trend, trend_pct = self._compute_price_trend(sales)

    # Subject vs market comparison
    subject_vs, diff_pct = self._compare_to_market(subject_price, med_price)

    # Zestimate vs comps
    zest_comp = None
    if zestimate and avg_price:
        diff = zestimate - avg_price
        zest_comp = {
            "zestimate": zestimate,
            "comp_avg": round(avg_price),
            "difference": round(diff),
            "difference_pct": round(diff / avg_price * 100, 1) if avg_price else None,
        }

    return {
        "comp_count": len(prices),
        "avg_sale_price": round(avg_price),
        "median_sale_price": round(med_price),
        "avg_price_per_sqft": round(avg_ppsf) if avg_ppsf else None,
        "median_price_per_sqft": round(med_ppsf) if med_ppsf else None,
        "price_range": {"min": min(prices), "max": max(prices)},
        "price_trend": trend,
        "trend_pct": trend_pct,
        "subject_vs_market": subject_vs,
        "subject_difference_pct": diff_pct,
        "zestimate_vs_comps": zest_comp,
    }
```

### Price Trend Calculation (`_compute_price_trend`)
```python
# Lines 387-409: Calculate if market is rising or falling

def _compute_price_trend(self, sales: list[dict]) -> tuple[str, Optional[float]]:
    # Filter sales with dates
    dated = [(s["sale_date"], s["sale_price"]) for s in sales if s.get("sale_date") and s.get("sale_price")]

    if len(dated) < 3:
        return "insufficient_data", None

    # Sort by date (oldest first)
    dated.sort(key=lambda x: str(x[0]))

    # Split into halves (older vs newer)
    mid = len(dated) // 2
    older_avg = mean([p for _, p in dated[:mid]])    # First half
    newer_avg = mean([p for _, p in dated[mid:]])    # Second half

    if older_avg == 0:
        return "stable", 0.0

    # Calculate percentage change
    change_pct = round((newer_avg - older_avg) / older_avg * 100, 1)

    # Classify trend
    if change_pct > 2:
        return "appreciating", change_pct
    elif change_pct < -2:
        return "depreciating", change_pct
    return "stable", change_pct
```

**Logic:**
1. Sort sales by date
2. Split into older half vs newer half
3. Compare average prices
4. If newer > older + 2% = appreciating
5. If newer < older - 2% = depreciating
6. Otherwise = stable

**Example:**
```
Older half (5 sales): $820k, $830k, $840k, $835k, $825k → avg: $830k
Newer half (5 sales): $850k, $860k, $855k, $865k, $870k → avg: $860k

Change: ($860k - $830k) / $830k * 100 = +3.6%
Result: "appreciating", +3.6%
```

---

### Subject vs Market (`_compare_to_market`)
```python
# Lines 411-421: Compare subject price to median comp price

def _compare_to_market(self, subject_price: float, median_price: float) -> tuple[Optional[str], Optional[float]]:
    if not subject_price or not median_price:
        return None, None

    # Calculate % difference
    diff_pct = round((subject_price - median_price) / median_price * 100, 1)

    # Classify position
    if abs(diff_pct) <= 5.0:  # Within 5% = at market
        return "at_market", diff_pct
    elif diff_pct > 0:
        return "above_market", diff_pct
    return "below_market", diff_pct
```

**Tolerance:** ±5% = "at_market"

**Examples:**
```
Median comp: $850,000
Subject: $850,000 → 0% → "at_market"
Subject: $800,000 → -5.9% → "below_market"
Subject: $900,000 → +5.9% → "above_market"
```

---

## 5. Pricing Recommendation

### Build Recommendation (`_build_pricing_recommendation`)
```python
# Lines 425-454: Generate natural language recommendation

def _build_pricing_recommendation(self, metrics: dict, subject_price: float, zestimate: Optional[float]) -> str:
    comp_count = metrics.get("comp_count", 0)
    med_price = metrics.get("median_sale_price")

    # No comps
    if comp_count == 0:
        rec = "No comparable sales data available. Recommend enriching with Zillow and running agentic research."
        if zestimate:
            rec += f" Zillow Zestimate is ${zestimate:,.0f}."
        return rec

    # Build recommendation parts
    parts = []

    # 1. Comp count and median
    if comp_count >= 5:
        parts.append(f"Based on {comp_count} comparable sales, estimated market value is ${med_price:,.0f}.")
    else:
        parts.append(f"Limited comp data ({comp_count} sale{'s' if comp_count != 1 else ''}). Median: ${med_price:,.0f}. Consider running agentic research for more data.")

    # 2. Subject vs market
    diff_pct = metrics.get("subject_difference_pct")
    vs = metrics.get("subject_vs_market")
    if vs and diff_pct is not None and vs != "at_market":
        label = "above" if vs == "above_market" else "below"
        parts.append(f"List price of ${subject_price:,.0f} is {abs(diff_pct):.0f}% {label} market.")
    elif vs == "at_market":
        parts.append(f"List price of ${subject_price:,.0f} is in line with the market.")

    # 3. Zestimate vs comps
    zest = metrics.get("zestimate_vs_comps")
    if zest and zest.get("difference_pct") is not None:
        label = "above" if zest["difference_pct"] > 0 else "below"
        parts.append(f"Zestimate (${zest['zestimate']:,.0f}) is {abs(zest['difference_pct']):.0f}% {label} comp average.")

    return " ".join(parts)
```

**Output Examples:**

```
✅ "Based on 15 comparable sales, estimated market value is $850,000. List price of $850,000 is in line with the market."

⚠️ "Limited comp data (2 sales). Median: $825,000. Consider running agentic research for more data. List price of $850,000 is 3% above market."

📉 "Based on 12 comparable sales, estimated market value is $800,000. List price of $850,000 is 6% above market. Zestimate ($810,000) is 1% below comp average."
```

---

## 6. Voice Summary (TTS-Optimized)

### Build Voice Summary (`_build_voice_summary`)
```python
# Lines 458-485: Generate 1-2 sentence summary for text-to-speech

def _build_voice_summary(self, subject: dict, metrics: dict, comp_count: int, rental_count: int) -> str:
    if comp_count == 0 and rental_count == 0:
        return "No comparable sales or rental data available for this property. Consider running agentic research."

    parts = []
    addr = subject["address"].split(",")[0]  # Just street address

    # Sales comps summary
    if comp_count > 0:
        parts.append(f"{addr} has {comp_count} comparable sale{'s' if comp_count != 1 else ''}.")
        med = metrics.get("median_sale_price")
        if med:
            parts.append(f"Median comp price is ${med:,.0f}.")
        diff = metrics.get("subject_difference_pct")
        vs = metrics.get("subject_vs_market")
        if vs and diff is not None and vs != "at_market":
            label = "above" if vs == "above_market" else "below"
            parts.append(f"Your list price is {abs(diff):.0f}% {label} market.")
        trend = metrics.get("price_trend")
        trend_pct = metrics.get("trend_pct")
        if trend and trend not in ("stable", "insufficient_data") and trend_pct:
            parts.append(f"Market is {trend} at {abs(trend_pct):.1f}%.")

    # Rental comps summary
    if rental_count > 0:
        med_rent = metrics.get("median_rent")
        if med_rent:
            parts.append(f"{rental_count} rental comp{'s' if rental_count != 1 else ''}, median ${med_rent:,.0f}/mo.")

    return " ".join(parts)
```

**Voice Examples:**

```
"123 Main St has 15 comparable sales. Median comp price is $850,000. Your list price is at market. Market is appreciating at 3.6%."

"123 Main St has 2 comparable sales. Median comp price is $825,000. Your list price is 3% above market."

"123 Main St has 8 rental comps, median $2,750/mo."
```

---

## 7. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  Subject Property                                           │
│  - properties table                                         │
│  - ZillowEnrichment (zestimate, rent_zestimate)             │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Load Comps from 3 Sources                                  │
├─────────────────────────────────────────────────────────────┤
│  1. Agentic Research                                        │
│     └── comp_sale table (by research_property_id)           │
│         Returns: address, sale_price, sale_date,            │
│                  distance_mi, sqft, beds, baths,            │
│                  similarity_score, source_url               │
│                                                              │
│  2. Zillow Price History                                    │
│     └── zillow_enrichments.price_history JSON               │
│         Filter: event contains "sold"                       │
│         Returns: address, sale_price, sale_date,            │
│                  similarity_score=0.5, source=zillow        │
│                                                              │
│  3. Internal Portfolio                                      │
│     └── properties table (same city/state)                  │
│         Filter: similarity_score >= 0.3                     │
│         Returns: property_id, address, price, status,       │
│                  similarity_score                           │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Merge & Sort Comps                                         │
│  - Combine: research_sales + zillow_sales                   │
│  - Sort by: similarity_score (DESC)                        │
│  - Limit: top 20 sales, top 20 rentals, top 10 portfolio   │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Calculate Market Metrics                                   │
├─────────────────────────────────────────────────────────────┤
│  Sales Metrics:                                             │
│  - comp_count, avg/median_sale_price                        │
│  - avg/median_price_per_sqft                                │
│  - price_range (min, max)                                   │
│                                                              │
│  Price Trend:                                               │
│  - Split sales by date (older half vs newer half)           │
│  - Compare averages → "appreciating"/"depreciating"/"stable"│
│                                                              │
│  Subject vs Market:                                         │
│  - Compare subject_price to median_comp_price               │
│  - ±5% tolerance → "at_market"/"above_market"/"below_market"│
│                                                              │
│  Zestimate vs Comps:                                        │
│  - Compare zestimate to avg_comp_price                      │
│  - Calculate $ and % difference                             │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│  Build Outputs                                              │
├─────────────────────────────────────────────────────────────┤
│  1. Pricing Recommendation (3-4 sentences)                  │
│  2. Voice Summary (1-2 sentences, TTS-optimized)            │
│  3. Full Dashboard JSON                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Database Tables

### comp_sale (Agentic Research Comps)
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| research_property_id | Integer | FK to research_property |
| address | String | Comp property address |
| sale_price | Float | Sold price |
| sale_date | Date | Sale date |
| distance_mi | Float | Distance from subject (miles) |
| sqft | Integer | Square footage |
| beds | Integer | Bedrooms |
| baths | Integer | Bathrooms |
| year_built | Integer | Year built |
| similarity_score | Float | Pre-calculated similarity (0-1) |
| source_url | String | Source URL |

### comp_rental (Agentic Research Rentals)
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| research_property_id | Integer | FK to research_property |
| address | String | Comp property address |
| rent | Float | Monthly rent |
| date_listed | Date | Listing date |
| distance_mi | Float | Distance from subject (miles) |
| sqft | Integer | Square footage |
| beds | Integer | Bedrooms |
| baths | Integer | Bathrooms |
| similarity_score | Float | Pre-calculated similarity (0-1) |
| source_url | String | Source URL |

### properties (Internal Portfolio)
| Column | Type | Used For |
|--------|------|----------|
| id | Integer | Property ID |
| address | String | Matching by city/state |
| city | String | **Primary filter** |
| state | String | **Primary filter** |
| price | Float | Similarity scoring (40%) |
| bedrooms | Integer | Similarity scoring (20%) |
| bathrooms | Integer | Similarity scoring (10%) |
| square_feet | Integer | Similarity scoring (30%) |
| status | Enum | Filter active properties |

### zillow_enrichments (Zillow Data)
| Column | Type | Used For |
|--------|------|----------|
| property_id | Integer | FK to property |
| zestimate | Float | Market value estimate |
| rent_zestimate | Float | Rental value estimate |
| price_history | JSONB | **Sold properties extraction** |

---

## 9. API Endpoints

### 1. Full Dashboard
```python
GET /comps/{property_id}
```
**Returns:**
- comp_sales (20)
- comp_rentals (20)
- internal_portfolio_comps (10)
- market_metrics (sales + rental)
- pricing_recommendation
- data_sources breakdown
- voice_summary

**MCP Tool:** `get_comps_dashboard`
**Voice:** "Show me comps for property 5"

---

### 2. Sales Comps Only
```python
GET /comps/{property_id}/sales
```
**Returns:**
- comp_sales (20)
- market_metrics (sales only)
- pricing_recommendation
- voice_summary

**MCP Tool:** `get_comp_sales`
**Voice:** "What have similar properties sold for?"

---

### 3. Rental Comps Only
```python
GET /comps/{property_id}/rentals
```
**Returns:**
- comp_rentals (20)
- rental_metrics
- voice_summary

**MCP Tool:** `get_comp_rentals`
**Voice:** "What are similar properties renting for?"

---

## 10. Performance Optimizations

1. **Pre-calculated Similarity Scores:**
   - Agentic research comps store `similarity_score` in database
   - No need to recalculate on every query

2. **Internal Portfolio Filtering:**
   - Filter by city/state first (index-friendly)
   - Limit to 50 candidates before scoring
   - Apply 30% threshold to reduce noise

3. **Lazy Loading:**
   - Only load research comps if `research_property` exists
   - Only load Zillow comps if `price_history` exists
   - Graceful degradation if data missing

4. **Sorted Queries:**
   - Database sorts by similarity (not application)
   - Reduces memory usage

5. **Limits:**
   - Sales: 20 research + 20 Zillow = 40 max
   - Rentals: 20 max
   - Portfolio: 50 candidates → 10 results

---

## 11. Edge Cases Handled

| Scenario | Behavior |
|----------|----------|
| No comps found | Return empty arrays, `comp_count=0`, recommendation to enrich/research |
| Missing sqft/beds/baths | Weight re-normalization (skip missing factors) |
| No Zillow enrichment | Skip Zillow price history, use other sources |
| No agentic research | Skip research comps, use Zillow + portfolio |
| Empty price_history | Return empty Zillow sales list |
| Invalid price_history (not list) | Return empty Zillow sales list |
| Zero price in sales | Exclude from metrics calculations |
| Same property in portfolio | Excluded by `Property.id != prop.id` |
| Different cities/states | Not included in internal portfolio comps |

---

## 12. Key Constants

```python
MARKET_TOLERANCE_PCT = 5.0  # ±5% = "at_market"
SIMILARITY_THRESHOLD = 0.3  # 30% min for internal comps
MAX_SALES_COMPS = 20        # Limit research + Zillow sales
MAX_RENTAL_COMPS = 20       # Limit rental comps
MAX_PORTFOLIO_COMPS = 10    # Limit internal portfolio
MAX_PORTFOLIO_CANDIDATES = 50  # Candidates to score
MIN_SALES_FOR_TREND = 3     # Minimum sales to calculate trend
TREND_THRESHOLD_PCT = 2.0   # ±2% = "stable"
```

---

## Summary

The Comps API aggregates comparable sales from **3 sources**:

1. **Agentic Research** (`comp_sale` table) - High-quality comps from deep research
2. **Zillow Price History** (`price_history` JSON) - Historical sales of subject property
3. **Internal Portfolio** (`properties` table) - Agent's other properties in same market

Each comp gets a **similarity score** (0-1) based on:
- Price similarity (40%)
- Bedroom match (20%)
- Bathroom match (10%)
- Square footage (30%)

**Market metrics** include:
- Comp count, median/average prices
- Price per square foot
- Price trend (appreciating/depreciating/stable)
- Subject vs market (at/above/below)
- Zestimate vs comps comparison

**3 API endpoints** serve different use cases:
- Full dashboard (all data)
- Sales comps only (pricing analysis)
- Rental comps only (rental analysis)

**3 MCP tools** enable voice control:
- "Show me comps for property 5"
- "What have similar properties sold for?"
- "What are similar properties renting for?"

---

**Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)**
