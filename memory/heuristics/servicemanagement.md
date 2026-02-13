# Heuristics: servicemanagement

Generated from failures, successes, and observations in the **servicemanagement** domain.

---

## H-254: Learning Capture service activation

**Confidence**: 0.95
**Source**: success
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-12

Learning Capture service was inactive because background-learning-capture.py was not running. Started the service manually. The service monitors system activity and auto-captures heuristics every 60 seconds. It records learnings, heuristics, and trails to the database. Total learnings captured: 1,809 (411 successes, 1,397 failures).

---

## H-255: Orchestrator auto-start services architecture

**Confidence**: 0.95
**Source**: success
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-12

Implemented _ensure_services_started() method in UnifiedOrchestrator to auto-start essential services (EventBridge, Learning Capture, Sentinel) on initialization. This eliminates need for crontab/systemd by having Orchestrator manage its own dependencies. Services are started in proper order: EventBridge first (critical), then Learning Capture, then Sentinel. The orchestrator also performs health checks every 100 seconds and can restart failed services automatically.

---

