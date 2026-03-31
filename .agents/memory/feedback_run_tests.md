---
name: Run tests with just test
description: Use `just test` to run the test suite, not pytest or behave directly
type: feedback
---

Run tests as `just test`.

**Why:** User preference for using the justfile runner.
**How to apply:** Whenever running the test suite, use `just test` instead of `uv run pytest`, `uv run behave`, or `make test`.
