# Proposal: Spec `create`'s dep/link/parent resolution as active-only

## Why

`specs/reference/id-resolution/spec.md`'s "ID resolution across commands" requirement enumerates the mutation commands whose ID resolution stays active-only as `edit`, `start`, `close`, `cancel`, `reopen` -- it omits `create`, even though `ticket-lifecycle`'s "Create ticket" requirement says `create` reuses `ticket-edit`'s dep/link/parent field-options. `id-resolution`'s own overview line ("used by all commands that accept ticket IDs") is a blanket claim the enumeration doesn't back up for `create`.

This was surfaced as a non-blocking inter-spec reservation by `spexl-spec-critic` while merging the `lookup-archived-tickets` change (2026-07-06), which is what made the read/write command split explicit for the first time. The user has confirmed the gap should be closed: the spec should explicitly rule out `create`'s dep/link/parent targets resolving against archived tickets.

Verified against the actual code first: `src/tiquette/commands/lifecycle.py`'s `_handle_create` calls `apply_field_changes` -- the same function `edit.py` calls -- which resolves `--dep`/`--link`/`--parent` targets via `resolve_id_in_dir` (active-only) inside `store.py`'s `_validate_changes`. So `tq create --dep <archived-only-id>` already fails today, identically to `edit`. This is a spec-and-test gap, not a runtime bug -- no production code changes.

## What Changes

- `id-resolution`'s "ID resolution across commands" requirement adds `create` (and its dep/link/parent targets) to the active-only enumeration, alongside `edit`/`start`/`close`/`cancel`/`reopen`.
- Adds a scenario proving `tq create --dep <archived-only-id>` does not resolve, mirroring the existing `edit --dep` scenario.
- `ticket-lifecycle`'s "Create ticket" requirement gets a one-line cross-reference to `id-resolution`'s active-only rule, so a reader of `ticket-lifecycle` alone isn't left to guess. The mechanic itself (the SHALL rule + scenario) lives once, in `id-resolution`, per the "don't duplicate cross-cutting scenarios" guidance -- `ticket-lifecycle` just points at it.

## Capabilities

### Modified Capabilities

- `id-resolution`: "ID resolution across commands" now names `create` explicitly as active-only.
- `ticket-lifecycle`: "Create ticket" cross-references the active-only resolution rule.

## Impact

- `specs/reference/id-resolution/spec.md` and `specs/reference/ticket-lifecycle/spec.md` only.
- `tests/test_cli_edit.py` (or a new lifecycle test file) gets one new test for the `create --dep` archive-only-rejection scenario.
- No changes to `src/tiquette/**` -- the behavior this documents already exists.

## Out of Scope

- The broader "thin coverage" reservation the critic also raised (no scenario tests `edit <archive-only-id>` itself, or `start`/`close`/`cancel`/`reopen` rejecting an archive-only ID) -- the user asked specifically about the `create` gap (tiqt-fc56); the broader coverage gap is a separate concern, not addressed here.
