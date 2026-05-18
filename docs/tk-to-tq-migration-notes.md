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

## v1.1 → v1.2 (0.1.x → 0.2.0)

### Removed verbs (no aliases)

`tag`, `untag`, `dep`, `undep`, `nest`, `unnest`, `link`, `unlink`,
`assign`, `change-prio`, `change-type`, `describe`, `add-note`, `xref`.

Replacement: every one folds into `tq edit <id> [field-options]`. The
field-options are the same vocabulary as `tq create`, plus the
`edit`-only removers (`--title`, `--untag`, `--undep`, `--unlink`,
`--unset`).

| Old | New |
|---|---|
| `tq tag id foo bar` | `tq edit id --tag foo --tag bar` |
| `tq untag id stale` | `tq edit id --untag stale` |
| `tq dep id dep1 dep2` | `tq edit id --dep dep1 --dep dep2` |
| `tq undep id dep1` | `tq edit id --undep dep1` |
| `tq nest c1 c2 parent` | `tq edit c1 --parent parent` (then again for c2) |
| `tq unnest id` | `tq edit id --unset parent` |
| `tq link a b` | `tq edit a --link b` |
| `tq unlink a b` | `tq edit a --unlink b` |
| `tq assign id Alice` | `tq edit id -A Alice` |
| `tq assign id` (clear) | `tq edit id --unset assignee` |
| `tq change-prio id 0` | `tq edit id -p 0` |
| `tq change-type id bug` | `tq edit id -t bug` |
| `tq describe id "text"` | `tq edit id -d "text"` |
| `tq add-note id "text"` | `tq edit id --note "text"` |
| `tq xref id gh-1` | `tq edit id --xref gh-1` |
| `tq xref id` (clear) | `tq edit id --unset xref` |

### Status rename: `completed` → `closed`

The verb is `close`, so the stored status is now `closed` too. The
old `completed` value is migrated by `tq autofix` (unconditional, no
flag). `tq ls --status completed` exits non-zero with a pointer at
the new spelling and at `autofix`.

The legacy `closed → completed/canceled` migrator that shipped in
v0.1.4 is removed. If you have data that predates v0.1.4 (status
`closed` with a `resolution` field), run `tq autofix` on v0.1.5
**before** upgrading to v0.2.0 — v0.2.0's `autofix` is forward-only.

### Create surface

- `tq create <title>` — title is now required. No more implicit
  "Untitled".
- `tq create --link <id>` — symmetric, writes both sides.
- `tq create --note <text>` — appends a timestamped note; multiple
  notes in one call share a timestamp (the same UTC instant as the
  ticket's `created` field).

### Short-flag cleanup

- `-T` short for `ls --tag` removed. Use `--tag`.

## Future (not v1)

- `validate` command (lint pass: orphaned deps, malformed frontmatter, out-of-range values)

## Preserved

- Plugin system (`tq-<cmd>` / `tiquette-<cmd>` in PATH)
- `super` command for bypassing plugins
- Ticket file format (YAML frontmatter + markdown body in `.tickets/`)
- Partial ID matching
- ID generation (directory-name prefix + random suffix)
