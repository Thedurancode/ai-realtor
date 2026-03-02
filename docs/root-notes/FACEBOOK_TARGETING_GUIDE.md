# 🎯 Facebook Ad Targeting Assistant - AI-Powered

## What It Does

The AI analyzes your property and suggests **optimal Facebook ad audiences** based on:
- Property price tier (budget, medium, high, luxury)
- Property type (house, condo, townhouse, land, commercial)
- Location characteristics (urban, suburban, beachfront, resort)
- Property features (bedrooms, bathrooms, amenities)

---

## 🎭 6 Buyer Personas

### 1. Luxury Home Buyer
- **Age:** 35-65
- **Income:** High
- **Interests:** Luxury goods, High-end real estate, Private jet, Yachting, Fine dining, Art collection, Wealth management
- **Best for:** Properties $1M+

### 2. First-Time Home Buyer
- **Age:** 25-40
- **Income:** Medium
- **Interests:** Home buying, Mortgage calculator, Interior design, Home improvement, Apartment hunting
- **Best for:** Properties under $500K

### 3. Real Estate Investor
- **Age:** 30-65
- **Income:** High
- **Interests:** Real estate investing, Rental properties, Property management, House flipping, REIT, Passive income
- **Best for:** Multi-family, land, commercial, or high-ROI properties

### 4. Vacation/Second Home Buyer
- **Age:** 40-65
- **Income:** High
- **Interests:** Vacation homes, Beach houses, Mountain properties, Resort living, Luxury travel
- **Best for:** Beachfront, resort, or vacation properties

### 5. Empty Nester/Downsizer
- **Age:** 55-75
- **Income:** Medium-High
- **Interests:** Condominium, Retirement communities, Low maintenance homes, Gated community, Senior living
- **Best for:** Condos, single-level homes

### 6. Family Home Buyer
- **Age:** 30-50
- **Income:** Medium-High
- **Interests:** Family home, Suburban living, School district, Child care, Parenting, Backyard design
- **Best for:** 3+ bedroom houses in good school districts

---

## 📍 4 Location Strategies

### Urban
- **Radius:** 10km
- **Additional Interests:** Urban living, City life, Public transportation, Walkability
- **Description:** Target urban professionals and city dwellers
- **Best for:** NYC, San Francisco, Boston, Chicago

### Suburban
- **Radius:** 25km
- **Additional Interests:** Suburban living, Family-friendly, School ratings, Community events
- **Description:** Target families and suburban home seekers
- **Best for:** Most suburban properties

### Beachfront
- **Radius:** 40km
- **Additional Interests:** Beach houses, Oceanfront living, Water sports, Coastal living
- **Description:** Target oceanfront property seekers
- **Best for:** Miami Beach, Malibu, Hamptons, Cape Cod

### Resort
- **Radius:** 50km
- **Additional Interests:** Luxury travel, Vacation destinations, Resort amenities, Golf courses
- **Description:** Target vacation home buyers and luxury seekers
- **Best for:** Aspen, Vail, Park City, Scottsdale, Naples

---

## 💰 Budget Recommendations by Price Tier

| Price Tier | Price Range | Min Budget | Max Budget | Avg CPL |
|------------|-------------|------------|------------|---------|
| **Budget** | <$300K | $10/day | $30/day | $15 |
| **Medium** | $300K-$500K | $20/day | $50/day | $30 |
| **High** | $500K-$1M | $50/day | $100/day | $50 |
| **Luxury** | $1M+ | $100/day | $200/day | $100 |

*CPL varies by location multiplier (Urban 1.5x, Beachfront 1.3x, Resort 1.4x, Suburban 1.0x)*

---

## 🎨 What You Get

### Primary Audience
- Detailed persona based on property type
- Age range and demographics
- 10-15 targeted interests
- Behaviors to target
- Income and education levels

### Secondary Audience
- Alternative buyer persona
- Narrower interest targeting
- For testing against primary

### Location Strategy
- Radius recommendations
- Location type detection
- Additional location-based interests
- Strategy description

### Budget Recommendations
- Min/max daily budget
- Projected CPL (min/avg/max)
- Recommended campaign duration

### Creative Recommendations
- 3 creative angles (value, luxury, urgency)
- Headline keywords
- Customer pain points to address

### Testing Strategy
- How to test angles
- Duration recommendations
- Budget allocation
- Success metrics

---

## 🚀 How to Use

### Via API

```bash
# Analyze property for targeting
curl -X POST "http://localhost:8000/facebook-targeting/analyze" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{"property_id": 5}'
```

**Response includes:**
```json
{
  "property_analysis": {...},
  "primary_audience": {
    "name": "Luxury Home Buyer",
    "age_min": 35,
    "age_max": 65,
    "interests": ["Luxury goods", "High-end real estate", ...],
    "income_level": "high"
  },
  "location_targeting": {...},
  "budget_recommendations": {...},
  "creative_recommendations": {...}
}
```

### Via Voice (MCP Tools)

**"Get Facebook targeting for property 5"**
```
Uses: get_facebook_targeting
```

**"List all targeting personas"**
```
Uses: list_targeting_personas
```

**"Suggest Facebook audiences for this property"**
```
Uses: suggest_facebook_audiences
```

---

## 📊 Example Output

### Property: 8801 Collins Ave 4D, Miami Beach
- **Price:** $450,000
- **Type:** Condo
- **Bedrooms:** 2
- **Bathrooms:** 2

### Primary Audience: Luxury Home Buyer
- **Age:** 35-65
- **Location:** Miami Beach, FL (40km radius)
- **Interests:** Luxury goods, Real estate investing, Oceanfront property, Miami Beach, High-end condominiums, Condominium, Low maintenance living
- **Behaviors:** Facebook Page Admins, Engaged Shoppers (High)
- **Income:** High

### Secondary Audience: Empty Nester/Downsizer
- **Age:** 55-75
- **Interests:** Condominium, Retirement communities, Low maintenance homes, Senior living

### Budget: $20-50/day
- **Projected CPL:** $39 ($27-$51 range)
- **Duration:** 30 days

### Creative Angles:
1. **Value:** "Premium Miami Beach Property at Market Price"
2. **Luxury:** "Exclusive Miami Beach Living"
3. **Urgency:** "Limited Opportunity in Miami Beach"

---

## 🎯 Complete Workflow

1. **Get Targeting Recommendations**
   ```
   POST /facebook-targeting/analyze
   ```

2. **Review AI Suggestions**
   - Primary audience
   - Secondary audience
   - Location targeting
   - Budget recommendations

3. **Generate Ad Content**
   ```
   POST /zuckerbot/campaigns/create
   ```

4. **Copy to Meta Ads Manager**
   - Use AI-recommended targeting
   - Use AI-generated ad copy
   - Set recommended budget

---

## 📁 Files Created

- `app/services/facebook_targeting_service.py` - AI targeting engine (500+ lines)
- `app/routers/facebook_targeting.py` - API endpoints (4 endpoints)
- `mcp_server/tools/facebook_targeting.py` - Voice tools (3 tools)
- `app/main.py` - Router registered

---

## ✅ All Pushed to GitHub!

Commit: `feat: Add AI-powered Facebook ad targeting assistant`

Total: **855 lines of production code** 🚀
