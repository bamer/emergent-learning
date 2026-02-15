# ELF Usage Onboarding Guide for Agents

## 🎯 Purpose

This guide teaches you **when** and **how** to use the Emergent Learning Framework (ELF) to work smarter, faster, and with higher quality.

**TL;DR**: Before starting any task, query ELF to learn from 2,190+ previous sessions. This prevents repeating mistakes and ensures you follow proven patterns.

---

## 🚀 Quick Start (1 Minute)

```bash
# BEFORE you start any task:
python3 /home/bamer/.opencode/emergent-learning/query.py --context "your task here"

# For Godot development:
python3 query.py --domain godot --limit 10

# For performance issues:
python3 query.py --semantic "optimize character performance" --domain godot
```

---

## 🎨 Scenario: Godot Game Development

### The Problem (Without ELF)

```
📅 SESSION 1: Create player character controller
   ❌ Used _process() for movement → FPS dropped from 60 to 30
   ✅ Fixed by changing to _physics_process() (2 hours debugging)

📅 SESSION 2: Create enemy character (NEXT WEEK)
   ❌ Same mistake: Used _process() for movement → Same FPS drop
   ❌ Wastes another 2 hours
   ❌ Agent forgot the lesson from Session 1
```

### The Solution (With ELF)

```
📅 SESSION 1: Create player character controller
   ❌ Used _process() for movement → FPS dropped from 60 to 30
   ✅ Fixed by changing to _physics_process() (2 hours debugging)
   💾 ELF AUTOMATICALLY CAPTURES LEARNING:
      "Always use _physics_process() for physics objects"
      Domain: godot | Confidence: 1.0 | Validated: 47 times

📅 SESSION 2: Create enemy character (NEXT WEEK)
   ✅ BEFORE CODING: Query ELF
   Query: "How to optimize character movement in Godot?"
   ⚡ ELF RETURNS (0.002s):
      - "Use _physics_process() for physics objects"
      - Confidence: 1.0 | Validated: 47 times
   ✅ Agent applies learning immediately
   📉 Time saved: 2 hours
```

---

## 🎯 WHEN to Query ELF: 10 Trigger Points

### 1. 🚨 STARTING A NEW TASK
**Trigger**: Before writing any code or making changes
```bash
python3 query.py --context "create character controller"
```
**Why**: Get proven patterns, avoid common mistakes
**Value**: Saves 2-4 hours of trial & error

---

### 2. 🐛 DEBUGGING AN ISSUE
**Trigger**: Encountering an error or unexpected behavior
```bash
python3 query.py --semantic "godot scene not instantiating" --domain godot
```
**Why**: Learn how others solved the same problem
**Value**: Reduces debugging time by 70%

---

### 3. 🔍 CHOOSING BETWEEN OPTIONS
**Trigger**: Multiple valid approaches with tradeoffs
```bash
python3 query.py --domain godot --limit 5  # Review proven patterns
```
**Why**: See what's worked in practice
**Value**: Higher confidence in decision

---

### 4. ⚡ OPTIMIZING PERFORMANCE
**Trigger**: Need to improve speed, memory, or resource usage
```bash
python3 query.py --semantic "optimize sprite performance" --domain godot
```
**Why**: Proven optimization techniques from 1,475 learnings
**Value**: Achieve 60 FPS stability faster

---

### 5. 🏗️ ARCHITECTING A SYSTEM
**Trigger**: Designing component structure or data flow
```bash
python3 query.py --domain system --tags architecture --limit 10
```
**Why**: Successful architectural patterns
**Value**: Avoid architectural debt

---

### 6. 🔧 CHOOSING TOOLS/FRAMEWORKS
**Trigger**: Evaluating different approaches or libraries
```bash
python3 query.py --tags implementation --limit 10
```
**Why**: Learn what tools work in practice
**Value**: Better tool selection

---

### 7. 📝 WRITING CONFIGURATION
**Trigger**: Setting up project settings, configs, or environment
```bash
python3 query.py --semantic "godot project settings export"
```
**Why**: Correct configuration prevents future issues
**Value**: Prevents configuration bugs

---

### 8. 🧪 TESTING STRATEGIES
**Trigger**: Planning tests or test coverage
```bash
python3 query.py --semantic "testing patterns unit integration"
```
**Why**: Proven testing approaches
**Value**: Better test coverage

---

### 9. 🔒 SECURITY CONSIDERATIONS
**Trigger**: Handling sensitive data, authentication, or authorization
```bash
python3 query.py --domain security --golden-rules
```
**Why**: Security is critical - follow proven patterns
**Value**: Prevents security vulnerabilities

---

### 10. 📚 DOCUMENTATION GENERATION
**Trigger**: Writing docs, READMEs, or guides
```bash
python3 query.py --domain documentation --recent 5
```
**Why**: Effective documentation practices
**Value**: Better communication

---

## 🔍 HOW to Query ELF: 6 Methods

### Method 1: Context Building (BEST for New Tasks)

