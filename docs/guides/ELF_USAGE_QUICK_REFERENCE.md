# ELF Quick Reference: When & How to Use ELF

## ⚡ 10-Second Rule
**Before starting ANY task, run:**
```bash
python3 /home/bamer/.opencode/emergent-learning/query.py --context "your task here"
```

This one command saves you 2-4 hours of trial & error.

---

## 🎯 10 Triggers: When to Query ELF

| # | Trigger | Command | Time Saved |
|---|---------|---------|------------|
| 1 | Starting new task | `query.py --context "task"` | 2-4 hours |
| 2 | Debugging issue | `query.py --semantic "error description"` | 2-3 hours |
| 3 | Choosing between options | `query.py --domain godot --limit 5` | 1-2 hours |
| 4 | Optimizing performance | `query.py --semantic "optimize X"` | 2-3 hours |
| 5 | Architecting system | `query.py --domain system --limit 10` | 2-3 hours |
| 6 | Choosing tools/frameworks | `query.py --tags implementation` | 1-2 hours |
| 7 | Writing configuration | `query.py --semantic "config X"` | 1 hour |
| 8 | Planning tests | `query.py --semantic "testing patterns"` | 1-2 hours |
| 9 | Security considerations | `query.py --domain security --golden-rules` | 1-2 hours |
| 10 | Writing docs | `query.py --domain documentation --recent 5` | 30 min |

**Average time saved per task: 2.5 hours**

---

## 🔍 6 Query Methods

### 1. Context Building (Best for New Tasks)
```bash
python3 query.py --context "describe your task"
# Returns: Golden rules + Domain heuristics + Semantic search
```

### 2. Domain Query
```bash
python3 query.py --domain godot --limit 10
# Returns: All knowledge in specific domain
```

### 3. Semantic Search (Find by Meaning)
```bash
python3 query.py --semantic "what you're trying to do"
# Returns: Relevant learnings by semantic similarity
```

### 4. Golden Rules (Critical)
```bash
python3 query.py --golden-rules
# Returns: 5 immutable rules (ALWAYS follow these)
```

### 5. Recent Learnings
```bash
python3 query.py --recent 10
# Returns: Latest learnings from all sessions
```

### 6. Statistics
```bash
python3 query.py --stats
# Returns: Database metrics and domain breakdown
```

---

## 💼 Real Examples: Before/After

### Example 1: Godot Character Controller

**WITHOUT ELF (8 hours)**:
- Write code → Bug → Debug → Fix (2 hours)
- → Repeat 4 times → 8 hours total

**WITH ELF (2 hours)**:
```bash
python3 query.py --context "character controller physics"
# Returns: "Use _physics_process()" (validated 47 times)
```
- Apply pattern → Works → 2 hours total
- **Saved: 6 hours (75%)**

---

### Example 2: Debug Scene Instantiation

**WITHOUT ELF (4 hours)**:
- Check scene → Try scripts → Debug (3 hours)
- → Finally fix (1 hour) → 4 hours total

**WITH ELF (30 min)**:
```bash
python3 query.py --semantic "enemy not spawning godot"
# Returns: "Add type='Node' to .tscn file"
```
- Add attribute → Works → 30 min total
- **Saved: 3.5 hours (87%)**

---

## 📊 ELF Statistics

```
Total Knowledge:
  - Learnings:    2,190
  - Heuristics:   167 (rules)
  - Embeddings:   1,475 (semantic search)
  - Trails:       65,517 (pattern tracking)

Domains Available:
  - godot, debugging, performance, testing
  - system, architecture, documentation
  - security, infrastructure, and more
```

---

## ✅ Checklist: ELF Usage

### Before Starting Task:
```
□ Query ELF for context (10 seconds)
□ Review heuristics
□ Check golden rules
□ Identify patterns
□ Note anti-patterns
```

### After Completing Task:
```
□ Record new learnings
□ Extract heuristics
□ Update documentation
```

---

## 🚨 Common Mistakes

❌ **Don't skip the query** - Always query first
❌ **Don't ignore heuristics** - They're validated 0.5-1.0 confidence
❌ **Don't use memory** - Query ELF instead
❌ **Don't repeat mistakes** - Learnings prevent this

✅ **DO query first** - 10 seconds saves hours
✅ **DO follow heuristics** - Proven patterns
✅ **DO record learnings** - Benefits everyone
✅ **DO think compoundingly** - Each query grows the knowledge base

---

## 💡 Pro Tips

1. **Combine queries**: Context + Domain = Best results
2. **Set threshold**: `--threshold 0.8` for high-confidence only
3. **Use tags**: `--tags godot,performance` for specific topics
4. **Check stats**: Know what's available before querying

---

## 🔗 Full Documentation

See: [ELF_USAGE_ONBOARDING.md](ELF_USAGE_ONBOARDING.md) for complete guide with examples

---

## 📞 Quick Help

```bash
# Get help
python3 query.py --help

# Verify working
python3 query.py --stats

# Test query
python3 query.py --recent 5
```

---

**Remember**: Query First, Build Second. 10 seconds of querying saves 4+ hours of work. 🚀
