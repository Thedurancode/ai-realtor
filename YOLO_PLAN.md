# YOLO Plan
Goal: Production hardening — security, architecture, consolidation

## Tasks

### Security
- [x] 1. Secure setup endpoints — require API key or setup token once platform is configured

### Architecture
- [x] 2. Deduplicate pipeline.py — replaced 39 inline worker methods with imports from workers/ modules (3,896 → 829 lines)

### Router Consolidation
- [x] 3. analytics.py (3 endpoints) → merged into analytics_dashboard.py
- [x] 4. voice_memo.py (2 endpoints) → merged into voice_agent.py
- [x] 5. property_notes.py (3 endpoints) + property_scoring.py (4 endpoints) → merged into property_recap.py
- [x] 6. follow_ups.py (3 endpoints) → merged into follow_up_sequences.py

## Completed
- [x] Round 4: Setup security, pipeline dedup (3,067 lines removed), 5 router merges (93 → 88 routers)
- [x] Round 3: Security hardening — path traversal, eval(), GAQL injection, hardcoded keys, timeouts, memory leaks
- [x] Round 2: Production audit — SQL injection, bare excepts, dummy embeddings, DB logging, print→logger
- [x] Round 1: 5 Remotion improvements, TypeScript fixes, MCP tools
