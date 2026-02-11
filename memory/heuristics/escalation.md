# Heuristics: escalation

Generated from failures, successes, and observations in the **escalation** domain.

---

## H-27: ELF sentinel system in critical state with repeated escalation failures - requires immediate CEO intervention

**Confidence**: 0.9
**Source**: system-monitoring
**Created**: 2026-01-30



---

## H-203: Distinguish between service unreachable and empty response in escalations

**Confidence**: 0.9
**Source**: observation
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-11

Before reporting empty health payload, check actual HTTP status code. 404 = service down, not empty payload bug. This misdiagnosis wastes debugging time.

---

