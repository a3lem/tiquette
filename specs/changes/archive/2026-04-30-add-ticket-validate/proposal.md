## Why

Ticket files can accumulate dangling references -- a dependency, parent, or link that was deleted or archived without updating the tickets that point to it. There is no way to detect this today short of manually inspecting every file.

## What Changes

- New `tq validate` command that scans all non-archived tickets and reports referential integrity violations.
- Checks `deps`, `parent`, and `links` fields for existence of referenced tickets.
- Distinguishes violations (missing references, non-zero exit) from warnings (references to archived tickets, zero exit).
- Structured output format: `<ticket-id>: <message>`.
- Always prints a summary line.

## Capabilities

### New Capabilities

- `ticket-validate`: Validate referential integrity of ticket dependencies, parent, and link fields.

## Impact

- New command module under `src/tiquette/commands/`.
- New subcommand registered in `cli.py`.
- No changes to existing commands or ticket format.
