# Context-Aware Contract Management System

## Overview

The AI Realtor platform now features an intelligent, flexible contract management system that combines **automation**, **AI intelligence**, and **manual control**. This system automatically attaches required contracts to properties while allowing you to override decisions and get AI-powered recommendations.

## Three-Tier Contract System

### 1. Template-Based Auto-Attach (Automation)
**When it runs:** Automatically when properties are created

**How it works:**
- Contract templates are configured with rules (state, city, property type, price range)
- When a property is created, the system evaluates all active templates
- Applicable contracts are automatically attached
- Contracts marked with `requirement_source: AUTO_ATTACHED`

**Example:**
```bash
# Create property - contracts auto-attach automatically
curl -X POST http://localhost:8000/properties/ \
  -H "Content-Type: application/json" \
  -d '{
    "address": "123 Broadway",
    "city": "New York",
    "state": "NY",
    "price": 1000000,
    "property_type": "condo"
  }'

# Response includes auto-attached contracts:
# - NY Residential Purchase Agreement (REQUIRED)
# - NYC Property Disclosure (REQUIRED)
# - Condo Association Rules (RECOMMENDED)
```

### 2. AI-Powered Suggestions (Intelligence)
**When to use:** When you want intelligent analysis of contract requirements

**How it works:**
- Claude Sonnet 4 analyzes property characteristics
- AI considers state/local regulations and best practices
- Returns categorized suggestions: REQUIRED vs OPTIONAL
- Each suggestion includes reasoning

**API Endpoints:**
- `POST /contracts/property/{id}/ai-suggest` - Get AI suggestions
- `POST /contracts/property/{id}/ai-apply-suggestions` - Apply suggestions
- `GET /contracts/property/{id}/ai-analyze-gaps` - Analyze gaps

### 3. Manual Override (Full Control)
**When to use:** When you know better than automated systems

**How it works:**
- Manually mark any contract as required or optional
- Overrides both template defaults and AI suggestions
- Can add custom reasons and deadlines
- Contracts marked with `requirement_source: MANUAL`

**API Endpoints:**
- `PATCH /contracts/{id}/mark-required` - Mark contract as required/optional
- `POST /contracts/property/{id}/set-required-contracts` - Bulk update

## MCP Tools (Voice Integration)

### AI-Powered Tools
- **ai_suggest_contracts** - Get AI contract suggestions
- **apply_ai_contract_suggestions** - Apply AI recommendations
  
### Manual Control Tools
- **mark_contract_required** - Manual override for contract requirements

### Enhanced Tools
- **check_property_contract_readiness** - Respects is_required flag
- **attach_required_contracts** - Template-based auto-attach

## How the Three Tiers Work Together

### Scenario 1: Fully Automated
Create property → Templates auto-attach → Done

### Scenario 2: AI-Enhanced
Create property → Get AI suggestions → Review → Apply suggestions

### Scenario 3: Full Control
Create property → Review auto-attached → Manual overrides

## Benefits

### For Agents
- Save time with automatic contract attachment
- Get intelligent recommendations from AI
- Full control when you need it
- Track why each contract is required

### For Brokerages
- Ensure compliance with state/local laws
- Standardize processes across agents
- Reduce errors and missed contracts
- Complete audit trail

## Summary

This system fulfills your request for:

✅ **Manual selection:** Pick which contracts are required per property
✅ **AI intelligence:** Get smart recommendations based on property analysis
✅ **Auto-attach:** Automatic contract attachment based on templates

All three work together seamlessly, giving you maximum flexibility.
