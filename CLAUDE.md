# CLAUDE.md

## Project

`tiquette` (CLI: `tq`) is a Python reimplementation of the `ticket` (`tk`) bash CLI -- a minimal file-based ticket system with dependency tracking for use by humans and AI agents.

## Key Docs

- `docs/cli-design.md` -- CLI interface spec (commands, flags, help text)
- `docs/architecture.md` -- Project structure, design decisions, dependencies
- `docs/migration-notes.md` -- Behavioral differences from the original `tk`

## Development

- Python 3.10+, managed with `uv`
- Use `uv run python` instead of `python`
- CLI entry point: `tq` (installed via pyproject.toml console_scripts)

## Behavior

- Always use the AskUserQuestion tool to ask questions 

