# Architecture

## Overview

`tiquette` (CLI: `tq`) is a Python rewrite of the `ticket` (`tk`) bash CLI. It's a minimal file-based ticket system with dependency tracking, designed for use by both humans and AI agents.

## Prior Art

This is a reimplementation of [ticket](https://github.com/wedow/ticket), originally a single-file bash script using awk for bulk operations and sed for YAML manipulation. The rewrite addresses:

- Fragile sed-based YAML manipulation (unescaped replacements, brittle array ops)
- ~350 lines of duplication between ready/blocked listing commands
- No input validation (priority, type, status enums)
- Maintenance difficulty (bash + awk vs Python, the author's primary language)

## Project Structure

```
tiquette/
  src/tiquette/
    __init__.py
    cli.py              # CLI entry point, argument parsing
    commands/           # Command implementations (one module per group)
      lifecycle.py      # create, start, close, cancel, reopen
      relationships.py  # dep, undep, nest, unnest, link, unlink
      fields.py         # assign, tag, prioritize, etc.
      content.py        # describe, add-note
      query.py          # show, info, path, ls, dep tree, tags, archive
    ticket.py           # Ticket model (read/write YAML+markdown)
    store.py            # Ticket store (find tickets dir, load/save, ID resolution)
    plugins.py          # Plugin discovery and dispatch
  tests/
    features/           # BDD feature files (behave)
      steps/            # Step definitions
  docs/
    cli-design.md       # CLI interface specification
    architecture.md     # This file
```

## Key Design Decisions

### CLI framework

Use `argparse` (stdlib) for argument parsing. Subcommands via `add_subparsers`, grouped help output (Lifecycle, Relationships, etc.) via custom help formatter. Zero runtime dependencies.

### Ticket as a model

A `Ticket` class wraps the markdown file. It handles:
- Parsing YAML frontmatter into typed fields (hand-rolled parser, no PyYAML)
- Reading/writing the markdown body (title, description, notes sections)
- Validation (priority range, type enum, status transitions)

### Store layer

The `Store` class manages the `.tickets/` directory:
- Finding the tickets directory (walks up from cwd, or uses `TICKETS_DIR` env var)
- Loading tickets by ID (full or partial match)
- Saving tickets back to disk
- ID generation (directory-name prefix + random suffix)

### Plugin system

Preserved from the original:
- Executables named `tq-<cmd>` or `tiquette-<cmd>` in PATH
- `tq super <cmd>` bypasses plugins
- Plugins receive `TICKETS_DIR` and `TQ_SCRIPT` environment variables

### Testing

pytest, with tests ported from the original project's behave suite. The original has ~730 scenarios across 15 feature files. Tests run against the actual CLI (integration tests).

The original test suite is the primary reference for expected behavior:
- Feature files: `../ticket-fork/features/*.feature` (15 files)
- Step definitions: `../ticket-fork/features/steps/ticket_steps.py`

These should be adapted (not copied verbatim) to reflect the redesigned CLI -- see `docs/migration-notes.md` for all behavioral changes. The step definitions will need reworking since they shell out to the `ticket` script; the new steps should invoke `tq` instead.

### Reference specs

The original project uses spexl for spec-driven development. Reference specs describe current behavior and should be consulted during implementation:
- `../ticket-fork/specs/reference/` -- behavioral contracts for existing capabilities
- `../ticket-fork/specs/changes/` -- active and archived spec changes

Of particular relevance:
- `../ticket-fork/specs/reference/hierarchical-listing/spec.md` -- tree-based rendering of parent-child relationships in listings

## Dependencies

- Python 3.10+
- No runtime dependencies (argparse, YAML frontmatter parsing all use stdlib)
- pytest (dev dependency)
