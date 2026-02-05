# Heuristics: database-performance

Generated from failures, successes, and observations in the **database-performance** domain.

---

## H-63: Always avoid SELECT * and use specific column lists with LIMIT for SQL queries to prevent memory accumulation

**Confidence**: 0.95
**Source**: performance-optimization
**Created**: 2026-02-02

Corrected 26 inefficient SELECT * queries that were causing 60-80% unnecessary data transmission and 318 memory leak risks across the codebase

---

