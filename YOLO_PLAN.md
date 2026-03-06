# YOLO Plan
Goal: Build ClaudeBot system, memory layer, and project organization

## Completed
- [x] Fix YOLO alias (recursive alias → full path to claude binary)
- [x] Build persistent memory system (8 topic files + MEMORY.md index)
- [x] Create CLAUDE.md with session-start learning + end-of-session saving
- [x] Build ClaudeBot — Telegram + Discord bridge to Claude API
  - [x] claude_agent.py — Claude API with tool-calling loop
  - [x] tools.py — 15 tools mapped to AI Realtor REST API
  - [x] telegram_bot.py — Telegram bot
  - [x] discord_bot.py — Discord bot
  - [x] main.py — runs both bots + cron together
- [x] Add cron jobs (morning digest, market scan, evening recap)
- [x] Add heartbeat system (reads HEARTBEAT.md every 30 min, acts on tasks)
- [x] Add HEARTBEAT.md check to CLAUDE.md (Claude Code checks on session start)
- [x] Add project tracking (projects.md in memory)
- [x] Add install.sh + launchd plist for Mac auto-start
- [x] Add Dockerfile for server deployment
- [x] Update codebase_map.md with claudebot/ files
- [x] Update decisions.md with today's architectural choices
- [x] Full verification — all 13 files, 15 tools, 5 crons, 8 memory files passing

## Blocked (needs Ed's API keys)
- [ ] Get Anthropic API key and add to claudebot/.env
- [ ] Create Telegram bot via @BotFather, add token to .env
- [ ] Create Discord bot via Developer Portal, add token to .env
- [ ] Get Telegram chat ID via @userinfobot for cron notifications
- [ ] Start backend + ClaudeBot and test end-to-end

## Status: YOLO COMPLETE — waiting on user input
