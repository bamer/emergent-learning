# Heuristic: Preserve Learning Data Even in Failures

## Domain learning-operations
## Confidence: 0.90
## Status: heuristic

### The Heuristic

Never delete learning artifacts (even apparent failures) without human consultation. What looks like "pollution" may be valuable data showing system behavior, debugging patterns, or evolution.

### When It Applies

**Context:** Learning system maintenance, database cleanup, data archiving

**Trigger:** Considering deletion of learning data (failures, anomalies, etc.)

### The Pattern

```python
# ❌ WRONG - Automatically cleans up "pollution"
def cleanup_failures():
    """Remove old failure embeddings to save space."""
    old_failures = get_old_failures()
    delete(old_failures)  # Lost valuable data!

# ✅ CORRECT - Preserves data with archiving strategy
def cleanup_failures():
    """Archive old failures but preserve for learning."""
    old_failures = get_old_failures()

    # 1. Export to archive (preserves for analysis)
    export_to_archive(old_failures)

    # 2. Remove from active DB (keeps query performance)
    delete_from_active_db(old_failures)

    # 3. Maintain searchable archive (not lost!)
    # 4. Can restore if needed later
```

### Why This Matters

1. **Visible Evolution:** Failures show how system behaved and evolved
2. **Debugging Evidence:** What went wrong, when, how often
3. **Pattern Recognition:** Failure patterns may reveal deeper issues
4. **Testing Ground:** Synthetic failures help train validation
5. **Documentation:** What was attempted, what failed, what we learned

### Real-World Evidence

**Decision Point:** Feb 13, 2026 - 1,300 "failure" embeddings

**Initial Thought:**
"These are false positives polluting the database. I should delete them."

**Second Thought (After Human Input):**
"Wait - these failures show the learning capture system's behavior. They show what commands were executed, what debugging was happening. They're evidence of the bug and its resolution."

**Final Decision:**
- ✅ Retained all 1,300 failures
- ✅ Exported to archive for analysis
- ✅ Restored after temporary removal
- ✅ Now using 15-day archival strategy (not deletion)

### What "Pollution" Actually Contains

**Failure Embeddings Include:**
- Timestamp (when debugging happened)
- Task names (what was being attempted)
- Error patterns (what went wrong)
- Frequency (how often it occurred)
- Timeline (start/stop of issue)

**Value Beyond Obvious:**
- System performance over time
- Command usage patterns
- Debugging workflow evolution
- Correlation with other events
- Evidence for incident post-mortems

### Archiving Strategy

Don't delete - archive:

**0-15 Days:** Keep in active database
**15-90 Days:** Archive to CSV, compress
**90+ Days:** Archive to cold storage, keep searchable
**1+ Years:** Historical archive, maybe delete

**Always:**
- Preserve full content
- Maintain searchable metadata
- Keep backup/restore capability
- Document deletion decisions

### When to Delete (Carefully)

**OK to delete when:**
- User confirms: "This is garbage, no value"
- Duplicate data (verified exact copies)
- Test data (explicitly marked as experimental)
- After thorough review and approval

**Always before deletion:**
- Export to archive
- Human review and confirmation
- Verify no ongoing issues
- Document the deletion decision

### Implementation Checklist

- [ ] Never auto-delete learning data
- [ ] Export to archive before removal from active DB
- [ ] Implement retention policies (not deletion)
- [ ] Human approval required for deletion
- [ ] Document all deletion decisions
- [ ] Maintain searchable archives

### Related Patterns

- **Data Lifecycle:** Define retention stages, not binary delete
- **Archive Strategy:** Export → Compress → Cold → Historical
- **Human-in-Loop:** Critical decisions require approval
- **Version Control:** Dataset changes should be tracked

### Counter-Examples

**Sometimes the data IS worthless:**
- Test runs clearly marked "test/garbage"
- Corrupted data beyond recovery
- Exact duplicates verified
- Privacy concerns (PII)

But even then: Archive first, document decision.

### Real-World Consequences

**Scenario A: Delete Immediately**
- ✅ Short term: Cleaner database
- ❌ Long term: Lost history, can't debug past issues

**Scenario B: Archive and Retain**
- ✅ Short term: Slightly more storage
- ✅ Long term: Full history, can investigate any past issue

**Winner:** Archive and retain

### Validation

**When you see:** "This data is polluting the system"

**Then check:**
1. Does it contain timestamps and patterns?
2. Could it help debug past issues?
3. Is it evidence of system evolution?
4. Could we export to archive instead of delete?

**If answers suggest value:**
- Export to archive
- Document reasons for retention
- Use archival strategy (never delete entirely)

### Learning Sources

**Incident:**
- Database cleanup decision (Feb 13, 2026)
- 1,300 failure embeddings initially removed
- User input corrected decision to preserve
- All data restored and archived

**Command:**
Human confirmed: "decision to retain failure embeddings is correct"

### Times Validated

Initial: 2026-02-13

### Times Violated

Before human input: 1 (deleted 1,300 failures)
After validation: 0 (preserved with archival strategy)

### Quote

> "Failure data is valuable - it shows what went wrong, when, and how often. Preserve it, don't delete it."

---

**Last Updated:** 2026-02-13
**Source:** Human feedback - Data preservation decision
