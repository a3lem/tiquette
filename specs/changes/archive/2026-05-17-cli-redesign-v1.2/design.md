# Design: CLI redesign v1.2

## Context

`tq` today exposes a separate verb for every field-level mutation. The
verbs share no machinery: each has its own subparser, its own handler
function, and its own helper in `store.py`. Adding a field means touching
three places. Multi-field edits require multiple invocations, each of
which re-reads, re-validates, and re-writes the ticket file.

v1.2 takes the orthogonal view: there is one mutation surface (`edit`)
and one creation surface (`create`); both share a single vocabulary of
field-flags. The per-verb subparsers and handlers go away. In their place,
a single field-flag schema lives in one module and is reused by both
parsers.

The change also resolves a long-standing vocabulary wart: the verb is
`close` but the stored status is `completed`. v1.2 renames the status to
`closed`. This breaks every ticket file currently on disk; `autofix` is
extended to perform the one-shot rewrite.

Reference: `docs/cli-design-v1.2.md` (the user-facing spec), and
`docs/v1.2-implementation-map.md` (the exhaustive inventory of touched
files).

## Goals / Non-Goals

### Goals

- One mutation surface (`edit`) with the same field-flag vocabulary as
  `create`.
- Single source of truth for the field-flag schema, so adding a new
  field is one edit, not three.
- Status vocabulary aligned with the verb: `close` → `closed`.
- One-shot, unconditional migration of legacy `status: completed` →
  `status: closed` via `autofix`.
- Clear, mechanical phasing so the work can be paused at any phase
  boundary with the test suite green.

### Non-Goals

- CLI-level back-compat. Removed verbs return a parser error, not a
  deprecation warning. Users on the old CLI run `autofix` once and then
  re-learn the verbs.
- Touching the on-disk ticket format beyond the `status` rename.
- Interactive `edit` (drop into `$EDITOR`). Out of scope; can come
  later behind its own flag.
- Changing read-only listings (`deps`, `links`, `tags`, `show`, `info`,
  `path`).

## Decisions

### D1. Field-flag schema lives in one module

A new module `src/tiquette/commands/_fields.py` (leading underscore =
internal) exports two functions: `add_create_flags(parser)` and
`add_edit_flags(parser)`. Both call a shared `_add_shared_field_flags`
that registers `-d/--description`, `-t/--type`, `-p/--priority`,
`-A/--assignee`, `--xref`, `--parent`, `--tag` (repeatable),
`--dep` (repeatable), `--link` (repeatable), `--note` (repeatable).
`add_edit_flags` then additionally registers `--title`, `--untag`,
`--undep`, `--unlink`, and `--unset` (choices = `{parent, xref,
assignee}`, repeatable).

