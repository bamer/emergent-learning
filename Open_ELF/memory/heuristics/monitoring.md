# Heuristics: monitoring

Generated from failures, successes, and observations in the **monitoring** domain.

---

## H-59: Always verify server startup directory when using uvicorn

**Confidence**: 0.8
**Source**: observation
**Created**: 2026-02-02

HTTP 404 on orchestrator endpoint caused by uvicorn running from wrong directory, fixed by ensuring proper working directory

---

