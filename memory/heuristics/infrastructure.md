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

## H-96: Health summary mechanism provides stale data; always verify process state directly using ps aux before taking action

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-09

Health summary consistently reported Watcher as down despite it running for 69+ minutes. Verified through direct process check each time.

---

## H-99: Use current process paths in health checks

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-10

Health monitoring must use current process locations, not legacy paths. When moving services, update all health check patterns including pgrep, pkill, and restart commands. Issue: unified_orchestrator.py used 'watcher/elf_watcher.py' but actual path is 'core/watcher.py'.

---

## H-100: Fetch metrics from source of truth API

**Confidence**: 0.95
**Source**: observation
**Created**: 2026-02-10

Always fetch health metrics from live API endpoints, not local state or internal queues. Caches become stale, while API provides real-time data. Issue: events_processed used len(self.events) which was always 0.

---

