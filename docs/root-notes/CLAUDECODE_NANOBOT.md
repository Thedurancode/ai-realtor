# 🎨 Claude Code in Nanobot Container - Complete Guide

## 📦 What This Does

Preinstalls **Claude Code** (VS Code) inside the Nanobot Linux container with:
- ✅ Default settings optimized for development
- ✅ Pre-installed extensions (Python, Docker, YAML, Git)
- ✅ AI Realtor workspace configuration
- ✅ Convenient command-line aliases
- ✅ Remote access capability

---

## 🚀 Quick Start

### **1. Build with Claude Code**

```bash
cd /Users/edduran/Documents/GitHub/ai-realtor
docker-compose -f docker-compose-claude.yml up -d --build
```

This will:
- Build Nanobot with Claude Code pre-installed
- Start both AI Realtor and Nanobot
- Mount AI Realtor code at `/root/ai_realtor` in Nanobot container

---

### **2. Access Claude Code**

**Option A: Attach to running container**
```bash
# Open terminal in Claude Code
docker exec -it nanobot-gateway bash

# Then launch Claude Code
claude-code
```

**Option B: Open directly (if port 8080 exposed)**
```bash
# From local terminal
code --folder-uri=vscode-remote://ssh-remote/root/ai_realtor
```

**Option C: Use helper script**
```bash
docker exec nanobot-gateway /root/bin/claude-code
```

---

## 🎨 Default Claude Code Configuration

### **Editor Settings**
- Font Size: 14px
- Tab Size: 2 spaces
- Word Wrap: On
- Auto Save: After 1 second
- Format on Save: Enabled
- Minimap: Enabled
- Rulers: 80 & 120 columns

### **Theme**
- Color Theme: One Dark Pro
- Font Family: JetBrains Mono / Fira Code

### **Python Support**
- Python Interpreter: `/usr/bin/python3`
- Linting: Enabled
- Formatting: Black formatter

### **Security**
- Telemetry: **Disabled** (no data sent)
- Auto Update: **Disabled**
- Workspace Trust: Enabled

---

## 🧩 Pre-installed Extensions

| Extension | Purpose |
|-----------|---------|
| `ms-python.python` | Python syntax highlighting, linting |
| `ms-azuretools.vscode-docker` | Docker container management |
| `redhat.vscode-yaml` | YAML syntax highlighting |
| `eamodio.gitlens` | Git supercharged (git blame, etc.) |
| `ms-vscode-remote.remote-ssh` | Remote SSH access |

---

## 🔧 Convenient Aliases

Once inside the container, these aliases are available:

```bash
cc     # Launch Claude Code
cca    # Claude Code → AI Realtor project
ccn    # Claude Code → Nanobot project
cc-ext # List installed extensions

# Project aliases
ai-realtor      # cd to AI Realtor project
ll             # ls -la format
la             # list all files (including hidden)

# Git shortcuts
gs             # git status
ga             # git add
gc             # git commit
gp             # git push
gl             # git log (last 10 commits)

# Python shortcuts
python         # python3
pip            # uv pip install

# Info
container-info  # Show container information
show-workspace  # Show workspace directories
```

---

## 📁 Workspace Setup

### **AI Realtor Project**
- **Path:** `/root/ai_realtor` (mounted read-only)
- Contains: All AI Realtor source code
- Use for: Viewing code, navigating, understanding architecture

### **Nanobot Project**
- **Path:** `/app`
- Contains: Nanobot gateway source code
- Use for: Modifying Nanobot behavior, adding skills

### **How Workspace Works**

When you use `claude-code` or `cca`:
1. Opens Claude Code
2. Loads AI Realtor project automatically
3. All files are read-only (mounted with `:ro`)
4. You can browse, search, and analyze code
5. Changes require modifying source on host

---

## 🌐 Remote Access (Optional)

If you want to access Claude Code from your local machine:

### **Enable Remote SSH**

```bash
# Expose SSH in docker-compose
# Add to nanobot service:
ports:
  - "8080:8080"    # Already exposed in compose file
  - "2222:2222"    # Add this for SSH
environment:
  - SSH_KEY: "your-public-key-here"
```

