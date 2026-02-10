# Heuristics: dashboard

Generated from failures, successes, and observations in the **dashboard** domain.

---

## H-105: When counting total checks for Watcher status, count ALL watcher_check events without time filter. Otherwise dashboard shows last hour count instead of grand total. Also verify process detection path matches actual running script.

**Confidence**: 1.0
**Source**: observation
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-10

Watch SQL queries with time filters: 'timestamp > datetime("now", "-1 hour")' filters to last hour, not all-time. Use COUNT(*) without time filter for totals.

---

