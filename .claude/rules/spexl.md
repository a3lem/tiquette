# spexl – Spec-Driven Development

You are working in a project that uses spexl for spec-driven development. Specs are the source of truth. Code serves specs.

## Core Model

**Reference specs** (`specs/reference/<capability>/spec.md`) describe how the system behaves now. **Changes** (`specs/changes/<slug>/`) propose modifications as deltas against the reference. When a change is complete, its deltas merge into the reference. The next change builds on the updated reference.

## Specs

A spec is a behavioral contract using requirements (SHALL statements) and scenarios (Given/When/Then).

```
### Requirement: Session Timeout
The system SHALL expire sessions after 30 minutes of inactivity.

#### Scenario: Idle timeout
- Given an authenticated session
- When 30 minutes pass without activity
- Then the session is invalidated
```

Specs are organized by **capability** – a logical grouping of related behavior (e.g. `authentication`, `billing`). A capability is a domain concept, not a code module.

## Changes

A change lives in `specs/changes/<slug>/` and contains:

| Artifact | Purpose | Required |
|----------|---------|----------|
| `proposal.md` | Why this change, what it affects | Yes |
| `deltas/<capability>/spec.md` | Behavioral changes per capability | Yes |
| `design.md` | Technical approach | When non-trivial |
| `tasks.md` | Implementation checklist | When multi-step |
| `notes/*` | Learnings, research | Freely |

The slug names the change (`add-oauth`), not the capability (`authentication`).

## Spec Deltas

Deltas describe what's changing relative to the reference:

| Section | Meaning | On archive |
|---------|---------|------------|
| `ADDED` | New behavior | Appended to reference |
| `MODIFIED` | Changed behavior (full replacement) | Replaces matching requirement |
| `REMOVED` | Deprecated behavior | Deleted from reference |
| `RENAMED` | Name change only | Heading updated |

MODIFIED replaces the entire requirement block. Include all scenarios, even unchanged ones.

## Archive

Archiving completes a change: deltas merge into reference, change moves to `changes/archive/` with a date prefix. Reference always reflects current behavior.

## Directory Structure

```
specs/
├── reference/                        # Source of truth
│   └── <capability>/spec.md
└── changes/
    ├── archive/                      # Completed changes
    └── <slug>/                       # Active change
        ├── proposal.md
        ├── deltas/<capability>/spec.md
        ├── design.md
        ├── tasks.md
        └── notes/
```

## Key Terms

- **Capability**: logical grouping of related behavior
- **Requirement**: a rule the system must follow (SHALL statement)
- **Scenario**: a concrete testable example of a requirement (Given/When/Then)
- **Spec delta**: behavioral changes relative to the reference spec
- **Reference spec**: source of truth for a capability's current behavior
- **Slug**: the kebab-case name identifying a change
- **Archive**: completing a change by merging deltas into reference

## Rules

1. Specs are the source of truth. Code serves specs.
2. `specs/` is for specs only. No code files.
3. Don't fabricate. Only document what was discussed or confirmed.
4. Prove your work. Never claim "done" without passing tests.
5. Mark unknowns with `[CLARIFICATION NEEDED]`.

## Workflow

Work moves through five phases. Each phase has a dedicated skill (slash command).

| Phase | Skill | What happens |
|-------|-------|-------------|
| Explore | `/explore` | Investigate before committing. Read code, ask questions, draw diagrams. No implementation. |
| Propose | `/propose` | Create a change: proposal → spec deltas → design (optional) → tasks (optional). |
| Refine | `/refine` | Update any existing artifact (proposal, spec, design, tasks). |
| Apply | `/apply` | Implement the change. Verify against every requirement and scenario. |
| Archive | `/archive` | Merge deltas into reference specs. Move the change to `changes/archive/`. |

Phases can be revisited. An apply snag may reveal a spec gap; changing a spec may invalidate the design.

## Agents

Two sub-agents provide adversarial review and automated merging:

- **spec-critic** – Reviews specs for coherence, code alignment, and cross-spec consistency. Modes: `intra-spec`, `spec-code`, `inter-spec`, `all`. Verdicts: `approved`, `approved-with-reservations`, `needs-work`, `blocked`.
- **spec-sync** – Merges deltas into reference specs during archive. Handles ADDED, MODIFIED, REMOVED, and RENAMED operations.

## CLI

### Plumbing (spec management)

| Command | Purpose |
|---------|---------|
| `spexl new <slug>` | Scaffold a new change directory |
| `spexl changes` | List active changes |
| `spexl info <slug>` | Show change overview |
| `spexl refs` | List reference specs |
| `spexl validate` | Check changes for structural problems |
| `spexl archive <slug>` | Archive a completed change |
| `spexl link <a> <b>` | Link two changes across spec roots |
| `spexl unlink <a> <b>` | Remove a link between changes |

### Steering (knowledge on demand)

| Command | Purpose |
|---------|---------|
| `spexl explain <topic>` | Deep guidance on a technique (spec-notation, design, tasks, verification, critique) |
| `spexl template <type>` | Artifact scaffolding (proposal, spec-delta, reference-spec, design, tasks) |

Run `spexl explain --list` and `spexl template --list` to see all available topics and artifact types.
