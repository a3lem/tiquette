---
name: tiquette architecture decisions
description: Key technical decisions made during CLI skeleton phase (2026-03-30/31)
type: project
---

Decided during the CLI skeleton implementation phase:

- **argparse** (stdlib) for CLI, not click. Zero runtime dependencies.
- **Hand-rolled YAML** frontmatter parser, no PyYAML.
- **Python >=3.12** (pyproject.toml), though architecture.md says 3.10+.
- **Two-tier help**: bare `tq` shows compact summary, `tq --help` shows full reference with all flags (designed for system prompts).
- **Static help text**: help output is a hand-crafted string, not generated from argparse. Easier to control formatting.
- **Variadic positionals** for multi-value args: `tq tag t-001 ui backend`, not comma-split.
- **Repeated flags** for multi-value options on create: `--tag ui --tag backend`, `--dep d-001 --dep d-002`.
- **Optional positional = clear**: `assign <id>` clears assignee, `xref <id>` clears xref. No separate `unassign`/`unset-ref` commands.
- **Stubs validate args and exit 0** during skeleton phase.
- **Group modules from day one**: `commands/lifecycle.py`, `commands/relationships.py`, etc.
- **Plugins and `super` deferred** to implementation phase.

**Why:** These were resolved via /grill-me on 2026-03-30 and refined on 2026-03-31.

**How to apply:** Don't revisit these without Adriaan's input. They're settled.
