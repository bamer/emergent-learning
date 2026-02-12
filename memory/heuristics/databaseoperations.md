# Heuristics: databaseoperations

Generated from failures, successes, and observations in the **databaseoperations** domain.

---

## H-251: Metrics table explosion crisis

**Confidence**: 0.95
**Source**: failure
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-12

The metrics table accumulated 564 MB (89,097 event records) in 1.5 days, driven by message.part.updated (20,485), message.updated (4,382), and lsp.diagnostics events. Emergency procedures: delete old metrics, implement retention policy (keep 12 hours max), reduce event logging frequency, or disable non-essential metrics collection.

---

