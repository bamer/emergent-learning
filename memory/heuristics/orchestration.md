# Heuristics: orchestration

Generated from failures, successes, and observations in the **orchestration** domain.

---

## H-113: Orchestrator Workflow: PLAN (ask specialist for plan) → DELEGATE (parallel implementation) → REVIEW (Reviewer validates work) → ITERATE (reject = send back for correction, approve = next task) → FINAL (update CHANGELOG). Quality gate ensures no defective work advances.

**Confidence**: 1.0
**Source**: observation
**Created**: 2026-02-10

Golden Rule #200: Systematic orchestration with review gate. Ask specialist to plan, delegate in parallel to multiple specialists for implementation, review with Reviewer agent for quality control (max 3 corrections), only move to next task when approved. Update changelog AFTER full workflow complete, not per-task.

---

## H-114: Orchestrator Golden Rule #200 SUCCESS: Successfully executed PLAN→DELEGATE→REVIEW→FINAL protocol for R-Type refactoring. Agent godot-gdscript-patterns implemented 4 tasks, code-reviewer APPROVED all on first iteration, CHANGELOG updated. Autonomous execution time: 75 seconds for 4 tasks vs manual ~60 minutes. Acceleration: ~48:1.

**Confidence**: 1.0
**Source**: observation
**Created**: 2026-02-10

Real-world validation of Orchestrator workflow protocol. Quality gate (code-reviewer) prevents defects, ensures ELF compliance. Autonomous orchestration achieves massive time acceleration with code quality guarantee.

---

