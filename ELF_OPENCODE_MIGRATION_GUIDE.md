# ELF OpenCode Migration & Feature Fix Guide

## Executive Summary

ELF framework has been partially migrated to OpenCode but several features are broken or frozen due to:
1. **Path issues** - `.claude` → `.opencode` conversion incomplete
2. **Model configuration** - agents still calling Claude models instead of `opencode/big-pickle`
3. **Hook system** - ELF_superpowers.js plugin not properly wired
4. **Database paths** - hardcoded paths not respecting environment variables
5. **Async operations** - watcher and learning loops not executing properly

---

## ✅ Completed Actions

### 1. Path Conversion (FIXED)
- ✅ Updated `convert-claude-to-opencode.js` to handle body content paths
- ✅ Created `fix_paths.py` - converted 62 files with hardcoded `.claude` paths
- ✅ All Python files now reference `~/.opencode/emergent-learning`

**Files updated:**
- `agents/*.py` - dashboard sentinel agents
- `agents/*/personality.md` - agent personality files  
- `dashboard-app/backend/` - database and session paths
- `hooks/learning-loop/` - learning hook documentation
- `query/` - all query system files
- `watcher/` - watcher system files
- `scripts/` - maintenance scripts

---

## 🚨 Critical Issues to Fix

### Issue 1: Auto-Learning with [LEARNED:] Markers
**Status**: Broken  
**Root Cause**: Hook system not integrated

**Fix Steps:**
1. Verify ELF_superpowers.js is properly symlinked:
   ```bash
   ls -la ~/.opencode/plugins/ELF_superpowers.js
   # Should point to: ~/.opencode/emergent-learning/ELF_superpowers.js
   ```

2. Create symlink if missing:
   ```bash
   mkdir -p ~/.opencode/plugins
   ln -sf ~/.opencode/emergent-learning/ELF_superpowers.js ~/.opencode/plugins/
   ```

3. Check hook paths in ELF_superpowers.js:
   ```javascript
   // Line 29-30: Verify these exist
   const HOOKS_DIR = path.join(ELF_DIR, "hooks", "learning-loop");
   const QUERY_DIR = path.join(ELF_DIR, "query");
   ```

4. Verify Python hooks exist:
   ```bash
   ls -la ~/.opencode/emergent-learning/hooks/learning-loop/pre_tool_learning.py
   ls -la ~/.opencode/emergent-learning/hooks/learning-loop/post_tool_learning.py
   ```

**Workaround for now:**
- Manually invoke: `/elf_activate` command in OpenCode to enable hooks
- Check logs: `~/.opencode/emergent-learning/logs/`

---

### Issue 2: Heuristics - Confidence Validation (0.0 → 1.0)
**Status**: Partially broken - database schema correct, query system issues

**Root Cause:**
- Query system (`query.py`) not properly extracting heuristics from database
- Missing validation loop integration

**Fix Steps:**
1. Test query system directly:
   ```bash
   export ELF_BASE_PATH=~/.opencode/emergent-learning
   python3 ~/.opencode/emergent-learning/query/query.py --list-heuristics
   ```

2. Check database integrity:
   ```bash
   sqlite3 ~/.opencode/emergent-learning/memory/index.db ".tables"
   # Should show: heuristics, golden_rules, sessions, etc.
   ```

3. If missing heuristics table, run:
   ```bash
   python3 ~/.opencode/emergent-learning/setup_db.py
   ```

4. Verify heuristic validation in `query/models.py`:
   - Check `HeuristicModel.validate()` method
   - Ensure confidence scores update on each use

**Key Files:**
- `query/models.py` - Heuristic model definitions
- `query/query.py` - Query system main
- `hooks/learning-loop/extract_patterns.py` - Pattern extraction

---

### Issue 3: Golden Rules Display vs Usage Mismatch
**Status**: Dashboard shows rules, but agents don't use them consistently

**Root Cause:**
- Dashboard reads from `memory/golden-rules.md`
- Agents query database but golden rules not synced
- Missing validation during decision-making

**Fix Steps:**
1. Sync golden rules to database:
   ```bash
   python3 ~/.opencode/emergent-learning/query/repair_database.py
   ```

2. Verify golden rules are in database:
   ```bash
   sqlite3 ~/.opencode/emergent-learning/memory/index.db \
     "SELECT COUNT(*) FROM golden_rules WHERE is_active = 1"
   ```

3. Update agent query initialization in `agents/dashboard_sentinel.py`:
   ```python
   # Add before agent execution
   self.load_golden_rules()
   self.apply_rules_to_context()
   ```

4. Check dashboard loads fresh data:
   - Restart backend: `pkill -f "python3.*dashboard-app"`
   - Backend should be at: `http://localhost:8888`

---

### Issue 4: Cross-Session Continuity
**Status**: Database exists but session checkout not running

**Root Cause:**
- Session lifecycle hooks in ELF_superpowers.js may not be triggered
- Checkout scripts not being called
- No cleanup between sessions

