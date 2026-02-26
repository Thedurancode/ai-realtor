# 📊 ALL DATA FIELDS - Quick Reference

## 🎯 Summary

Your AI Realtor system has **50 database tables** with **500+ data fields** tracking every aspect of real estate deals.

---

## 🏠 Property Data (Core)

### Basic Property Info - 22 fields
```
✅ Location: address, city, state, zip_code
✅ Details: price, beds, baths, sqft, lot_size, year_built
✅ Type: property_type, status, deal_type
✅ Scoring: deal_score, score_grade, score_breakdown
✅ Pipeline: pipeline_status, timestamps
✅ Metadata: id, agent_id, created_at, updated_at
```

### Zillow Enrichment - 24 fields
```
✅ Valuation: zestimate, rent_zestimate
✅ Details: living_area, lot_size, home_type
✅ Engagement: page_view_count, favorite_count
✅ Financial: tax_rate, annual_tax
✅ Media: photos (array), description
✅ Arrays: schools, tax_history, price_history
✅ 100+ RESO facts
```

### Skip Trace - 11 fields
```
✅ Owner: name, first_name, last_name
✅ Contacts: phone_numbers (JSON), emails (JSON)
✅ Address: mailing_address, city, state, zip
```

### Contacts - 10 fields
```
✅ Identity: name, first_name, last_name
✅ Role: buyer, seller, lender, contractor, etc.
✅ Contact: phone, email, company, notes
```

### Contracts - 13 fields
```
✅ Document: name, description, template_id
✅ Status: status, is_required, required_by_date
✅ DocuSeal: submission_id, signing_url
✅ Timestamps: sent_at, completed_at
```

### Offers - 17 fields
```
✅ Terms: price, earnest_money, financing_type, closing_days
✅ Contingencies (JSON array)
✅ MAO Analysis: mao_low, mao_base, mao_high
✅ Timestamps: submitted_at, expires_at, responded_at
```

### Notes - 6 fields
```
✅ Content: content text
✅ Source: voice, manual, ai, phone_call, system
✅ Timestamp: created_at
```

### AI Recap - 8 fields
```
✅ Summary: recap_text, voice_summary
✅ Context: recap_context (JSON)
✅ Metadata: version, last_trigger
```

---

## 📈 Analytics Data

### Agent Performance - 14 fields
```
📊 Deals: total_deals, closed_deals, closed_won
💰 Volume: total_volume, average_deal_size, total_profit
⏱️ Speed: average_days_to_close
🎯 Success: best_property_types, best_cities (JSON)
📈 Patterns: success_patterns, failure_patterns (JSON)
```

### Predictions - 11 fields
```
🔮 Type: prediction_type, model_version
📊 Input: input_data (JSON)
📈 Output: predicted_value, confidence_low/high
✅ Actual: actual_value, accuracy_error, directional_correct
```

### Deal Outcomes - 12 fields
```
✅ Result: outcome_type, outcome_date, sale_price
⏱️ Timeline: days_to_close
💵 Terms: buyer_type, financing_type
📉 Pricing: was_listed, original_list_price, price_reductions
📝 Notes: lessons_learned, market_conditions (JSON)
```

### Risk Scores - 13 fields
```
⚠️ Risk Types: title, environmental, market, financial, legal
📊 Overall: overall_risk_score
🛡️ Mitigation: risk_factors, mitigation_strategies (JSON)
```

### Compliance - 61 fields (rules + checks + violations)
```
📋 Rules: 39 fields per rule (state, city, category, severity, etc.)
✅ Checks: 11 fields (passed, failed, warning counts)
❌ Violations: 10 fields (severity, resolution, etc.)
```

---

## 🔄 Automation Data

### Scheduled Tasks - 12 fields
```
⏰ Timing: scheduled_for, due_date
📝 Details: task_type, title, description
🔄 Recurrence: recurrence_rule (JSON)
📊 Metadata: priority, status, metadata (JSON)
```

