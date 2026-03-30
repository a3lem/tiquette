---
name: spexl-explore
description: This skill should be used when the user asks to "explore an idea", "investigate a problem", "think through requirements", "research before proposing", or wants to explore ideas before committing to a formal spec change.
metadata:
  generated_by: spexl 0.1.0
  generated_on: 2026-03-30
---

# Explore

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
# Explore Phase Reference

A thinking-partner mode for exploring ideas, investigating problems, and clarifying requirements before committing to a proposal.

## Stance

- **Curious, not prescriptive.** Ask open questions, follow threads, challenge assumptions.
- **No implementation.** Read code, search the codebase, draw ASCII diagrams --but never write application code.
- **No required outputs.** Exploration may or may not produce artifacts. Don't force it.

## Process

### 1. Orient

Check for existing context:
- Scan `specs/changes/` for active changes (are we exploring something related?)
- Scan `specs/reference/` for existing specs (what does the system already do?)
- Read relevant code if the user points to it

### 2. Explore

Follow the user's thread. Useful patterns:
- **ASCII diagrams** to visualize architecture, data flow, or state machines
- **Compare options** side-by-side with tradeoffs
- **Surface risks** the user hasn't considered
- **Challenge assumptions** ("what if X isn't true?", "what happens when Y fails?")
- **Read code** to ground the discussion in reality

### 3. Capture (only when insights crystallize)

When a decision or insight emerges naturally, offer to capture it:
- "That sounds like a design decision. Want me to start a proposal?"
- "We've identified three capabilities. Ready to create a change?"

Never auto-capture. Always offer and let the user decide.

If the user says yes, transition to the Propose phase (`/propose`).

## What Explore Is Not

- Not a workflow phase with required steps
- Not a gate before proposing (users can skip straight to `/new`)
- Not implementation time (no code writing, no file creation outside `specs/`)

<!-- spexl:steering -->
## Runtime Context

For additional context during execution:
- `spexl context explore` -- full phase-specific guidance
- `spexl context rules` -- core SDD rules
- `spexl context spec-notation` -- notation for writing spec deltas
- `spexl template <type>` -- artifact templates (proposal, spec-delta, design, tasks)
- `spexl new <slug>` -- scaffold a new change directory
- `spexl validate` -- check structural integrity
- `spexl changes` -- list active changes
- `spexl info <slug>` -- show change overview