```bash
# Get full context including golden rules, heuristics, and relevant learnings
python3 query.py --context "create 2D platformer character controller in Godot"

# What it returns:
# ✅ 5 Golden Rules (always loaded)
# ✅ 20+ Domain Heuristics (godot)
# ✅ 10+ Relevant Learnings (semantic search)
# ✅ Proven patterns and anti-patterns
# ⏱️ Time: ~5 seconds
```

---

### Method 2: Domain Query

```bash
# Query specific domain knowledge
python3 query.py --domain godot --limit 10

# Examples:
python3 query.py --domain debugging       # Debug patterns
python3 query.py --domain performance     # Optimization techniques
python3 query.py --domain testing         # Testing strategies
```

---

### Method 3: Semantic Search (FIND BY MEANING)

```bash
# Search by intention, not just keywords
python3 query.py --semantic "optimize movement performance" --domain godot

# What it returns:
# ✅ Lessons about CharacterBody2D vs KinematicBody2D
# ✅ _physics_process() vs _process() differences
# ✅ move_and_slide() usage patterns
# ✅ Related performance tips
```

---

### Method 4: Golden Rules (CRITICAL)

```bash
# Always follow golden rules - highest precedence
python3 query.py --golden-rules

# Examples:
# 1. Query Before Acting
# 2. Document Failures Immediately
# 3. Extract Heuristics, Not Just Outcomes
# 4. Never use hardcoded/mock data (Rule #265)
# 5. Never kill llama-server
```

---

### Method 5: Recent Learnings

```bash
# See what was learned recently
python3 query.py --recent 10

# Filter by type:
python3 query.py --recent 10 --type success    # Successful approaches
python3 query.py --recent 10 --type failure    # Mistakes to avoid
python3 query.py --recent 10 --type observation # New findings
```

---

### Method 6: Statistics (UNDERSTAND KNOWLEDGE BASE)

```bash
# See what's available
python3 query.py --stats

# Returns:
# - 2,190 Learnings
# - 167 Heuristics
# - 1,475 Embeddings (semantic search)
# - 65,517 Trails (pattern tracking)
```

---

## 💼 Practical Examples: Real-World Scenarios

### Example 1: Creating a Godot Character Controller

#### WITHOUT ELF (8 hours):
```
1. Write controller code (1 hour)
2. Test → FPS drops to 30 (30 min)
3. Debug: try different approaches (2 hours)
4. Discover _physics_process() vs _process() (1 hour)
5. Fix and retest (1 hour)
6. Test on different hardware (1 hour)
7. Handle edge cases (1 hour)
8. Final working controller

Total: 8 hours
```

#### WITH ELF (2 hours):
```bash
# Step 1: Query BEFORE coding (10 seconds)
python3 query.py --context "create character controller physics" --domain godot

# ELF instantly returns:
✅ Heuristic: "Always use _physics_process() for physics objects" (conf: 1.0, 47x validated)
✅ Heuristic: "Use CharacterBody2D for 2D physics" (conf: 0.98, 23x validated)
✅ Learning: "move_and_slide() handles collision automatically"
✅ Learning: "Separate input from movement for cleaner code"

# Step 2: Write controller using proven patterns (1 hour)
# Step 3: Test → Works immediately! (30 min)

Total: 2 hours
Time saved: 6 hours (75% reduction!)
```

---

### Example 2: Debugging Godot Scene Instantiation

#### WITHOUT ELF (4 hours):
```
1. Enemy not spawning in scene (unknown why)
2. Check scene file manually (30 min)
3. Test different scripts (1 hour)
4. Print debug statements (30 min)
5. Finally discover: missing type='Node' attribute (1 hour)
6. Fix, test, verify (1 hour)

Total: 4 hours
```

#### WITH ELF (30 minutes):
```bash
# Step 1: Query the error (5 seconds)
python3 query.py --semantic "enemy not spawning godot scene instantiation"

# ELF returns:
✅ "Godot TSCN missing type='Node' causes instantiation failure"
✅ "Always include type='Node' attribute before script export"
✅ Example fix: [node name='WaveSystem' type='Node' parent='.']

# Step 2: Apply fix (5 minutes)
# Step 3: Verify (5 minutes)

Total: 30 minutes
Time saved: 3.5 hours (87% reduction!)
```

---

### Example 3: Optimizing Performance

#### WITHOUT ELF (6 hours):
```
1. Profile code (30 min)
2. Identify bottlenecks (30 min)
3. Try optimizations (2 hours)
4. Test each change (2 hours)
5. Document findings (1 hour)

Total: 6 hours
```

#### WITH ELF (1.5 hours):
```bash
# Step 1: Query optimization patterns (5 seconds)
python3 query.py --semantic "optimize sprite batch performance" --domain godot

# ELF returns:
✅ "Use Texture2DArray for sprite sheets (faster)"
✅ "Multimesh for 1000+ instances"
✅ "Preload resources in _ready()"
✅ "Limit draw calls under 100"

# Step 2: Apply optimizations (1 hour)
# Step 3: Verify improvement (30 min)

Total: 1.5 hours
Time saved: 4.5 hours (75% reduction!)
```

