# Auto-Learning System Documentation

## Overview

The ELF auto-learning system enables continuous knowledge extraction from agent interactions using **three complementary mechanisms**:

1. **Explicit annotations** `[LEARNED:domain] text`
2. **Context-based detection** (error outputs → heuristics)
3. **Pattern matching** (anti-patterns → best practices)

---

## Mechanism 1: Explicit Annotations

### Description
Agents can explicitly mark learnings using special markers in their output.

### Supported Formats
```
[LEARNED:react] Always use refs for callbacks in useEffect
[LEARNED:python] Check file exists before reading
[LEARNING:database] Always verify table exists before querying
[LEARNED] This will be stored with domain='general'
```

### Confidence Levels
- **High (0.9)**: Contains strong directive words (always, never, must)
- **Standard (0.8)**: Default for explicit markers
- **Medium (0.7)**: General statements without directive words

### Example
```python
# In task output:
[LEARNED:security] Never hardcode passwords - use environment variables

# Extracted as heuristic:
{
    "rule": "Never hardcode passwords - use environment variables",
    "domain": "security",
    "confidence": 0.9,
    "source": "explicit_marker"
}
```

---

## Mechanism 2: Context-Based Detection

### Description
When errors occur, the system analyzes the error type and automatically generates preventive heuristics.

### Trigger Conditions
- Task outcome is `"failure"`
- Output contains error keywords (error, exception, failed, traceback, blocker)
- Timeout or permission denied errors

### Error Pattern Mappings

#### Database Errors
```python
("IntegrityError|UNIQUE constraint.*failed",
 "Always check for unique constraints before INSERT")

("sqlite3\.OperationalError.*locked",
 "Database locked - use proper connection management and timeouts")

("no such table",
 "Always verify table exists before querying")
```

#### File System Errors
```python
("FileNotFoundError",
 "Check file exists before accessing")

("Permission denied",
 "Verify file/directory permissions before write operations")

("NotADirectoryError|Is.*is a directory",
 "Use path.is_dir()/is_file() to check path type")
```

#### Network Errors
```python
("ConnectionRefusedError",
 "Service unavailable - check if server is running")

("TimeoutError|timed out",
 "Add proper timeout handling for network requests")

("HTTP 4\d\d",
 "Client error - check request parameters")
```

#### JSON Errors
```python
("JSONDecodeError|Expecting.*delimiter",
 "Validate JSON before parsing")

("json\.loads.*failed",
 "Check JSON structure and encoding")
```

#### Python Errors
```python
("ModuleNotFoundError",
 "Install missing dependencies or check import path")

("ImportError.*No module named",
 "Verify module name and installation")

("AttributeError.*has no attribute",
 "Check object type before accessing attribute")
```

#### AsyncIO Errors
```python
("RuntimeError.*event loop is closed",
 "Check event loop state before scheduling tasks")

("asyncio\.CancelledError",
 "Handle task cancellation gracefully")

("Future.*already awaited",
 "Use proper await patterns, avoid double-await")
```

#### React Errors
```python
("RenderError.*cyclic dependency",
 "Check for circular component dependencies")

("Cannot read.*of (undefined|null)",
 "Add proper null checks before property access")

("Warning.*deprecated",
 "Replace deprecated APIs with modern alternatives")

("Warning.*key prop missing",
 "Always provide unique keys for list items")
```

### Example
```python
# Error output:
Traceback (most recent call last):
  File "app.py", line 42
sqlite3.OperationalError: database is locked

# Extracted heuristic:
{
    "rule": "Database locked - use proper connection management and timeouts",
    "domain": "database",
    "confidence": 0.75,
    "source": "error_context"
}
```

---

## Mechanism 3: Pattern Matching

### Description
Scans code for known anti-patterns and automatically generates best practice heuristics.

### Anti-Pattern Mappings

#### Security Anti-Patterns
```python
("eval\s*\(",
 "Never use eval() - use safe alternatives like literal_eval or JSON parsing")

("exec\s*\(",
 "Never use exec() - dangerous code injection risk")

("shell\s*=\s*True",
 "Avoid shell=True in subprocess - use list of args instead")

('password\s*=\s*[\'"\']',
 "Never hardcode passwords - use environment variables")

('api_key\s*=\s*[\'"\']',
 "Never hardcode API keys - use secrets management")
```

#### Performance Anti-Patterns
```python
("open\(.*(?:(?!with|close).)*",
 "Always use context managers (with statements) for file operations")

("while\s+True:",
 "Infinite loops should have exit conditions")

('recursion.*depth', re.IGNORECASE,
 "For deep recursion, consider iterative alternatives or increase recursion limit")
```

#### Testing Anti-Patterns
```python
("assert.*==", re.IGNORECASE,
 "For floats, use assertAlmostEqual instead of ==")

("time\.sleep\(.*test", re.IGNORECASE,
 "Avoid time.sleep() in tests - use mocks instead")

("open\(.*test", re.IGNORECASE,
 "Use tempfile or fixtures in tests instead of real files")
```

### Example
```python
# Code output:
# Bad code:
result = eval(user_input)

# Detected anti-pattern:
{
    "rule": "Never use eval() - use safe alternatives like literal_eval or JSON parsing",
    "domain": "security",
    "confidence": 0.7,
    "source": "anti_pattern"
}
```

---

