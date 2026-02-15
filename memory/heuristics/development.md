# Heuristics: development

Generated from failures, successes, and observations in the **development** domain.

---

## H-32: Always read surrounding code and understand intent before implementing TODO comments

**Confidence**: 0.8
**Source**: observation
**Created**: 2026-01-31

Analysis of TODO fixing pattern reveals context-first approach prevents overengineering and breaking changes

---

## H-268: Separate frontend files for parallel agent processing

**Confidence**: 0.9
**Source**: observation
**Created**: 2026-02-14

Always use separate files: utils, api client, router, and each panel. This enables parallel execution without file write conflicts.

---

## H-269: Never manually kill/restart development server - User manages dev server

**Confidence**: 1.0
**Source**: observation
**Created**: 2026-02-14

The user controls and manages the development server lifecycle. Do not attempt to kill or restart processes running on development ports. Always test existing server before attempting to modify.

---

