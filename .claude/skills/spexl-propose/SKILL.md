---
name: spexl-propose
description: This skill should be used when the user asks to "propose a change", "create a spec", "start a new feature", "define requirements", or wants to create a formal specification for a new capability or modification.
metadata:
  generated_by: spexl 0.1.0
  generated_on: 2026-03-30
---

# Propose

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

<!-- spexl:action -->
# Propose Phase Reference

Create a new change and generate all artifacts in one flow: proposal → specs → design (optional) → tasks (optional).

## 1. Determine Specs Location

### Monorepo

In a monorepo, each sub-project has its own `specs/` directory next to its code. `spexl changes -r` discovers them (recursive walk from the current directory). Use `--dir` to target a specific `specs/` directory explicitly.

No central config file is needed. Each `specs/` directory is self-contained with its own `reference/` and `changes/`.

## 2. Get Description and Create Directory

If no description was provided with the command, use AskUserQuestion:
- "What feature or capability are you specifying?"
- Keep it brief (2-5 words ideal)

Slugify the description:
- Lowercase, replace spaces with hyphens, remove special characters
- The slug names the *change*, not the capability being changed. It should describe what's being done: `add-oauth`, `fix-session-leak`, `refactor-auth-flow` -- not just `oauth` or `sessions`. A capability may be touched by many changes over time; the slug distinguishes *this* change.
- **Be precise and specific.** `add-spec-sync` is too vague if the deliverable is a subagent -- `spec-sync-subagent` is better. The slug should tell a reader exactly what the change produces without opening the proposal.
- Capability names live under `deltas/` and `reference/` and are a separate concern.

**Collision handling:** If the slug already exists in `specs/changes/`, ask user whether to continue the existing change or pick a different name.

## 3. Write Proposal

The first artifact is `proposal.md`. Run `spexl template proposal` for the template.

The template has four sections: **Why**, **What Changes**, **Capabilities**, **Impact**. Keep it concise (1-2 pages). Focus on the "why" not the "how" --implementation details belong in design.md.

The **Capabilities** section lists which features you're changing -- each one becomes a directory in `deltas/`. Check `specs/reference/` for existing capability names before filling in Modified Capabilities.

### Optional Sections

For larger or more complex changes, add any of these sections after **Why**:

- **Alternatives Considered** – Other approaches and why they were rejected
- **Constraints** – Technical limitations, business rules, dependencies
- **Assumptions** – Assumptions that must hold for this change to work
- **Stakeholders** – Who cares about this change and why
- **Out of Scope** – Explicitly excluded to prevent scope creep

These are not in the template by default. Add them when they carry real information.

## 4. Write Specs

After the proposal, proceed to per-capability spec deltas. Run `spexl context spec-notation` for notation and structure guidance.

One `spec.md` per capability listed in the proposal's Capabilities section. Run `spexl template spec-delta` for the template.

## 5. Write Design (optional)

For features with multiple valid approaches or architectural decisions that need user input. Run `spexl context design` for guidance.

**Skip for:** simple features, bug fixes, obvious implementations.

## 6. Write Tasks (optional)

For changes with 3+ implementation steps or multi-session work. Run `spexl context tasks` for guidance. Run `spexl template tasks` for the template.

**Skip for:** simple specs where the spec itself is sufficient.

## Completion

All artifacts that make sense for the change should exist before moving to `/apply`.

**Interactive mode:** Inform user the change is ready for implementation.

**Autonomous mode:**
- After proposal → invoke **spec-critic** (`intra-spec`)
- After specs + design → invoke **spec-critic** (`intra-spec` + `spec-code`)
- Then proceed to apply

## Example Flows

**Single-project:**
```
User: /propose user authentication

1. Create: mkdir -p specs/changes/user-authentication
2. Write proposal.md (gather context, motivation, capabilities)
3. Write deltas/user-auth/spec.md (requirements, scenarios)
4. Write design.md (if non-trivial)
5. Write tasks.md (if multi-step)
```

**Monorepo:**
```
User: /propose login redesign (working in packages/web-app/)

1. specs/ exists at packages/web-app/specs/ (or use --dir)
2. Create: mkdir -p packages/web-app/specs/changes/login-redesign
3. Continue as above
```

<!-- spexl:steering -->
## Runtime Context

For additional context during execution:
- `spexl context propose` -- full phase-specific guidance
- `spexl context rules` -- core SDD rules
- `spexl context spec-notation` -- notation for writing spec deltas
- `spexl template <type>` -- artifact templates (proposal, spec-delta, design, tasks)
- `spexl new <slug>` -- scaffold a new change directory
- `spexl validate` -- check structural integrity
- `spexl changes` -- list active changes
- `spexl info <slug>` -- show change overview
