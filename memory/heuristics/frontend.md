# Heuristics: frontend

Generated from failures, successes, and observations in the **frontend** domain.

---

## H-274: DataTable date filter - event binding code existed but HTML elements were never created in _createControls(). Always verify that UI elements are actually created when you have event binding code that expects them.

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-15

The DataTable had code to bind date filter events but never created the date input HTML elements. Fixed by adding the HTML creation in _createControls() method.

---

