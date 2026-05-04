# Tasks: Split Closed Status

Each phase is a single commit that leaves the suite green.

## Phase 1 — Schema

- [x] Drop `resolution` from `Ticket` dataclass and `_NULLABLE_FIELDS` in `store.py`
- [x] Update status enum constants to `{open, in_progress, completed, canceled}`
- [x] Add `TERMINAL_STATUSES` constant and `is_terminal()` helper in `store.py`
- [x] Frontmatter reader silently ignores stray `resolution` keys
- [x] Frontmatter writer never emits `resolution`
- [x] Update `test_store.py` to drop resolution coverage and add terminal-status coverage

## Phase 2 — Lifecycle commands

- [x] `close` sets `status = "completed"` directly; no resolution write
- [x] `cancel` sets `status = "canceled"` directly; no resolution write
- [x] `reopen` sets `status = "open"`; no resolution clear
- [x] Replace `t.status != "closed"` checks with `not is_terminal(t)` in descendant/sibling logic
- [x] Force-cascade assigns the parent's terminal status to non-terminal descendants
- [x] Update `test_cli_lifecycle.py` for new statuses and absence of `resolution` field

## Phase 3 — Query commands

- [x] `VALID_STATUSES` updated; `--status` accepts the four-value enum
- [x] Add `-s` as short alias for `--status` in `ls`
- [x] Remove `--completed` and `--canceled` argparse entries
- [x] Collapse the `--completed`/`--canceled` dispatch branch into a single status filter
- [x] `_checkbox()` derives glyph from `status` alone (four-way match)
- [x] `archive` uses `is_terminal()` for eligibility; update diagnostic strings ("No closed tickets ..." → "No completed or canceled tickets ...")
- [x] `tags` listing uses `is_terminal()` to exclude terminal tickets
- [x] `show`/`info` JSON output drops the `resolution` field
- [x] `show` plain output drops the `resolution:` line
- [x] Update `test_cli_query.py` accordingly

## Phase 4 — CLI help and docs

- [x] Update short help (cli.py top-of-file)
- [x] Update long help reference block (cli.py command help section)
- [x] Update `docs/cli-design.md`
- [x] Update `test_cli_help.py` if it asserts on changed lines

## Phase 5 — Autofix migration

- [x] Add migration rule in `commands/autofix.py`: closed → completed/canceled based on resolution; missing resolution → completed
- [x] Strip stray `resolution` from non-closed tickets
- [x] Apply to active tickets and archived tickets
- [x] Emit summary line (`- Migrated N ticket(s) from closed status` or `- Stripped resolution from N ticket(s)`)
- [x] Idempotent — second run reports no fixes
- [x] Update `test_cli_autofix.py`

## Phase 6 — Release prep

- [x] CHANGELOG.md entry under `## [Unreleased]` covering the breaking changes and the autofix migration
- [x] Bump version per project's "zero-ver" convention
- [x] Run full pytest suite and `tq autofix` against `.tickets/` in this repo to dogfood the migration

## Verification

One task per requirement in the deltas. Each task is done when the requirement has at least one annotated test.

### ticket-lifecycle

- [x] Tests for requirement: Close command (modified)
- [x] Tests for requirement: Cancel command (modified)
- [x] Tests for requirement: Reopen command (modified)

### ticket-query

- [x] Tests for requirement: List tickets (modified)
- [x] Tests for requirement: List ticket line format (modified)
- [x] Tests for requirement: Archive (modified)
- [x] Tests for requirement: List source axis (modified)

### ticket-store

- [x] Tests for requirement: Ticket file format (modified)

### ticket-autofix

- [x] Tests for requirement: Migrate legacy closed status (added)

## Notes

- Phases 1–4 require changes-in-lockstep with their tests so each commit leaves the suite green.
- `autofix` is the migration path; users running the new build on legacy `.tickets/` should be told (CHANGELOG) to run `tq autofix` once.
- Reader silently ignores stray `resolution` so partial migration doesn't break reads.
