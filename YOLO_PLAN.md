# YOLO Plan
Goal: Production hardening — security, performance, reliability fixes

## Tasks

### Security (Critical)
- [x] 1. Remove hardcoded API keys from scripts/manual/diagnose_docuseal.py and tests/manual/test_docuseal_api.py
- [x] 2. Fix path traversal in document_analysis.py — validate file_path is within allowed dirs
- [x] 3. Fix eval() in ai_assistant.py — replaced with ast.parse+compile for safe math-only eval
- [x] 4. Fix GAQL injection in google_ads_mcp.py — validate IDs are numeric, status from allowlist
- [x] 5. Fix uploaded filename path traversal — use os.path.basename() before path join
- [x] 6. Stop leaking str(e) in HTTP 500 responses — use generic messages in document_analysis.py

### Performance (High)
- [x] 7. Add default 30s timeout to MCP http_client.py (central HTTP client used by all tools)
- [x] 8. Add 30s timeout to vapi_service.py requests calls
- [x] 9. Fix N+1 queries in analytics_service.py — replaced enum loops with GROUP BY
- [x] 10. Fix memory leak: prune completed tasks from _background_tasks list in main.py
- [x] 11. Fix memory leak: add TTL eviction to conversation_context.py _contexts dict

### Code Quality (Medium)
- [x] 12. Fix 2 remaining bare excepts in mcp_server/tools/calls.py
- [x] 13. Fix print() statements in activity_logging.py — replaced with logger

## Completed
- [x] Round 3: Security hardening — path traversal, eval(), GAQL injection, hardcoded keys, timeouts, memory leaks
- [x] Round 2: Production audit — SQL injection, bare excepts, dummy embeddings, DB logging, print→logger
- [x] Round 1: 5 Remotion improvements, TypeScript fixes, MCP tools
- [x] Before: Transaction Coordinator Agent + Milestone Reminders
- [x] Before: PropertyShowcase outro, custom fonts, TimelineEditor polish
