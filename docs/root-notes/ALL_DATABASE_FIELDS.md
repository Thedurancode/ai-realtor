# 🗄️ Complete Database Schema - All Fields Reference

## Database Overview

**Total Tables:** 50
**Database Engine:** SQLite (ai_realtor.db)
**Location:** Docker container at `/app/data/ai_realtor.db`

---

## 📊 All 50 Tables - Quick Reference

| # | Table Name | Purpose | Est. Fields |
|---|-----------|---------|-------------|
| 1 | **properties** | Core property data | 22 |
| 2 | **agents** | Real estate agents | 8 |
| 3 | **contacts** | Property contacts | 10 |
| 4 | **contracts** | Contract documents | 13 |
| 5 | **zillow_enrichments** | Zillow API data | 24 |
| 6 | **skip_traces** | Owner info discovery | 11 |
| 7 | **property_notes** | Knowledge base notes | 6 |
| 8 | **property_recaps** | AI summaries | 8 |
| 9 | **offers** | Property offers | 17 |
| 10 | **comps_sales** | Comparable sales | 14 |
| 11 | **comps_rentals** | Rental comps | 13 |
| 12 | **notifications** | System alerts | 15 |
| 13 | **scheduled_tasks** | Reminders/follow-ups | 12 |
| 14 | **activity_events** | Tool execution logs | 9 |
| 15 | **conversation_history** | Chat history | 7 |
| 16 | **market_watchlists** | Saved searches | 10 |
| 17 | **contract_templates** | Reusable contracts | 20 |
| 18 | **compliance_rules** | Regulatory rules | 39 |
| 19 | **compliance_checks** | Compliance audits | 11 |
| 20 | **compliance_violations** | Rule violations | 10 |
| 21 | **deal_outcomes** | Deal results tracking | 12 |
| 22 | **agent_performance_metrics** | Agent analytics | 14 |
| 23 | **prediction_logs** | ML predictions | 11 |
| 24 | **risk_scores** | Property risk analysis | 13 |
| 25 | **deal_type_configs** | Deal configurations | 11 |
| 26 | **agent_preferences** | Agent settings | 7 |
| 27 | **agent_skills** | Installed skills | 8 |
| 28 | **skills** | Available skills | 21 |
| 29 | **voice_campaigns** | Call campaigns | 11 |
| 30 | **voice_campaign_targets** | Campaign recipients | 9 |
| 31 | **voice_memory_nodes** | Memory graph nodes | 8 |
| 32 | **voice_memory_edges** | Memory graph edges | 7 |
| 33 | **workspaces** | Team workspaces | 12 |
| 34 | **workspace_api_keys** | Workspace keys | 7 |
| 35 | **command_permissions** | Access control | 7 |
| 36 | **todos** | Task management | 10 |
| 37 | **worker_runs** | Background jobs | 9 |
| 38 | **portal_cache** | Web scraping cache | 5 |
| 39 | **research_properties** | Research system | 13 |
| 40 | **research** | Research records | 10 |
| 41 | **research_templates** | Research templates | 19 |
| 42 | **agentic_jobs** | AI agent jobs | 12 |
| 43 | **agent_conversations** | AI conversation logs | 17 |
| 44 | **dossiers** | Property dossiers | 11 |
| 45 | **evidence** | Research evidence | 11 |
| 46 | **underwriting** | Deal underwriting | 16 |
| 47 | **skill_reviews** | Skill reviews | 8 |
| 48 | **compliance_rule_templates** | Rule templates | 7 |
| 49 | **contract_submitters** | Contract signers | 8 |
| 50 | **alembic_version** | Migration tracking | 1 |

**Total Estimated Fields: 500+**

---

## 🏠 Core Property Tables

### 1. properties (22 fields)
```
- id, title, description
- address, city, state, zip_code
- price, bedrooms, bathrooms, square_feet, lot_size, year_built
- property_type, status, deal_type
- agent_id (FK)
- deal_score, score_grade, score_breakdown (JSON)
- pipeline_status, pipeline_started_at, pipeline_completed_at
- created_at, updated_at
```

### 2. zillow_enrichments (24 fields)
```
- id, property_id (FK), zpid
- zestimate, zestimate_low, zestimate_high
- rent_zestimate, living_area, lot_size, lot_area_units
- year_built, home_type, home_status
- days_on_zillow, page_view_count, favorite_count
- property_tax_rate, annual_tax_amount
- photos (JSON), schools (JSON), tax_history (JSON)
- price_history (JSON), reso_facts (JSON)
- description, hdp_url, zillow_url
- raw_response (JSON), created_at, updated_at
```

