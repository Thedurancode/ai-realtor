# Nanobot Skill Preloading Implementation Guide

## Current System Analysis

### How Skills Currently Load

Nanobot has a **progressive loading system** for skills:

1. **Always Skills** - Skills marked with `always: true` are loaded fully into context on startup
   - Example: `memory` skill is always loaded
   - These are included in the system prompt automatically

2. **Available Skills** - Other skills are listed by name/description in the skills summary
   - The agent sees a summary: skill name, description, file location
   - When needed, the agent uses `read_file` to load the full skill content
   - This saves context space but requires an extra step

### Current Skill Locations

**Builtin Skills** (in `nanobot/nanobot/skills/`):
- `memory` - Two-layer memory system (always: true)
- `cron` - Schedule reminders and recurring tasks
- `github` - GitHub CLI integration
- `tmux` - Terminal multiplexer
- `weather` - Weather information
- `clawhub` - ClawHub integration
- `skill-creator` - Create new skills
- `summarize` - Summarization tools

**Workspace Skills** (in `~/.nanobot/workspace/skills/`):
- Custom skills can be added here
- Override builtin skills if same name

### Skill Loading Flow

```
1. Agent Loop starts
   ↓
2. ContextBuilder.build_system_prompt()
   ↓
3. SkillsLoader.get_always_skills()
   - Scans all skills (builtin + workspace)
   - Checks for `always: true` in frontmatter
   - Filters by requirements (bins, env vars)
   ↓
4. SkillsLoader.load_skills_for_context(always_skills)
   - Loads full content of always skills
   ↓
5. SkillsLoader.build_skills_summary()
   - Lists ALL available skills (with availability status)
   - Shows name, description, location, requirements
   ↓
6. System prompt assembled with:
   - Identity
   - Bootstrap files
   - Memory context
   - Always skills (full content)
   - Skills summary (progressive loading)
```

### Example Skill Structure

```yaml
---
name: github
description: "Interact with GitHub using the `gh` CLI"
metadata: {
  "nanobot": {
    "emoji": "🐙",
    "requires": {"bins": ["gh"]},
    "install": [...]
  }
}
always: false  # Set to true to preload
---

# GitHub Skill
...content...
```

## Problem

When nanobot first launches, only `always: true` skills are loaded. Other skills need to be manually read by the agent using `read_file`, which:
- Adds an extra tool call step
- Slows down first use of the skill
- Requires the agent to know to read the skill file

## Solution: Configurable Skill Preloading

We can implement **selective preloading** of skills at startup based on configuration.

### Option 1: Environment Variable (Simple)

Set an environment variable with comma-separated skill names to preload:

```bash
export NANOBOT_PRELOAD_SKILLS="github,cron,tmux,weather"
```

### Option 2: Configuration File (Flexible)

Add a `preload_skills` array to the config file:

```yaml
# ~/.nanobot/config.yaml
agents:
  defaults:
    workspace: ~/.nanobot/workspace

skills:
  preload:
    - github
    - cron
    - tmux
    - weather
    - clawhub
  # Or use patterns:
  preload_patterns:
    - "github"
    - "cron"
    - "tmux"
```

### Option 3: Auto-Detect High-Value Skills (Smart)

Automatically preload skills based on:
- `always: true` (current behavior)
- Skills that have no requirements (safe to load)
- Skills with met requirements

## Implementation

### Files to Modify

1. **`nanobot/nanobot/config/schema.py`**
   - Add `preload_skills` configuration

2. **`nanobot/nanobot/agent/skills.py`**
   - Add `get_preload_skills()` method to check config

3. **`nanobot/nanobot/agent/context.py`**
   - Include preload skills alongside always skills

### Proposed Implementation

#### Step 1: Update Config Schema

```python
# In nanobot/config/schema.py

class SkillsConfig(Base):
    """Skills configuration."""

    preload: list[str] = Field(default_factory=list)  # Skills to preload at startup
    preload_available: bool = True  # Auto-preload skills with met requirements

class ToolsConfig(Base):
    """Tools configuration."""

    web: WebToolsConfig = Field(default_factory=WebToolsConfig)
    exec: ExecToolConfig = Field(default_factory=ExecToolConfig)
    restrict_to_workspace: bool = False
    mcp_servers: dict[str, MCPServerConfig] = Field(default_factory=dict)
    skills: SkillsConfig = Field(default_factory=SkillsConfig)  # Add this
```

#### Step 2: Update SkillsLoader

```python
# In nanobot/agent/skills.py

class SkillsLoader:
    def __init__(self, workspace: Path, builtin_skills_dir: Path | None = None, preload_config: list[str] | None = None):
        # ... existing code ...
        self.preload_config = preload_config or []

    def get_preload_skills(self) -> list[str]:
        """
        Get skills marked for preloading that meet requirements.

        Combines:
        1. Skills marked with always=true
        2. Skills configured in preload list
        """
        result = []

        # Always skills (existing behavior)
        for s in self.list_skills(filter_unavailable=True):
            meta = self.get_skill_metadata(s["name"]) or {}
            skill_meta = self._parse_nanobot_metadata(meta.get("metadata", ""))
            if skill_meta.get("always") or meta.get("always"):
                result.append(s["name"])

        # Configured preload skills
        for skill_name in self.preload_config:
            if skill_name not in result:
                # Check if skill exists and requirements are met
                if self.load_skill(skill_name) and self._check_requirements(self._get_skill_meta(skill_name)):
                    result.append(skill_name)

        return result
```

#### Step 3: Update ContextBuilder

