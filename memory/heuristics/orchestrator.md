# Heuristics: orchestrator

Generated from failures, successes, and observations in the **orchestrator** domain.

---

## H-200: Verify EventBridge is running before checking /api/v1/health endpoint

**Confidence**: 0.9
**Source**: observation
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-11

HTTP 404 means service down, not empty payload. When Sentinel reports empty health payload, first check if service is running.

---

