---
name: find-skills
description: Discover and install skills from the open agent skills ecosystem (skills.sh and GitHub)
license: MIT
metadata:
  author: AI Realtor Platform (inspired by Vercel Labs)
  version: 1.0.0
  category: productivity
  tags: [skills, discovery, installation, ecosystem, productivity]
  allowed-tools: []
---

# Find Skills

## Overview

This skill helps you discover and install skills from the **open agent skills ecosystem**. It enables agents to extend their capabilities by finding specialized knowledge packages from the community.

## What is the Skills Ecosystem?

The **Skills CLI** (`npx skills`) is the package manager for the open agent skills ecosystem. Skills are modular packages that extend agent capabilities with specialized knowledge, workflows, and tools.

**Key commands:**
```bash
npx skills find [query]           # Search for skills
npx skills add <package>          # Install a skill
npx skills check                  # Check for updates
npx skills update                 # Update installed skills
```

**Browse skills:** https://skills.sh/

---

## When to Use This Skill

Use this skill when the user:

- Asks "how do I do X" where X might be a common task with an existing skill
- Says "find a skill for X" or "is there a skill for X"
- Asks "can you do X" where X is a specialized capability
- Expresses interest in extending agent capabilities
- Wants to search for tools, templates, or workflows
- Mentions they wish they had help with a specific domain (negotiation, marketing, compliance, etc.)

---

## How to Help Users Find Skills

### **Step 1: Understand What They Need**

When a user asks for help, identify:

1. **The domain** — What area is this? (e.g., luxury sales, first-time buyers, investment properties)
2. **The specific task** — What do they want to accomplish? (e.g., negotiate deals, create marketing, analyze investments)
3. **Likelihood of existing skill** — Is this common enough that a skill probably exists?

**Examples:**
- "How do I negotiate luxury deals?" → Domain: negotiation, Task: luxury sales
- "Can you help me with first-time buyers?" → Domain: buyer education, Task: coaching
- "I need to analyze investment properties" → Domain: investment, Task: financial analysis

---

### **Step 2: Search for Skills**

Run the find command with a relevant query:

```bash
npx skills find [query]
```

**Examples:**

| User Request | Search Command |
|--------------|---------------|
| "How do I make my React app faster?" | `npx skills find react performance` |
| "Can you help me with PR reviews?" | `npx skills find pr review` |
| "I need to create a changelog" | `npx skills find changelog` |
| "How do I negotiate luxury deals?" | `npx skills find luxury negotiation` |
| "Help with first-time buyers" | `npx skills find first-time buyer` |

**The command will return results like:**

```
Install with npx skills add <owner/repo@skill>

vercel-labs/agent-skills@vercel-react-best-practices
└ https://skills.sh/vercel-labs/agent-skills/vercel-react-best-practices

ai-realtor/skills@luxury-negotiation
└ https://skills.sh/ai-realtor/skills/luxury-negotiation
```

---

### **Step 3: Present Options to the User**

When you find relevant skills, present them with:

1. **Skill name** and what it does
2. **Install command** they can run
3. **Link** to learn more at skills.sh

**Example response:**

```
I found a skill that might help!

The "luxury-negotiation" skill provides advanced negotiation
tactics for high-value real estate transactions ($1M+),
including the Anchor Effect, multiple offer strategies,
and communication templates.

To install it:
npx skills add ai-realtor/skills@luxury-negotiation

Learn more: https://skills.sh/ai-realtor/skills/luxury-negotiation
```

---

### **Step 4: Offer to Install**

If the user wants to proceed, install the skill:

```bash
npx skills add <owner/repo@skill> -g -y
```

**Flags:**
- `-g` — Install globally (user-level)
- `-y` — Skip confirmation prompts

---

## Common Skill Categories

When searching, consider these common categories:

| Category | Example Queries |
|----------|-----------------|
| **Real Estate Sales** | negotiation, luxury, commercial, fsbo |
| **Buyer Coaching** | first-time buyer, investor, luxury buyer |
| **Marketing** | social media, email marketing, content |
| **Operations** | transaction coordination, admin workflow |
| **Compliance** | fair housing, disclosures, contracts |
| **Technology** | mls, crm, automation |
| **Investment** | rental analysis, flip analysis, cap rate |
| **Development** | web development, api integration |

---

## Popular Skill Sources

When searching, check these popular repositories:

- **ai-realtor/skills** — Real estate-specific skills
- **vercel-labs/agent-skills** — Vercel's agent skills (web dev focused)
- **ComposioHQ/awesome-claude-skills** — Community-curated skills
- **custom skills** — Create your own with `npx skills init`

---

## Tips for Effective Searches

### **1. Use Specific Keywords**

