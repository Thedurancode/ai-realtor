---
tags: [api]
summary: api implementation decisions and patterns
relevantTo: [api]
importance: 0.7
relatedFiles: []
usageStats:
  loaded: 0
  referenced: 0
  successfulFeatures: 0
---
# api

#### [Pattern] Contract management router (66KB) combines document lifecycle, signature workflow, party management, and negotiation history in single module (2026-02-19)
- **Problem solved:** Real estate contracts are complex multi-party documents with e-signature, counter-offers, contingency tracking, and compliance requirements
- **Why this works:** Contracts are inseparable from offers, properties, and compliance state. Keeping related operations together prevents service boundary mismatches. DocuSeal integration is contract-specific.
- **Trade-offs:** Single large module (66KB) is harder to understand but eliminates temporal coupling issues. All contract state changes are transactionally consistent. Trade readability for correctness.

### 40+ FastAPI routers with 223 endpoints organized by business domain (properties, contracts, offers, leads) rather than by CRUD operation (2026-02-19)
- **Context:** Real estate platform has complex multi-step workflows (offer creation → negotiation → signing) and complex queries (property search with filters, research correlation)
- **Why:** Domain routers align with mental models and API documentation. Users think 'create offer' not 'POST /offers'. Easier to find and maintain related endpoints.
- **Rejected:** Generic CRUD routers (properties_crud.py, contracts_crud.py - loses workflow semantics), monolithic single router (unmaintainable at 223 endpoints), REST sub-resource nesting (confusing URL structures)
- **Trade-offs:** More routers to import/configure but much clearer API organization. Requires discipline to prevent duplicate business logic across routers.
- **Breaking if changed:** Flattening to monolithic router makes 223 endpoints impossible to navigate or maintain

### Standardized execute() method signature across all agents with AgentRequest/AgentResponse objects (2026-02-19)
- **Context:** Framework orchestrates diverse agents (property analysis, research workers, etc.) in conversation chains
- **Why:** Loose coupling - orchestrator doesn't know agent internals. Standard interface allows orchestrator to invoke any agent without special cases. AgentRequest/Response allows context threading and error propagation without coupling
- **Rejected:** Agent-specific execute signatures; kwargs-based flexibility; streaming responses only
- **Trade-offs:** Gains: composability, type safety, easy testing. Loses: flexibility for agents with unique signatures (mitigated by AgentRequest.metadata extensibility)
- **Breaking if changed:** Removing standardization would require orchestrator to know each agent's API, making adding new agents expensive and error-prone