### **Connect from VS Code**

1. Install "Remote - SSH" extension
2. Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
3. Type: "Remote-SSH: Connect to Host"
4. Enter: `localhost:2222`
5. Username: `root`
6. Password: (container password or key)

---

## 🛠️ Common Use Cases

### **1. Debug Nanobot Issues**
```bash
# Enter container
docker exec -it nanobot-gateway bash

# Launch Claude Code
claude-code

# In Claude Code:
# • Navigate /app (Nanobot source)
# • Set breakpoints
# • Use integrated terminal to run commands
# • Inspect variables
# • View logs in debug console
```

### **2. Understand AI Realtor Architecture**
```bash
docker exec nanobot-gateway claude-code

# In Claude Code:
# • Browse /root/ai_realtor
# • Search for specific functions
# • Read API routes
# • Understand data models
# • View configuration
```

### **3. Modify Nanobot Skills**
```bash
docker exec -it nanobot-gateway bash

# Edit skill configuration
claude-code

# Find and open:
# /root/.nanobot/workspace/skills/ai-realtor/skill.py

# Make changes, then restart Nanobot
docker restart nanobot-gateway
```

### **4. Live Code Analysis**
```bash
# Run Claude Code with debug console
docker exec -it nanobot-gateway bash

# Launch with debug console
code --enable-proposed-api --log debug

# In debug console:
# - Execute Python code
# - Inspect variables
# - Test API calls
# - Run nanobot commands
```

---

## 📊 Container Resource Impact

### **Image Size Comparison**

| Image | Size | Increase |
|-------|------|----------|
| Nanobot (original) | ~500 MB | - |
| Nanobot + Claude Code | ~800 MB | +300 MB |

### **Memory Usage**

Running Claude Code adds:
- RAM: ~100-200 MB (idle)
- CPU: Minimal (when idle)
- Disk: 800 MB image

**Total for both containers:** ~1.5 GB RAM when running Claude Code

---

## 🎯 Best Practices

### **For Development:**
1. Use Claude Code for code analysis only
2. Make changes on host, rebuild container
3. Use read-only mounts to prevent accidental edits
4. Leverage integrated terminal for testing

### **For Debugging:**
1. Attach debugger to running Nanobot process
2. Set breakpoints in Python code
3. Use debug console to execute code
4. Inspect variables and state

### **For Learning:**
1. Browse AI Realtor codebase
2. Understand Nanobot architecture
3. Experiment with AI Realtor API
4. Test MCP tools directly

---

## ⚠️ Limitations

### **Read-Only Access**
- Source code mounted as read-only (`:ro`)
- Changes require editing on host machine
- Must rebuild container to apply changes

### **No Background Tasks**
- Claude Code runs in foreground
- Container must stay running
- Closing Claude Code shuts it down

### **Performance**
- Container needs more resources
- Slower on low-memory machines
- Recommend 4GB+ RAM minimum

---

## 🔧 Build vs Use

### **When to Build with Claude Code:**
✅ Debugging Nanobot issues
✅ Learning codebase architecture
✅ Live code analysis
✅ Development and testing
✅ Educational purposes

### **When to Use Original:**
✅ Production deployment (smaller image)
✅ Resource-constrained environments
✅ Only need chatbot functionality
✅ Don't need code editing

---

## 📝 Summary

**Pros:**
✅ Full VS Code experience in container
✅ Pre-configured with extensions
✅ AI Realtor workspace ready
✅ Great for debugging and learning
✅ Convenient aliases and scripts

**Cons:**
⚠️ Larger image size (+300 MB)
⚠️ Higher resource usage
⚠️ Read-only source code
⚠️ Not for production

---

## 🚀 Getting Started

```bash
# 1. Build with Claude Code
docker-compose -f docker-compose-claudecode.yml up -d --build

# 2. Wait for build (5-10 minutes)

# 3. Check status
docker ps

# 4. Enter container
docker exec -it nanobot-gateway bash

# 5. Launch Claude Code
claude-code

# 6. Start exploring!
```

---

**You now have a full development environment inside your Nanobot container!** 🎨
