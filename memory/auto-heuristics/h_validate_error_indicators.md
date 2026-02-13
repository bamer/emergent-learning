# Heuristic: Validate Actual Error Indicators

## Domain autonomous-operations
## Confidence: 0.95
## Status: heuristic

### The Heuristic

Always validate for **actual error indicators** in output content before recording a failure. An "unknown" outcome means insufficient information, not a failed operation.

### When It Applies

**Context:** Auto-failure capture systems, learning capture, outcome classification

**Trigger:** Recording tool/command outputs as failures

### The Pattern

```python
# ❌ WRONG - Records "unknown" as failure
if outcome == "unknown":
    record_failure(event)

# ✅ CORRECT - Only record if actual errors present
if outcome == "unknown":
    # Check for real error indicators
    error_patterns = [r"\b(error|exception|failed|traceback)\b"]
    has_error = any(re.search(p, output) for p in error_patterns)

    if has_error:
        record_failure(event)
    else:
        # This is just pending/undetermined, not a failure
        skip_or_mark_pending(event)
```

### Why This Matters

1. **Prevents False Positives:** Internal debugging commands aren't real failures
2. **Accurate Learning:** System learns from real failures, not noise
3. **Prevents Pollution:** False failures contaminate learning data
4. **Credible Signals:** Real failure patterns become recognizable

### Real-World Evidence

**Incident:** Feb 11-13, 2026 - 1,300 false-positive failures captured

**What Happened:**
- Learning capture system recorded "unknown" outcomes as failures
- Internal ELF commands like "Check X", "Verify Y" were classified as failures
- Created database pollution and wasted storage

**Fix Applied:**
```python
# Added validation before recording failure
actual_error_patterns = [
    r"\b(error|exception|failed|could not|unable to|permission denied|traceback|blocker)\b",
]
has_actual_error = any(re.search(p, output_content) for p in actual_error_patterns)

if not has_actual_error:
    logger.debug(f"[AUTO_FAILURE_SKIP] Not an actual failure (outcome='unknown')")
    return
```

**Result:** Failures stopped immediately (0 new failures after fix)

### Key Indicators

**True Failures Have:**
- Error messages: "Error:", "Exception:", "Permission denied"
- Stack traces
- Failure keywords: "failed", "could not", "unable to"
- Blocker indicators: "[BLOCKER]"

**False "Failures" Look Like:**
- Task descriptions: "Check X", "Verify Y", "Test Z"
- Unknown outcomes: Insufficient data to determine success/failure
- Pending states: Command not yet executed
- Diagnostic output

### Implementation Checklist

- [ ] Add error pattern validation before recording failures
- [ ] Skip internal system commands (check tool name/input)
- [ ] distinguish "unknown" from "failed" outcomes
- [ ] Add logging for skipped failures (monitoring)
- [ ] Test with both real and false failures

### Related Patterns

- **Internal Event Skip:** Flag internal commands separately
- **Outcome Classification:** Use explicit states (pending/success/failure/unknown)
- **Error Pattern Library:** Maintain reusable pattern list
- **Monitoring:** Track skip/reject rates for quality control

### Counter-Examples

**Do NOT skip when:**
- Output contains actual error patterns
- User explicitly reports failure
- Tool returns error code/exception
- Operation clearly failed

### False Positives to Avoid

Pattern like these are NOT failures if no actual error:
- "Check for errors" (checking is not an error)
- "Without errors" (negative validation)
- "Error handling" (implementation detail)
- "Fixed the error" (resolution, not failure)

### Validation

**When you see:** A new failure being recorded

**Then check:**
1. Does the output contain actual error patterns?
2. Is this an internal system command?
3. Is the outcome actually "unknown" vs "failed"?
4. Should this be skipped as not a real failure?

**If answers suggest false positive:**
- Don't record as failure
- Log as skipped with reason
- Review classification logic

### Learning Sources

**Incident:**
- Critical health check failure loop (Feb 11-13, 2026)
- 1,300 false-positive failures in 48 hours
- Root cause: Missing error indicator validation

**Git History:**
- Commit `3d06715` (Feb 12, 2026) - Applied fix
- File: `core/learning_processor.py`

### Times Validated

Initial: 2026-02-13 (after incident resolution)

### Times Violated

Before fix: 1,300+ violations (false positives)
After fix: 0 violations (working correctly)

---

**Last Updated:** 2026-02-13
**Source:** Autonomous remediation - Incident analysis