### 3. skip_traces (11 fields)
```
- id, property_id (FK)
- owner_name, owner_first_name, owner_last_name
- phone_numbers (JSON), emails (JSON)
- mailing_address, mailing_city, mailing_state, mailing_zip
- raw_response (JSON), created_at, updated_at
```

### 4. property_notes (6 fields)
```
- id, property_id (FK), content
- source (voice/manual/ai/phone_call/system)
- created_by, created_at
```

### 5. property_recaps (8 fields)
```
- id, property_id (FK), recap_text, recap_context (JSON)
- voice_summary, version, last_trigger
- created_at, updated_at
```

### 6. contacts (10 fields)
```
- id, property_id (FK), name, first_name, last_name
- role (buyer/seller/lender/etc.)
- phone, email, company, notes
- created_at, updated_at
```

### 7. contracts (13 fields)
```
- id, property_id (FK), contact_id (FK)
- name, description
- docuseal_template_id, docuseal_submission_id, docuseal_url
- status, is_required, required_by_date
- requirement_source, requirement_reason
- sent_at, completed_at, created_at, updated_at
```

### 8. offers (17 fields)
```
- id, property_id (FK), buyer_contact_id (FK), parent_offer_id (FK)
- offer_price, earnest_money, financing_type, closing_days
- contingencies (JSON), notes, status
- is_our_offer
- mao_low, mao_base, mao_high
- submitted_at, expires_at, responded_at
- created_at, updated_at
```

---

## 📊 Analytics & Intelligence Tables

### 9. agent_performance_metrics (14 fields)
```
- id, agent_id (FK)
- period_type, period_start, period_end
- total_deals, closed_deals, closed_won, closing_rate
- total_volume, average_deal_size, total_profit
- average_days_to_close, average_deal_score
- best_property_types (JSON), best_cities (JSON)
- best_price_ranges (JSON), success_patterns (JSON)
- failure_patterns (JSON), created_at
```

### 10. prediction_logs (11 fields)
```
- id, property_id (FK), agent_id (FK)
- prediction_type, model_version, input_data (JSON)
- predicted_value, confidence_low, confidence_high
- actual_value, accuracy_error, directional_correct
- created_at, occurred_at
```

### 11. deal_outcomes (12 fields)
```
- id, property_id (FK), agent_id (FK)
- outcome_type, outcome_date, sale_price
- days_to_close, buyer_type, financing_type
- was_listed, original_list_price, price_reductions
- lessons_learned, market_conditions (JSON)
- created_at
```

### 12. risk_scores (13 fields)
```
- id, research_property_id (FK), job_id (FK)
- title_risk, environmental_risk, market_risk
- financial_risk, legal_risk, overall_risk_score
- risk_factors (JSON), mitigation_strategies (JSON)
- confidence_score, created_at
```

### 13. compliance_checks (11 fields)
```
- id, property_id (FK), agent_id (FK)
- check_type, status
- total_rules_checked, passed_count, failed_count, warning_count
- completion_time_seconds, ai_summary
- created_at, completed_at
```

### 14. compliance_rules (39 fields)
```
- id, state, city, county, applies_to_all_cities
- rule_code, version, parent_rule_id (FK)
- category, subcategory, tags (JSON)
- title, description, legal_citation, source_url
- rule_type, field_to_check, condition, threshold_value
- allowed_values (JSON), ai_prompt, use_ai_fallback
- requires_document, document_type, document_description
- property_type_filter (JSON), min_price, max_price
- min_year_built, max_year_built, severity
- penalty_description, fine_amount_min, fine_amount_max
- how_to_fix, estimated_fix_cost, estimated_fix_time_days
- is_active, is_draft, effective_date, expiration_date
- created_by (FK), created_at, updated_at, last_reviewed_at
- times_checked, times_violated
```

---

## 🔄 Automation & Workflow Tables

### 15. scheduled_tasks (12 fields)
```
- id, property_id (FK), agent_id (FK)
- task_type, title, description
- scheduled_for, due_date, status
- priority, recurrence_rule, metadata (JSON)
- completed_at, created_at
```

### 16. notifications (15 fields)
```
- id, type, priority, title, message
- property_id (FK), contact_id (FK), contract_id (FK), agent_id (FK)
- data (JSON), icon, action_url
- is_read, is_dismissed, created_at
- read_at, dismissed_at, auto_dismiss_seconds
```

### 17. voice_campaigns (11 fields)
```
- id, agent_id (FK), name, campaign_type
- script, target_criteria (JSON), status
- started_at, completed_at, total_calls
- successful_calls, created_at, updated_at
```

### 18. voice_campaign_targets (9 fields)
```
- id, campaign_id (FK), property_id (FK)
- contact_id (FK), phone_number, status
- call_attempts, last_attempt_at, outcome
```

### 19. activity_events (9 fields)
```
- id, timestamp, tool_name, user_source
- event_type, status, data (JSON)
- duration_ms, error_message
```

