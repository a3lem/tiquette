# Tasks: CLI redesign v1.2

Implementation follows the six phases in `design.md`. Each phase ends
with `pytest` green; pause-friendly at every phase boundary.

## Phase 1 — Status rename (`completed` → `closed`)

- [x] Add `Status` class to `store.py` (open / in_progress / closed /
      canceled / TERMINAL frozenset)
- [x] Replace internal `"completed"` literals with `Status.CLOSED`
      across `src/tiquette/`
- [x] Update `commands/query.py` `--status` choices; reject
      `completed` with autofix hint
- [x] Update `commands/lifecycle.py` `close` writes `closed`
- [x] Add unconditional `completed → closed` migrator to
      `commands/autofix.py`
- [x] Update `commands/validate.py` terminal-state checks
- [x] Update test fixtures and assertions across the suite for
      `closed`
- [x] Update `tests/test-drives/01-basic-lifecycle.md` and
      `10-scoping-by-parent-and-dep.md` for the new vocab

## Phase 2 — `edit` command alongside legacy verbs

- [x] Add `src/tiquette/commands/_fields.py` with shared field-flag
      schema (`add_create_flags`, `add_edit_flags`)
- [x] Add `FieldChanges` dataclass and `apply_field_changes` in
      `store.py`
- [x] Refactor `create` handler to build `FieldChanges` and call
      `apply_field_changes`
- [x] Add `src/tiquette/commands/edit.py` with set/unset conflict
      check, symmetric `--link`/`--unlink`, `--unset
      {parent,xref,assignee}`
- [x] Wire `edit` registration into `cli.py`; add `edit` block to
      HELP_TEXT
- [x] Add `tests/test_cli_edit.py` covering every flag,
      repeatability, conflict cases, `--title`, multi-field
      invocations, atomicity

## Phase 3 — `--link`/`--note` on create; required title

- [x] Add `--link` and `--note` to create handler (via shared schema)
- [x] Implement symmetric link writes from `create`
- [x] Make `title` positional required; remove "Untitled" default
- [x] Update `tests/test_cli_lifecycle.py` for required title,
      create-with-link, create-with-note

## Phase 4 — Delete legacy verbs

- [x] Delete `src/tiquette/commands/fields.py`
- [x] Delete `src/tiquette/commands/content.py`
- [x] Strip mutation handlers from
      `src/tiquette/commands/relationships.py`; relocate cycle-check
      to where `edit --dep`/`--parent` invokes it
- [x] Remove deleted-verb `register()` calls from `cli.py`
- [x] Delete `tests/test_cli_fields.py`
- [x] Delete `tests/test_cli_content.py`
- [x] Trim `tests/test_cli_relationships.py` to read-only and
      cycle-detection coverage

## Phase 5 — Help text, README, SKILL, short flags

- [x] Rewrite `HELP_TEXT` and `HELP_SUMMARY` to match
      `docs/cli-design-v1.2.md`
- [x] Remove `-T` short for `ls --tag`
- [x] Update `tests/test_cli_help.py`
- [x] Run `shablon` to regenerate `README.md` and SKILL outputs
- [x] Edit hand-written sections of
      `.shablon/templates/skills/tiquette/SKILL.md` (Resolution row,
      checkbox legend, `tq nest`/`tq dep`/`tq ls --completed`
      examples, replace verb examples with `edit`)

## Phase 6 — Test drives, docs, changelog, version

- [x] Rewrite `tests/test-drives/05-field-mutations.md` for `edit`
- [x] Spot-check other test-drives for legacy verb invocations
- [x] Replace `docs/cli-design.md` body with v1.2; delete or rename
      `docs/cli-design-v1.2.md`
- [x] Append "v1.1 → v1.2" section to `docs/migration-notes.md`
- [x] Update `docs/architecture.md` references to per-field command
      modules
- [x] Spot-check `docs/ethos.md`
- [x] Add dated section to `CHANGELOG.md`
- [x] Bump `project.version` in `pyproject.toml`

## Verification

One task per requirement; each requires at least one annotated test
proving the behavior.

- [x] Test for `ticket-edit / Edit command`
- [x] Test for `ticket-edit / Rename via --title`
- [x] Test for `ticket-edit / Description replace via --description`
- [x] Test for `ticket-edit / Notes append via --note`
- [x] Test for `ticket-edit / Tag add/remove`
- [x] Test for `ticket-edit / Dependency add/remove`
- [x] Test for `ticket-edit / Link add/remove`
- [x] Test for `ticket-edit / Parent set via --parent`
- [x] Test for `ticket-edit / Single-value field clear via --unset`
- [x] Test for `ticket-edit / Set/unset conflict`
- [x] Test for `ticket-edit / Type and priority via --type / --priority`
- [x] Test for `ticket-edit / External reference via --xref`
- [x] Test for `ticket-edit / Atomicity`
- [x] Test for `ticket-lifecycle / Create ticket` (incl. required
      title, --link, --note)
- [x] Test for `ticket-lifecycle / Close command` (closed vocab)
- [x] Test for `ticket-lifecycle / Cancel command` (closed vocab)
- [x] Test for `ticket-lifecycle / Reopen command` (closed vocab)
- [x] Test for `ticket-lifecycle / Transition output` (closed vocab)
- [x] Test for `ticket-relationships / Cycle detection` (triggered
      from `edit`/`create`)
- [x] Test for `ticket-query / List tickets` (closed vocab, -T gone)
- [x] Test for `ticket-query / List ticket line format` (closed
      glyph)
- [x] Test for `ticket-query / Tags listing` (closed vocab)
- [x] Test for `ticket-query / Archive` (closed vocab)
- [x] Test for `ticket-autofix / Migrate completed status to closed`
- [x] Test for `ticket-store / Ticket file format` (closed vocab,
      `--unset assignee`)

## Notes

- The shablon template `tq --help` block regenerates automatically
  once `cli.py` is updated — run `shablon` after phase 5.
- Phase 1 must ship its autofix migrator together; do not merge the
  status rename without the migration path.
- The capability collapse (REMOVE `ticket-fields` and
  `ticket-content`, slim `ticket-relationships`) takes effect at
  archive time, not during implementation.