```python
# In nanobot/agent/context.py

class ContextBuilder:
    def __init__(self, workspace: Path, preload_skills: list[str] | None = None):
        self.workspace = workspace
        self.memory = MemoryStore(workspace)
        self.skills = SkillsLoader(workspace, preload_config=preload_skills)

    def build_system_prompt(self, skill_names: list[str] | None = None) -> str:
        """
        Build the system prompt from bootstrap files, memory, and skills.
        """
        parts = []

        # Core identity
        parts.append(self._get_identity())

        # Bootstrap files
        bootstrap = self._load_bootstrap_files()
        if bootstrap:
            parts.append(bootstrap)

        # Memory context
        memory = self.memory.get_memory_context()
        if memory:
            parts.append(f"# Memory\n\n{memory}")

        # Skills - preload skills (includes always + configured)
        preload_skills = self.skills.get_preload_skills()
        if preload_skills:
            preload_content = self.skills.load_skills_for_context(preload_skills)
            if preload_content:
                parts.append(f"# Active Skills\n\n{preload_content}")

        # Available skills: only show summary (agent uses read_file to load)
        # Exclude already loaded skills from summary
        all_skills = self.skills.list_skills(filter_unavailable=False)
        remaining_skills = [s for s in all_skills if s["name"] not in preload_skills]

        if remaining_skills:
            # Build skills summary for remaining skills only
            skills_summary = self._build_skills_summary(remaining_skills)
            if skills_summary:
                parts.append(f"""# Additional Skills

The following skills extend your capabilities. To use a skill, read its SKILL.md file using the read_file tool.
Skills with available="false" need dependencies installed first - you can try installing them with apt/brew.

{skills_summary}""")

        return "\n\n---\n\n".join(parts)

    def _build_skills_summary(self, skills: list[dict]) -> str:
        """Build skills summary for a specific list of skills."""
        if not skills:
            return ""

        def escape_xml(s: str) -> str:
            return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        lines = ["<skills>"]
        for s in skills:
            name = escape_xml(s["name"])
            path = s["path"]
            desc = escape_xml(self._get_skill_description(s["name"]))
            skill_meta = self._get_skill_meta(s["name"])
            available = self._check_requirements(skill_meta)

            lines.append(f"  <skill available=\"{str(available).lower()}\">")
            lines.append(f"    <name>{name}</name>")
            lines.append(f"    <description>{desc}</description>")
            lines.append(f"    <location>{path}</location>")

            if not available:
                missing = self._get_missing_requirements(skill_meta)
                if missing:
                    lines.append(f"    <requires>{escape_xml(missing)}</requires>")

            lines.append(f"  </skill>")
        lines.append("</skills>")

        return "\n".join(lines)
```

#### Step 4: Update AgentLoop Initialization

```python
# In nanobot/agent/loop.py

class AgentLoop:
    def __init__(
        self,
        bus: MessageBus,
        provider: LLMProvider,
        workspace: Path,
        # ... existing params ...
        preload_skills: list[str] | None = None,
    ):
        # ... existing code ...
        self.context = ContextBuilder(workspace, preload_skills=preload_skills)
        # ... rest of init ...
```

## Usage Examples

### Method 1: Environment Variable

```bash
# Set preload skills via environment
export NANOBOT_SKILLS__PRELOAD="github,cron,tmux,weather"

# Start nanobot
python -m nanobot
```

### Method 2: Config File

```yaml
# ~/.nanobot/config.yaml
skills:
  preload:
    - github
    - cron
    - tmux
    - weather
    - clawhub
```

### Method 3: Smart Preload (Recommended)

```yaml
# ~/.nanobot/config.yaml
skills:
  preload_available: true  # Auto-preload all skills with met requirements
```

## Benefits

1. **Faster First Use** - Skills are immediately available without extra `read_file` call
2. **Flexible Configuration** - Choose which skills to preload based on your workflow
3. **Backward Compatible** - Existing behavior (always skills) continues to work
4. **Context Efficient** - Only preload skills you actually use
5. **Smart Defaults** - Option to auto-preload all available skills

## Trade-offs

### Pro
- Faster skill access
- Better user experience
- Configurable based on needs

### Con
- Larger system prompt (more tokens)
- Slightly longer startup time
- Need to manage preload list

## Recommendations

### For Development/General Use
Preload commonly-used skills:
```yaml
skills:
  preload:
    - github    # For repo management
    - cron      # For scheduling
    - tmux      # For terminal sessions
    - memory    # Already always:true
```

### For Minimal Context
Only preload `always` skills (current behavior):
```yaml
skills:
  preload: []
```

### For Maximum Capability
Preload all available skills:
```yaml
skills:
  preload_available: true
```

## Migration Path

1. **Phase 1**: Add config schema support
2. **Phase 2**: Implement `get_preload_skills()` method
3. **Phase 3**: Update ContextBuilder to use preload skills
4. **Phase 4**: Update AgentLoop initialization
5. **Phase 5**: Test and document

## Testing

```python
# Test preload functionality
from nanobot.agent.skills import SkillsLoader

loader = SkillsLoader(workspace=Path("~/.nanobot/workspace"), preload_config=["github", "cron"])
preload = loader.get_preload_skills()
print(f"Preloading skills: {preload}")
# Should output: ['memory', 'github', 'cron']
```

## Next Steps

1. Review this proposal
2. Decide on configuration approach (env var vs config file vs smart)
3. Implement based on chosen approach
4. Test with existing skills
5. Document configuration options
6. Update README with preloading instructions
