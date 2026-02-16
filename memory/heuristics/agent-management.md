# Heuristics: agent-management

Generated from failures, successes, and observations in the **agent-management** domain.

---

## H-294: Always use dynamic agent discovery via client.app.agents() instead of hardcoded catalogs

**Confidence**: 0.9
**Source**: success
**Created**: 2026-02-16

OpenCode API provides comprehensive agent list that stays synchronized with available agents. Hardcoded catalogs cause 'Agent Unknown' errors when agents are renamed or new agents are added.

---

