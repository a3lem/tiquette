---
name: spexl-apply
description: This skill should be used when the user asks to "implement a spec", "apply a change", "build the feature", "start implementation", or wants to implement and verify a proposed spec change.
metadata:
  generated_by: spexl 0.1.0
  generated_on: 2026-03-30
---

# Apply

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

<!-- spexl:structure -->
## Directory Structure

```
specs/
├── reference/                        # Source of truth
│   ├── authentication/
│   │   └── spec.md
│   └── billing/
│       └── spec.md
└── changes/
    ├── archive/                      # Completed changes
    │   └── 2026-03-01-initial-auth/
    └── add-oauth/                    # Active change
        ├── proposal.md               # Why (intent, scope, capabilities)
        ├── deltas/                   # What (per-capability behavioral changes)
        │   ├── session-management/
        │   │   └── spec.md
        │   └── user-auth/
        │       └── spec.md
        ├── design.md                 # How (optional)
        ├── tasks.md                  # Steps (optional)
        └── notes/                    # Learnings (optional)
```

A delta at `deltas/user-auth/spec.md` targets `reference/user-auth/spec.md`. Changes are identified by slug -- look for matching slugs in `specs/changes/*/`.

**Monorepo:** Each sub-project has its own `specs/` directory. `spexl` discovers them with `-r` (recursive). Use `--dir` to target a specific one.

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

<!-- spexl:cross-phase -->
## Iteration

All phases can be revisited. Use `spexl context refine` for guidance on updating existing artifacts.

- Apply snag → may reveal a design flaw, spec gap, or proposal issue
- Changing a spec may invalidate the design -- always warn the user
- Scope changes require user confirmation in interactive mode; in autonomous mode, document in `notes/` and proceed

<!-- spexl:interactive-vs-autonomous -->
## Interactive vs Autonomous

**Interactive** (default): Ask the user at each phase for input and confirmation (use AskUserQuestion tool).

**Autonomous** (when user requests it, e.g. "work on this until done"):

1. **Propose:** Draft all artifacts. Invoke **spec-critic** (`intra-spec` after proposal, `intra-spec` + `spec-code` after specs + design).
2. **Apply:** Implement and verify against all requirements and scenarios. Invoke **spec-critic** (`all`) before marking complete.
3. **Archive:** Invoke **spec-sync** → validate with **spec-critic** (`inter-spec`) → move to archive.

Only pause for genuine ambiguities or when the critic can't resolve after 5 rounds.

<!-- spexl:action -->
# Apply Phase Reference

How to implement a proposed change, tracking progress and capturing learnings.

## Process

### 1. Load Context

Read the change directory:
- `proposal.md` - Why this change exists
- `deltas/*/spec.md` - What's changing (requirements and scenarios to satisfy)
- `tasks.md` - Progress overview (if exists)
- `design.md` - Technical approach (if exists)
- `notes/` - Previous learnings (if exists)

### 2. Determine Code Location

**Important:** The `deltas/` directory is for specification files only. All generated code must go elsewhere.

1. Check project structure for obvious code locations (e.g., `src/`, `lib/`, `app/`, project root)
2. Check `design.md` for specified file paths
3. If unclear, use AskUserQuestion: "Where should I place the generated code?"

Never write code files (`.js`, `.ts`, `.py`, `.html`, etc.) inside `deltas/*/`.

### 3. Implement

Work through the implementation:
- Follow the design decisions
- Satisfy each requirement and scenario from `deltas/*/spec.md`
- Update `tasks.md` checkboxes as tasks are completed (if exists)
- Track progress in notes if the work spans multiple sessions

### 4. Verify

Write tests alongside implementation -- not after. Spec scenarios translate directly to test cases. Run `spexl context verification` for test strategies, annotation conventions, and coverage expectations.

Every requirement needs at least one test. Every non-trivial scenario needs a corresponding test. Tests are annotated with `# spec:` comments linking back to the spec.

### 5. Capture Learnings (Optional)

Create or update `notes/` when there's new information worth recording. Notes can be created during any phase.

**Suggested note files:**
- `research.md` - Exploration findings, links, citations (any phase)
- `implementation.md` - Apply-phase learnings, gotchas, failed approaches

**What belongs in notes:**
- Learnings and gotchas discovered during implementation
- Research findings and explored files index
- Failed approaches and why they didn't work
- Context for future maintainers that isn't obvious from the code

**What does NOT belong in notes:**
- Restatements of proposal context (already in proposal.md)
- Restatements of scenarios (already in deltas/*/spec.md)
- Restatements of design decisions (already in design.md)

### 6. Complete

Before claiming completion:

1. **Run all tests** -- fix failures before proceeding
2. **Walk through each requirement** from `deltas/*/spec.md` and confirm a corresponding test exists
3. **If verification fails**, surface the choice: fix implementation, or adjust spec (needs user confirmation)

**Never claim "all scenarios satisfied" without passing tests.**

## Finding Specs

Specs are directories: `specs/changes/feature-name/`

When user references a spec by name, look for matching slugs in `specs/changes/*/`.

## Updating Specs

Only modify spec files in `deltas/` with user confirmation -- changes affect scope.

<!-- spexl:steering -->
## Runtime Context

For additional context during execution:
- `spexl context apply` -- full phase-specific guidance
- `spexl context rules` -- core SDD rules
- `spexl context spec-notation` -- notation for writing spec deltas
- `spexl template <type>` -- artifact templates (proposal, spec-delta, design, tasks)
- `spexl new <slug>` -- scaffold a new change directory
- `spexl validate` -- check structural integrity
- `spexl changes` -- list active changes
- `spexl info <slug>` -- show change overview
