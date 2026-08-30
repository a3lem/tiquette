# Changelog

## [[Unreleased]]

Driven by a usage analysis of 237 real agent invocations (tiqt-aa0e): most command-surface failures were guesses at a note verb. The surface stays canonical -- the answer is teaching, not aliases.

- changed: `tq show`, `tq info`, and `tq path` accept multiple IDs, validated up front like the transition commands (an unknown or ambiguous ID exits non-zero and prints nothing; repeated IDs display once). `tq deps` stays single-ID.
- changed: `show`/`info` `--json` with multiple IDs emits one JSON array of ticket objects; a single ID keeps the existing single-object shape. (`--jsonl` remains `ls`-only.)
- added: unknown subcommands print a hint that teaches the canonical form -- `tq note ...` → `use: tq edit <id> --note TEXT`, `tq tree ...` → `use: tq ls --parent <id>`, the v1.2-removed verbs map to their `edit` equivalents, and other typos get a closest-match suggestion. Hints are error text; every wrong verb still exits 2.
- changed: the session-priming snippet (`prime.md`) is now policy-only and mandates a `tiquette`-skill load before the first `tq` call; all command-surface teaching moved to the skill, which gains "there is no `note`/`tree`/`-m`" tips and the `ls` mutual-exclusion pairs.
- improved: `--help` documents `prune -t` (short for `--type`) and the `--json` output shape.
- removed: the generated skill no longer documents a plugin system (`tq super`, `tq-<cmd>` executables); it was inherited from another project and never implemented here.

## v0.3.0 – 2026-07-24

- added: global `--dir PATH` option (before the command word) targets the store at `PATH/.tickets`, overriding `TICKETS_DIR` and walk-up. Works for every command; in a monorepo it lets an agent create/read/edit a specific project's tickets without `cd`.
- added: `tq ls -r`/`--recursive` aggregates every `.tickets/` store at or below the root (the `--dir` path, else cwd) into a read-only overview grouped by store path (root store heading `.`). Skips `.git`/`node_modules` and never treats a store's `archive/` as a separate store. Mutually exclusive with `--parent`/`--dep`.
- added: `tq ls -r --jsonl` emits a flat stream of one object per ticket across all stores, each tagged with a `store` field (relative path) — the machine-facing monorepo overview.
- changed: `deps`/`links`/`parent` are documented and enforced as store-local; a relationship target that exists only in another store is rejected as "not found". ID resolution never spans stores.

## v0.2.5 – 2026-07-06

- fixed: `tq show`/`info`/`path`/`deps` no longer fail with `ticket '<id>' not found` on archived tickets; ID resolution and file lookup for these commands now cover `.tickets/archive/` as well as `.tickets/` (tiqt-c4bb)

## v0.2.4 – 2026-05-26

- added: `tq start`/`close`/`cancel`/`reopen` accept `--note TEXT` (repeatable). Each note is appended to the `## Notes` section of every ticket whose status the invocation actually changed, auto-prefixed with a verb tag (`[started]`, `[closed]`, `[canceled]`, `[reopened]`). All notes in one invocation share a timestamp. Cascades via `-f/--force` propagate the same note(s) to every affected descendant. Failed transitions write no notes.
- changed: `tq start`/`close`/`cancel`/`reopen` reject idempotent transitions; an explicitly-named target whose current status already equals the requested target status is rejected with `error: <id> is already <status>`. In a batch, a single already-at-status ticket aborts the whole invocation before any write. `--force` does not bypass this check for the named target (still rejected even if descendants are open).
- changed: ticket timestamps (frontmatter `created` and Notes entries) are now written in minute-precision Zulu form `YYYY-MM-DDTHH:MMZ`. Legacy microsecond+offset timestamps remain readable; run `tq autofix` to normalize them on disk (active and archived).
- improved: `tq --help` now shows `[--note]` in each transition command signature with a one-line description; the short `tq` help stays minimal.
- fixed: `tq autofix` prefix-rename no longer drops `## Notes` or other body content for tickets without an explicit `## Description` heading (tiqt-0896).

## v0.2.3 – 2026-05-22

- added: `tq prune` permanently deletes archived tickets by filter (`-s`/`--status`, `-t`/`--type`, `--before YYYY-MM-DD`); filters AND-combine, at least one is required, and deletion is a dry run unless `-y`/`--yes` is passed

## v0.2.2 – 2026-05-21

- added: `tq start`/`close`/`cancel`/`reopen` accept multiple ticket IDs; IDs are validated up front, so an unknown ID or a descendant-blocked target aborts the whole batch before any write (atomic, fail-fast)

## v0.2.1 – 2026-05-20

