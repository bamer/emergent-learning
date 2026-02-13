# Heuristics: dashboardmonitoring

Generated from failures, successes, and observations in the **dashboardmonitoring** domain.

---

## H-253: System Health real-time data

**Confidence**: 0.95
**Source**: failure
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-12

The System Health model card was showing stale/empty data because the system_health table only had 2 records from Feb 1 and Feb 9. Fixed by adding generate_realtime_health() function that calculates live metrics: db size, disk space, git status, stale locks, and database integrity. The endpoint now generates real-time data when table is empty or data is older than 5 minutes.

---

