# Emergent Learning Framework - Setup

This folder contains the configuration files and scripts to install the emergent learning framework.

**Default install path:** `~/.opencode/emergent-learning` (set `ELF_BASE_PATH` to run from a different location).

## Quick Install

From the repository root:

```bash
# Mac/Linux
./install.sh

# Windows
.\install.ps1
```
Use PowerShell or CMD on Windows; Git Bash is not supported for the installer scripts.

## What Gets Installed

| Component | Destination | Purpose |
|-----------|-------------|---------|
| `AGENTS.md` | `~/.opencode/AGENTS.md` | Main configuration - instructions for Claude |
| Commands | `~/.opencode/commands/` | Slash commands like `/search`, `/checkin`, `/swarm` |
| Core Files | `~/.opencode/emergent-learning/` | Query system, memories, dashboard backend |
| Hooks | `~/.opencode/emergent-learning/hooks/` | Logic for pre/post task hooks |
| `settings.json` | `~/.opencode/settings.json` | Configures Claude to use the ELF hooks |

## Manual Install

We strongly recommend using the installer script as it handles path configuration and virtual environments correctly.

If you must install manually, the high-level steps are:

1. Copy `templates/AGENTS.md.template` to `~/.opencode/AGENTS.md`.
2. Copy `library/commands/*` to `~/.opencode/commands/`.
3. Copy the entire repository `src` content to `~/.opencode/emergent-learning/`.
4. Copy `tools/scripts/*` to `~/.opencode/emergent-learning/scripts/`.
5. Create a Python virtual environment in `~/.opencode/emergent-learning/.venv` and install `requirements.txt`.
6. Configure `~/.opencode/settings.json` to add `PreToolUse` and `PostToolUse` hooks pointing to `~/.opencode/emergent-learning/hooks/learning-loop`.

## What Each Component Does

### AGENTS.md
The constitution. Instructs Claude to:
- Query the building at conversation start
- Follow golden rules
- Use the session memory system

### Slash Commands
- `/search` - Search session history
- `/checkin` - Manual building check-in
- `/swarm` - Multi-agent coordination

### Hooks (settings.json)
Configured in `settings.json`, these ensure that:
- **PreToolUse:** `pre_tool_learning.py` runs before tasks to provide context.
- **PostToolUse:** `post_tool_learning.py` runs after tasks to record outcomes.

## Customization

Edit `~/.opencode/AGENTS.md` after installation to:
- Change package manager preference (bun vs npm)
- Modify dashboard ports
- Add project-specific instructions
