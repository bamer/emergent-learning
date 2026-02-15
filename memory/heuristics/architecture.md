# Heuristics: architecture

Generated from failures, successes, and observations in the **architecture** domain.

---

## H-50: Mission systems must bridge fire-and-forget APIs with persistent task tracking - creating task files in ~/.opencode/tasks/ enables Task Kanban visibility

**Confidence**: 0.6
**Source**: observation
**Created**: 2026-02-01



---

## H-61: FastAPI routers with prefix and middleware provide excellent API structure

**Confidence**: 0.85
**Source**: observation
**Created**: 2026-02-02

The Emergent Learning Framework demonstrates excellent API architecture with 15+ specialized routers, proper middleware integration, CORS handling, security headers, and structured documentation - this pattern should be replicated in similar systems

---

## H-283: ** Incomplete resource management implementations often create more risk than no implementation at all **

**Confidence**: 0.4
**Source**: observation
**Created**: 2026-02-15



---

## H-290: God Object anti-pattern: When a file exceeds 500 lines, consider splitting into modules. The modal.js at 1071 lines was refactored into 5 focused modules (~150 lines each) for better maintainability.

**Confidence**: 0.9
**Source**: success
**Created**: 2026-02-15

Large files become unmaintainable. Split by responsibility: each modal type (expense, revenue, invoice) gets its own module with a factory to orchestrate.

---

