---
name: spexl-refine
description: This skill should be used when the user asks to "refine a spec", "update the proposal", "modify the design", "change requirements", or wants to update any existing spec artifact.
metadata:
  generated_by: spexl 0.1.0
  generated_on: 2026-03-30
---

# Refine

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

<!-- spexl:file-ownership -->
## File Ownership

| File | Owner | Others May Edit |
|------|-------|-----------------|
| `proposal.md` | Propose phase | With user confirmation |
| `deltas/*/spec.md` | Propose phase | With user confirmation |
| `design.md` | Propose phase | With user confirmation |
| `tasks.md` | Propose phase | Apply phase (checkboxes only) |
| `notes/*` | Any phase | Freely |

**Changing a spec may invalidate the design.** Always warn the user.

<!-- spexl:action -->
# Refine Phase Reference

Update an existing artifact based on user instruction.

## Routing

Determine which artifact to update from the instruction:

- Context, motivation, scope → `proposal.md`
- Requirements, scenarios, behavior → relevant `spec.md` in `deltas/`
- Architecture, technical decisions → `design.md`
- Task breakdown, progress → `tasks.md`

If unclear, ask the user.

## Process

### 1. Load Context

Read the change directory to understand the current state:
- `proposal.md` for scope and motivation
- `deltas/*/spec.md` for current requirements
- `design.md` for technical decisions (if exists)
- `tasks.md` for progress (if exists)

### 2. Apply the Refinement

Follow the user's instruction. When updating:

- **Proposal:** Run `spexl context propose` for guidance on proposal structure.
- **Spec deltas:** Run `spexl context spec-notation` for notation guidance.
- **Design:** Run `spexl context design` for design guidance.
- **Tasks:** Run `spexl context tasks` for tasks guidance.

### 3. Check for Cascading Effects

**Changing a spec may invalidate the design.** Always warn the user.

- If a spec changes, check whether the design still makes sense
- If scope changes, check whether tasks need updating
- If the proposal changes, check whether specs still align

### 4. Confirm

**Interactive mode:** Show the user what changed and ask for confirmation.

**Autonomous mode:** Document the refinement in `notes/` and proceed.

<!-- spexl:steering -->
## Runtime Context

For additional context during execution:
- `spexl context refine` -- full phase-specific guidance
- `spexl context rules` -- core SDD rules
- `spexl context spec-notation` -- notation for writing spec deltas
- `spexl template <type>` -- artifact templates (proposal, spec-delta, design, tasks)
- `spexl new <slug>` -- scaffold a new change directory
- `spexl validate` -- check structural integrity
- `spexl changes` -- list active changes
- `spexl info <slug>` -- show change overview
