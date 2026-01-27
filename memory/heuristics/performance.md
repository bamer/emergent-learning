# Heuristics: performance

Generated from failures, successes, and observations in the **performance** domain.

---

## H-3: Database query optimization requires index analysis for tables > 10K rows

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-01-28

Large tables without proper indexes cause slow queries. Monitor row counts and add indexes for frequently queried columns.

---

