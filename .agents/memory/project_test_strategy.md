---
name: tiquette test strategy
description: Testing approach for tiquette - pytest with spec annotations, TDD, and manual test drives
type: project
---

## Pytest (automated)

Tests use pytest (not behave). The original tk project used behave with gherkin feature files.

- Strict red-green-refactor TDD: write failing tests first, then implement to make them pass
- Port tk's behave scenarios to pytest, adapting for the redesigned tq interface
- Tests link back to spexl reference specs via `# spec:` annotations
- Annotation format: `# spec: <capability> requirement=<slug> scenario=<slug>`
- Reference specs in `specs/reference/<capability>/spec.md` are the source of truth
- Tests run against the CLI via subprocess (`uv run tq ...`)

## Test drives (manual)

High-level scenario scripts in `tests/test-drives/*.md`. Each file describes a realistic multi-step workflow in natural language. Not automated -- meant to be followed manually (by a human or AI) in a temp directory using `TICKETS_DIR` to isolate from the project.

- Focus on end-to-end interactions that unit tests miss (cascading state changes, multi-command workflows)
- Each file has: setup, numbered steps, and "what to watch for" highlighting non-obvious behaviors
- Run in isolation: `TICKETS_DIR=$(mktemp -d)/tickets uv run tq ...`

**Why:** Adriaan introduced test drives on 2026-03-31 to complement pytest. Pytest covers individual command correctness; test drives verify that commands compose correctly in realistic scenarios.

**How to apply:** Write specs first, then tests with `# spec:` annotations, then code. Use test drives for exploratory/integration testing of multi-step workflows. When adding new commands, consider adding a test drive scenario if the command has interesting interactions with others.
