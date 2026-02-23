---
tags: [testing]
summary: testing implementation decisions and patterns
relevantTo: [testing]
importance: 0.7
relatedFiles: []
usageStats:
  loaded: 0
  referenced: 0
  successfulFeatures: 0
---
# testing

#### [Pattern] Fixture-based sample plugin for integration testing instead of mocking (2026-02-19)
- **Problem solved:** Need to test plugin lifecycle (load, execute, unload) with realistic plugin behavior
- **Why this works:** Mocking a plugin doesn't test the real plugin loading machinery - filesystem access, module imports, interface compliance. Real fixture catches integration bugs that mocks miss. Sample plugin also serves as reference implementation for developers
- **Trade-offs:** Gains: integration test fidelity, self-documenting plugin development. Loses: slower tests, more files to maintain