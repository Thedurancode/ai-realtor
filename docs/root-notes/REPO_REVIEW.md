# Repository Review — February 28, 2026

## Overview

RealtorClaw is an ambitious AI-powered real estate platform (FastAPI + Next.js) with ~23K lines of code, 458 Python files, 78 routers, 96 services, 56 models, and 12+ external API integrations. The breadth of features is impressive.

---

## Critical Issues

### 1. Leaked API Keys (Severity: CRITICAL)

`.env.bak` is committed to version control with **live production API keys** for:
- Google Places, DocuSeal, Resend, RapidAPI, Exa, Zhipu AI, Telegram Bot, VideoGen, Zuckerbot, Meta/Facebook

These same keys appear hardcoded across **42 files** (docs, scripts, markdown guides).

**Action required:**
- Rotate ALL exposed keys immediately
- Remove `.env.bak` from git history (`git filter-branch` or BFG Repo Cleaner)
- Add `*.bak` to `.gitignore`
- Audit all 42 files and remove hardcoded credentials

### 2. Hardcoded Secret in Portal

`app/routers/portal.py` contains:
```python
SECRET_KEY = "your-secret-key-change-in-production"
```
Move to environment variables.

---

## Architecture Concerns

### Monolithic main.py
- 623 lines acting as a registration dumping ground for 78 routers
- Two separate `@app.on_event("startup")` handlers
- Inline imports scattered between router registrations
- Several features commented out as "temporarily disabled"

**Recommendation:** Group routers into sub-applications or use a registry pattern.

### Unauthenticated Endpoints
- `/cache/stats` and `/cache/clear` bypass API key auth — anyone can clear caches
- WebSocket endpoint (`/ws`) has no authentication
- CORS uses `allow_methods=["*"]` and `allow_headers=["*"]` (overly permissive)

### Database Session Handling
`ApiKeyMiddleware` manually creates/closes DB sessions per request instead of using FastAPI's dependency injection system.

---

## Testing

- **38 test files** for **458 source files** (~8% file coverage)
- 15 tests in `tests/`; 23 scattered at project root
- No CI/CD pipeline for running tests
- No `pytest.ini`, `pyproject.toml`, or `conftest.py` configuration
- No linting configuration (ESLint, flake8, black)

**Recommendation:** Add GitHub Actions CI, consolidate tests into `tests/`, add linting.

---

## Dependency Management

- `requirements.txt` uses loose pins (`>=`) — builds not reproducible
- 40 dependencies with no dev/prod separation
- No lock file (`requirements.lock` or `pip-compile` output)

---

## Docker

- `apt-get update` runs twice in Dockerfile (wasteful)
- Healthcheck pings `/docs` instead of the actual `/health` endpoint
- `COPY scripts ./scripts` copies scripts containing hardcoded API keys into the image

---

## Code Quality

### Strengths
- Clean service layer pattern (routers → services → models)
- Pydantic v2 validation on all inputs
- API key authentication with SHA-256 hashing
- HMAC webhook signature verification
- Rate limiting with configurable tiers
- 32 versioned Alembic migrations
- Credential scrubbing service exists

### Concerns
- 47 `print()` statements instead of `logging`
- No structured/JSON logging for production
- Root-level clutter: diagnostic scripts and status markdown files
- 237 markdown files — many are personal notes rather than docs

---

## Priority Actions

| Priority | Issue | Action |
|----------|-------|--------|
| **P0** | Leaked API keys in 42 files + git history | Rotate keys, scrub history |
| **P0** | `.env.bak` with live credentials | Remove, add to `.gitignore` |
| **P1** | No CI/CD for tests | Add GitHub Actions workflow |
| **P1** | Unauthenticated cache/WebSocket endpoints | Add auth or remove from public paths |
| **P1** | Hardcoded portal SECRET_KEY | Move to env var |
| **P2** | 78 routers in monolithic main.py | Refactor into grouped sub-apps |
| **P2** | Scattered test files at project root | Move to `tests/` directory |
| **P2** | Loose dependency pins | Pin exact versions, add lock file |
| **P3** | Root-level status markdown files | Move to `docs/` or remove |
| **P3** | `print()` statements | Replace with logging module |
| **P3** | Duplicate Dockerfile apt-get | Consolidate RUN layers |
