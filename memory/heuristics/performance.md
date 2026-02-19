# Heuristics: performance

Generated from failures, successes, and observations in the **performance** domain.

---

## H-3: Database query optimization requires index analysis for tables > 10K rows

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-01-28

Large tables without proper indexes cause slow queries. Monitor row counts and add indexes for frequently queried columns.

---

## H-33: Always use async database operations in async contexts

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-01-31

Synchronous SQLite calls in async contexts block the entire event loop, causing significant performance degradation. Use aiosqlite or connection pools for all database operations in async code.

---

## H-34: Implement batch operations for multiple database writes

**Confidence**: 0.85
**Source**: observation
**Created**: 2026-01-31

Individual database calls in loops create N+1 query problems. Use batch operations (executemany) to reduce round trips and improve transaction efficiency.

---

## H-35: Cache frequently accessed data to reduce I/O overhead

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-01-31

Repeated reads of the same data (session state, golden rules, file contents) cause unnecessary I/O. Implement caching with TTL and invalidation strategies.

---

## H-62: Automated SQL optimization with SELECT column lists instead of SELECT *

**Confidence**: 0.95
**Source**: observation
**Created**: 2026-02-02

Successfully optimized 26 SQL queries by replacing SELECT * with specific column lists, added memory limits to 318 locations, and created 64 database indexes (45 simple + 19 composite) for 60-80% performance improvement

---

## H-112: Object pooling essential for Godot with many projectiles

**Confidence**: 0.7
**Source**: orchestration
**Project**: `/home/bamer/shootemup_game`
**Created**: 2026-02-10

Pool sizes: 50 projectiles, 20 enemies maintains 60 FPS during intense combat

---

## H-300: Monitor Core Web Vitals (LCP, FID, CLS) in real-time to catch performance regressions early

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-19



---

