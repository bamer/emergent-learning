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

## H-305: EventBridge must exist and be running before Unified Orchestrator can start

**Confidence**: 1.0
**Source**: observation
**Created**: 2026-02-19

Unified Orchestrator has hard dependency on EventBridge (port 9998). EventBridge is SSE client connecting to OpenCode. If missing, orchestrator exits with dependency error immediately. Always verify event_bridge.py exists at ~/Open_ELF/orchestrator/event_bridge.py and is running on port 9998 before starting orchestrator.

---