- fixed: legacy `status: completed` no longer crashes `tq validate`/`tq ls`/`tq show` with a raw `ValueError` traceback; the error is now a clean diagnostic pointing at `tq autofix` (tiqt-280e)
- fixed: `tq archive` now propagates the "not archivable" constraint through `links` as well as `deps` and `parent`; previously a link-only chain (open A → link → closed B → link → closed C) could archive C while keeping B (tiqt-6e82)
- fixed: malformed ticket files now raise a clear `TicketParseError` (unknown frontmatter keys, missing `: ` separator, id mismatch, unknown types, missing fields) instead of crashing with a raw `TypeError`/`ValueError` (tiqt-de75, tiqt-4e3d, tiqt-8d9f)
- fixed: `read_ticket` title now comes from the first non-empty line after `---` (strips leading `# `); the `## Description` marker is matched as a whole line, not a substring (tiqt-f586)
- fixed: `read_ticket` now filters self-links and self-deps on read, emitting a warning to stderr (tiqt-6deb)
- fixed: `_is_blocked` now treats dangling (unknown) dep IDs as blocking, so `tq ls --ready` and `tq validate` agree on what is actionable (tiqt-5781)
- fixed: `tq ls --dep ""` and `--parent ""` now exit with a clear error instead of silently producing all tickets (tiqt-0fd3)
- fixed: `tq start`/`close`/`cancel`/`reopen` no longer silently swallow a missing-ticket error; it now prints a diagnostic and exits 1 (tiqt-cac3)
- improved: `tq show` dependency-tree view memoizes subtree depths, preventing exponential blowup on wide/shared dependency subtrees (tiqt-6478)
- improved: `tq archive` builds a reverse-reference index once (O(n)) and propagates the "not archivable" constraint in a single pass, replacing the O(n²) iterative convergence loop (tiqt-ea43)

### Code Cleanup

- changed: `_handle_archive` split into `_build_referrer_index`, `_compute_archivable`, and `_move_to_archive` (tiqt-6e82)
- removed: unused `list_ticket_ids` from `store.py` (tiqt-757b)
- changed: `TERMINAL_STATUSES` is now a module-level `frozenset[Status]`; removed `Status.TERMINAL` monkey-patch and three `# type: ignore[attr-defined]` comments (tiqt-dc74)
- changed: `UNSET_TARGETS` moved to `store.py`; `FieldChanges.conflicting_set_and_unset` and `_apply_validated`'s unset block now iterate the tuple instead of hard-coding the three field names (tiqt-e9d6)
- changed: `_abbreviate` renamed to `abbreviate` (public) since it's imported by `commands/autofix.py` (tiqt-855c)
- changed: `tq links` builds sorted link pairs without `tuple(sorted(...))` and dropped the `# type: ignore[arg-type]` (tiqt-8e45)
- changed: `validate` no longer re-globs `archive/` after `load_all_tickets`; it loads active and archived separately and unions them (tiqt-3c26)
- changed: `_ticket_to_dict` return-type annotation is honest; status is coerced to `str` at the boundary (tiqt-0d9b)
- changed: `start`/`close`/`cancel`/`reopen` carry their target `Status` via `set_defaults(target_status=...)`; `_handle_status` dispatches on the enum and `is_terminal()` instead of a four-way string compare on `args.command` (tiqt-d266)
- changed: added a test asserting the `_handle_status` cascade keeps the parent open when `write_ticket` raises between the last descendant and the parent write (parent-last invariant) (tiqt-3914)
- changed: extracted `_required_str`, `_optional_str`, `_required_list` helpers in `store.py`; `read_ticket` no longer repeats the same `isinstance` check eleven times (tiqt-6893)
- changed: extracted `_merge_unique` helper in `store.py` and reused it for the tags/deps/links sections of `_apply_validated` (tiqt-5d5e)
- changed: `_apply_scope` raises `_LsScopeError` instead of `sys.exit`-ing mid-pipeline; the top-level `_handle_ls` handler prints and exits (tiqt-7cf8)
- changed: `_TreePrinter._has_filtered_descendants` renamed to `has_filtered_descendants` since `_handle_ls` calls it from outside the class (tiqt-1069)
- changed: `_handle_deps` no longer defines `_subtree_depth` and `_print_tree` as closures; they are now module-level (`_subtree_depth`) and a dataclass (`_DepTreePrinter`), mirroring the `_TreePrinter` pattern used by `ls` (tiqt-6ee4)
- changed: hoisted function-local `datetime`/`timezone`/`Path` imports in `commands/lifecycle.py` to module level (tiqt-4597)
- changed: `--priority` argparse argument now uses `type=int, choices=range(5)` instead of string choices; removed `VALID_PRIORITIES` constant and manual `int()` conversion in `namespace_to_field_changes` (tiqt-6695)
- changed: replaced private `T._GenericAlias` annotation on all five `register()` signatures with `argparse._SubParsersAction[argparse.ArgumentParser]`; removed `type: ignore` comments and unused `import typing as T` (tiqt-d348)
- changed: `Status` converted from plain string-constant class to `StrEnum`; `Ticket.status` is now typed `Status`; `_checkbox` match is now exhaustive over enum members (tiqt-43f8)
- changed: `is_terminal` now accepts `status: Status` instead of a full `Ticket`; callers updated to pass `t.status` (tiqt-77ba)
- changed: replaced `T.Any` annotations in `store.py` and `cli.py` with concrete types (`_FrontmatterValue` union, `str | Sequence[str] | None`) (tiqt-66f7)
- changed: `has_dep_cycle` is now a pure predicate; signature changed to `(graph, extra_edges)` -- no longer mutates the graph (tiqt-963a)
- changed: `apply_field_changes` split into `_validate_changes` + `_apply_validated`; validation and mutation are now structurally separate (tiqt-bbd8)
- changed: added `iter_tickets` and `load_all_tickets` in `store.py`; all glob-and-parse loops in lifecycle, autofix, validate, and query now route through them (tiqt-c629)
- changed: `_find_open_descendants` returns `dict[str, Ticket]`; `_handle_status` reuses those loaded tickets for the mutation pass instead of re-reading from disk (tiqt-d5f1)
- changed: `resolve_id` now accepts `Iterable[str]` candidates; `resolve_id_in_dir(partial, tickets_dir)` is the directory-based wrapper; `_resolve_in_set` in query.py removed (tiqt-a713)
- changed: added `_resolve_or_exit` helper in query.py; replaces four identical try/except blocks around resolve_id_in_dir (tiqt-86e8)
- changed: added `_ticket_to_dict` helper in query.py; replaces three near-identical JSON serialization literals in show, info, and ls --jsonl (tiqt-07e1)
- changed: `_handle_ls` decomposed into `_select_source`, `_apply_scope`, `_apply_filter`, `_render_flat`, `_render_jsonl`, and `_render_tree`; duplicate sort logic eliminated; `_TreePrinter` dataclass replaces `nonlocal` closure (tiqt-8288, tiqt-ed8c)

