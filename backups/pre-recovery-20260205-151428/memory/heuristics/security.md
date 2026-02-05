# Heuristics: security

Generated from failures, successes, and observations in the **security** domain.

---

## H-60: Always avoid exec() and validate external API responses

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-02

Found dangerous exec() usage in learning-loop hooks and hardcoded URLs without TLS verification in monitoring.py - critical security vulnerability requiring immediate fix

---

## H-64: Always validate file paths to prevent directory traversal attacks

**Confidence**: 0.95
**Source**: observation
**Created**: 2026-02-02

Path traversal vulnerability allows attackers to read arbitrary files. Validate paths contain no '..' sequences and resolve to ensure they stay within allowed directories.

---

