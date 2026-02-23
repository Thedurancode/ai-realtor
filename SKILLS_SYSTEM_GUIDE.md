# 🎓 Skills System — Complete Guide

## Overview

The Skills System allows AI agents to **learn new capabilities** from community TOML + Markdown packs, inspired by [skills.sh](https://skills.sh) and ZeroClaw's skills system. Think of it as an "App Store for AI Agents" where skills are reusable knowledge packages that extend agent capabilities.

---

## 🎯 What Are Skills?

**Skills** are reusable knowledge packages that:
- Teach agents specialized expertise (negotiation, coaching, compliance)
- Provide step-by-step workflows for complex tasks
- Include best practices, scripts, and templates
- Can be shared across teams and the community
- Are versioned and rateable like software packages

**Examples:**
- `luxury-property-negotiation` — Advanced tactics for $1M+ properties
- `first-time-home-buyer-coach` — Guide new buyers through the process
- `short-sale-expert` — Navigate short sale transactions
- `investment-property-analyzer` — Evaluate rental properties
- `fsbo-converter` — Convert For Sale By Owners to clients

---

## 📁 Skill Package Format

### **Option 1: SKILL.md (Markdown + YAML frontmatter)**

```markdown
---
name: luxury-negotiation
description: Advanced negotiation tactics for luxury properties
license: MIT
metadata:
  author: Your Name
  version: 1.0.0
  category: negotiation
  tags: [luxury, high-value, sales]
  allowed-tools: [send_contract, create_offer, counter_offer]
---

# Luxury Property Negotiation

## Overview
[Your instructions here...]
```

### **Option 2: skill.toml (TOML + separate markdown)**

```toml
name = "first-time-buyer-coach"
description = "Specialized guidance for first-time buyers"
version = "1.0.0"
author = "AI Realtor Platform"
license = "MIT"
category = "buyer-coaching"
tags = ["education", "guidance", "first-time"]

allowed_tools = ["get_property", "calculate_deal", "get_comps_dashboard"]

instructions_file = "INSTRUCTIONS.md"
```

---

## 🚀 Quick Start

### **1. Browse the Skills Marketplace**

```bash
GET /skills/marketplace

Response:
{
  "total_skills": 25,
  "skills": [
    {
      "id": 1,
      "name": "luxury-negotiation",
      "description": "Advanced negotiation tactics...",
      "category": "negotiation",
      "version": "1.0.0",
      "installation_count": 150,
      "average_rating": 5
    }
  ]
}
```

---

### **2. Install a Skill**

```bash
POST /skills/install

{
  "skill_name": "luxury-negotiation",
  "agent_id": 2
}

Response:
{
  "status": "installed",
  "skill": {
    "id": 1,
    "name": "luxury-negotiation"
  }
}
```

---

### **3. Use the Skill**

When the AI agent assists you, it now has access to the skill's knowledge:

```
Agent: "I see you're working on a luxury property at $2.4M.
Based on my luxury-negotiation skill, here's my recommended
approach for multiple offers..."
```

---

### **4. View Installed Skills**

```bash
GET /skills/installed/2

Response:
{
  "agent_id": 2,
  "total_skills": 3,
  "skills": [
    {
      "name": "luxury-negotiation",
      "description": "Advanced tactics..."
    },
    {
      "name": "first-time-buyer-coach",
      "description": "Guidance for new buyers..."
    }
  ]
}
```

---

## 📡 API Endpoints

### **Browse Skills**

```bash
GET /skills/marketplace?query=negotiation&category=sales
```

**Parameters:**
- `query` — Search in name, description, tags
- `category` — Filter by category
- `tag` — Filter by tag

---

### **Install Skill**

```bash
POST /skills/install

{
  "skill_name": "luxury-negotiation",
  "agent_id": 2,
  "config": {}  # Optional config
}
```

---

### **Uninstall Skill**

```bash
DELETE /skills/uninstall/luxury-negotiation?agent_id=2
```

---

### **Get Skill Instructions**

```bash
GET /skills/instructions/2?skill_name=luxury-negotiation
```

**Returns:** Combined markdown with all skill instructions for AI context.

---

### **Get Skill Detail**

```bash
GET /skills/detail/luxury-negotiation
```

**Returns:** Full skill details including instructions, reviews, ratings.

---

### **Rate a Skill**

```bash
POST /skills/rate/luxury-negotiation

{
  "agent_id": 2,
  "rating": 5,
  "review": "Excellent strategies for luxury deals!"
}
```

---

### **Create Custom Skill**

```bash
POST /skills/create

{
  "name": "my-custom-workflow",
  "description": "My specialized process",
  "instructions": "# Instructions\n...",
  "category": "custom",
  "tags": ["workflow"],
  "allowed_tools": ["get_property"]
}
```

---

### **Discover Skills from Directory**

```bash
GET /skills/discover
```

**Returns:** Skills found in `skills/` folder.

---

### **Sync Skills to Database**

```bash
POST /skills/sync
```

Imports any new skills from `skills/` folder into the database.

---

## 🎨 Creating Your Own Skills

### **Step 1: Create Skill Directory**

```bash
mkdir -p skills/my-custom-skill
cd skills/my-custom-skill
```

---

### **Step 2: Create SKILL.md**

```markdown
---
name: my-custom-skill
description: My specialized workflow for [use case]
license: MIT
metadata:
  author: Your Name
  version: 1.0.0
  category: custom
  tags: [specialized, workflow]
  allowed-tools: [list, of, tools]
---

# My Custom Skill

## Overview
[Brief description of what this skill does]

## When to Use
[When to activate this skill]

## Step-by-Step Process
1. First step...
2. Second step...
3. Third step...

## Templates
[Include scripts, email templates, checklists]

## Common Mistakes to Avoid
[List common pitfalls]

## Quick Reference
| Situation | Action |
|-----------|--------|
| Scenario A | Do X |
| Scenario B | Do Y |
```

---

### **Step 3: Sync to Database**

```bash
POST /skills/sync
```

Your skill is now available in the marketplace!

---

## 📚 Example Skills Included

### **1. Luxury Property Negotiation** (`skills/luxury-negotiation/`)

**Focus:** Advanced negotiation for $1M+ properties

**Key Topics:**
- The Anchor Effect
- Silence as Power
- Give-to-Get Technique
- Creating Scarcity
- Multiple Offer Strategies
- Price Reduction Tactics
- Communication Templates

**MCP Tools:** `send_contract`, `create_offer`, `counter_offer`, `withdraw_offer`

---

### **2. First-Time Home Buyer Coach** (`skills/first-time-buyer-coach/`)

**Focus:** Educating first-time buyers

**Key Topics:**
- Pre-purchase education
- Understanding mortgages
- House hunting strategies
- Making offers
- Under contract process
- Closing preparation
- Common mistakes to avoid

**MCP Tools:** `calculate_deal`, `get_comps_dashboard`, `list_properties`

---

## 🎯 Skill Categories

| Category | Description | Example Skills |
|----------|-------------|----------------|
| **negotiation** | Deal-making strategies | luxury-negotiation, multiple-offers |
| **buyer-coaching** | Buyer education | first-time-buyer-coach, investor-guide |
| **seller-coaching** | Seller strategies | home-staging, pricing-strategy |
| **compliance** | Legal/regulatory | fair-housing, disclosure-requirements |
| **marketing** | Lead generation | social-media, open-house-pro |
| **operations** | Business management | transaction-coordination, admin-workflow |
| **niche** | Specialized markets | commercial, luxury, investment |
| **custom** | Agent-created skills | my-custom-workflow |

---

## 🔧 Skill Metadata

### **Required Fields**

- `name` — Unique skill identifier
- `description` — What the skill does
- `instructions` — Markdown content

### **Optional Fields**

- `version` — Semantic version (1.0.0)
- `author` — Creator name
- `license` — License type (default: MIT)
- `category` — Category for organization
- `tags` — List of tags for search
- `allowed_tools` — MCP tools this skill can use
- `compatibility` — System requirements
- `code` — Optional executable code

---

## 💡 Best Practices

### **1. Clear Structure**

Use consistent headings:
```markdown
## Overview
## When to Use This Skill
## Key Principles
## Step-by-Step Workflows
## Templates/Scripts
## Common Mistakes
## Quick Reference Table
```

---

### **2. Actionable Content**

Include scripts and templates:
```
**Initial Call Script:**
"Hi [Name], this is [Agent] from [Brokerage].
I noticed you're looking at [Property]..."
```

---

### **3. MCP Tool Integration**

List tools at the end:
```markdown
## MCP Tool Integration
When using this skill, you have access to:
- `create_offer` — Draft offers
- `counter_offer` — Generate counters
```

---

### **4. Quick Reference Tables**

```markdown
| Situation | Recommended Approach |
|-----------|---------------------|
| Multiple offers | Set deadline, counter top 2-3 |
| Lowball offer | Counter with data |
| Price reduction | 5-10% decrease, round to psychology |
```

---

### **5. Version Control**

Update version when making changes:
```yaml
version: 1.1.0  # Added new negotiation tactic
```

---

## 🌟 Community Skills Marketplace

In the future, the platform will support:

### **Public Skills Repository**
- Share skills with the community
- Browse community-created skills
- Rate and review skills
- Contribute improvements

### **Installation from GitHub**
```bash
POST /skills/install-from-github

{
  "repo_url": "https://github.com/username/repo",
  "agent_id": 2
}
```

### **Skill Updates**
```bash
POST /skills/update/luxury-negotiation
```

---

## 🎭 How Skills Integrate with AI

### **1. Context Injection**

When an agent has skills installed, the AI receives:

```python
# Get agent's skill instructions
instructions = skills_service.get_skill_instructions(db, agent_id)

# Inject into AI context
system_prompt += f"""

## Installed Skills

{instructions}

When assisting the agent, reference these skills when relevant.
"""
```

---

### **2. Tool Access Control**

Skills specify which MCP tools they can use:

```yaml
allowed_tools:
  - send_contract
  - create_offer
```

The AI only uses these tools when the skill is active.

---

### **3. Progressive Disclosure**

Skills load in layers:
1. **Metadata** — What the skill does
2. **Core Instructions** — Main content
3. **Resources** — Templates, scripts, checklists

This saves tokens and improves performance.

---

## 📊 Skill Statistics

### **Installation Tracking**
- Total installations
- Installations by agent
- Last used timestamp

### **Rating System**
- 1-5 star ratings
- Written reviews
- Average rating calculation

### **Usage Analytics**
- Most installed skills
- Highest-rated skills
- Most-used skills

---

## 🔐 Security & Permissions

### **Public vs Private Skills**
- **Public:** Available to all agents
- **Private:** Only visible to creator

### **Skill Verification**
- Verified skills have been reviewed by platform
- Badge displayed in marketplace

### **Code Execution**
- Skills can include optional Python code
- Code runs in sandboxed environment
- Requires explicit approval

---

## ✅ Summary

**The Skills System provides:**

✅ **Reusable knowledge packages** — Install/uninstall as needed
✅ **Community marketplace** — Browse and install skills
✅ **Custom skill creation** — Create your own workflows
✅ **Version control** — Track updates and improvements
✅ **Rating system** — Find the best skills
✅ **MCP tool integration** — Skills can use platform tools
✅ **Two formats** — SKILL.md or skill.toml
✅ **Progressive disclosure** — Efficient token usage

**Install skills to:**
- Specialize in niche markets
- Streamline workflows
- Ensure consistency
- Train new agents
- Share best practices

**Like an App Store for AI Agents!**

---

Sources:
- [Skills.sh — 61,000+ Skills: AI Agent's "App Store"](https://m.blog.csdn.net/2301_81413380/article/details/158206227)
- [AI Agent Skills: Complete Guide](https://m.blog.csdn.net/2401_85373898/article/details/157902688)
- [GitHub Top Skills Libraries](https://juejin.cn/post/7599852042529619978)

---

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)