### Notifications - 15 fields
```
🔔 Type: type (22 types), priority, icon
📝 Content: title, message, data (JSON)
🔗 Links: action_url
✅ Status: is_read, is_dismissed
⏱️ Timestamps: created_at, read_at, dismissed_at
```

### Voice Campaigns - 20 fields (campaigns + targets)
```
📞 Campaign: name, script, target_criteria (JSON)
📊 Stats: total_calls, successful_calls
🎯 Targets: phone_number, call_attempts, outcome
```

### Activity Events - 9 fields
```
🔧 Tool: tool_name, event_type, status
📊 Data: data (JSON), duration_ms
⏱️ Timestamp: timestamp
```

---

## 🧠 AI & Memory Data

### Agent Conversations - 17 fields
```
🤖 Config: model, temperature, max_tokens
📝 Task: task, system_prompt
📊 Execution: status, iterations, tool_calls_count
💬 Output: final_response, tool_calls_made (JSON)
📜 Trace: execution_trace (JSON)
```

### Memory Graph - 15 fields (nodes + edges)
```
🧠 Nodes: node_type, node_key, summary, payload (JSON)
🔗 Edges: source_node_id, target_node_id, relation, weight
```

### Research - 81 fields (properties + jobs + evidence + dossiers)
```
🏠 Properties: address, geo_lat, geo_lng, profile (JSON)
🤖 Jobs: strategy, assumptions, results (JSON)
📋 Evidence: category, claim, source_url, confidence
📁 Dossiers: dossier_type, content (JSON), summary
```

### Comparable Sales - 27 fields (sales + rentals)
```
💰 Sales: sale_price, sale_date, similarity_score
🏠 Rentals: rent, date_listed, similarity_score
📍 Location: address, distance_mi
📊 Details: details (JSON) with full property data
```

### Underwriting - 16 fields
```
📊 ARV: arv_low/base/high
💵 Rent: rent_low/base/high
🔧 Rehab: rehab_tier, rehab_low/high
💰 Offer: offer_low/base/high
📈 Sensitivity: fees (JSON), sensitivity (JSON)
```

---

## 🔧 Configuration Data

### Contract Templates - 20 fields
```
📋 Template: name, category, docuseal_template_id
🎯 Filters: state, city, property_type_filter (JSON)
💰 Price: min_price, max_price
⚙️ Config: auto_attach_on_create, auto_send
👥 Signers: required_signer_roles (JSON), default_recipient_role
```

### Deal Types - 11 fields
```
📝 Config: name, display_name, description
📋 Templates: contract_templates (JSON)
👥 Contacts: required_contact_roles (JSON)
✅ Checklist: checklist (JSON)
🏷️ Tags: compliance_tags (JSON)
```

### Agent Preferences - 7 fields
```
⚙️ Settings: key, value pairs
📝 Description: what each preference does
✅ Status: is_active flag
```

### Skills - 21 fields
```
📦 Package: name, slug, description
📝 Content: instructions, code
👤 Author: author_name, author_email, license
🎯 Metadata: compatibility, allowed_tools (JSON)
📊 Stats: installation_count, average_rating
```

---

## 🏢 Organization Data

### Workspaces - 12 fields
```
🏢 Team: name, owner_email, owner_name
🔑 Access: api_key_hash
⚙️ Settings: settings (JSON)
📊 Limits: subscription_tier, max_agents, max_properties
```

### Agents - 8 fields
```
👤 Identity: name, email, phone
📜 License: license_number
🔑 Access: api_key_hash
🏢 Workspace: workspace_id
```

### Permissions - 14 fields (workspace + command)
```
🔐 Workspace Keys: key_hash, scopes (JSON)
🚦 Command Permissions: command_pattern, permission, reason
```

---

## 📝 Task & History Data

