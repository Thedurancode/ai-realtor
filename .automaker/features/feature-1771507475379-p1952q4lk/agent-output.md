I'll explore this codebase to understand its structure and purpose. Let me start by examining the top-level directory and key configuration files.

🔧 Tool: Bash
Input: {
  "command": "ls -la",
  "description": "List top-level directory contents"
}

🔧 Tool: Glob
Input: {
  "pattern": "**/*.json"
}

🔧 Tool: Glob
Input: {
  "pattern": "**/*.md"
}
Let me read the main documentation files and explore the core structure of the application:

🔧 Tool: Read
Input: {
  "file_path": "/Users/edduran/Documents/GitHub/ai-realtor/README.md"
}

🔧 Tool: Read
Input: {
  "file_path": "/Users/edduran/Documents/GitHub/ai-realtor/CODEBASE_STRUCTURE.md"
}

🔧 Tool: Bash
Input: {
  "command": "ls -la /Users/edduran/Documents/GitHub/ai-realtor/app",
  "description": "List app directory contents"
}

🔧 Tool: Bash
Input: {
  "command": "ls -la /Users/edduran/Documents/GitHub/ai-realtor/mcp_server",
  "description": "List MCP server directory contents"
}
Let me continue exploring the key components:

🔧 Tool: Bash
Input: {
  "command": "ls -la /Users/edduran/Documents/GitHub/ai-realtor/app/routers",
  "description": "List routers directory"
}

🔧 Tool: Bash
Input: {
  "command": "ls -la /Users/edduran/Documents/GitHub/ai-realtor/app/services",
  "description": "List services directory"
}

🔧 Tool: Bash
Input: {
  "command": "ls -la /Users/edduran/Documents/GitHub/ai-realtor/app/models",
  "description": "List models directory"
}

🔧 Tool: Bash
Input: {
  "command": "ls -la /Users/edduran/Documents/GitHub/ai-realtor/frontend/src 2>/dev/null || ls -la /Users/edduran/Documents/GitHub/ai-realtor/frontend",
  "description": "List frontend directory"
}
Now let me examine the MCP tools and the main application file to understand the voice control and AI integration better:

🔧 Tool: Bash
Input: {
  "command": "ls -la /Users/edduran/Documents/GitHub/ai-realtor/mcp_server/tools",
  "description": "List MCP tools directory"
}

🔧 Tool: Read
Input: {
  "file_path": "/Users/edduran/Documents/GitHub/ai-realtor/app/main.py"
}

🔧 Tool: Read
Input: {
  "file_path": "/Users/edduran/Documents/GitHub/ai-realtor/requirements.txt"
}
Let me also explore the frontend structure and a sample MCP tool file:

🔧 Tool: Bash
Input: {
  "command": "ls -la /Users/edduran/Documents/GitHub/ai-realtor/frontend/app",
  "description": "List frontend app directory"
}

🔧 Tool: Bash
Input: {
  "command": "ls -la /Users/edduran/Documents/GitHub/ai-realtor/frontend/components",
  "description": "List frontend components"
}

🔧 Tool: Read
Input: {
  "file_path": "/Users/edduran/Documents/GitHub/ai-realtor/mcp_server/tools/properties.py"
}
Now I have a comprehensive understanding of the codebase. Let me provide a complete summary:

<summary>
## Summary: Codebase Exploration - AI Realtor Platform

### Overview

This is a **voice-first AI real estate management platform** called "AI Realtor" that handles the entire property lifecycle through natural language. It's a sophisticated full-stack application designed to be controlled primarily through Claude Desktop via the Model Context Protocol (MCP).

### Architecture

```
┌─────────────────────────────────────────┐
│         Claude Desktop (Voice)          │
└───────────────┬─────────────────────────┘
                │ MCP Protocol
                ▼
┌─────────────────────────────────────────┐
│      MCP Server (Python) - 61 Tools     │
│   31 tool modules in mcp_server/tools/  │
└───────────────┬─────────────────────────┘
                │ HTTP/REST API
                ▼
┌─────────────────────────────────────────┐
│        FastAPI Backend (Python)         │
│  • 40+ routers (223 endpoints)          │
│  • 51+ services                         │
│  • 37+ models (SQLAlchemy)              │
│  • PostgreSQL + pgvector                │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  External APIs (12 integrations)        │
│  Google, Zillow, DocuSeal, VAPI,        │
│  ElevenLabs, Resend, Anthropic, etc.    │
└─────────────────────────────────────────┘
```

### Key Components

**Backend (`/app/`):**
- `main.py` - FastAPI app with WebSocket support, 40 routers
- `routers/` - 43 API endpoint modules (contracts.py is 66KB!)
- `services/` - 51 business logic services (voice_goal_planner.py is 75KB)
- `models/` - 37 SQLAlchemy data models
- `schemas/` - Pydantic request/response schemas

**MCP Server (`/mcp_server/`):**
- `server.py` - MCP server implementation
- `tools/` - 31 tool modules exposing 61 voice-controlled tools
- Categories: properties, contracts, offers, research, calls, campaigns, search, reports

**Frontend (`/frontend/`):**
- Next.js 15 with TypeScript
- Real-time TV display dashboard
- Components: BloombergTerminal, TVDisplay, VoiceCompanion, PropertyDetailView
- WebSocket-powered live updates

### Core Features

1. **Property Management** - CRUD with Google Places autocomplete
2. **Zillow Enrichment** - Photos, Zestimate, schools, tax history
3. **Skip Tracing** - Owner discovery and contact info
4. **Contract Management** - DocuSeal e-signature integration, multi-party signing
5. **Offer Engine** - Create, counter, accept, reject offers with negotiation chains
6. **Deal Calculator** - Wholesale, Fix & Flip, Rental, BRRRR analysis with A-F scoring
7. **Agentic Research** - 12+ parallel AI workers for property due diligence
8. **Vector Search** - pgvector semantic search across properties and research
9. **Phone Automation** - VAPI + ElevenLabs voice calls with live tool access
10. **Voice Campaigns** - Bulk outbound calling with retry logic
11. **Compliance Engine** - AI-powered regulatory checks
12. **PDF Reports** - Professional property reports via fpdf2

### Technology Stack

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, pgvector, Alembic
- **AI:** Anthropic Claude, OpenAI Embeddings, GPT-4
- **Voice:** VAPI, ElevenLabs Conversational AI
- **Integrations:** DocuSeal, Resend, Google Places, Zillow (RapidAPI), Exa
- **Frontend:** Next.js 15, TypeScript, Zustand, Framer Motion
- **Infrastructure:** Docker, Fly.io

### Files Summary

| Category | Count | Notes |
|----------|-------|-------|
| API Routers | 43 | `/app/routers/` |
| Services | 51 | `/app/services/` |
| Models | 37 | `/app/models/` |
| MCP Tools | 61 | Across 31 files in `/mcp_server/tools/` |
| API Endpoints | 223 | Documented in README |
| Documentation | 35+ | `.md` files at root |

### Files Modified
- None (exploration only)

### Notes for Developer
- The codebase is production-ready with live deployment at https://ai-realtor.fly.dev
- Voice-first design means all features are accessible via natural language through Claude Desktop
- The MCP server bridges Claude Desktop to the FastAPI backend
- WebSocket support enables real-time TV display updates
- Comprehensive test files exist for various integrations
- Database uses PostgreSQL with pgvector for semantic search capabilities
</summary>