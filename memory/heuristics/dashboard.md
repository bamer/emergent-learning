# Heuristics: dashboard

Generated from failures, successes, and observations in the **dashboard** domain.

---

## H-105: When counting total checks for Sentinel status, count ALL sentinel_check events without time filter. Otherwise dashboard shows last hour count instead of grand total. Also verify process detection path matches actual running script.

**Confidence**: 1.0
**Source**: observation
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-10

Watch SQL queries with time filters: 'timestamp > datetime("now", "-1 hour")' filters to last hour, not all-time. Use COUNT(*) without time filter for totals.

---

## H-292: Always use proper modal component for detailed views rather than expanding cards in kanban

**Confidence**: 0.7
**Source**: success
**Created**: 2026-02-16

Provides better UX for complex mission details with full logs, output, and action buttons (Restart, Escalate, Archive)

---

## H-293: Never merge large file modifications in single write operations

**Confidence**: 0.9
**Source**: failure
**Created**: 2026-02-16

Large write operations to MissionModal.tsx caused file corruption - use incremental approach with small edits to avoid truncation

---

## H-298: Always implement code splitting with React.lazy() and Suspense for large dashboards to reduce bundle size

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-19



---

