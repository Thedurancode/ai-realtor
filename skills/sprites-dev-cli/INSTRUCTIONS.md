# Sprites.dev CLI

## Overview

**Sprites.dev** is a cloud development environment platform (similar to GitHub Codespaces) that provides instant, ephemeral development environments in the cloud. It's built on Fly.io infrastructure.

**Key Features:**
- ☁️ Instant cloud dev environments
- 🔄 Checkpoint/snapshot system
- 🐚 Shell access via CLI
- 🔀 Port forwarding/proxy
- 🔐 Built-in authentication
- 📦 Persistent storage with restore capability

---

## What is a Sprite?

A **Sprite** is a cloud development environment that includes:
- Full Linux environment
- Your code and dependencies
- Network access
- Persistent storage
- Checkpoint/restore capability

---

## Installation

The CLI is already installed:

```bash
# Location
~/.local/bin/sprite

# Verify installation
sprite --help

# Check version
sprite upgrade --check
```

---

## Quick Start

### 1. Authenticate

```bash
# Authenticate with Fly.io
sprite login

# Or authenticate for a specific organization
sprite login -o my-org
```

### 2. Create a Sprite

```bash
# Create a new sprite
sprite create my-project-sprite

# Create in a specific organization
sprite create -o myorg dev-sprite
```

### 3. Use a Sprite

```bash
# Activate sprite for current directory
sprite use my-sprite

# Or specify org and sprite
sprite use -o myorg dev-sprite
```

### 4. Execute Commands

```bash
# Run a command in the sprite
sprite exec ls -la

# Run npm in sprite
sprite exec npm install

# Run tests
sprite exec npm test
```

---

## Core Commands

### Authentication

| Command | Description |
|---------|-------------|
| `sprite login` | Authenticate with browser |
| `sprite logout` | Remove configuration |
| `sprite org auth` | Add API token manually |
| `sprite auth setup --token <token>` | Auth from existing token |

### Sprite Management

| Command | Description |
|---------|-------------|
| `sprite create <name>` | Create new sprite |
| `sprite list` | List all sprites |
| `sprite use <name>` | Activate for current dir |
| `sprite destroy <name>` | Delete a sprite |

### Execution

| Command | Description |
|---------|-------------|
| `sprite exec <cmd>` | Execute command in sprite |
| `sprite console` | Interactive shell (not for automation) |
| `sprite x <cmd>` | Short form of exec |

### Checkpoints

| Command | Description |
|---------|-------------|
| `sprite checkpoint create` | Create snapshot |
| `sprite checkpoint list` | List all checkpoints |
| `sprite restore <id>` | Restore from checkpoint |

### Networking

| Command | Description |
|---------|-------------|
| `sprite url` | Show sprite URL |
| `sprite url update --auth public` | Make URL public |
| `sprite proxy <port>...` | Forward local ports |

---

## Python Integration

```python
from skills.sprites_dev_cli import (
    sprite_create,
    sprite_exec,
    sprite_checkpoint_create,
    sprite_restore,
    sprite_list,
    sprite_url
)

# Create a new sprite
result = sprite_create("my-dev-env")
print(result)

# Execute commands in sprite
result = sprite_exec("npm install", sprite="my-dev-env")
print(result)

# Create checkpoint
result = sprite_checkpoint_create()
print(result)

# Get sprite URL
url = sprite_url()
print(f"Sprite URL: {url}")

# List all sprites
result = sprite_list()
print(result)
```

---

## Common Workflows

### Workflow 1: New Project Setup

```bash
# 1. Create sprite
sprite create my-new-project

# 2. Activate for current directory
sprite use my-new-project

# 3. Execute setup commands
sprite exec npm init -y
sprite exec npm install express

# 4. Create checkpoint
sprite checkpoint create

# 5. Start development
sprite exec npm run dev
```

### Workflow 2: Team Development

```bash
# 1. Create shared dev environment
sprite create -o myorg team-dev

# 2. Share URL with team
sprite url

# 3. Make accessible
sprite url update --auth public

# 4. Team members use same sprite
sprite use -o myorg team-dev
```

### Workflow 3: Testing in Isolated Environment

```bash
# 1. Create test sprite
sprite create test-env

# 2. Run tests
sprite exec npm test

# 3. If tests pass, create checkpoint
sprite checkpoint create

# 4. If tests fail, restore and retry
sprite restore <checkpoint-id>
```

### Workflow 4: Port Forwarding

```bash
# Forward local ports to sprite
sprite proxy 3000 8080 5000

# Now access:
# localhost:3000 → sprite:3000
# localhost:8080 → sprite:8080
# localhost:5000 → sprite:5000
```

