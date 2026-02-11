# Heuristics: python

Generated from failures, successes, and observations in the **python** domain.

---

## H-207: Use relaxed timeouts - minimum 20 seconds, up to 10 minutes for async operations

**Confidence**: 0.95
**Source**: observation
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-11

Aggressive timeouts cause false failures. SSE: 5-10 minutes. API calls: 60-120 seconds. Database: 30-60 seconds. Long-running tools: 2-5 minutes. Semantic search: 60 seconds. Relaxed timeouts accommodate network latency, processing delays, and prevent unnecessary retries.

---

## H-208: Always use async/await for all new development - No blocking I/O in async functions

**Confidence**: 1.0
**Source**: observation
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-11

Async/await enables non-blocking I/O, prevents resource exhaustion, enables concurrent processing. Use aiosqlite for DB, aiohttp for HTTP, aiofiles for file I/O. Use asyncio.gather for concurrent tasks. Use asyncio.Semaphore for rate limiting. NO blocking operations (sqlite3, requests, open) in async code.

---