**Fix Steps:**
1. Manual session check-in/checkout:
   ```bash
   # Check in
   python3 ~/.opencode/emergent-learning/query/checkin.py
   
   # Check out (at end of work)
   python3 ~/.opencode/emergent-learning/query/checkout.py --final
   ```

2. Verify session recording is working:
   ```bash
   ls -la ~/.opencode/emergent-learning/event_chronicle/
   # Should have daily JSONL files
   ```

3. Enable automatic session hooks in plugins:
   - Ensure OpenCode is loading ELF_superpowers.js plugin
   - Check OpenCode console for hook activation logs

---

### Issue 5: Async Watcher (Model Migration)
**Status**: Partially fixed - code updated to use `opencode/big-pickle`

**Current Implementation:**
- Updated to use `opencode/big-pickle` model
- Uses `claude --print --model opencode/big-pickle` commands
- Located in `watcher/run_with_bigpickle.py`

**Remaining Issues:**
- Watcher not auto-spawning on user interaction
- Database not recording watcher executions

**Fix Steps:**
1. Test watcher manually:
   ```bash
   cd ~/.opencode/emergent-learning/watcher
   python3 run_with_bigpickle.py
   ```

2. Verify model works:
   ```bash
   claude --print --model opencode/big-pickle "test: return Hello"
   ```

3. Enable watcher auto-spawn:
   - Must be triggered from main OpenCode session hook
   - Currently requires manual invocation

4. Check watcher logs:
   ```bash
   tail -f ~/.opencode/emergent-learning/logs/watcher.log
   ```

---

### Issue 6: Swarm Agents
**Status**: Code incomplete - missing agent spawning

**Root Cause:**
- Conductor system expects Claude Code CLI
- OpenCode uses different agent model (`opencode/big-pickle`)
- No Task tool equivalent for spawning subagents

**Fix Steps:**
1. Review swarm configuration:
   ```bash
   cat ~/.opencode/emergent-learning/agents/parties.yaml
   ```

2. Verify agent party coordination:
   - Check `.coordination/blackboard.json` for agent states
   - Ensure agents can write to coordination directory

3. For now, use sequential agent invocation:
   ```python
   # In coordinator.py - instead of parallel spawning
   for agent in agents:
       result = execute_agent_sequential(agent)
       update_blackboard(agent, result)
   ```

4. Future: Once OpenCode supports subagents, update to parallel model

---

### Issue 7: Pheromone Trails (File Hotspot Analysis)
**Status**: Data structure exists but not recording

**Root Cause:**
- Post-tool hook not being executed (hook system not active)
- Pheromone trails require consistent tool execution tracking
- Watcher not recording file accesses

**Fix Steps:**
1. Enable post-tool hook execution:
   - Ensure ELF_superpowers.js hooks are active
   - Call `/elf_activate` in OpenCode session

2. Verify pheromone database table:
   ```bash
   sqlite3 ~/.opencode/emergent-learning/memory/index.db \
     "SELECT * FROM pheromone_trails LIMIT 5"
   ```

3. If table missing, create it:
   ```bash
   python3 ~/.opencode/emergent-learning/setup_db.py
   ```

4. Check trail recording in hooks:
   - `hooks/learning-loop/post_tool_learning.py` should record trails
   - Verify file paths are being captured

5. Query trails for hotspot analysis:
   ```python
   from query.models import get_hotspots
   hotspots = get_hotspots(min_trails=3)
   for file, count in hotspots:
       print(f"{file}: {count} accesses")
   ```

---

## 🔧 Converter Tool Usage

### Using the Enhanced Claude-to-OpenCode Converter

**What it does:**
1. Converts frontmatter format (Claude → OpenCode)
2. **NEW**: Converts path references in markdown body
3. Maps model aliases to `opencode/big-pickle`
4. Converts permissions from tools list

**How to use:**
```bash
cd /path/to/agent/directory
node ~/.opencode/emergent-learning/convert-claude-to-opencode.js

# Output goes to: ./converted-opencode/
```

**Converted agent files should be created in:**
```
converted-opencode/
├── agent1.md  (converted to OpenCode format)
├── agent2.md
└── ...
```

**What gets converted in body:**
- `~/.claude/emergent-learning` → `~/.opencode/emergent-learning`
- `claude --print --model opus` → `claude --print --model opencode/big-pickle`
- Python command paths
- Documentation references

---

## 📋 Health Check Script

Create and run this to diagnose the system:

