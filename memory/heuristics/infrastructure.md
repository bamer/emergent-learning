# Heuristics: infrastructure

Generated from failures, successes, and observations in the **infrastructure** domain.

---

## H-65: Database tables can disappear while file remains intact

**Confidence**: 0.9
**Source**: failure
**Created**: 2026-02-02

Self-test failed at database integrity check - failures table missing. Database file exists (4MB) but core tables are gone, causing all database operations to fail.

---

## H-93: Treat >90% disk usage as critical; trigger automatic cleanup before escalation.

**Confidence**: 0.85
**Source**: observation
**Created**: 2026-02-09

Disk pressure caused service instability on 2026-02-09 when usage reached ~92%. Log cleanup of ~174MB resolved the issue.

---

## H-94: After escalation is resolved, clear escalation counter and archive files to prevent residual flags

**Confidence**: 0.8
**Source**: observation
**Created**: 2026-02-09

Residual escalation_count=1 persisted after services recovered autonomously. Archiving escalation files documents resolution and clears state.

---

## H-95: After resolving escalations, immediately archive resolved documents and resolution notes to prevent false-positive escalation_count alerts

**Confidence**: 0.85
**Source**: observation
**Created**: 2026-02-09

Watcher counted 2 'escalations' that were actually resolved documents and notes from earlier in the day. Archiving to archive/ directory prevented false positives.

---

