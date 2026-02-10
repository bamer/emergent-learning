# Heuristics: error-handling

Generated from failures, successes, and observations in the **error-handling** domain.

---

## H-146: NEVER silently ignore errors. Every error MUST be either logged with the unified ELF logger OR raised (or both). Use logger.error() with exc_info=True for exception details. Bare 'except:' or 'except Exception:' blocks without logging are strictly forbidden.

**Confidence**: 1.0
**Source**: observation
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-10

Silently swallowing errors makes debugging impossible and hides real problems. The 'ça marche ou ça crash' philosophy means we should either handle errors properly with logging or let the system crash visibly. Logging errors with exc_info=True provides stack traces for troubleshooting.

---

## H-148: Never silently swallow exceptions - always log errors with log_debug() or re-raise

**Confidence**: 0.95
**Source**: observation
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-10

Enforced error logging across 12 ELF files. Pattern: replace 'except Exception: pass' with 'except Exception as e: log_debug("module", f"Error: {e}")'. Never silently swallow exceptions - always log or re-raise. This ensures visibility into failures and prevents silent bugs.

---

