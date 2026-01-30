# Proposal: Systematic File Analysis for Project Identification

**Type:** heuristic
**Confidence:** 0.7
**Source Sessions:** [2025-01-31_15-44-16-checkin.jsonl]
**Domain:** debugging

## Summary
Reading key configuration files (package.json, vite.config.ts, tsconfig.json, and component files) in sequence provides reliable project identification and context understanding.

## Evidence
- Sequential reading of package.json revealed "elf-dashboard" name
- vite.config.ts showed port 3001 configuration  
- tsconfig.json confirmed React + TypeScript setup
- DashboardLayout component in src/components confirmed dashboard functionality
- Combined analysis enabled accurate project characterization

## Proposed Content
**Rule:** Use systematic file reading (package.json → build config → component structure) to identify unknown projects quickly
**Explanation:** Configuration files contain project metadata, build settings, and framework clues. Reading them in sequence from package.json outward reveals project identity, tech stack, and purpose faster than guessing or random exploration.
**When to Apply:** When entering an unfamiliar directory or needing to understand project context quickly
**Suggested Confidence:** 0.7

## Cross-References
- Validates: debugging-check-obvious-first heuristic
- Relates to: core-principles heuristic #1 (Query Before Acting)

---
**Status:** pending
**Generated:** 2025-01-31T15:44:16Z
**Reviewed:**
```

The session also shows a pattern of providing comprehensive project overviews after file analysis, which could be valuable as a communication pattern.

```markdown