---

## Configuration

### Config File Location

| Platform | Location |
|----------|----------|
| macOS/Linux | `~/.sprites/sprites.json` |
| Windows | `%USERPROFILE%\.sprites\sprites.json` |

### Config Structure

```json
{
  "tokens": {
    "org-name": "token-value"
  },
  "current_org": "org-name",
  "current_sprite": "sprite-name"
}
```

### Local Directory Context

Create a `.sprite` file to remember which sprite to use:

```bash
# Set sprite for current directory
sprite use my-sprite

# This creates .sprite file
cat .sprite
# Output: my-sprite

# Add to .gitignore (user-specific)
echo ".sprite" >> .gitignore
```

---

## Checkpoints Explained

**Checkpoints** are snapshots of your sprite's filesystem at a point in time.

**Use cases:**
- Save state before risky changes
- Roll back to known good state
- Share environment state with team
- Debug by restoring to previous state

**Example:**
```bash
# Before making changes
sprite checkpoint create
# Output: checkpoint-abc123

# Make changes...
sprite exec npm install risky-package

# Something broke? Restore!
sprite restore checkpoint-abc123

# List all checkpoints
sprite checkpoint list
```

---

## Advanced Usage

### Multi-Organization Support

```bash
# Work with different organizations
sprite create -o org1 sprite1
sprite create -o org2 sprite2

# List sprites in specific org
sprite list -o org1
sprite list -o org2

# Execute in specific org/sprite
sprite exec -o org2 -s sprite2 npm start
```

### Debug Mode

```bash
# Enable debug logging to stdout
sprite --debug exec npm start

# Log to file
sprite --debug=/tmp/sprite-debug.log exec npm start

# Show detailed version info
SPRITE_VERSION_DEBUG=true sprite --version
```

### Port Proxy for Development

```bash
# Forward multiple ports
sprite proxy 3000 8080 5432

# Now you can:
# - Access web app at localhost:3000
# - Access API at localhost:8080
# - Access database at localhost:5432
# All traffic goes through the sprite's network
```

### API Calls with Auth

```bash
# Make authenticated API calls
sprite api /api/sprites
sprite api /api/sprites -X POST -d '{"name":"test"}'
```

---

## Troubleshooting

### Command Not Found

```bash
# Check if sprite is in PATH
which sprite

# Add to PATH if needed
export PATH="$HOME/.local/bin:$PATH"

# Add to ~/.zshrc or ~/.bashrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
```

### Permission Denied

```bash
# Fix permissions
chmod +x ~/.local/bin/sprite
```

### macOS Security Warning

```bash
# Remove quarantine attribute
xattr -d com.apple.quarantine ~/.local/bin/sprite
```

### Authentication Issues

```bash
# Logout and re-auth
sprite logout
sprite login

# Or use token directly
sprite auth setup --token "org/token-id/token-value"
```

---

## Best Practices

1. **Use checkpoints** before major changes
2. **Create dedicated sprites** for different projects
3. **Use `.sprite` file** for team collaboration
4. **Forward only necessary ports** with `sprite proxy`
5. **Clean up** with `sprite destroy` when done
6. **Use org-specific sprites** for team projects
7. **Set up auth from tokens** in CI/CD environments

---

## Comparison: Sprites vs Alternatives

| Feature | Sprites.dev | GitHub Codespaces | Gitpod |
|---------|-------------|-------------------|--------|
| **CLI-first** | ✅ | ❌ | ❌ |
| **Checkpoint/Restore** | ✅ | ❌ | ❌ |
| **Port Proxy** | ✅ | ✅ | ✅ |
| **Free Tier** | ✅ | Limited | Limited |
| **Self-hostable** | ❌ | ❌ | ✅ |
| **Fly.io Integration** | ✅ | ❌ | ❌ |

---

## Resources

- **Official Docs:** https://docs.sprites.dev
- **Installation:** https://docs.sprites.dev/cli/installation
- **GitHub:** https://github.com/sprites-dev/sprite
- **Fly.io:** https://fly.io

---

## Quick Reference

```bash
# Essential Commands
sprite login                      # Authenticate
sprite create <name>              # New sprite
sprite use <name>                 # Activate
sprite exec <cmd>                 # Run command
sprite checkpoint create          # Save state
sprite restore <id>               # Restore state
sprite list                       # Show sprites
sprite url                        # Get URL
sprite destroy <name>             # Delete sprite
```

---

**Version:** 1.0.0
**Author:** AI Realtor Platform
**License:** MIT
**Category:** Development Tools
**Last Updated:** 2026-02-25