### 20. worker_runs (9 fields)
```
- id, worker_type, status, started_at
- completed_at, duration_ms, result (JSON)
- error_message, retry_count
```

---

## 🧠 AI & Memory Tables

### 21. agent_conversations (17 fields)
```
- id, template_id (FK), agent_name, task
- property_id (FK), agent_id (FK)
- model, system_prompt, temperature, max_tokens
- status, iterations, tool_calls_count
- final_response, tool_calls_made (JSON)
- execution_trace (JSON), error_message
- started_at, completed_at, created_at
```

### 22. voice_memory_nodes (8 fields)
```
- id, session_id, node_type, node_key
- summary, payload (JSON), importance
- created_at, updated_at, last_seen_at
```

### 23. voice_memory_edges (7 fields)
```
- id, session_id, source_node_id (FK), target_node_id (FK)
- relation, weight, payload (JSON)
- created_at, last_seen_at
```

### 24. research_properties (13 fields)
```
- id, stable_key, raw_address, normalized_address
- city, state, zip_code, apn
- geo_lat, geo_lng, latest_profile (JSON)
- created_at, updated_at
```

### 25. agentic_jobs (12 fields)
```
- id, trace_id, research_property_id (FK)
- status, progress, current_step
- strategy, assumptions (JSON), limits (JSON)
- results (JSON), error_message
- started_at, completed_at, created_at, updated_at
```

### 26. dossiers (11 fields)
```
- id, research_property_id (FK), job_id (FK)
- dossier_type, content (JSON)
- summary, confidence_score
- sources (JSON), created_at, updated_at
```

---

## 📈 Research & Analysis Tables

### 27. comps_sales (14 fields)
```
- id, research_property_id (FK), job_id (FK)
- address, distance_mi, sale_date, sale_price
- sqft, beds, baths, year_built
- similarity_score, source_url, details (JSON)
- is_current, superseded_at, created_at
```

### 28. comps_rentals (13 fields)
```
- id, research_property_id (FK), job_id (FK)
- address, distance_mi, rent, date_listed
- sqft, beds, baths, similarity_score
- source_url, details (JSON)
- is_current, superseded_at, created_at
```

### 29. underwriting (16 fields)
```
- id, research_property_id (FK), job_id (FK)
- strategy, assumptions (JSON)
- arv_low, arv_base, arv_high
- rent_low, rent_base, rent_high
- rehab_tier, rehab_low, rehab_high
- offer_low, offer_base, offer_high
- fees (JSON), sensitivity (JSON)
- is_current, superseded_at, created_at
```

### 30. evidence (11 fields)
```
- id, research_property_id (FK), job_id (FK)
- category, claim, source_url
- captured_at, raw_excerpt, confidence
- hash, created_at
```

---

## 🔧 Configuration & Settings Tables

### 31. contract_templates (20 fields)
```
- id, name, description, category
- requirement, docuseal_template_id, docuseal_template_name
- state, city, property_type_filter (JSON)
- min_price, max_price, deal_type_filter (JSON)
- auto_attach_on_create, auto_send
- default_recipient_role, required_signer_roles (JSON)
- message_template, is_active, priority
- created_at, updated_at
```

### 32. deal_type_configs (11 fields)
```
- id, name, display_name, description
- is_builtin, is_active
- contract_templates (JSON), required_contact_roles (JSON)
- checklist (JSON), compliance_tags (JSON)
- created_at, updated_at
```

### 33. agent_preferences (7 fields)
```
- id, agent_id (FK), key, value
- description, is_active
- created_at, updated_at
```

### 34. agent_skills (8 fields)
```
- id, agent_id (FK), skill_id (FK)
- config (JSON), is_enabled, notes
- installed_at, last_used_at
```

### 35. skills (21 fields)
```
- id, name, slug, description, skill_metadata (JSON)
- instructions, code, version
- author_name, author_email, license
- compatibility (JSON), allowed_tools (JSON)
- is_public, is_verified, is_featured
- category, tags (JSON), github_repo
- installation_count, average_rating, rating_count
- created_at, updated_at
```

### 36. research_templates (19 fields)
```
- id, name, description, category, icon
- research_type, ai_prompt_template, ai_system_prompt
- ai_model, ai_temperature, ai_max_tokens
- api_endpoints (JSON), research_parameters (JSON)
- is_system_template, is_active, execution_count
- agent_name, agent_expertise
- created_at, updated_at
```

---

## 🏢 Workspace & Access Tables

### 37. workspaces (12 fields)
```
- id, name, owner_email, owner_name
- api_key_hash, settings (JSON), is_active
- subscription_tier, max_agents, max_properties
- created_at, updated_at, deleted_at
```

