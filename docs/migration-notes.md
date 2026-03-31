# Migration Notes from `tk` to `tq`

> **STALE** (2026-03-31): This document reflects the initial redesign proposal.
> The CLI has since been refined during implementation. For the current interface,
> see `docs/cli-design.md` or run `tq --help`. Key drift from this document:
>
> - `set-ref`/`unset-ref` → `xref <id> [xref]` (one command, omit to clear)
> - `assign`/`unassign` → `assign <id> [assignee]` (one command, omit to clear)
> - `--ref` → `--xref` on create
> - `dep tree` → `deps`
> - `show-deps` → `deps`
> - New command: `links` (list all linked pairs)
> - Section rename: Query → View
> - Section moves: `archive` → Lifecycle, `deps`/`links` → Relationships, `tags` → Fields

This documents all behavioral changes from the original bash `ticket` (`tk`) CLI.

## Removed

- `--design` flag on create (belongs in ticket body)
- `--acceptance` flag on create (belongs in ticket body)
- `status <id> <status>` command (redundant with start/close/reopen)
- `dep cycle` command (cycle detection now happens on write in `dep`)
- `ready` command (replaced by `ls --ready`)
- `blocked` command (replaced by `ls --blocked`)
- `closed` command (replaced by `ls --status closed`)
- `-T` short flag on listing commands (ambiguous between tag and type)

## New Commands

- `cancel <id>` -- close as canceled (was `close --reason rejected`)
- `info <id>` -- frontmatter + computed relationships, no body
- `path <id>` -- print file path for direct content editing
- `tags` -- list all tags with counts (moved from plugin to core)
- `archive` -- move closed/canceled tickets to archive dir (moved from plugin to core)
- `nest` / `unnest` -- parent-child hierarchy management
- `assign` / `unassign` -- assignee management
- `change-prio <id> <priority>` -- update priority
- `change-type <id> <type>` -- change ticket type
- `tag` / `untag` -- tag management
- `set-ref` / `unset-ref` -- external reference management
- `describe <id>` -- set/replace description section

## New Flags

- `--deps` on create (set blocker dependencies at creation time)
- `ls` flags: `--status`, `--ready`, `--blocked`, `--completed`, `--canceled`, `--assignee`, `--tag`, `--type`, `--sort`, `--limit`, `--jsonl`
- `--json` on `show` and `info`

## Changed Behavior

- Assignee defaults to null (was: git user.name)
- `-d`/`--description` sets body content (markdown below frontmatter), not a YAML field
- `--external-ref` renamed to `--ref`
- `close --reason` replaced by distinct `close` (completed) and `cancel` (canceled) commands
- Resolution field (`completed`/`canceled`) replaces `close_reason`/`rejected`
- `dep` accepts multiple dep-ids in one call
- `undep` accepts multiple dep-ids in one call
- `unlink` accepts multiple target ids in one call
- `dep` validates for cycles on write (rejects and exits non-zero)
- `close` rejects if ticket has open children
- `close` prints notification when closing last open child of a parent
- `dep tree` argument order changed: `dep tree <id> [--full]` (was `dep tree [--full] <id>`)
- `ls` replaces `ready`/`blocked`/`closed` as unified listing command (was plugin, now core)
- `query`/`query-all` plugins replaced by `--jsonl` on `ls` and `--json` on `show`/`info`
- Help output organized into sections: Lifecycle, Relationships, Fields, Content, Query, Plumbing

## Future (not v1)

- `validate` command (lint pass: orphaned deps, malformed frontmatter, out-of-range values)

## Preserved

- Plugin system (`tq-<cmd>` / `tiquette-<cmd>` in PATH)
- `super` command for bypassing plugins
- Ticket file format (YAML frontmatter + markdown body in `.tickets/`)
- Partial ID matching
- ID generation (directory-name prefix + random suffix)
