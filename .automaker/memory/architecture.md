---
tags: [architecture]
summary: architecture implementation decisions and patterns
relevantTo: [architecture]
importance: 0.7
relatedFiles: []
usageStats:
  loaded: 1
  referenced: 1
  successfulFeatures: 1
---
# architecture

### MCP server as bridge layer between Claude Desktop and FastAPI backend via HTTP/REST (2026-02-19)
- **Context:** Voice-first AI platform needs natural language interface to real estate operations while maintaining separate backend systems
- **Why:** MCP protocol is Claude Desktop's standard for tool access; exposing 61 tools via MCP allows voice commands directly without building custom Claude integration. HTTP bridge preserves backend REST API for other clients.
- **Rejected:** Direct Claude API integration (loses MCP ecosystem benefits), Claude plugins (deprecated), embedding FastAPI directly in desktop app (deployment and security issues)
- **Trade-offs:** Added HTTP marshalling layer increases latency but gains loose coupling, independent scaling, and standard MCP tool distribution. Protocol overhead is negligible vs I/O operations.
- **Breaking if changed:** Removing MCP server loses Claude Desktop voice control entirely; all 61 voice-commanded tools become inaccessible despite backend API existing

#### [Pattern] 31 specialized MCP tool modules organized by domain (properties, contracts, offers, calls, campaigns, search, reports) rather than generic CRUD (2026-02-19)
- **Problem solved:** Real estate workflow requires domain-specific operations that compose multiple backend services (e.g., offer creation chains, skip tracing, deal analysis)
- **Why this works:** Domain tools align with user mental models and voice interaction patterns. Voice UX requires fewer, more powerful tools over granular CRUD endpoints. Easier to maintain tool documentation and voice prompt engineering.
- **Trade-offs:** More code duplication between MCP tools and backend routers, but vastly better voice UX and clearer domain intent. Requires tooling to keep MCP/API in sync.

### WebSocket support in FastAPI for real-time TV display dashboard updates rather than polling (2026-02-19)
- **Context:** Frontend needs live property updates, call status, campaign results, research progress displayed on Bloomberg Terminal-style display
- **Why:** WebSocket provides true real-time push semantics. Polling would waste resources on idle connections (real estate operations have long gaps). Critical for voice campaign monitoring and deal status.
- **Rejected:** Server-Sent Events (SSE) is one-way, unidirectional, loses backend-to-frontend communication richness; gRPC adds infrastructure complexity; polling is inefficient
- **Trade-offs:** WebSocket connection management adds complexity (reconnection logic, message ordering), but enables interactive features like live call monitoring, real-time research progress, campaign status without polling overhead.
- **Breaking if changed:** Removing WebSocket forces polling, making TV display unusable for real-time monitoring (campaigns, voice calls, research workers)

#### [Gotcha] Voice command latency from Claude Desktop → MCP server → FastAPI → external APIs (Google, Zillow, VAPI, ElevenLabs) can exceed user expectations in real-time voice conversations (2026-02-19)
- **Situation:** Platform integrates with 12+ external services; voice calls require synchronous responses from skip tracing, property enrichment, and deal analysis
- **Root cause:** Real estate operations inherently require external data (Zillow photos, owner contact info, market comps). Voice expects <500ms responses but Zillow RapidAPI, skip tracing, and email sending are I/O bound.
- **How to avoid:** Hybrid approach: fast data cached (Zillow enrichment cache), background workers for enrichment, streaming responses for long operations. Voice conversations accept 'researching...' delays.

### 12+ agentic research workers (voice_goal_planner.py 75KB) that parallelize due diligence instead of sequential property analysis (2026-02-19)
- **Context:** Property due diligence requires market analysis, comparable sales research, neighborhood deep-dive, zoning/development potential, historical research, regulatory checks
- **Why:** Sequential analysis takes 5-10min per property. Parallel workers complete in 60-90sec. Voice users expect rapid turnaround. Each worker is independently useful (market research, regulation checking, comps finding).
- **Rejected:** Single sequential analyzer (simple but slow), traditional property report templates (non-adaptive), requiring human analyst (defeats AI-first vision)
- **Trade-offs:** Parallel workers require coordination, de-duplication, and result synthesis. Higher token cost but massively better user experience. Anthropic's concurrent API calls make this economical.
- **Breaking if changed:** Removing parallel workers reverts to 5-10min analysis times, making voice-first workflow impractical; users abandon mid-analysis