### 38. workspace_api_keys (7 fields)
```
- id, workspace_id (FK), name, key_hash
- scopes (JSON), is_active, expires_at
- created_at
```

### 39. command_permissions (7 fields)
```
- id, workspace_id (FK), agent_id (FK)
- command_pattern, permission, reason
- created_by (FK), created_at
```

### 40. agents (8 fields)
```
- id, email, name, phone, license_number
- api_key_hash, workspace_id (FK)
- created_at, updated_at
```

---

## 📝 Task & History Tables

### 41. todos (10 fields)
```
- id, property_id (FK), agent_id (FK)
- title, description, status
- priority, due_date, completed_at
- created_at, updated_at
```

### 42. conversation_history (7 fields)
```
- id, session_id, property_id (FK)
- role, content, metadata (JSON)
- timestamp
```

### 43. market_watchlists (10 fields)
```
- id, agent_id (FK), name, is_active
- city, state, property_type
- min_price, max_price, min_bedrooms, min_bathrooms, min_sqft
- created_at, updated_at
```

---

## 🔍 Utility & Cache Tables

### 44. portal_cache (5 fields)
```
- id, url_hash, source_url, raw_html
- captured_at, expires_at
```

### 45. compliance_rule_templates (7 fields)
```
- id, name, description, rule_type
- template_json (JSON), category, created_at
```

### 46. contract_submitters (8 fields)
```
- id, contract_template_id (FK), role, name
- email, phone, company, default_order
```

### 47. skill_reviews (8 fields)
```
- id, skill_id (FK), agent_id (FK)
- rating, review, verified_purchase
- created_at, updated_at
```

### 48. compliance_violations (10 fields)
```
- id, property_id (FK), agent_id (FK)
- rule_id (FK), severity, violation_details (JSON)
- detected_at, resolved_at, resolution_notes
- created_at, updated_at
```

### 49. alembic_version (1 field)
```
- version_num
```

### 50. research (10 fields)
```
- id, property_id (FK), template_id (FK)
- status, research_type, query, results (JSON)
- started_at, completed_at, error_message
- created_at, updated_at
```

---

## 📊 Field Types Summary

### Data Types Used
- **INTEGER** - IDs, counts, numeric values
- **VARCHAR(N)** - Text with max length
- **FLOAT** - Decimal numbers (prices, scores, coordinates)
- **TEXT** - Unlimited text (descriptions, JSON)
- **BOOLEAN** - True/false flags
- **DATETIME** - Timestamps
- **DATE** - Dates without time
- **JSON** - Structured data arrays/objects

### Special Fields
- **Primary Keys** - `id` in all tables
- **Foreign Keys** - Link related tables
- **Indexes** - Performance optimization
- **Unique Constraints** - Prevent duplicates
- **Defaults** - Auto-populated values

---

## 🔗 Relationships Summary

### Property-Centric
```
property (1) → (0-1) zillow_enrichment
property (1) → (0-many) skip_traces
property (1) → (0-many) contacts
property (1) → (0-many) contracts
property (1) → (0-many) notes
property (1) → (0-1) recap
property (1) → (0-many) offers
property (1) → (0-many) comps_sales
property (1) → (0-many) comps_rentals
```

### Agent-Centric
```
agent (1) → (0-many) properties
agent (1) → (0-many) performance_metrics
agent (1) → (0-many) prediction_logs
agent (1) → (0-many) notifications
agent (1) → (0-many) watchlists
```

### System Tables
- workspaces → agents → properties
- skills → agent_skills
- contract_templates → contracts
- compliance_rules → compliance_checks

---

## 📈 Statistics

- **Total Tables:** 50
- **Total Fields:** ~500+
- **Foreign Key Relationships:** 80+
- **Indexes:** 100+
- **JSON Columns:** 50+ (flexible schema)
- **Lookup Tables:** 10+ (enums, configs)

---

## 📁 Complete Schema File

The full database schema has been saved to:
**`COMPLETE_DATABASE_SCHEMA.txt`**

This file contains:
- All CREATE TABLE statements
- All field definitions
- All indexes
- All foreign key relationships
- All constraints

Use it for:
- Database migrations
- Schema documentation
- API integration planning
- Data analysis

---

## 🎯 Key Takeaways

1. **500+ Data Fields** across 50 tables
2. **Property-centric design** - everything links to properties
3. **Rich JSON columns** for flexible data storage
4. **Comprehensive tracking** - activities, history, performance
5. **AI-powered features** - predictions, research, recommendations
6. **Compliance built-in** - rules, checks, violations
7. **Multi-tenant** - workspaces and agents
8. **Audit trail** - created/updated timestamps everywhere

This is a **production-grade real estate CRM platform** with enterprise-level data architecture! 🚀
