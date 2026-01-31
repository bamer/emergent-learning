# Heuristics: system-migration

Generated from failures, successes, and observations in the **system-migration** domain.

---

## H-25: Table Structure Migration > Dashboard API

**Confidence**: 0.7
**Source**: observation
**Created**: 2026-01-30

When dashboard shows empty but query system works, check table schema mismatch between router expectations and actual table structure. Migrate old table to new schema rather than patching router for future compatibility.

---

