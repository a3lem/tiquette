# Proposal: Fix CLI Output Gaps

## Problem

A test-drive of scenarios 01 (basic lifecycle) and 07 (listing and filtering) against the
current implementation revealed three behavioral gaps:

1. **Transition commands are silent.** `tq start`, `close`, `cancel`, and `reopen` print nothing
   on success. The test-drive notes and general CLI convention expect the ticket ID to be echoed
   so callers (humans and scripts alike) can confirm which ticket was affected.

2. **`resolution: null` persists after reopen.** The spec's reopen scenario explicitly states the
   ticket "has no `resolution` field" after reopening. The implementation sets `resolution = None`
   and serializes it as `resolution: null`, violating that requirement. The same is true for all
   nullable fields (`assignee`, `parent`, `xref`): the spec says cleared fields leave no trace in
   the file, but the serializer always writes every field.

3. **`ls` is missing `-a` and `-T` short flags.** `--assignee` and `--tag` work on `ls` but have
   no short forms. The `create` command already uses `-a` for `--assignee`; consistency and
   test-drive usability call for the same aliases on `ls`.

## Intent

- Bring `start`, `close`, `cancel`, and `reopen` in line with the CLI convention of echoing the
  affected ticket ID to stdout.
- Fix the serializer to omit nullable fields when their value is null, so reopening a ticket
  (and clearing any other nullable field) leaves no `null` trace in the file.
- Add `-a` / `-T` as short aliases for `--assignee` / `--tag` on `ls`.

## Capabilities

- `ticket-lifecycle` — ADDED requirement for transition output (all four transition commands)
- `ticket-store` — MODIFIED file format requirement (nullable fields omitted when null)
- `ticket-query` — MODIFIED ls (add `-a` and `-T` short aliases)

## Notes

Gap 3 (short flags) is a usability convenience, not a behavioral spec requirement. The spec
scenarios already use the long forms. The delta is included here for completeness and consistency
with `create`.
