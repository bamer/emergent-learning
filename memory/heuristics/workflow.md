# Heuristics: workflow

Generated from failures, successes, and observations in the **workflow** domain.

---

## H-297: Always document observed system behaviors during analysis before proposing fixes

**Confidence**: 0.95
**Source**: observation
**Created**: 2026-02-18

When debugging system issues, capture current state first (behaviors, evidence, patterns) before designing remediation. This creates clear baseline and prevents fix-guessing. Discovered during Sentinel escalation where documenting actual service behaviors (HTML responses, wrong ports, duplicate data) provided clear remediation path.

---

