# Changelog

## [Unreleased]

- fixed: `_subtree_depth` in `tq show` tree view now memoizes results, preventing exponential blowup on wide/shared dependency subtrees (tiqt-6478)

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
