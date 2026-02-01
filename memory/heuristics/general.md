# Heuristics: general

Generated from failures, successes, and observations in the **general** domain.

---

## H-1: Schema migration failures need auto-repair protocol

**Confidence**: 0.7
**Source**: observation
**Created**: 2026-01-27

When schema migrations fail with missing column/table errors, the database structure is out of sync with the model expectations. Create a comprehensive repair script that: 1) identifies all required columns from model definitions, 2) adds missing columns with appropriate defaults, 3) creates missing tables with full structure, 4) validates repairs by testing queries.

---

## H-56: Not all tasks require complex analysis - simple requests should get direct responses without over-engineering This is a valuable heuristic about recognizing when to apply minimal vs. maximal effort, which is crucial for efficiency and avoiding unnecessary complexity.

**Confidence**: 0.6
**Source**: observation
**Created**: 2026-02-01



---