#### [Pattern] Deal calculator with A-F scoring system for wholesale, Fix & Flip, Rental, and BRRRR strategies rather than generic IRR/ROI (2026-02-19)
- **Problem solved:** Real estate investors use fundamentally different analysis criteria per strategy. Wholesale focuses on ARV and acquisition cost. Rentals focus on cash flow and cap rate. BRRRR focuses on refinance equity.
- **Why this works:** Domain-specific calculators encode investor mental models. A-F scoring is familiar from real estate circles. Generic formulas don't capture strategy-specific constraints and opportunities.
- **Trade-offs:** Multiple calculators require maintenance but enable better UX and trust. Scoring system is transparent and tweakable. More code but better domain alignment.

### Next.js 15 frontend as secondary UI (TV display dashboard) rather than primary interface, with Claude Desktop as primary (2026-02-19)
- **Context:** Voice-first platform needs real-time monitoring dashboard for campaigns, calls, research, but primary interaction is voice through Claude Desktop
- **Why:** Voice is primary because it enables multitasking and hands-free operation. Dashboard is secondary for monitoring, status checks, and visual confirmations. Separating concerns prevents UI from blocking backend.
- **Rejected:** Building voice into web frontend (web audio API is limited, no Claude integration), making web primary interface (requires mouse/keyboard contradicts voice-first vision)
- **Trade-offs:** Secondary frontend means users switch context between voice and dashboard, but decouples frontend from backend scaling. WebSocket keeps them synchronized.
- **Breaking if changed:** Removing dashboard forces users to trust voice feedback alone; can't visually verify campaign progress or research completion

#### [Pattern] SQLAlchemy with 37+ data models and Alembic migrations for complex real estate domain with evolving requirements (2026-02-19)
- **Problem solved:** Platform tracks properties, owners, contacts, contracts, offers, deals, research, compliance, campaigns—all with complex relationships and temporal tracking
- **Why this works:** SQLAlchemy enables type-safe ORM with declarative models, automatic migrations preserve schema history. Alembic allows reversible schema changes without data loss.
- **Trade-offs:** SQLAlchemy adds abstraction overhead but gains type safety and automatic schema management. Alembic migrations are slower than downtime-based SQL but safer.

### Extension-based approach: Building plugin system on top of existing MCP server and orchestrator rather than replacing them (2026-02-19)
- **Context:** Need to add 140+ existing tools and 20+ research workers to new agent framework without disrupting production
- **Why:** Existing patterns are proven and entrenched. Replacement would require revalidating all 140+ tools and migrating 20+ worker implementations. Extension allows gradual adoption and rollback
- **Rejected:** Complete rewrite of tool registration and orchestration layers; parallel systems approach
- **Trade-offs:** Gains: backwards compatibility, incremental risk, existing team knowledge preserved. Loses: potential architectural purity, some code duplication during transition period
- **Breaking if changed:** If switched to replacement approach, would need comprehensive regression testing of all 140+ tools and potential service disruptions during migration

### Plugin namespace isolation in MCP server to prevent tool name collisions (2026-02-19)
- **Context:** 140+ existing tools plus new plugin-originated tools could create naming conflicts
- **Why:** MCP tool registry uses flat namespace. Without namespacing, plugin name collisions silently override existing tools, causing silent failures in production that are hard to diagnose
- **Rejected:** No namespacing (rely on naming conventions); separate registries for plugins vs built-in
- **Trade-offs:** Gains: collision detection and clear ownership of tools. Loses: simpler API if no collisions exist. But collisions are likely with 140+ tools and extensibility
- **Breaking if changed:** Removing namespace isolation would require global tool name coordination and risk of production incidents from accidental overrides

#### [Gotcha] Session-based context storage with Redis fallback requires careful TTL management (2026-02-19)
- **Situation:** Multi-turn conversations need to share state between agents; in-memory storage doesn't survive restarts
- **Root cause:** In-memory caching is fast but loses data on deployment. Redis provides persistence. However, expired sessions hanging around consume memory and complicate debugging
- **How to avoid:** Gains: data persistence and horizontal scaling. Loses: additional Redis dependency, complexity of TTL management, potential for stale context bugs