```bash
#!/bin/bash
# health_check.sh

echo "🔍 ELF OpenCode Health Check"
echo "=============================="

# 1. Paths
echo "✓ Checking paths..."
test -d ~/.opencode/emergent-learning && echo "  ✅ ELF directory exists" || echo "  ❌ ELF directory missing"
test -d ~/.opencode/plugins && echo "  ✅ Plugins directory exists" || echo "  ❌ Plugins directory missing"

# 2. Database
echo "✓ Checking database..."
test -f ~/.opencode/emergent-learning/memory/index.db && echo "  ✅ Database file exists" || echo "  ❌ Database missing"
sqlite3 ~/.opencode/emergent-learning/memory/index.db ".tables" > /dev/null 2>&1 && echo "  ✅ Database accessible" || echo "  ❌ Database corrupted"

# 3. Plugin
echo "✓ Checking plugin..."
test -L ~/.opencode/plugins/ELF_superpowers.js && echo "  ✅ Plugin symlink exists" || echo "  ❌ Plugin symlink missing"

# 4. Hooks
echo "✓ Checking hooks..."
test -f ~/.opencode/emergent-learning/hooks/learning-loop/pre_tool_learning.py && echo "  ✅ Pre-hook exists" || echo "  ❌ Pre-hook missing"
test -f ~/.opencode/emergent-learning/hooks/learning-loop/post_tool_learning.py && echo "  ✅ Post-hook exists" || echo "  ❌ Post-hook missing"

# 5. Query system
echo "✓ Checking query system..."
python3 ~/.opencode/emergent-learning/query/query.py --list-heuristics > /dev/null 2>&1 && echo "  ✅ Query system working" || echo "  ❌ Query system error"

# 6. Model
echo "✓ Checking model..."
claude --print --model opencode/big-pickle "test: return OK" > /dev/null 2>&1 && echo "  ✅ big-pickle model available" || echo "  ❌ big-pickle model unavailable"

echo ""
echo "Health check complete!"
```

---

## 🎯 Recommended Fix Priority

1. **HIGH (Blocking core features):**
   - [ ] Enable ELF_superpowers.js plugin
   - [ ] Fix database paths and initialization
   - [ ] Activate hook system (pre/post-tool)

2. **MEDIUM (Feature functionality):**
   - [ ] Sync golden rules to database
   - [ ] Implement heuristic confidence tracking
   - [ ] Test session lifecycle hooks

3. **MEDIUM (Data collection):**
   - [ ] Enable pheromone trail recording
   - [ ] Start watcher auto-spawn mechanism
   - [ ] Verify event chronicle recording

4. **LOW (Future enhancement):**
   - [ ] Parallel swarm agent execution
   - [ ] Advanced hotspot analysis
   - [ ] Continuous learning optimization

---

## 📝 Configuration Checklist

- [ ] `ELF_BASE_PATH` environment variable set to `~/.opencode/emergent-learning`
- [ ] OpenCode installed and working
- [ ] `claude` command-line tool available
- [ ] `opencode/big-pickle` model configured
- [ ] Database file accessible at `~/.opencode/emergent-learning/memory/index.db`
- [ ] Plugin directory exists: `~/.opencode/plugins/`
- [ ] ELF_superpowers.js symlinked to plugins directory
- [ ] Python 3.8+ available
- [ ] Required Python packages installed (sqlite3, pathlib, etc.)

---

## 🆘 Troubleshooting

### "Hook not firing" / "[LEARNED:] not being captured"
1. Check plugin is loaded: OpenCode console should show "ELF hooks activated"
2. Call `/elf_activate` command
3. Check ELF logs: `~/.opencode/emergent-learning/logs/`

### "Database path errors"
1. Verify `ELF_BASE_PATH` is set: `echo $ELF_BASE_PATH`
2. If not set, add to shell profile:
   ```bash
   export ELF_BASE_PATH=~/.opencode/emergent-learning
   ```

### "Golden rules not showing"
1. Check file exists: `ls ~/.opencode/emergent-learning/memory/golden-rules.md`
2. Sync to database: `python3 ~/.opencode/emergent-learning/query/repair_database.py`
3. Restart dashboard backend

### "Watcher not running"
1. Check logs: `tail ~/.opencode/emergent-learning/logs/watcher.log`
2. Test manually: `python3 ~/.opencode/emergent-learning/watcher/run_with_bigpickle.py`
3. Verify model: `claude --print --model opencode/big-pickle "test: return OK"`

---

## 📚 Key Files Reference

| Component | File | Purpose |
|-----------|------|---------|
| Plugin | `ELF_superpowers.js` | OpenCode hooks integration |
| Database | `memory/index.db` | SQLite learning data |
| Paths | `elf_paths.py` | Path resolution logic |
| Query | `query/query.py` | Heuristics & golden rules lookup |
| Hooks | `hooks/learning-loop/*.py` | Learning capture hooks |
| Watcher | `watcher/run_with_bigpickle.py` | System monitoring |
| Config | `elf_config.yaml` | System configuration |
| Converter | `convert-claude-to-opencode.js` | Format conversion tool |

---

## 🚀 Next Steps

1. **Immediate**: Activate plugin system and verify hook execution
2. **Short-term**: Fix golden rules sync and heuristic confidence updates
3. **Medium-term**: Enable watcher auto-spawn and session continuity
4. **Long-term**: Implement parallel swarm agents for OpenCode model

