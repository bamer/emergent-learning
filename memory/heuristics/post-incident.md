# Heuristics: post-incident

Generated from failures, successes, and observations in the **post-incident** domain.

---

## H-231: Monitor service health check endpoints after service restarts - Sentinel process running (PID 832583) but health check showing False for 40+ minutes

**Confidence**: 0.9
**Source**: monitoring
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-11

Sentinel process operational and performing autonomous checks, but /api/v1/health reports sentinel: false. May be health endpoint initialization issue affecting status reporting only.

---

## H-236: Day start verification confirms embedding pipeline working - 20 embeddings confirmed operational after memory crisis incident. llama-server still consuming 46.5GB (critical unresolved)

**Confidence**: 1.0
**Source**: critical-issue
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-12

Memory crisis at 22:04 (284MB free) resolved by terminating processes. CEO reviewed escalation at 23:55 and inbox cleared. However llama-server (14.7GB=46%) is still running - PRIMARY RISK UNRESOLVED.

---

