# Heuristics: monitoring

Generated from failures, successes, and observations in the **monitoring** domain.

---

## H-59: Always verify server startup directory when using uvicorn

**Confidence**: 0.8
**Source**: observation
**Created**: 2026-02-02

HTTP 404 on orchestrator endpoint caused by uvicorn running from wrong directory, fixed by ensuring proper working directory

---

## H-230: Post-incident verification at 22:26 UTC - all ELF services recovered after memory exhaustion incident

**Confidence**: 0.95
**Source**: post-incident
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-11

Services restarted at 22:06, system memory recovered to 6.5GB free from 284MB critical. All subsystems operational.

---

## H-241: Sentinel escalation criteria

**Confidence**: 0.8
**Source**: observation
**Project**: `/home/bamer/.opencode`
**Created**: 2026-02-12

Sentinel should only escalate to CEO when actual anomalies are detected, not for routine health checks. Routine checks should be logged but not escalated as 'critical' severity.

---

## H-295: Always verify health endpoint implementations return consistent JSON structure before deploying monitoring scripts

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-18

Health endpoints must return JSON with fields: status, service, overall, timestamp and Content-Type: application/json header. HTML responses or missing 'overall' field break monitoring. Discovered during system analysis where OpenCode returned HTML and Event Bridge lacked 'overall' field.

---

