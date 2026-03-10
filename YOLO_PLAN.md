# YOLO Plan
Goal: Round 6 — Bug hunt across the codebase

## Tasks

- [x] 1. Audit for AttributeError-class bugs — found & fixed 4: Agent.full_name→name (direct_mail.py x2), contract.docuseal_document_id→docuseal_submission_id, contract.docuseal_signing_url→docuseal_url (portal.py)
- [x] 2. Audit for unhandled None/empty cases — fixed 4: agent_brand.py unguarded .first().name, hybrid_search.py fetchone()[0] x2, sqlite_tuning.py fetchone()[0]
- [x] 3. Audit for async/sync mismatches — fixed vapi_service.py: converted sync requests→httpx.AsyncClient (3 methods)
- [x] 4. Audit for SQL/ORM bugs — portal.py relationship→relationship_type (6 refs, fixed in Round 5)
- [x] 5. Fix all confirmed bugs — all bugs fixed

## Completed
- [x] Round 6: Bug hunt — AttributeError, None crashes, async/sync, ORM column ref bugs
- [x] Round 5: DB indexes, N+1 fixes, pool_recycle, asyncio.sleep, VAPI error handling
- [x] Round 4: Setup security, pipeline dedup (3,067 lines removed), 5 router merges
- [x] Round 3: Security hardening — path traversal, eval(), GAQL injection, hardcoded keys, timeouts, memory leaks
- [x] Round 2: Production audit — SQL injection, bare excepts, dummy embeddings, DB logging, print→logger
- [x] Round 1: 5 Remotion improvements, TypeScript fixes, MCP tools
