# LearningProcessor: Embedding Decision Logic

**Version**: 1.0 - 2026-02-11
**Purpose**: Exact conditions that determine when LearningProcessor embeds records

---

## 🤖 LearningProcessor Embedding Overview

**What it is**: The LearningProcessor (`core/learning_processor.py`) is the central hub that:
1. Processes tool events (from EventBridge SSE stream)
2. Extracts learnings from tool outputs
3. Records heuristics to database
4. **Auto-embeds** important content to semantic daemon

**When it runs**: After EVERY tool execution via `post_tool_process()` method

---

## ✅ Auto-Embedded Records

### 1. **Heuristics** (MUST EMBED)
- **Trigger**: `_extract_and_record_learnings()` captures heuristic
- **Condition**: Tool output contains heuristic indicators
- **Method**: `_store_embedding()` called after upsert

**Heuristic Captured (YES)**:
```
✅ Tool output: "You should always use unified logging for consistency"
✅ Tool output: "Never block on I/O operations in async functions"
✅ Tool output: "Prefer aiohttp over requests for async HTTP calls"
```

**Heuristic NOT Captured (NO)**:
```
❌ Tool output: "The logging system is configured with INFO level"
❌ Tool output: "Using async pattern for better performance"
❌ Tool output: "Configuration loaded successfully"
```

**Code Location**: `learning_processor.py:1327-1336`

```python
# After heuristic is recorded to database
# Store embedding in semantic daemon
self._store_embedding(
    text=f"{domain}: {rule}",
    source_id=f"heuristic_{domain}_{hash(rule) % 100000}",
    source_type="heuristic",
    metadata={
        "domain": domain,
        "confidence": learning.get("confidence", 0.5),
        "source": learning.get("source", "auto"),
    },
)
```

---

### 2. **Failures** (MUST EMBED)
- **Trigger**: `_auto_record_failure()` called
- **Condition**: `outcome == "failure"` in `post_tool_process()`
- **Method**: `_store_embedding()` called after failure record

**Examples (Auto-Embedded)**:
```
✅ Tool: Write | Outcome: failure
✅ Tool: Bash | Output: "Error: Permission denied" | Outcome: failure
✅ Tool: Edit | Output: "Failed to apply edit" | Outcome: failure
```

**Non-Failures (NOT Embedded)**:
```
❌ Tool: Write | Outcome: success → NOT embedded (unless has learnings)
❌ Tool: Edit | Outcome: success → NOT embedded (unless has learnings)
❌ Tool: Bash | Output: "0 exit code" → NOT embedded
```

**Code Location**: `learning_processor.py:1463-1471`

```python
# Store failure embedding
self._store_embedding(
    text=f"Failure: {description[:200]}. {reason}",
    source_id=f"failure_{timestamp.strftime('%Y%m%d_%H%M%S')}",
    source_type="failure",
    metadata={
        "domain": domains[0] if domains else "general",
        "reason": reason,
    },
)
```

---

## 📋 Learnings Extraction Conditions

### Condition: `outcome in ("success", "unknown")`

```python
# In post_tool_process()
if outcome in ("success", "unknown"):
    learnings = self._extract_and_record_learnings(event, outcome)
```

### Types of Learnings That Get Embedded

| Type | Source | When Embedded | Example |
|------|--------|----------------|---------|
| **Implicit** | Tool output has `should/always/never/must` | Auto | "should use unified logging" |
| **Explicit** | Tool output has `[LEARNED:]` markers | Auto | "[LEARNED: Always use async for I/O]" |
| **Error Context** | Tool contains error + pattern match | Auto | "database locked: use connection pooling" |
| **Anti-Pattern** | Code matches anti-pattern definitions | Auto | "don't use eval(): security risk" |

### Examples of Embedded Learnings

```python
# ✅ IMPLICIT (Auto-Extracted)
"should use unified logging for consistency"
"always use async/await for blocking I/O"
"never use eval() on user input"
"avoid global state in async functions"

# ✅ EXPLICIT (Agent markers in tool output)
"[LEARNED: Database needs warmup before queries]"
"[LEARNED: Cache invalidation prevents stale reads]"
"[LEARNING: Use connection池 for database stability]"

# ✅ ERROR CONTEXT (Tool failure + pattern match)
"sqlite3.OperationalError: database is locked → Use connection pooling"
"TimeoutError: database not responding → Implement retry logic"
"PermissionError: cannot write file → Check permissions before write"

# ✅ ANTI-PATTERN (Code analysis)
"result = eval(user_input) → Use ast.literal_eval for safety"
"global variable in async function → Use proper state management"
"bare except Exception: pass → Log errors or re-raise"
```

---

## ❌ What Does NOT Get Embedded

### 1. **Normal Tool Success Without Learnings**
```python
# Tool: Write | Outcome: success
Output: "File updated successfully"
→ NOT embedded (no learnings extracted)

# Tool: Edit | Outcome: success  
Output: "Successfully replaced 3 lines"
→ NOT embedded (no learnings extracted)
```

### 2. **Informational Messages**
```python
# Tool: Bash | Outcome: success
Output: "System updated via checkin"
"Configuration loaded"
"Dependencies installed"
→ NOT embedded (informational, not a learning)
```

