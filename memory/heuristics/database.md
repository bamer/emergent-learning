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

## H-276: SQLite CHECK constraints are not easily removable. To allow new values, either recreate the table or simply remove the CHECK constraint entirely and validate in application code instead.

**Confidence**: 0.9
**Source**: success
**Created**: 2026-02-15

When expanding from 5 to 50+ categories, the CHECK(category IN ('food', 'drinks', ...)) constraint blocked new values. Removed constraint from schema.sql and validate in app code.

---

## H-296: Always implement UNIQUE constraints and upsert logic for tables with high-volume duplicate-prone data

**Confidence**: 0.95
**Source**: observation
**Created**: 2026-02-18

Discovered trails table had 79% duplication (142,959 trails vs 1,808 unique). Without UNIQUE constraint on (run_id, location) and INSERT OR REPLACE logic, duplicates accumulate unchecked, wasting storage and degrading query performance.

---

## H-304: Composite covering indexes on date+category+amount columns provide 43% performance improvement for aggregation queries on SQLite with 60K+ records

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-19



---

