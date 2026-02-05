# Heuristics: infrastructure

Generated from failures, successes, and observations in the **infrastructure** domain.

---

## H-65: Database tables can disappear while file remains intact

**Confidence**: 0.9
**Source**: failure
**Created**: 2026-02-02

Self-test failed at database integrity check - failures table missing. Database file exists (4MB) but core tables are gone, causing all database operations to fail.

---