## Learning Confidence Hierarchy

| Source | Confidence | Notes |
|--------|-----------|-------|
| Explicit marker with directive words | 0.9 | Highest trust |
| Explicit marker (standard) | 0.8 | User-intentional |
| Error context | 0.75 | Inferred from actual failure |
| Anti-pattern match | 0.7 | Inferenced from code patterns |
| Implicit text extraction | 0.6 | Lowest confidence |

---

## Deduplication

The system automatically deduplicates learnings based on:
- **Rule text** (case-insensitive)
- **Higher confidence wins** when duplicates exist
- **Source tracking** to understand provenance

---

## Storage in Database

All learnings are stored in the `heuristics` table:

```sql
INSERT INTO heuristics (domain, rule, explanation, confidence, source_type, created_at)
VALUES (?, ?, 'Auto-extracted from task output', ?, ?, ?)
ON CONFLICT(domain, rule) DO UPDATE SET
    times_validated = times_validated + 1,
    confidence = MIN(1.0, confidence + 0.05),
    updated_at = CURRENT_TIMESTAMP
```

### Source Types
- `explicit_marker`: Mechanism 1 - explicit annotations
- `error_context`: Mechanism 2 - error-based detection
- `anti_pattern`: Mechanism 3 - pattern matching
- `implicit`: Implicit text extraction (original mechanism)
- `auto`: Original auto-extraction mechanism

---

## Integration Points

### 1. Learning Processor (`core/learning_processor.py`)
- `extract_implicit_learnings()` - Original mechanism
- `_extract_explicit_learnings()` - Mechanism 1
- `_extract_error_context_learnings()` - **NEW** Mechanism 2
- `_extract_anti_pattern_learnings()` - **NEW** Mechanism 3

### 2. Post Tool Hook (`hooks/learning-loop/post_tool_learning.py`)
- `extract_implicit_learnings()` - Original mechanism
- `extract_explicit_learnings()` backup - Mechanism 1
- `extract_error_context_learnings()` - **NEW** Mechanism 2
- `extract_anti_pattern_learnings()` - **NEW** Mechanism 3

---

## Usage Examples

### Example 1: Explicit Learning
```python
# Agent output after fixing a bug:
[LEARNED:react] useEffect with callback deps causes reconnect loops - use refs for callbacks

# System extracts and stores:
{
    "rule": "useEffect with callback deps causes reconnect loops - use refs for callbacks",
    "domain": "react",
    "confidence": 0.9,
    "source": "explicit_marker"
}
```

### Example 2: Error Context Learning
```python
# Task fails with error:
FileNotFoundError: [Errno 2] No such file or directory: 'config.yaml'

# System automatically extracts:
{
    "rule": "Check file exists before accessing",
    "domain": "filesystem",
    "confidence": 0.75,
    "source": "error_context"
}
```

### Example 3: Anti-Pattern Detection
```python
# Agent writes code:
password = "hardcoded123"  # TODO: remove this

# System detects anti-pattern:
{
    "rule": "Never hardcode passwords - use environment variables",
    "domain": "security",
    "confidence": 0.7,
    "source": "anti_pattern"
}
```

---

## Testing

### Test Explicit Markers
```bash
python -c "
from learning_processor import extract_learnings
text = '[LEARNED:security] Check before eval'
learnings = extract_learnings(text)
print(learnings)
"
```

### Test Error Detection
```bash
python -c "
from learning_processor import extract_learnings
text = 'FileNotFoundError: config.json not found'
learnings = extract_learnings(text, outcome='failure')
print(learnings)
"
```

### Test Anti-Patterns
```bash
python -c "
from learning_processor import extract_learnings
text = 'result = eval(user_input)'
learnings = extract_learnings(text)
print(learnings)
"
```

---

## Configuration Patterns

### Adding New Error Patterns
Edit `ERROR_PATTERN_HEURISTICS` in the relevant file:
```python
ERROR_PATTERN_HEURISTICS = {
    "your_domain": [
        (r"YourErrorPattern", "Your preventive heuristic"),
        (r"AnotherPattern", "Another heuristic"),
    ],
}
```

### Adding New Anti-Patterns
Edit `ANTI_PATTERN_HEURISTICS`:
```python
ANTI_PATTERN_HEURISTICS = {
    "your_domain": [
        (r"bad_pattern", "Best practice alternative"),
        ("another_bad_regex", "better approach"),
    ],
}
```

---

## Benefits

1. **Continuous** - Operates automatically on every tool execution
2. **Multi-source** - Combines explicit user intent with inferred patterns
3. **Self-correcting** - Confidence increases with validation, decreases with failures
4. **Domain-aware** - Heuristics are categorized by domain for relevance
5. **Provenance tracking** - Source type indicates how learning was derived

---

## Limitations

1. **False positives** - Pattern matching may incorrectly flag benign code
2. **Over-generalization** - Error context may produce overly broad heuristics
3. **Context loss** - Heuristics lose some context from original events
4. **Validation needed** - Low-confidence learnings require human review

---

## Future Enhancements

- [ ] Machine learning model for better pattern recognition
- [ ] Semantic similarity-based deduplication
- [ ] Cross-domain heuristic linking
- [ ] Confidence-based suggestion prompting
- [ ] Heuristic A/B testing framework
- [ ] User feedback loop for learning quality