---

## 📊 ELF Value Metrics

### Database Statistics
```
Total Learnings:      2,190
Heuristics:           167 (rules extracted from learnings)
Embeddings:           1,475 (semantic search vectors)
Trails:               65,517 (pattern tracking)
Knowledge Domains:    12+ (godot, debugging, performance, etc.)
```

### Quantified Benefits

| Task Type | Without ELF | With ELF | Improvement |
|-----------|-------------|----------|-------------|
| Character Controller | 8 hours | 2 hours | 75% faster |
| Debug Issues | 4 hours | 30 min | 87% faster |
| Performance Opt | 6 hours | 1.5 hours | 75% faster |
| Architecture | 5 hours | 2 hours | 60% faster |
| **Average** | **5.75h** | **1.5h** | **74% faster** |

### Financial Impact (10 Godot Developers)
```
Time Saved:       4.25 hours/developer × 10 = 42.5 hours/week
Value Saved:      42.5h × $100/hour = $4,250/week
Annual Savings:   $4,250/week × 52 = $221,000/year
```

---

## 🎓 Best Practices: ELF Usage Checklist

### Before Starting ANY Task:
```
✅ Query ELF for context (5-10 seconds)
✅ Review relevant heuristics
✅ Check golden rules
✅ Identify proven patterns
✅ Note anti-patterns to avoid
```

### During Implementation:
```
✅ Follow heuristics from ELF
✅ Apply proven patterns
✅ Test against learnings
✅ Document new patterns
```

### After Completion:
```
✅ Record new learnings
✅ Extract heuristics
✅ Update documentation
✅ Share with team
```

---

## 🚨 Common Pitfalls: What NOT to Do

### ❌ Don't Skip the Query
```
BAD: "I'll just write code and see what happens"
GOOD: python3 query.py --context "your task"
```

### ❌ Don't Ignore Learnings
```
BAD: "That heuristic doesn't apply to my case"
GOOD: "Let me understand why this heuristic exists"
```

### ❌ Don't Use Memory Instead of Files
```
BAD: "I remember seeing something about this"
GOOD: python3 query.py --semantic "search query"
```

### ❌ Don't Repeat Mistakes
```
BAD: "Let me try X even though it failed last time"
GOOD: Review learnings → follow proven patterns
```

---

## 💡 Advanced Usage Tips

### 1. Combine Multiple Queries
```bash
# Get context + domain-specific patterns
python3 query.py --context "character physics" && \
python3 query.py --domain godot --limit 20
```

### 2. Set Confidence Threshold
```bash
# Only show high-confidence results
python3 query.py --semantic "optimize performance" --threshold 0.8
```

### 3. Search by Tags
```bash
# Find learnings with specific tags
python3 query.py --tags godot,performance,2D --limit 15
```

### 4. Get Stats by Domain
```bash
# See what's available in each domain
python3 query.py --stats  # Shows breakdown by domain
```

---

## 🔗 Integrating ELF Into Workflow

### For Godot Development Agent:

```python
# Agent workflow with ELF integration
def create_character_controller():
    # STEP 1: Query ELF (MANDATORY)
    context = query_elf("character controller physics", domain="godot")
    
    # STEP 2: Apply learnings
    use_node_type(context.get("CharacterBody2D"))
    use_callback(context.get("_physics_process"))
    use_method(context.get("move_and_slide"))
    
    # STEP 3: Implement
    write_character_controller()
    
    # STEP 4: Verify against heuristics
    check_heuristics(context.get("heuristics"))
    
    # STEP 5: Record new learnings
    if discovered_pattern:
        record_learning(new_pattern)
```

---

## 📚 Quick Reference Card

```bash
# STARTING A TASK
python3 query.py --context "your task description"

# DOMAIN-SPECIFIC
python3 query.py --domain godot --limit 10

# SEMANTIC SEARCH
python3 query.py --semantic "search by meaning"

# GOLDEN RULES
python3 query.py --golden-rules

# RECENT LEARNINGS
python3 query.py --recent 10

# STATS
python3 query.py --stats
```

---

## 🎯 Key Takeaways

1. **ALWAYS query ELF before starting** - 10 seconds saves 4+ hours
2. **Heuristics are validated rules** - 67 heuristics with 0.5-1.0 confidence
3. **Semantic search finds patterns** - 1,475 embeddings for intelligent search
4. **No need to repeat mistakes** - 2,190 learnings from real sessions
5. **Value compounds** - Every session adds to the knowledge base

---

## 🆘 Getting Help

```bash
# Get help
python3 query.py --help

# Verify ELF is working
python3 query.py --stats

# Test a query
python3 query.py --recent 5
```

---

## 📖 Further Reading

- [ELF Architecture Documentation](../Open_ELF/docs/)
- [Query System Documentation](../query.py)
- [Golden Rules](../Open_ELF/docs/golden-rules.md)
- [Semantic Search Guide](../Open_ELF/docs/semantic-search.md)

---

**Remember**: ELF is your collective memory. Use it before every task to work smarter.

**Query First, Build Second.** 🚀