#### [Pattern] Singleton AgentFrameworkService as main entry point following existing LLMService pattern (2026-02-19)
- **Problem solved:** Framework needs to initialize plugin manager, registries, and execution engine once per app startup
- **Why this works:** Existing codebase uses singleton pattern for services (LLMService example). This maintains consistency, ensures single initialization point, and makes dependency injection straightforward. New developers recognize the pattern
- **Trade-offs:** Gains: familiar pattern, simple integration with existing code, single responsibility. Loses: harder to test in isolation, makes async initialization trickier during startup

### Lazy plugin loading (load on first use) instead of eager initialization (2026-02-19)
- **Context:** Framework could have 20+ plugins; early startup is already a bottleneck
- **Why:** Plugins not used during a session waste startup time and memory. Lazy loading keeps startup fast and only loads what's needed. This is critical for voice-first app where latency is user-perceived
- **Rejected:** Eager loading all plugins at startup; async preloading in background
- **Trade-offs:** Gains: faster startup, lower memory footprint, scales to many plugins. Loses: first use of a plugin incurs latency (but acceptable for non-critical paths)
- **Breaking if changed:** Eager loading would slow startup time and impact voice-first user experience; removing lazy loading entirely would break latency requirements

#### [Gotcha] Context sharing between agents requires explicit isolation to prevent accidental shared state mutations (2026-02-19)
- **Situation:** Multi-agent conversation chains need to pass context (property data, conversation history) between steps
- **Root cause:** If agents share references to context objects, one agent's mutations affect downstream agents in unpredictable ways. This causes subtle bugs where agent B receives unexpected state from agent A. Deep copying prevents this but is expensive
- **How to avoid:** Gains: predictable agent behavior, easy debugging. Loses: some performance overhead from copying, complexity of knowing what to copy

### Plugin validation against base interfaces via static analysis tool, not runtime enforcement (2026-02-19)
- **Context:** Plugins are user-developed code; malformed plugins could crash the framework at runtime
- **Why:** Early validation (pre-load) catches errors before agents execute. Static analysis (plugin_validator) gives developers fast feedback without running the plugin. Runtime enforcement requires catching exceptions and gracefully degrading, which hides bugs
- **Rejected:** Runtime validation only; no validation; strict runtime enforcement that blocks plugin loading
- **Trade-offs:** Gains: developer feedback loop, catch errors before agents run. Loses: need to maintain validation logic alongside interface changes
- **Breaking if changed:** No validation would let broken plugins load and fail mid-conversation, degrading user experience; runtime-only validation delays error discovery

#### [Gotcha] Hot reload in development requires thread-safe registry updates without downtime for existing agents (2026-02-19)
- **Situation:** Developers want to reload plugin code without restarting server; existing conversations must not be interrupted
- **Root cause:** Naive reload (lock registry during update) blocks all agent execution while reload happens. This causes visible latency to users. Safe reload requires versioning plugins, running new and old code concurrently during transition, then draining old plugin users
- **How to avoid:** Gains: seamless reload, no user interruption. Loses: complex state management, must track multiple plugin versions

#### [Pattern] Dependency resolver for plugin dependencies placed in plugin lifecycle, not application startup (2026-02-19)
- **Problem solved:** Plugins can depend on other plugins (research agent depends on data enrichment agent)
- **Why this works:** Moving resolution from startup to plugin load time allows dynamic plugin ordering and late binding. Startup doesn't fail if optional plugins are missing. Dependencies are discovered only when actually needed
- **Trade-offs:** Gains: flexible plugin composition, handles optional dependencies. Loses: harder to detect circular dependencies early, more runtime validation needed

### Voice-friendly response aggregation in execution engine rather than leaving to orchestrator (2026-02-19)
- **Context:** Multiple agents in a conversation chain produce structured outputs; final user response must be conversational
- **Why:** Orchestrator shouldn't know about voice formatting - that's a concern of the agent framework. Keeping voice formatting in execution engine allows non-voice clients (API, UI) to get structured responses without conversational wrapping
- **Rejected:** Each agent returns voice-formatted text; orchestrator handles aggregation; no aggregation (raw agent outputs)
- **Trade-offs:** Gains: flexible response formatting, clean separation of concerns. Loses: need to maintain aggregation logic and templates
- **Breaking if changed:** If aggregation is in orchestrator, voice-first design becomes coupled to internal APIs