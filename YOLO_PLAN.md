# YOLO Plan
Goal: Get to 100% production-ready — fix all bugs found in audit

## Tasks
- [x] 1. Fix SQL injection in sqlite_tuning.py — whitelist table names + quote identifiers
- [x] 2. Fix 12 bare except clauses — replaced with specific exceptions across 9 files
- [x] 3. Fix == None patterns — verified these are SQLAlchemy ORM (correct, generates IS NULL)
- [x] 4. Fix hybrid_search.py dummy embeddings — wired up OpenAI text-embedding-3-small
- [x] 5. Fix command_guard.py — persist audit logs to ActivityEvent table
- [x] 6. Fix approval.py — persist approval logs to ActivityEvent table
- [x] 7. Fix compliance_engine.py — wired up Contract model for document verification
- [x] 8. Fix photo_order_service.py — BoxBrownie uses webhooks, added proper logging
- [x] 9. Clean up ~50 print() statements → proper logger calls across 15 files

## Completed
- [x] This round: Production audit — SQL injection, bare excepts, dummy embeddings, DB logging, print→logger
- [x] Previous: 5 Remotion improvements, TypeScript fixes, MCP tools
- [x] Before: Transaction Coordinator Agent + Milestone Reminders
- [x] Before: PropertyShowcase outro, custom fonts, TimelineEditor polish
