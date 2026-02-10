# Heuristics: logging

Generated from failures, successes, and observations in the **logging** domain.

---

## H-147: Always use unified ELF logger (get_logger, log_debug) instead of custom _log_debug methods or print statements

**Confidence**: 0.9
**Source**: observation
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-10

Replaced custom _log_debug() functions with unified ELF logger across 4 files (context.py, core.py, session_integration.py, queries/base.py). Pattern: import get_logger, log_debug from Open_ELF.utils.elf_logging, then replace self._log_debug(msg) with log_debug('module_name', msg). This ensures consistent logging format and centralized log management.

---

