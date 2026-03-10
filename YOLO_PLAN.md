# YOLO Plan
Goal: Round 7 — Full MCP coverage + disabled feature fixes

## Tasks

- [x] 1. Fix 3 legacy MCP tools (facebook_targeting, property_websites, enhanced_property_videos) — rewritten to register_tool pattern
- [x] 2. Fix broken web_scraper MCP import — re-enabled in __init__.py
- [x] 3. Build 8 new MCP tool modules (todos, compliance, address, approval, document_analysis, context, agents, onboarding)
- [x] 4. Fix duplicate photo_orders import in MCP __init__.py
- [x] 5. Fix disabled timeline router — added missing RenderJobResponse schema, re-enabled import
- [x] 6. Resolve MCP tool name conflicts (context.py vs conversation.py) — deduplicated to 2 unique tools
- [x] 7. Register timeline router in registry.py

## Stats
- MCP tool modules: 62 → 69 (+7 new)
- MCP tools registered: ~313 total
- Disabled features fixed: 4 (timeline, web_scraper, facebook_targeting, property_websites + enhanced_property_videos)

## Completed
- [x] Round 7: Full MCP coverage — 8 new tool modules, 4 legacy fixes, timeline re-enabled
- [x] Round 6: Bug hunt — AttributeError, None crashes, async/sync, ORM column ref bugs
- [x] Round 5: DB indexes, N+1 fixes, pool_recycle, asyncio.sleep, VAPI error handling
- [x] Round 4: Setup security, pipeline dedup (3,067 lines removed), 5 router merges
- [x] Round 3: Security hardening — path traversal, eval(), GAQL injection, hardcoded keys, timeouts, memory leaks
- [x] Round 2: Production audit — SQL injection, bare excepts, dummy embeddings, DB logging, print→logger
- [x] Round 1: 5 Remotion improvements, TypeScript fixes, MCP tools
