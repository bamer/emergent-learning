# Heuristics: javascript

Generated from failures, successes, and observations in the **javascript** domain.

---

## H-275: ES6 export syntax (export default) cannot be used in scripts loaded without type=module. Always remove export statements when converting ES6 modules to regular script tags.

**Confidence**: 0.95
**Source**: failure
**Created**: 2026-02-15

When loading JS files as regular <script> tags (not type=module), ES6 export syntax causes 'Unexpected token export' errors. Fixed by removing export statements and using window.Toast = Toast instead.

---

