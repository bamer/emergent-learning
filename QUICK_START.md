# ELF OpenCode - Quick Start (After Migration)

## Status: Infrastructure ✅ | Features 🚨 (needs activation)

---

## Step 1: Activate ELF Hooks

In your OpenCode session, run:
```
/elf_activate
```

You should see:
```
✅ ELF activated
Hooks are now active for this session.
```

---

## Step 2: Test Auto-Learning

Type something with a learning marker:
```
[LEARNED: Testing the ELF learning system]
```

The hook should capture it. Check logs:
```bash
tail ~/.opencode/emergent-learning/logs/elf-hooks.log
```

---

## Step 3: Test Session Lifecycle

At the end of your OpenCode session, run:
```bash
python3 ~/.opencode/emergent-learning/query/checkout.py --final
```

This persists all learnings from the session.

---

## Step 4: Check Golden Rules

View what the system has learned:
```bash
python3 ~/.opencode/emergent-learning/query/query.py --domain learning
```

---

## 🔧 Converter: Claude → OpenCode Agents

To convert Claude agents to OpenCode format:

```bash
cd /path/to/agents
node ~/.opencode/emergent-learning/convert-opencode-to-opencode.js

# Converted files appear in: ./converted-opencode/
```

This converter:
- ✅ Converts paths from `.opencode` to `.opencode`
- ✅ Updates frontmatter format
- ✅ Maps model to `opencode/big-pickle`
- ✅ Converts permissions

---

## 📋 Feature Status

| Feature | Status | Action |
|---------|--------|--------|
| Auto-Learning `[LEARNED:]` | 🚨 Hook not firing | Run `/elf_activate` |
| Heuristics Confidence | ✅ Schema ready | Test with patterns |
| Golden Rules | 🚨 Not synced | Run `query/repair_database.py` |
| Session Continuity | 🚨 Lifecycle hooks | Manual: `query/checkout.py` |
| Async Watcher | 🚨 Not spawning | Run: `watcher/run_with_bigpickle.py` |
| Swarm Agents | 🚨 Incomplete | Pending implementation |
| Pheromone Trails | 🚨 Not recording | Enable post-tool hook |

---

## 🆘 Common Issues

### "ELF hooks not activating"
```bash
# Check plugin is installed
ls -la ~/.opencode/plugins/ELF_superpowers.js

# Should see: symlink to ~/.opencode/emergent-learning/ELF_superpowers.js
```

### "Database errors"
```bash
# Check database
sqlite3 ~/.opencode/emergent-learning/memory/index.db ".tables"

# Create missing tables if needed
python3 ~/.opencode/emergent-learning/fix_database.py
```

### "Golden rules not showing"
```bash
# Sync rules to database
python3 ~/.opencode/emergent-learning/query/repair_database.py

# Restart dashboard backend
pkill -f "python3.*dashboard"
```

---

## 📚 Full Documentation

- **Complete Guide**: `ELF_OPENCODE_MIGRATION_GUIDE.md`
- **Migration Status**: `MIGRATION_SUMMARY.md`
- **Health Check**: `python3 validate_migration.py`

---

## 🚀 Key Paths

```bash
# Base directory
~/.opencode/emergent-learning

# Database
~/.opencode/emergent-learning/memory/index.db

# Logs
~/.opencode/emergent-learning/logs/

# Hook system
~/.opencode/emergent-learning/hooks/learning-loop/

# Query system
~/.opencode/emergent-learning/query/

# Plugin
~/.opencode/plugins/ELF_superpowers.js
```

---

## 🎯 Recommended Order

1. **Activate** → `/elf_activate`
2. **Test hook** → Generate `[LEARNED:]` marker
3. **Check database** → `sqlite3 ... ".tables"`
4. **Sync golden rules** → `python3 query/repair_database.py`
5. **Test query** → `python3 query/query.py --domain learning`
6. **Run watcher** → `python3 watcher/run_with_bigpickle.py`
7. **Monitor logs** → `tail -f logs/*.log`

---

## ✨ Success = All These Work

- [x] `/elf_activate` → "ELF hooks activated"
- [x] `[LEARNED: test]` → captured in logs
- [x] Golden rules → shown in dashboard
- [x] Heuristics → queryable from database
- [x] Sessions → recorded across continuity
- [x] Watcher → running health checks
- [x] Pheromone → tracking file access

---

**Next:** See `MIGRATION_SUMMARY.md` for detailed feature fixes
