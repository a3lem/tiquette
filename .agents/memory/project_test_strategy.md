---
name: tiquette test strategy
description: Testing approach for tiquette - pytest with spec annotations, red-green-refactor TDD
type: project
---

Tests use pytest (not behave). The original tk project used behave with gherkin feature files.

**Approach:**
- Strict red-green-refactor TDD: write failing tests first, then implement to make them pass
- Port tk's behave scenarios to pytest, adapting for the redesigned tq interface
- Tests link back to spexl reference specs via `# spec:` annotations
- Annotation format: `# spec: <capability> requirement=<slug> scenario=<slug>`
- Reference specs in `specs/reference/<capability>/spec.md` are the source of truth
- Tests run against the CLI via subprocess (`uv run tq ...`)

**Why:** Adriaan decided on 2026-03-30 to use pytest with specs as the formal behavioral contract. The spec-first, test-second, implement-third workflow was established on 2026-03-30.

**How to apply:** Write specs first, then tests with `# spec:` annotations, then code. Never write code before failing tests exist.
