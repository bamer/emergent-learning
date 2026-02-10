# 🚀 ELF OpenCode - START HERE

## What Happened?

Your ELF framework has been **successfully migrated** from Claude to OpenCode infrastructure. All paths have been converted, the database is ready, and the hook system is in place.

**Status**: ✅ Infrastructure Complete | 🚨 Features Need Activation

---

## What You Need to Do Right Now

### 1️⃣ Activate ELF Hooks (30 seconds)

In your OpenCode session, run this command:
```
/elf_activate
```

You should see a response like:
```
✅ ELF activated

Hooks are now active for this session.
- Pre/post-tool learning enabled
- Session auto check-in/check-out enabled
```

### 2️⃣ Check the Documentation (5 minutes)

Read these in order:
1. **`QUICK_START.md`** - Get started immediately
2. **`MIGRATION_SUMMARY.md`** - Understand what was done
3. **`ELF_OPENCODE_MIGRATION_GUIDE.md`** - Detailed fixes for each feature

### 3️⃣ Validate the Setup (1 minute)

Run this health check:
```bash
python3 ~/.opencode/emergent-learning/validate_migration.py
```

Should show: ✅ All checks passed!

---

## What's Working Now ✅

- ✅ Paths converted from ~/.opencode to ~/.opencode
- ✅ Database with 27 tables created
- ✅ Hook system installed and ready
- ✅ Plugin symlinked to ~/.opencode/plugins/
- ✅ Converter tool enhanced (handles markdown)
- ✅ Tools for path migration & validation created
- ✅ Comprehensive documentation provided

---

## What Needs Fixing 🚨

| Feature | Status | Quick Fix |
|---------|--------|-----------|
| **Auto-Learning** | Hooks not firing | Run `/elf_activate` |
| **Golden Rules** | Not synced to DB | Run `python3 query/repair_database.py` |
| **Session Continuity** | Lifecycle events missing | Manual: `python3 query/checkout.py --final` |
| **Async Watcher** | Not auto-spawning | Test: `python3 sentinel/run_with_bigpickle.py` |
| **Swarm Agents** | Incomplete | See migration guide |
| **Pheromone Trails** | Not recording | Need post-tool hook active |

---

## 3 Quick Tests

### Test 1: Hook System
Generate a learning marker:
```
[LEARNED: Testing ELF OpenCode integration]
```

Check if captured:
```bash
tail ~/.opencode/emergent-learning/logs/elf-hooks.log
```

### Test 2: Database
Query golden rules:
```bash
sqlite3 ~/.opencode/emergent-learning/memory/index.db \
  "SELECT COUNT(*) FROM golden_rules"
```

Should return: 0 (or more if you have rules)

### Test 3: Query System
```bash
export ELF_BASE_PATH=~/.opencode/emergent-learning
python3 ~/.opencode/emergent-learning/query/query.py --list-heuristics
```

Should work without errors.

---

## Tools You Have

1. **convert-opencode-to-opencode.js** - Convert agent formats
   ```bash
   cd /path/to/agents
   node ~/.opencode/emergent-learning/convert-opencode-to-opencode.js
   ```

2. **validate_migration.py** - Health check (run anytime)
   ```bash
   python3 ~/.opencode/emergent-learning/validate_migration.py
   ```

3. **fix_paths.py** - Update any remaining .opencode paths
   ```bash
   python3 ~/.opencode/emergent-learning/fix_paths.py
   ```

---

## File Structure

```
~/.opencode/emergent-learning/
├── START_HERE.md                          ← You are here
├── QUICK_START.md                         ← Do this next
├── MIGRATION_SUMMARY.md                   ← Overview
├── ELF_OPENCODE_MIGRATION_GUIDE.md        ← Detailed fixes
├── DELIVERABLES.md                        ← What was built
│
├── memory/index.db                        ← Database (27 tables)
├── logs/                                  ← Check for activity
├── hooks/learning-loop/
│   ├── pre_tool_learning.py              ← Runs before each tool
│   ├── post_tool_learning.py             ← Runs after each tool
│   └── extract_patterns.py                ← NEW: Pattern extraction
│
├── query/                                 ← Learning system
├── sentinel/                               ← System monitoring
├── agents/                                ← Agent definitions
└── ELF_superpowers.js                     ← OpenCode plugin (symlinked)
```

---

## Recommended Next Steps

1. **Right now:**
   - [ ] Run `/elf_activate` in OpenCode
   - [ ] Read `QUICK_START.md`
   - [ ] Run validation check

2. **Today:**
   - [ ] Generate a `[LEARNED:]` marker and verify it's captured
   - [ ] Run `python3 query/repair_database.py` to sync golden rules
   - [ ] Check dashboard shows golden rules
   - [ ] Test sentinel: `python3 sentinel/run_with_bigpickle.py`

3. **This week:**
   - [ ] Verify all features working
   - [ ] Review `MIGRATION_SUMMARY.md` for any outstanding issues
   - [ ] Test agent conversion with `convert-opencode-to-opencode.js`
   - [ ] Check logs regularly: `tail -f logs/*.log`

---

## Key Paths

```bash
# Base
~/.opencode/emergent-learning

# Database
~/.opencode/emergent-learning/memory/index.db

# Logs
~/.opencode/emergent-learning/logs/

# Plugin
~/.opencode/plugins/ELF_superpowers.js
```

---

## Emergency Commands

If something breaks:

```bash
# Check status
python3 ~/.opencode/emergent-learning/validate_migration.py

# View logs
tail -f ~/.opencode/emergent-learning/logs/*.log

# Repair database
python3 ~/.opencode/emergent-learning/fix_database.py

# Sync golden rules
python3 ~/.opencode/emergent-learning/query/repair_database.py

# Manual session end
python3 ~/.opencode/emergent-learning/query/checkout.py --final
```

---

## Questions?

Check the documentation files:
1. **Quick answer?** → `QUICK_START.md`
2. **Understand the changes?** → `MIGRATION_SUMMARY.md`
3. **Fix a specific issue?** → `ELF_OPENCODE_MIGRATION_GUIDE.md`
4. **What was delivered?** → `DELIVERABLES.md`

---

**Ready to continue?** → Open `QUICK_START.md`
