# Field Mutations

Exercise all the field-editing commands and verify they persist correctly.

## Setup

Create a single ticket: "Tracking field changes" with defaults.

## Steps

1. Assign it to "alice". Verify `show` displays the assignee.
2. Clear the assignee (run `assign` with no second argument). Verify it's gone.
3. Change priority to 0. Verify `show` reflects it.
4. Change type to "bug". Verify.
5. Add tags "api" and "urgent". Verify both appear.
6. Remove tag "urgent". Verify only "api" remains.
7. Set an xref to "JIRA-42". Verify.
8. Clear the xref (run `xref` with no second argument). Verify.
9. Set a description with `describe`. Verify it appears in `show`.
10. Add two notes with `add-note`. Verify both appear in order with timestamps.
11. Run `tags` to see the global tag summary. "api" should appear with count 1.

## What to watch for

- Clearing optional fields (assignee, xref) leaves them null, not empty string.
- Tags are additive (`tag`) and subtractive (`untag`), not replacement.
- Notes are append-only with ISO timestamps.
- `describe` replaces the description entirely, not appends.
