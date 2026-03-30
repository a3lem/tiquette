---
name: tiquette test strategy
description: Testing approach for tiquette - pytest instead of behave, with spec linkage
type: project
---

Tests use pytest (not behave). The original tk project used behave with gherkin feature files.

**Approach:**
- Port tk's behave scenarios to pytest, adapting for the redesigned tq interface
- Gherkin-style features become comments alongside each test
- Tests must link back to spexl reference spec requirements/scenarios via comments
- Reference specs in `specs/reference/<capability>/spec.md` are the source of truth

**Why:** Adriaan decided on 2026-03-30 to switch from behave to pytest for this project, with specs as the formal behavioral contract instead of gherkin feature files.

**How to apply:** Every test function should have a comment referencing the spec capability and requirement/scenario it covers. The specs must be written first (source of truth), then tests written against them.
