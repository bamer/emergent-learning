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

## H-209: Handle FTS5 shadow table corruption - Drop orphaned shadows and recreate virtual table

**Confidence**: 0.9
**Source**: observation
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-11

After crashes, FTS5 external content tables can have orphaned shadow tables (embeddings_fts_data, _idx, _docsize, _config) without the main virtual table. Detect this by checking if virtual table exists but shadows don't, or vice versa automatically. Drop orphaned tables and recreate with 'CREATE VIRTUAL TABLE embeddings_fts USING fts5(...)'. Log all repair operations.

---

