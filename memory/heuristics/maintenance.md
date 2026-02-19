# Heuristics: maintenance

Generated from failures, successes, and observations in the **maintenance** domain.

---

## H-216: Database rollbacks can affect embedding counts - verify embedding pipeline separately after maintenance

**Confidence**: 0.95
**Source**: auto
**Project**: `/home/bamer/.opencode/emergent-learning`
**Created**: 2026-02-11

Heuristics persisted (117) but embeddings cleaned from old data (15). New embeddings still work perfectly.

---

## H-306: User caches (~/.cache/*) are safe to remove when disk space is critical

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-19

When root partition >85% full, remove user caches: ~/.cache/uv (Python), ~/.cache/pip (pip), ~/.cache/ccache (compiler), ~/.cache/google-chrome, ~/.cache/puppeteer. All rebuild automatically on next use. Recoverable 20-25GB with zero code/data loss. Safe autonomy action,不需要CEO审批.

---

