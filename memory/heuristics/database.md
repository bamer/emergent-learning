# Heuristics: database

Generated from failures, successes, and observations in the **database** domain.

---

## H-104: Always include project_path in INSERT statements when recording heuristics and learnings to maintain project-specific context

**Confidence**: 1.0
**Source**: observation
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-10

Fixed systemic data quality issue where 100% of entries (499 total) lacked project_path, causing cross-project contamination. The domain extraction bug also created garbage domains like 'recommendation:' from parsing artifacts.

---

