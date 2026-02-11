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