### Todos - 10 fields
```
✅ Task: title, description, status
🎯 Priority: priority
⏰ Due Date: due_date
📊 Progress: completed_at
```

### Conversation History - 7 fields
```
💬 Chat: session_id, role, content
🏠 Property: property_id
📊 Metadata: metadata (JSON)
⏱️ Timestamp: timestamp
```

### Watchlists - 10 fields
```
🔍 Criteria: city, state, property_type
💰 Price: min_price, max_price
🏠 Specs: min_bedrooms, min_bathrooms, min_sqft
✅ Status: is_active
```

---

## 🔗 Data Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                        WORKSPACE                            │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐   │
│  │    AGENTS    │→ │  PROPERTIES   │→ │ ENRICHMENTS  │   │
│  │              │  │               │  │              │   │
│  │ 8 fields     │  │  22 fields    │  │  24 fields   │   │
│  └──────┬───────┘  └───────┬───────┘  └──────────────┘   │
│         │                  │                               │
│         ↓                  ↓                               │
│  ┌──────────┐      ┌───────────────┐                     │
│  │ SKILLS   │      │   CONTACTS    │                     │
│  │ 21 flds  │      │   10 fields   │                     │
│  └──────────┘      └───────┬───────┘                     │
│                           │                               │
│         ┌─────────────────┼─────────────────┐            │
│         ↓                 ↓                 ↓            │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐     │
│  │CONTRACTS │      │  OFFERS  │      │  NOTES   │     │
│  │ 13 flds  │      │ 17 flds  │      │  6 flds  │     │
│  └──────────┘      └──────────┘      └──────────┘     │
│                                                            │
│  Analytics: PERFORMANCE, PREDICTIONS, OUTCOMES           │
│  Automation: TASKS, NOTIFICATIONS, CAMPAIGNS             │
│  Intelligence: RESEARCH, COMPS, UNDERWRITING            │
│  Compliance: RULES, CHECKS, VIOLATIONS                   │
└────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Types Used

| Type | Usage | Example |
|------|-------|---------|
| **INTEGER** | IDs, counts | id, bedrooms |
| **VARCHAR(N)** | Text with limit | address (255), city (100) |
| **FLOAT** | Decimals | price, sqft, latitude |
| **TEXT** | Long text | description, instructions |
| **BOOLEAN** | True/False | is_active, is_required |
| **DATETIME** | Timestamps | created_at, updated_at |
| **DATE** | Dates only | sale_date, effective_date |
| **JSON** | Structured data | score_breakdown, photos array |

---

## 🎯 Key Features by Data

### Property Management
- 22 core fields + 24 Zillow fields + 11 skip trace fields
- Full address, specs, pricing, scoring
- Rich media (photos, schools, history)

### Deal Tracking
- 17 offer fields + 13 contract fields
- Terms, contingencies, MAO analysis
- DocuSeal integration

### AI Intelligence
- 50+ fields in research tables
- Comparable sales/rentals
- Risk scoring, underwriting

### Compliance
- 39 compliance rule fields
- Automated checks
- Violation tracking

### Automation
- 15 notification fields
- 12 task fields
- 20 campaign fields

### Analytics
- 14 performance metrics
- 11 prediction fields
- 12 outcome fields

---

## 📁 Files Created

1. **COMPLETE_DATABASE_SCHEMA.txt** - Full SQL schema (1,107 lines)
2. **ALL_DATABASE_FIELDS.md** - This document
3. **PROPERTY_DATA_REFERENCE.md** - Property-specific fields
4. **NOTES_QUICK_REFERENCE.md** - Notes feature guide

---

## ✅ Summary

Your AI Realtor platform tracks:

- **🏠 50 Database Tables**
- **📊 500+ Data Fields**
- **🔗 80+ Relationships**
- **📈 100+ Indexes**
- **🎯 Every aspect of real estate deals**

From property discovery to closing, every detail is captured, analyzed, and accessible via voice, API, or UI! 🚀