## v0.2.0 – 2026-05-17

- changed (BREAKING): per-field mutation verbs removed: `tag`, `untag`, `dep`, `undep`, `nest`, `unnest`, `link`, `unlink`, `assign`, `change-prio`, `change-type`, `describe`, `add-note`, `xref`. No aliases.
- added: `tq edit <id> [field-options]` is the single post-creation mutation surface. Accepts every `create` field-option plus `--title`, `--untag`, `--undep`, `--unlink`, and `--unset {parent,xref,assignee}`. Setting and unsetting the same field in one call is rejected.
- changed (BREAKING): terminal status renamed `completed` → `closed`. `tq close` now writes `status: closed`. The verb and stored value match.
- added: `tq autofix` unconditionally rewrites legacy `status: completed` → `status: closed`. Idempotent.
- changed (BREAKING): the legacy `closed → completed/canceled` autofix migrator (from v0.1.4) is removed; under v1.2 `closed` is again the terminal status. Users on pre-v0.1.4 data must run `autofix` on a v0.1.4/v0.1.5 release before upgrading.
- changed (BREAKING): `tq create <title>` — title is now a required positional. The implicit "Untitled" default is gone.
- added: `tq create --link <id>` (symmetric, repeatable) and `tq create --note <text>` (timestamped at creation, repeatable). Both also valid on `tq edit`.
- changed (BREAKING): `tq ls --tag` short `-T` removed. Use `--tag`.
- changed: `tq ls --status completed` now exits non-zero with a message pointing at `autofix` and the `closed` spelling.

## v0.1.5 – 2026-05-04

- added: `tq ls --parent <id>` scopes the listing to a ticket and its transitive descendants, rendered as a tree rooted at `<id>`. The named root is shown as a context heading when it doesn't itself satisfy stacked filters. Stacks with all other filters.
- added: `tq ls --dep <id>` lists tickets whose `deps` directly contain `<id>`, rendered as a flat list. Direct dependents only -- transitive chains are excluded. Stacks with all other filters.
- added: `--parent` and `--dep` are mutually exclusive with each other.

## v0.1.4 – 2026-04-30

- changed (BREAKING): `closed` status no longer exists. The two terminal statuses are now `completed` (via `tq close`) and `canceled` (via `tq cancel`).
- changed (BREAKING): `tq close` sets `status: completed` directly; `tq cancel` sets `status: canceled`. The `resolution` field is removed entirely.
- changed (BREAKING): `tq ls --completed` and `tq ls --canceled` flags removed. Use `tq ls -s completed` or `tq ls -s canceled` (`-s` is short for `--status`).
- added: `tq autofix` migrates legacy `closed` tickets: `closed+resolution:canceled` → `canceled`, all other `closed` → `completed`. Strips stray `resolution` fields from non-closed tickets.

