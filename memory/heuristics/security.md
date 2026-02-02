# Heuristics: security

Generated from failures, successes, and observations in the **security** domain.

---

## H-60: Always avoid exec() and validate external API responses

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-02

Found dangerous exec() usage in learning-loop hooks and hardcoded URLs without TLS verification in monitoring.py - critical security vulnerability requiring immediate fix

---

