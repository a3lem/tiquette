---
name: spexl-archive
description: This skill should be used when the user asks to "archive a change", "merge deltas", "finalize a spec", "complete a change", or wants to merge spec deltas into reference specs and archive the change.
metadata:
  generated_by: spexl 0.1.0
  generated_on: 2026-03-30
---

# Archive

<!-- spexl:rules -->
## Rules

1. **Specs are the source of truth.** Code serves specs. Never write specs to describe existing code -- that's backwards.
2. **`specs/` is for specs only.** No code files. `deltas/` contains only `spec.md` files. All code goes elsewhere.
3. **Don't fabricate.** Only document what was discussed or confirmed. No invented assumptions, no invented constraints. If unsure, ask.
4. **Prove your work.** Never claim "done" without passing tests or user verification. Walk through each requirement and scenario.
5. **Mark unknowns with `[CLARIFICATION NEEDED]`** and resolve them before proceeding.

**Don't:**
- Over-specify (specs guide, they don't pin down every detail)
- Design before scenarios are clear
- Add "might need" features -- only what's explicitly required
- Let specs go stale -- a spec that doesn't match the code is worse than no spec

<!-- spexl:action -->
# Archive Phase Reference

How to archive a completed change by merging deltas into reference specs.

## Process

### 1. Check Completeness

If `tasks.md` exists, count incomplete tasks (`- [ ]`). Warn the user and confirm before proceeding if any remain.

### 2. Show Sync Summary

For each directory in `change-dir/deltas/`:
- Read the spec delta
- Read the corresponding `specs/reference/<same-name>/spec.md` (if it exists)
- Summarize what would change: requirements ADDED / MODIFIED / REMOVED per capability
- Present this summary to the user

### 3. Merge Deltas into Reference Specs

Invoke the **spec-sync agent** with the change directory path and spec root. The agent handles all delta-to-reference merging (ADDED, MODIFIED, REMOVED, RENAMED) and creates new capability specs as needed. Run `spexl template reference-spec` for the reference spec template when creating new capabilities.

```
"Merge the spec deltas from {change-dir} into the reference specs. Spec root: {spec-root}"
```

Do not merge inline. The merge is mechanical work that belongs in a subagent to keep the main context clean.

### 4. Validate Merged Specs

Invoke **spec-critic agent** (`inter-spec` mode) on the updated reference specs. The merge is mechanical -- the critic checks that the result makes sense and doesn't contradict itself. If the critic returns `needs-work` or `blocked`, fix the reference specs before proceeding.

### 5. Move to Archive

`specs/changes/slug/` → `specs/changes/archive/YYYY-MM-DD-slug/`

Archive keeps the change history browsable without cluttering active specs.

## Key Principle

Reference specs should describe how things work *now*, not how they changed. The archived change directory preserves the history.

<!-- spexl:steering -->
## Runtime Context

For additional context during execution:
- `spexl context archive` -- full phase-specific guidance
- `spexl context rules` -- core SDD rules
- `spexl context spec-notation` -- notation for writing spec deltas
- `spexl template <type>` -- artifact templates (proposal, spec-delta, design, tasks)
- `spexl new <slug>` -- scaffold a new change directory
- `spexl validate` -- check structural integrity
- `spexl changes` -- list active changes
- `spexl info <slug>` -- show change overview
