# AI Realtor - Project Instructions

## Memory System (ALWAYS FOLLOW)

You have a persistent memory at `~/.claude/projects/-Users-edduran-Documents-GitHub-ai-realtor/memory/`.

### End-of-Session Learning
At the END of every conversation (or when the user says "done", "bye", "thanks", etc.), you MUST:
1. Reflect on what you learned this session
2. Update the appropriate memory file:
   - `MEMORY.md` — high-level index (keep under 200 lines)
   - `decisions.md` — architectural decisions and why they were made
   - `bugs_and_fixes.md` — bugs encountered and how they were solved
   - `preferences.md` — Ed's coding preferences, style choices, workflow habits
   - `services.md` — API keys, service configs, integration notes
   - `codebase_map.md` — key files, what they do, how they connect
3. Do NOT duplicate — check existing files first and update in place
4. Keep entries concise: what happened, what was decided, what to remember

### Mid-Session Learning
When you discover something important during work, save it immediately:
- A tricky bug fix → `bugs_and_fixes.md`
- A new service integration → `services.md`
- Ed corrects you on a preference → `preferences.md`
- A key architectural choice → `decisions.md`

### Session Start
At the START of every conversation, silently read your memory files to recall context:
1. `MEMORY.md` — quick overview
2. `projects.md` — active projects, what's in progress, what's next
3. `HEARTBEAT.md` — tasks to act on
Do NOT narrate this to the user — just know your history and act on it.

## Project Context
- **Owner**: Ed Duran (Emprezario Inc)
- **Stack**: FastAPI backend + Next.js frontend
- **DB**: PostgreSQL via SQLAlchemy + Alembic migrations
- **Timezone**: America/New_York (always use for scheduling)

## Heartbeat System (ALWAYS CHECK)

At the START of every conversation, silently read `claudebot/HEARTBEAT.md`.
- If there are **Active Tasks**, review each one and take action using available tools.
- Report what you did, what's still pending, and what's done.
- Move completed tasks to the `## Completed` section with a timestamp.
- If the backend/API isn't running, note which tasks need it and skip them.
- Do NOT ask Ed about heartbeat tasks — just handle them quietly unless you need input.

## CRITICAL: Before Ending ANY Session
If the user says anything like "done", "bye", "thanks", "gtg", "that's it", "night", or just stops responding after work is complete — IMMEDIATELY save what you learned before the session ends. Do NOT skip this. This is how you maintain continuity.

## Coding Standards
- Keep it simple. No over-engineering.
- Prefer editing existing files over creating new ones.
- Run tests after changes when possible.
- Use existing patterns in the codebase — don't invent new ones.
