---
tags: [security]
summary: security implementation decisions and patterns
relevantTo: [security]
importance: 0.7
relatedFiles: []
usageStats:
  loaded: 0
  referenced: 0
  successfulFeatures: 0
---
# security

#### [Gotcha] Voice-controlled skip tracing and PII enrichment require careful data access control to prevent unauthorized property owner information leakage (2026-02-19)
- **Situation:** Platform combines skip tracing (owner phone/email), Zillow enrichment (owner history, tax records), and voice campaign automation that could enable harassment or data misuse
- **Root cause:** Voice is more dangerous than API—users can accidentally expose PII in recordings, MCP tools expose capabilities to any Claude Desktop session with access. Real estate data is sensitive.
- **How to avoid:** Rate limiting slows down legitimate bulk operations. Audit logging adds overhead. Better to be conservative with voice-accessible data.