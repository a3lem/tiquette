# Proposal: Cross-reference active-only ID resolution in `ticket-edit`

## Why

The `create-resolves-active-only` change (archived 2026-07-06) added a cross-reference to `id-resolution`'s active-only rule in `ticket-lifecycle`'s "Create ticket" requirement, but not in `ticket-edit`. That's backwards: `ticket-lifecycle`'s own text says `create` "accept[s] the field-options defined by `ticket-edit`" -- so `ticket-edit` is the canonical spec a reader lands on to find out what `--dep`/`--link`/`--parent` actually do, and it says nothing about active-only resolution. `spexl-spec-critic` flagged this during that change's inter-spec review as the reason to hold back approval; closing it was deferred to a follow-up rather than block that change further.

## What Changes

- `ticket-edit`'s "Dependency add/remove", "Link add/remove", and "Parent set via --parent" requirements each get a one-line cross-reference to `id-resolution`'s "ID resolution across commands" requirement, mirroring the sentence `ticket-lifecycle`'s "Create ticket" requirement already has.
- No behavior change, no code change -- `resolve_id_in_dir` (active-only) already backs `edit`'s `--dep`/`--link`/`--parent` targets; this only documents it in the one place a reader is directed to for their definition.

## Capabilities

### Modified Capabilities

- `ticket-edit`: three requirements gain a pointer to the active-only resolution rule.

## Impact

- `specs/reference/ticket-edit/spec.md` only. No code, no new tests -- `tests/test_cli_edit.py::test_edit_dep_does_not_resolve_archive_only_id` (added by `lookup-archived-tickets`) already exercises this exact behavior for `--dep`; the cross-reference just makes the spec match what the code (and that existing test) already do.
