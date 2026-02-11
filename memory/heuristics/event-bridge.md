# Heuristics: event-bridge

Generated from failures, successes, and observations in the **event-bridge** domain.

---

## H-201: Always provide a catch-all /api/v1/health endpoint for system-wide health monitoring

**Confidence**: 0.95
**Source**: observation
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-11

Sentinel needs a general /api/v1/health endpoint to monitor overall system health. Sub-routes alone are insufficient.

---