## v0.1.3 – 2026-04-30

- changed (BREAKING): `tq cancel` now rejects a ticket with open descendants (parity with `tq close`). Pass `-f` / `--force` to cascade-cancel the whole subtree.
- added: `tq close -f` / `--force` to cascade-close a parent and all open descendants as `completed`.
- changed (BREAKING): `tq ls` renders canceled tickets as `[~]` instead of `[x]`. `[x]` now means "closed, completed" only.
- added: `tq ls --archived` lists only archived tickets.
- added: `tq ls --all` (short: `-a`) lists active and archived tickets together. Mirrors `ls -a`.
- changed (BREAKING): `tq ls` short flag for `--assignee` is now `-A` (was `-a`). Use `-A "Alice"` or `--assignee "Alice"`.
- changed (BREAKING): `tq create` short flag for `--assignee` is now `-A` (was `-a`), matching `tq ls`.

## v0.1.2 – 2026-04-28

- changed: ticket ID prefix is now an abbreviation (max 4 chars) of the project directory name. Multi-token names use first letters of each token; single-token names use the first 4 characters; short multi-token names fill from the trailing characters of the last token.
- changed: prefix prefers a consonant in the 4th position. If the candidate 4th char is a vowel, scan further chars for a consonant; if none, fall back to a 3-char prefix (or accept the vowel if char 3 is also a vowel).
- added: `tq autofix` maintenance command that reconciles tickets with current behavior. Renames tickets with stale ID prefixes, propagating the new IDs into every `parent`, `deps`, and `links` reference (including archived tickets) so nothing is orphaned.
- fixed: `tq ls` now includes closed tickets by default. Previously the default filter hid `closed` status.

## v0.1.0 — 2026-04-27

Initial release of `tiquette` (`tq`), a Python reimplementation of the `ticket` (`tk`) bash CLI.

### Ticket lifecycle

- `tq create <title>` creates a ticket file in `.tickets/`, printing the generated ID to stdout. The ID uses the current directory name as prefix with a 4-hex suffix (e.g. `myproject-a9f9`).
- Supports all creation flags: `-p` (priority 0–4), `-t` (type), `-a` (assignee), `-d` (description), `--tag`, `--dep`, `--parent`, `--xref`.
- `tq start`, `close`, `cancel`, `reopen` transition ticket status. Note: these commands currently produce no output on success (ticket ID is not echoed).
- `tq close` rejects a parent with open descendants, printing the blocking child IDs to stderr.
- Closing the last open child of a parent prints a notification: `note: <parent-id> has no remaining open children`.
- After `tq reopen`, the `resolution` field is set to `null` in the file rather than being removed.

### Listing and filtering

- `tq ls` renders tickets as an indented tree using box-drawing characters for parent-child relationships. Children appear under their parent with `└──` connectors.
- Line format: `<id> [tags] - [checkbox] <title> <- [deps]`. Priority and type tags are hidden when they are the defaults (priority 2, type "task").
- Checkboxes: `[ ]` open, `[/]` in_progress, `[x]` closed.
- `--ready` shows only tickets with no open deps and no open children. A parent with open children is implicitly blocked. Closed deps count as satisfied.
- `--blocked` shows tickets with at least one open dep or open child. Parents appear as context headings with their blocked children indented.
- `--status <value>` filters by status. In filtered tree views, non-matching parents appear as unlabelled context headings.
- `--assignee` and `--tag` filters work (long form only; `-a` and `-T` short flags are not available).
- `--type`, `--limit`, `--sort`, `--jsonl` flags supported.

### Relationships

- `tq dep` / `tq undep`: add/remove blocking dependencies with cycle detection.
- `tq nest` / `tq unnest`: set/clear parent-child relationships.
- `tq link` / `tq unlink`: bidirectional symmetric links.
- Cycle detection rejects both direct and transitive cycles.

### Other commands

- `tq show <id>`: full ticket content with computed sections (Blockers, Blocking, Children, Linked).
- `tq info <id>`: frontmatter and relationships only, no body.
- `tq deps <id>`: transitive dependency tree with box-drawing characters.
- `tq path <id>`: prints the ticket file path.
- `tq tags`: tag frequency list for open/in-progress tickets.
- `tq links`: all linked pairs across the store.
- `tq archive`: moves closed tickets to `.tickets/archive/`, skipping any referenced by open tickets (with stderr diagnostics). Cascading block detection prevents archiving closed tickets that are deps of blocked-from-archiving tickets.
- `tq validate`: ticket store validation.
- Partial ID resolution: `tq show 9a50` resolves to the matching full ID.

### Storage

- Tickets are markdown files with YAML frontmatter in `.tickets/`.
- The `.tickets/` directory is created automatically on first `tq create`.
- The tickets directory can be overridden with the `TICKETS_DIR` environment variable.
