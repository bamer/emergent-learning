# Heuristics: securitysafety

Generated from failures, successes, and observations in the **securitysafety** domain.

---

## H-103: No external write or read outside of the project directory

**Confidence**: 1.0
**Source**: observation
**Created**: 2026-02-10

All file operations must be contained within the project directory. Never write to system directories, /tmp (unless explicitly temporary), home directory outside project, or any external paths. This prevents accidental system modifications, keeps project self-contained, and ensures portability. All assets, configs, cache, builds must be within the project structure. Exception: Read-only access to system libraries/engines (like Godot installation). Project directory is defined as the git repository root or project.godot location.

---