**Alternatives considered:** keeping the flag set inline in each parser
(today's pattern) is what we're escaping; using a class hierarchy was
considered and rejected as overkill — two functions and a private helper
is the simplest expression of "shared schema, one extension."

### D2. Single dispatch path for field mutations

Both `create` and `edit` resolve the argparse namespace into the same
`FieldChanges` dataclass:

```python
@dataclass
class FieldChanges:
    title: str | None              # edit only; None = no change
    description: str | None        # None = no change
    type: str | None
    priority: int | None
    assignee: str | None
    xref: str | None
    parent: str | None
    add_tags: list[str]
    remove_tags: list[str]         # edit only
    add_deps: list[str]
    remove_deps: list[str]         # edit only
    add_links: list[str]
    remove_links: list[str]        # edit only
    notes: list[str]               # append-only
    unset_fields: set[str]         # subset of {parent, xref, assignee}
```

A single `apply_field_changes(ticket, changes)` function in `store.py`
applies the dataclass to a `Ticket` in memory. `create` builds a fresh
`Ticket` then applies the changes; `edit` reads the ticket, applies, and
writes back. One code path for both, with one round of validation.

**Alternatives considered:** two parallel code paths (today's pattern)
duplicate validation and risk drift. A `**kwargs` shape is too loose for
basedpyright.

### D3. Set/unset conflict is parser-level, not handler-level

Detected after `parse_args` but before dispatch. If `changes.unset_fields`
intersects with the fields that were also set, exit non-zero with stderr
`error: cannot both set and unset '<field>' in one call`. Reuse argparse's
exit-2 convention.

**Alternatives considered:** detecting later in `apply_field_changes`
would work but would couple the store layer to argparse error-reporting.

### D4. `--note` timestamp policy

On `create`: the note's timestamp is the same UTC instant used for the
ticket's `created` field (one `datetime.now(timezone.utc)` per
invocation, reused). On `edit`: each `edit` invocation gets one
timestamp shared by every `--note` in that invocation (consistent with
how multiple `--note` flags read like "these notes were added together").

**Alternatives considered:** per-note timestamps would imply ordering
guarantees we don't have; per-call shared timestamp matches the
"transactional edit" framing.

### D5. `--link` on `create` is symmetric

Same atomic-write pattern as the former standalone `link` command: write
the new ticket with the link in its frontmatter, then patch the target
ticket(s) to back-reference. If the target write fails, roll back the new
ticket file. This is the existing two-phase write in
`store.add_link`, just driven from a different entry point.

### D6. Status migration is unconditional in `autofix`

`autofix` already runs over every ticket file. We add one new fixer that,
for any ticket where `status == "completed"`, rewrites it to `closed`.
No flag, no opt-in, no warning. The rationale: this is a vocabulary
rename with zero behavioral impact; running it twice is a no-op; gating
it would mean shipping the breaking change but not the fix.

### D7. Vocabulary constants

The status enum moves to a single `Status` class in `store.py`:

```python
class Status:
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    CANCELED = "canceled"
    TERMINAL = frozenset({CLOSED, CANCELED})
```

Every literal `"completed"` in the codebase becomes either `Status.CLOSED`
or, in test fixtures, the literal `"closed"`. The rename is mechanical
but exhaustive: see grep results in §3 of the implementation map.

### D8. `--unset description` is intentionally absent

The `--unset` enum is `{parent, xref, assignee}`. Description is not a
target: emptying a body is ambiguous (drop the section vs. set to empty
string) and the operation is unlikely to be needed. The workaround is
direct file editing via `tq path <id>`.

### D9. README and SKILL templates regenerate from `tq --help`

Shablon already calls `tq --help` at template-render time
(`.shablon/vars.py:11`). Once `cli.py`'s help strings are updated,
running `shablon` regenerates the README's help block and the
SKILL.md help block. Hand-written sections of the SKILL template still
need targeted edits — they're called out in §5 of the implementation
map.

## Phases

The change is large but partitions cleanly. Each phase ends with the
test suite green and the CLI usable; you can pause at any boundary.

### Phase 1 — Vocabulary rename (`completed` → `closed`)

**Goal:** Land the status rename as a standalone change first. This is
the highest-risk piece (touches every ticket file on disk) and isolating
it makes the subsequent edit-consolidation phases purely additive at the
storage layer.

**Steps**

1. Add `Status` class to `store.py` with `CLOSED = "closed"`. Keep
   `"completed"` accepted on read (back-compat in the parser) but write
   only `"closed"`.
2. Replace every internal literal `"completed"` with `Status.CLOSED`
   across `src/tiquette/`. Replace every test fixture that writes
   `status: completed` with `closed`.
3. Update `commands/query.py` so `--status` accepts `closed`. (Reject
   `completed` with an error pointing at `autofix`.)
4. Update `commands/lifecycle.py` so `close` writes `closed`.
5. Update `commands/autofix.py` to rewrite any on-disk
   `status: completed` to `closed`. Unconditional.
6. Update `commands/validate.py` terminal-state checks.
7. Update test fixtures and assertions across the whole test suite for
   the new vocabulary. Add an autofix test that proves the migration.

**Done when:** `pytest` is green; `tq autofix` on a repo with legacy
`completed` tickets rewrites them; `tq ls --status closed` works;
`tq ls --status completed` exits non-zero with a clear pointer to
`autofix`.

**Risk:** any place that reads `status` without going through the new
constant. Mitigation: grep for the literal `"completed"` after the phase
and ensure the only remaining hits are the autofix migrator and tests
that exercise it.

### Phase 2 — Create the `edit` command alongside the old verbs

**Goal:** introduce `edit` as a working command without removing
anything yet. This phase is purely additive — every old verb still
works. Lets `edit` be exercised in isolation before the deletion phase.

**Steps**

1. Add `src/tiquette/commands/_fields.py` (D1): shared field-flag
   schema with `add_create_flags(parser)` and `add_edit_flags(parser)`.
2. Define `FieldChanges` dataclass (D2) in `store.py` (or a new
   `commands/_field_changes.py` if it fits better) plus
   `apply_field_changes(ticket, changes)`.
3. Refactor `commands/lifecycle.py`'s `create` handler to build a
   `FieldChanges` and call `apply_field_changes` against a fresh
   ticket. Behavior unchanged.
4. Add `commands/edit.py`. Register `edit <id> [flags]`. Implements the
   set/unset conflict check (D3). Reads the ticket, applies field
   changes, writes back. Reuses the symmetric-link logic for `--link`
   and `--unlink` (D5).
5. Wire the edit registration into `cli.py`. Add the `edit` section to
   `HELP_TEXT`. Old verbs are still listed.
6. Add `tests/test_cli_edit.py` exercising every flag, including
   repeatability, `--unset`, the conflict error, set+unset same-field
   error, `--title`, and multi-field invocations.

**Done when:** `pytest` is green; `tq edit <id> --tag foo --priority 0
--note 'hi' --unset assignee` works and yields the same ticket state as
the equivalent sequence of legacy verbs.

**Risk:** divergence between the legacy verbs and `edit`. Mitigation:
the legacy verbs already call the same `store.py` helpers; route
`apply_field_changes` through those helpers so both paths share the
ground truth.

### Phase 3 — Add `--link` and `--note` to `create`; make title required

**Goal:** finish the `create` surface so it matches `edit`'s
vocabulary. Small phase, mechanical.

**Steps**

1. Add `--link` and `--note` flags via the shared schema (already
   wired in phase 2). `create` handler builds a `FieldChanges` that
   may include initial notes and initial links.
2. Implement the symmetric link writes from `create` (D5).
3. Change the `title` positional to required. Update help text and
   examples.
4. Update `tests/test_cli_lifecycle.py` for the required-title
   requirement and add coverage for create-with-link and
   create-with-note.

**Done when:** `pytest` is green; `tq create 'foo' --link other-id
--note 'kickoff'` creates a linked, annotated ticket atomically.

**Risk:** the required-title change breaks any existing scripts that
called `tq create` to interactively prompt. None known.

### Phase 4 — Delete the old verbs

**Goal:** flip the cutover. Every per-field mutation verb goes away in
one commit.

**Steps**

1. Delete `commands/fields.py` and `commands/content.py`.
2. Strip mutation handlers from `commands/relationships.py`; keep only
   what `deps` and `links` listings need (those live in `query.py`
   today, so this module may end up empty — if so, delete it and drop
   the cycle-detection logic into `store.py` or `_fields.py` wherever
   it's invoked from `edit --dep`).
3. Remove the `register()` calls for the deleted verb groups from
   `cli.py`. Strip the verb listings from `HELP_TEXT` and
   `HELP_SUMMARY`.
4. Delete `tests/test_cli_fields.py` and `tests/test_cli_content.py`.
5. Reduce `tests/test_cli_relationships.py` to read-only and cycle
   coverage; move any still-relevant mutation cases into
   `test_cli_edit.py` (most should already exist there from phase 2).

**Done when:** `pytest` is green; `tq tag`, `tq nest`, `tq describe`,
etc. all exit non-zero with argparse's "invalid choice" error.

**Risk:** users may have scripts. The migration notes in phase 6 cover
that.

### Phase 5 — Help text, README, SKILL, and short-flag cleanup

**Goal:** scrub user-facing surfaces to match the new CLI.

**Steps**

1. Rewrite `HELP_TEXT` and `HELP_SUMMARY` in `cli.py` to match
   `docs/cli-design-v1.2.md` exactly.
2. Remove the `-T` short for `ls --tag`.
3. Update `tests/test_cli_help.py` for the new strings.
4. Run `shablon` to regenerate `README.md` and the SKILL template
   outputs. Verify the regenerated files.
5. Edit the hand-written sections of
   `.shablon/templates/skills/tiquette/SKILL.md` — see §5 of the
   implementation map for the exact lines (Resolution row,
   checkbox-glyph legend, `tq nest`/`tq dep`/`tq ls --completed`
   examples). Replace verb examples with `edit` equivalents.

**Done when:** `pytest` is green; `tq --help` matches the design doc;
README and SKILL.md regenerated.

### Phase 6 — Test drives, docs, changelog, version

**Goal:** finish the surrounding artifacts.

**Steps**

1. Rewrite `tests/test-drives/05-field-mutations.md` for `edit`.
2. Update `tests/test-drives/01-basic-lifecycle.md` (resolution
   wording) and `tests/test-drives/10-scoping-by-parent-and-dep.md`
   (status vocab). Spot-check other test-drives for old verb
   invocations.
3. Replace `docs/cli-design.md` with the v1.2 body; delete
   `docs/cli-design-v1.2.md` (or rename it in place — git can track
   the move).
4. Append a "v1.1 → v1.2" section to `docs/migration-notes.md` covering
   removed verbs, the `edit` consolidation, the status rename, the
   `autofix` one-shot migration, and the `-T` short removal.
5. Update `docs/architecture.md` "Project Structure" / "Key Design
   Decisions" references to the per-field command modules. Spot-check
   `docs/ethos.md`.
6. Add a `## [Unreleased]` → dated section in `CHANGELOG.md`.
7. Bump `project.version` in `pyproject.toml` (0.x minor bump).

**Done when:** every file in the implementation map has been touched
and verified; `pytest` is green; `shablon` regenerates a fresh
README/SKILL with no drift.

## Risks / Trade-offs / Limitations

- **Risk:** Phase 1 leaves the codebase in a state where two status
  vocabularies briefly coexist (the parser accepts `completed` on
  read, writes `closed`). → **Mitigation:** time-bound this — phase 1
  ships the autofix that closes the loop; don't merge phase 1 without
  phase 1's autofix.
- **Risk:** divergence between legacy verbs and `edit` during phase 2.
  → **Mitigation:** route both through `store.apply_field_changes`;
  legacy verbs become thin shims calling the same code path.
- **Trade-off:** No deprecation period for removed verbs. Justified by
  the small user base (single-user tooling) and the loud failure mode
  (argparse rejects with a clear error). A deprecation period would
  double the surface area for one release.
- **Limitation:** The set/unset conflict check (D3) is per-call only;
  there's no way to express "unset, then set" in one invocation. This
  is intentional — that pattern is two `edit` calls, and conflating
  them invites bugs.
- **Limitation:** `--unset description` is absent (D8). Users who hit
  this case use `tq path <id>` and edit the file. A future change can
  add it if real demand appears.

## Open Questions

None remaining — the implementation map's §7 resolved them all.