### 3. **Debug/Trace Output**
```python
# Tool: Bash | Outcome: success
Output: "DEBUG: Process 123 started"
"[TRACE] Entering function main()"
→ NOT embedded (debug output, logging use only)
```

### 4. **Trivial Operations**
```python
# Tool: Grep | Outcome: success
Output: "Found 3 matches"
# Tool: Glob | Outcome: success
Output: "Found 12 files"
→ NOT embedded (too trivial)
```

### 5. **Failed Tool Without Error Context**
```python
# Tool: Bash | Outcome: failure
Output: "Process exited with code 1"
→ Still embedded as failure (but might lack context)
```

---

## 🔄 Complete Flow Decision Tree

```
Tool executed
    │
    ↓
post_tool_process()
    │
    ├─→ Outcome determined
    │   ├─ success
    │   ├─ failure
    │   └─ unknown
    │
    ├─→ Extract learnings (if success/unknown)
    │   ├─ Implicit Learnings?
    │   │   ├─ YES → Record + EMBED
    │   │   └─ NO → Continue
    │   ├─ Explicit Learnings ([LEARNED:])?
    │   │   ├─ YES → Record + EMBED
    │   │   └─ NO → Continue
    │   ├─ Error Context (if outcome == "failure")?
    │   │   ├─ YES → Record + EMBED
    │   │   └─ NO → Continue
    │   └─ Anti-Pattern (from code analysis)?
    │       ├─ YES → Record + EMBED
    │       └─ NO → Continue
    │
    ├─→ Auto-record failure (if outcome == "failure")
    │   ├─ YES → Record + EMBED failure
    │   └─ NO → Continue
    │
    └─→ Check golden rule promotion
        (No embedding involved)
```

---

## 📊 Embedding Conditions Summary Table

| Source Type | Condition | Method | Auto? |
|-------------|-----------|--------|------|
| **Heuristic** | Tool output has `should/always/never/must` | `_store_embedding` | ✅ YES |
| **Learning** | Any learning extraction + `outcome in (success, unknown)` | `_store_embedding` | ✅ YES |
| **Failure** | `outcome == failure` | `_store_embedding` | ✅ YES |
| **Decision** | Agent makes strategic choice | Agent calls `/store` | ❌ NO |
| **Action** | Agent performs action + outcome | Agent calls `/store` | ❌ NO |
| **Pattern** | Agent observes/reports pattern | Agent calls `/store` | ❌ NO |
| **Observation** | Agent notes important event | Agent calls `/store` | ❌ NO |
| **Debug** | Trace/debug output | ❌ NO | 
| **Info** | Informational message | ❌ NO |
| **Trivial** | Simple operation result (read/write success) | ❌ NO |

---

## 🔍 Verification

### Check what's embedded in semantic memory:
```bash
curl -s http://localhost:5001/stats
```

### Search for specific content:
```python
import requests

results = requests.post(
    "http://localhost:5001/search",
    json={"query": "logging", "top_k": 5, "source_type": "heuristic"}
).json()
```

### Check heuristics database:
```bash
sqlite3 memory/index.db "SELECT rule, source_type, created_at FROM heuristics ORDER BY created_at DESC LIMIT 5;"
```

### Check learnings database:
```bash
sqlite3 memory/index.db "SELECT title, summary, created_at FROM learnings ORDER BY created_at DESC LIMIT 5;"
```

---

## 📝 Key Conditions Summary

### LearningProcessor Auto-Embeds IF:

1. **Heuristic Captured**: `tool_output` contains `should/always/never/must` and rule is upserted to heuristics table

2. **Failure Occurred**: `outcome == "failure"` in tool execution result

3. **Learning Extracted**: `outcome in ("success", "unknown")` AND `learnings` extracted with:
   - Implicit patterns (`should`, `always`, etc.)
   - Explicit markers (`[LEARNED:]`, `[LEARNING:]`)
   - Error contexts (tool failed + pattern match found)
   - Anti-patterns (code analysis detected)

### LearningProcessor DOES NOT Embed IF:

1. **Tool success without learnings**: Normal operation without learning patterns

2. **Informational/Debug messages**: Not a learning, just logging

3. **Trivial operations**: Simple file reads/writes without learnings

4. **Agent decisions/actions**: Agent responsibility to call `/store` API

---

## 🎯 Agent vs System Responsibility

| Responsibility | When | Who | Method |
|---------------|------|-----|--------|
| **Strategic Decisions** | Agent makes choice | **Agent** | Call `POST /store` |
| **Actions with Outcomes** | Agent performs action | **Agent** | Call `POST /store` |
| **Pattern Discovery** | Agent observes pattern | **Agent** | Call `POST /store` |
| **Important Observations** | Agent notes trend | **Agent** | Call `POST /store` |
| **Heuristics** | Tool output has pattern | **System** | Auto-embed via `_store_embedding` |
| **Learnings** | Tool output has learning | **System** | Auto-embed via `_store_embedding` |
| **Failures** | Tool execution fails | **System** | Auto-embed via `_store_embedding` |
| **Debug/Info Messages** | Logging/tracing | **None** | Use logger |

---

**End of Document**
