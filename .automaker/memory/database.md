---
tags: [database]
summary: database implementation decisions and patterns
relevantTo: [database]
importance: 0.7
relatedFiles: []
usageStats:
  loaded: 0
  referenced: 0
  successfulFeatures: 0
---
# database

### pgvector extension for semantic search across properties and research data instead of separate embedding service (2026-02-19)
- **Context:** Platform needs intelligent property matching, skip tracing enrichment, and research correlation based on property characteristics and due diligence findings
- **Why:** pgvector allows semantic search without separate vector database (Pinecone, Weaviate). Simpler deployment, transactions span embeddings + relational data atomically, single source of truth.
- **Rejected:** Separate vector DB (Pinecone, Weaviate) adds operational overhead and eventual consistency issues; traditional SQL search lacks semantic understanding for property matching
- **Trade-offs:** Embedding model runs locally (resource cost) but stays in-process. Scaling becomes database scaling problem rather than distributed systems problem. Query costs higher than dedicated vector DBs for massive scale.
- **Breaking if changed:** Removing pgvector requires re-architecting property matching, research correlation, and personalized property recommendation features to pure keyword search