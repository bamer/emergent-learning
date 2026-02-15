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

Sentinel counted 2 'escalations' that were actually resolved documents and notes from earlier in the day. Archiving to archive/ directory prevented false positives.

---

## H-96: Health summary mechanism provides stale data; always verify process state directly using ps aux before taking action

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-09

Health summary consistently reported Sentinel as down despite it running for 69+ minutes. Verified through direct process check each time.

---

## H-99: Use current process paths in health checks

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-10

Health monitoring must use current process locations, not legacy paths. When moving services, update all health check patterns including pgrep, pkill, and restart commands. Issue: unified_orchestrator.py used 'sentinel/elf_sentinel.py' but actual path is 'core/sentinel.py'.

---

## H-100: Fetch metrics from source of truth API

**Confidence**: 0.95
**Source**: observation
**Created**: 2026-02-10

Always fetch health metrics from live API endpoints, not local state or internal queues. Caches become stale, while API provides real-time data. Issue: events_processed used len(self.events) which was always 0.

---

## H-145: Always use the unified ELF logger (Open_ELF.utils.elf_logging) for ALL logging. NEVER use print() or exotic loggers. The unified logger provides: centralized file logging, database event logging, crash policy enforcement, and consistent formatting across all agents.

**Confidence**: 1.0
**Source**: observation
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-10

Using print() or exotic loggers defeats the purpose of a unified logging system. The ELF unified logger ensures all logs go to the same location, have consistent formatting, and can be tracked in the database. Print statements bypass this and make debugging and monitoring difficult.

---

## H-205: Always use unified logging - All ELF components MUST import from Open_ELF.utils.elf_logging.get_logger()

**Confidence**: 0.95
**Source**: observation
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-11

Unified logging ensures consistent format, centralized rotation, crash policy support, and proper management across all components. Using basic logging causes fragmentation and misses crash policy benefits.

---

## H-206: Never use polling for event streaming - SSE connections only

**Confidence**: 0.95
**Source**: observation
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-11

Polling causes excessive connection overhead and system failures under load. SSE provides real-time event delivery with single persistent connection, preventing connection storms and resource exhaustion.

---

## H-211: Always verify API endpoint URLs before deployment - Wrong URLs cause silent failures

**Confidence**: 1.0
**Source**: auto
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-11

Background learning script posted to wrong URL causing 11 days of embedding failures

---

## H-220: Critical service failure detected at 22:04 UTC - EventBridge and Sentinel not running after system memory recovery from 284MB to 6.5GB free

**Confidence**: 1.0
**Source**: monitoring
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-11

Memory crisis resolved by system actions, but ELF services stopped and need restart

---

## H-232: EventBridge restarted again at 23:13 UTC - Second restart of the session after memory incident. Load average improved to 2.52 from 11+ (external processes likely stopped).

**Confidence**: 1.0
**Source**: monitoring
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-11

First restart at 22:06 after memory exhaustion. Second restart at 23:13 possibly for recovery or maintenance.

---

## 🥇 GR-233: All log files MUST be written to the unified ELF log directory at /home/bamer/.opencode/emergent-learning/Open_ELF/logs/. No exceptions.

**Confidence**: 1.0 (GOLDEN RULE)
**Source**: observation
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-12
**Validations**: 0
**Violations**: 0

This ensures centralized log management for the emergent learning framework.


---

## H-270: Always check for recent CEO decisions before creating new escalations - CEO may have already taken action

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-14

Escalations created at 12:34 was outdated because CEO had intervened at 12:32 with direct user instruction. Must verify escalation inbox/processed folder for recent CEO actions before escalating

---

## H-271: EventChronicle is the events table - not named 'events' table

**Confidence**: 1.0
**Source**: observation
**Created**: 2026-02-14

When querying for events, use event_chronicle table, not events table. Events are stored in event_chronicle table with proper schema.

---

## H-272: High load from external LLM servers (llama-server) often causes elevated but acceptable system load - ELF systems remain unaffected if EventBridge/Orchestrator CPU stays below 10% and swap usage remains 0%

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-14

Load average of 17.97 with ELF systems at 0% CPU indicates external LLMinference workload. Monitor ELF systems, not overall load. External user processes cannot be intervened with.

---

## H-273: Rapid memory declines (>12GB in <1 hour) without ELF system degradation indicate external user process memory bloat - monitor available RAM and swap. Escalate only when available RAM < 500 MB or swap > 5%, not based on overall memory percentage

**Confidence**: 0.95
**Source**: observation
**Created**: 2026-02-14

External processes (llama-server 2.4GB, opencode 2.7GB, code-insiders 1.6GB, godot 1.2GB) can cause rapid RAM decline. ELF systems unaffected until swap engages. Monitor actual available RAM in GB, not percentage.

---

## H-278: Git LFS orphaned objects can accumulate to tens of GB - run 'git lfs prune'定期清理孤立的 LFS 对象 (Git LFS orphaned objects can accumulate to tens of GB - run 'git lfs prune' periodically)

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-15



---

## H-280: Large Git LFS storage (>10GB) indicates orphaned objects - run 'git lfs prune --dry-run' first to preview cleanup impact

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-15



---