- ✅ Good: `"luxury negotiation"`, `"first-time buyer coaching"`, `"investment analysis"`
- ❌ Bad: `"help"`, `"how to"`, `"tips"`

### **2. Try Alternative Terms**

If `"negotiation"` doesn't work, try:
- `"deals"`
- `"offers"`
- `"counter-offers"`
- `"sales"`

### **3. Check Domain-Specific Sources**

- Real estate → `ai-realtor/skills`
- Web development → `vercel-labs/agent-skills`
- General productivity → `ComposioHQ/awesome-claude-skills`

---

## When No Skills Are Found

If no relevant skill exists:

### **Acknowledge and Offer Direct Help**

```
I searched for skills related to "xyz" but didn't find any matches.

I can still help you with this task directly using my general capabilities!
Would you like me to proceed?

Example: "I don't have a specialized skill for short sales, but I can
guide you through the short sale process step-by-step based on my training."
```

### **Suggest Creating a Custom Skill**

```
If this is something you do often, you could create your own skill:

npx skills init my-xyz-skill

This creates a template skill package that you can customize with your
expertise and share with your team or the community.
```

---

## Integration with AI Realtor Platform

### **1. Platform Skills Marketplace**

The AI Realtor platform has its own skills marketplace:

```bash
# Browse platform skills
GET /skills/marketplace

# Install platform skill
POST /skills/install
{
  "skill_name": "luxury-negotiation",
  "agent_id": 2
}
```

### **2. Hybrid Approach**

Combine both ecosystems:

1. **Platform skills** — Real estate-specific, integrated with MCP tools
2. **Community skills** — General productivity, web dev, automation

**Example workflow:**
```bash
# Search community skills
npx skills find react performance

# Search platform skills
GET /skills/marketplace?query=negotiation

# Install from best source
- Platform skill: luxury-negotiation (real estate specific)
- Community skill: react-best-practices (web dev)
```

### **3. Creating Platform Skills**

To create a skill for the AI Realtor platform:

1. Create skill in `skills/` directory
2. Sync to database:

```bash
POST /skills/sync
```

3. Skill appears in marketplace

---

## Example Conversations

### **Example 1: Finding Negotiation Help**

**User:** "I need help with luxury property negotiations"

**Agent:** "Let me search for skills that can help..."

```bash
npx skills find luxury negotiation
```

**Result:** Found `ai-realtor/skills@luxury-negotiation`

**Response:**
```
I found a skill that might help!

The "luxury-negotiation" skill provides advanced negotiation tactics
for high-value transactions ($1M+), including:
- The Anchor Effect for price positioning
- Silence as Power negotiation technique
- Multiple offer strategies
- Communication templates for buyers/sellers
- Quick reference for common scenarios

Would you like me to install it for you?

To install: npx skills add ai-realtor/skills@luxury-negotiation
Or I can install it to your profile: [Install button]
```

---

### **Example 2: No Skill Found**

**User:** "Is there a skill for short sale transactions?"

**Agent:** "Let me check..."

```bash
npx skills find short sale
```

**Result:** No skills found

**Response:**
```
I searched for skills related to "short sale" but didn't find any
matches in the community ecosystem.

However, I can still help you with short sales! I have training on:
- Short sale process overview
- Lender communication strategies
- Document requirements
- Timeline management
- Common pitfalls to avoid

Would you like me to guide you through a short sale transaction?

Alternatively, if this is something you do frequently, you could
create a custom skill:
npx skills init short-sale-expert
```

---

## Quick Reference

| User Request | Action |
|--------------|--------|
| "Find a skill for X" | `npx skills find X` |
| "How do I do X?" | Search first, then offer direct help if no skill |
| "Can you do X?" | Check skills ecosystem, then general capabilities |
| "Install skill X" | `npx skills add X -g -y` |
| "What skills do you have?" | Browse marketplace: `GET /skills/marketplace` |

---

## Remember

**Skills extend capabilities, but aren't required.**

Even when no skill exists, you can still help users using your general training and knowledge. Skills are specialized add-ons, not replacements for core capabilities.

**The goal:** Find the best skill when available, but always provide value regardless.

---

## Related Skills

- **luxury-negotiation** — Advanced tactics for $1M+ properties
- **first-time-buyer-coach** — Educate new home buyers
- **investment-property-analyzer** — Evaluate rental properties
- **short-sale-expert** — Navigate short sales (create this one!)

---

**Version:** 1.0.0
**Author:** AI Realtor Platform (inspired by Vercel Labs)
**License:** MIT
**Weekly Installs:** 293K (original find-skills skill)
**Repository:** ai-realtor/skills
**Last Updated:** 2026-02-22
